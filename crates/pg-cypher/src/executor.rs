//! Cypher query executor.
//!
//! Evaluates a parsed Cypher AST against a `PersonalGraph`.
//! Each MATCH clause produces a stream of "bindings" (variable → value maps),
//! which WHERE filters, and RETURN/SET/DELETE consume.

use std::collections::HashMap;

use ordered_float::OrderedFloat;
use pg_core::graph::{Edge, Node};
use pg_core::id::NodeId;
use pg_core::property::{Property, PropertyMap};
use pg_graph::PersonalGraph;
use serde::Serialize;

use crate::ast::*;
use crate::{CypherError, Result};

// ── Public types ─────────────────────────────────────────────────────────────

/// A single output row.
pub type Row = HashMap<String, Value>;

/// Results from executing a query.
#[derive(Debug, Serialize)]
pub struct QueryResult {
    pub columns: Vec<String>,
    pub rows: Vec<Row>,
    /// Nodes created/modified
    pub nodes_affected: usize,
    /// Edges created/modified
    pub edges_affected: usize,
}

// ── Value type ───────────────────────────────────────────────────────────────

#[derive(Debug, Clone, PartialEq, Serialize)]
pub enum Value {
    Null,
    Bool(bool),
    Int(i64),
    Float(f64),
    Str(String),
    Node(Node),
    Edge(Edge),
    List(Vec<Value>),
    Map(HashMap<String, Value>),
    Path(Vec<NodeId>),
}

impl Value {
    pub fn truthy(&self) -> bool {
        match self {
            Value::Null           => false,
            Value::Bool(b)        => *b,
            Value::Int(n)         => *n != 0,
            Value::Float(f)       => *f != 0.0,
            Value::Str(s)         => !s.is_empty(),
            Value::List(l)        => !l.is_empty(),
            _                     => true,
        }
    }

    pub fn as_str(&self) -> Option<&str> {
        match self { Value::Str(s) => Some(s), _ => None }
    }

    fn partial_cmp_val(&self, other: &Self) -> Option<std::cmp::Ordering> {
        match (self, other) {
            (Value::Int(a),   Value::Int(b))   => a.partial_cmp(b),
            (Value::Float(a), Value::Float(b)) => a.partial_cmp(b),
            (Value::Int(a),   Value::Float(b)) => (*a as f64).partial_cmp(b),
            (Value::Float(a), Value::Int(b))   => a.partial_cmp(&(*b as f64)),
            (Value::Str(a),   Value::Str(b))   => Some(a.cmp(b)),
            _                                   => None,
        }
    }
}

// ── Binding environment ───────────────────────────────────────────────────────

type Bindings = HashMap<String, Value>;

// ── Engine ────────────────────────────────────────────────────────────────────

pub struct CypherEngine<'a> {
    graph: &'a mut PersonalGraph,
}

impl<'a> CypherEngine<'a> {
    pub fn new(graph: &'a mut PersonalGraph) -> Self {
        Self { graph }
    }

    pub fn execute(&mut self, query: &Query) -> Result<QueryResult> {
        let mut bindings_set: Vec<Bindings> = vec![HashMap::new()];
        let mut nodes_affected = 0;
        let mut edges_affected = 0;
        let mut result: Option<QueryResult> = None;

        for clause in &query.clauses {
            match clause {
                Clause::Match(m) | Clause::OptionalMatch(m) => {
                    let optional = matches!(clause, Clause::OptionalMatch(_));
                    let mut next = Vec::new();
                    for b in &bindings_set {
                        let mut expanded = self.execute_match(m, b.clone())?;
                        if expanded.is_empty() && optional {
                            expanded.push(b.clone());
                        }
                        next.extend(expanded);
                    }
                    bindings_set = next;
                }

                Clause::Create(c) => {
                    for b in &mut bindings_set {
                        let (n, e) = self.execute_create(c, b)?;
                        nodes_affected += n;
                        edges_affected += e;
                    }
                }

                Clause::Merge(c) => {
                    for b in &mut bindings_set {
                        let (n, e) = self.execute_merge(c, b)?;
                        nodes_affected += n;
                        edges_affected += e;
                    }
                }

                Clause::Delete(d) | Clause::DetachDelete(d) => {
                    let detach = matches!(clause, Clause::DetachDelete(_));
                    for b in &bindings_set {
                        let (n, e) = self.execute_delete(d, b, detach)?;
                        nodes_affected += n;
                        edges_affected += e;
                    }
                }

                Clause::Set(s) => {
                    for b in &mut bindings_set {
                        let n = self.execute_set(s, b)?;
                        nodes_affected += n;
                    }
                }

                Clause::Remove(r) => {
                    for b in &mut bindings_set {
                        self.execute_remove(r, b)?;
                    }
                }

                Clause::Return(ret) => {
                    result = Some(self.execute_return(ret, &mut bindings_set)?);
                }

                Clause::With(w) => {
                    bindings_set = self.execute_with(w, bindings_set)?;
                }

                Clause::Unwind(u) => {
                    let mut next = Vec::new();
                    for b in &bindings_set {
                        let val = self.eval_expr(&u.expr, b)?;
                        match val {
                            Value::List(items) => {
                                for item in items {
                                    let mut nb = b.clone();
                                    nb.insert(u.var.clone(), item);
                                    next.push(nb);
                                }
                            }
                            _ => {
                                let mut nb = b.clone();
                                nb.insert(u.var.clone(), val);
                                next.push(nb);
                            }
                        }
                    }
                    bindings_set = next;
                }
            }
        }

        Ok(result.unwrap_or(QueryResult {
            columns: Vec::new(),
            rows: Vec::new(),
            nodes_affected,
            edges_affected,
        }))
    }

    // ── MATCH ─────────────────────────────────────────────────────────────────

    fn execute_match(&self, m: &MatchClause, seed: Bindings) -> Result<Vec<Bindings>> {
        let mut binding_sets = vec![seed];

        for pattern in &m.patterns {
            let mut next = Vec::new();
            for b in binding_sets {
                let expanded = self.match_pattern(pattern, b)?;
                next.extend(expanded);
            }
            binding_sets = next;
        }

        // Apply WHERE
        if let Some(cond) = &m.where_expr {
            binding_sets.retain(|b| self.eval_expr(cond, b).map(|v| v.truthy()).unwrap_or(false));
        }

        Ok(binding_sets)
    }

    fn match_pattern(&self, pattern: &Pattern, seed: Bindings) -> Result<Vec<Bindings>> {
        // Check for variable-length hop pattern
        let has_variable_hops = pattern.hops.iter().any(|(e, _)| e.hops != HopSpec::One);

        if has_variable_hops {
            return self.match_variable_hops(pattern, seed);
        }

        // Resolve or scan the start node
        let start_candidates = self.resolve_node_pattern(&pattern.start, &seed)?;

        let mut results = Vec::new();
        for (start_node, mut b) in start_candidates {
            if let Some(v) = &pattern.start.var {
                b.insert(v.clone(), Value::Node(start_node.clone()));
            }

            // If no hops, just yield the start node binding
            if pattern.hops.is_empty() {
                results.push(b);
                continue;
            }

            // BFS through hops
            let expanded = self.match_hops(&pattern.hops, start_node.id, b)?;
            results.extend(expanded);
        }

        Ok(results)
    }

    fn resolve_node_pattern(
        &self,
        np: &NodePattern,
        bindings: &Bindings,
    ) -> Result<Vec<(Node, Bindings)>> {
        // If already bound to a node, use it
        if let Some(var) = &np.var {
            if let Some(Value::Node(n)) = bindings.get(var) {
                if self.node_matches_pattern(n, np) {
                    return Ok(vec![(n.clone(), bindings.clone())]);
                } else {
                    return Ok(Vec::new());
                }
            }
        }

        // Scan by label if provided, else scan all
        let candidates = if let Some(label) = np.labels.first() {
            self.graph.find_by_label(label).map_err(|e| CypherError::Graph(e.to_string()))?
        } else {
            // No label filter — we'd need a full scan. For now collect via all known labels.
            // In a real system this would be a heap scan.
            self.full_node_scan()?
        };

        let mut out = Vec::new();
        for node in candidates {
            // Check all labels
            if np.labels.len() > 1 {
                // For multi-label we need all labels to match. We only support single label for now.
                // TODO: multi-label nodes
            }
            // Check property predicates
            if !self.node_matches_pattern(&node, np) { continue; }
            out.push((node, bindings.clone()));
        }
        Ok(out)
    }

    fn node_matches_pattern(&self, node: &Node, np: &NodePattern) -> bool {
        // Label match
        if let Some(label) = np.labels.first() {
            if node.data.label != *label { return false; }
        }
        // Property predicates
        for (k, v_expr) in &np.props {
            let expected = match self.eval_expr(v_expr, &HashMap::new()) {
                Ok(v) => v,
                Err(_) => return false,
            };
            let actual = prop_to_value(node.data.properties.get(k));
            if !values_eq(&actual, &expected) { return false; }
        }
        true
    }

    fn match_hops(
        &self,
        hops: &[(EdgePattern, NodePattern)],
        current_node_id: NodeId,
        bindings: Bindings,
    ) -> Result<Vec<Bindings>> {
        if hops.is_empty() {
            return Ok(vec![bindings]);
        }
        let (edge_pat, node_pat) = &hops[0];
        let rest = &hops[1..];

        // Find edges from current node per direction
        let edges = self.edges_for_direction(current_node_id, edge_pat.direction)?;

        let mut results = Vec::new();
        for edge in edges {
            // Check edge type filter
            if !edge_pat.types.is_empty() && !edge_pat.types.contains(&edge.data.label) {
                continue;
            }
            // Edge property predicates
            if !self.edge_matches_pattern(&edge, edge_pat) { continue; }

            // Get the other node
            let next_node_id = if edge_pat.direction == Direction::Incoming {
                edge.source
            } else {
                edge.target
            };

            let next_node = match self.graph.get_node(next_node_id)
                .map_err(|e| CypherError::Graph(e.to_string()))?
            {
                Some(n) => n,
                None    => continue,
            };

            if !self.node_matches_pattern(&next_node, node_pat) { continue; }

            let mut b = bindings.clone();
            if let Some(ev) = &edge_pat.var {
                b.insert(ev.clone(), Value::Edge(edge));
            }
            if let Some(nv) = &node_pat.var {
                b.insert(nv.clone(), Value::Node(next_node.clone()));
            }

            let expanded = self.match_hops(rest, next_node_id, b)?;
            results.extend(expanded);
        }
        Ok(results)
    }

    fn edge_matches_pattern(&self, edge: &Edge, ep: &EdgePattern) -> bool {
        for (k, v_expr) in &ep.props {
            let expected = match self.eval_expr(v_expr, &HashMap::new()) {
                Ok(v) => v,
                Err(_) => return false,
            };
            let actual = prop_to_value(edge.data.properties.get(k));
            if !values_eq(&actual, &expected) { return false; }
        }
        true
    }

    fn edges_for_direction(&self, id: NodeId, dir: Direction) -> Result<Vec<Edge>> {
        let mut edges = Vec::new();
        match dir {
            Direction::Outgoing => {
                edges.extend(self.graph.out_edges(id).map_err(|e| CypherError::Graph(e.to_string()))?);
            }
            Direction::Incoming => {
                edges.extend(self.graph.in_edges(id).map_err(|e| CypherError::Graph(e.to_string()))?);
            }
            Direction::Either => {
                edges.extend(self.graph.out_edges(id).map_err(|e| CypherError::Graph(e.to_string()))?);
                edges.extend(self.graph.in_edges(id).map_err(|e| CypherError::Graph(e.to_string()))?);
            }
        }
        Ok(edges)
    }

    fn match_variable_hops(&self, pattern: &Pattern, seed: Bindings) -> Result<Vec<Bindings>> {
        // For variable-length hops, do BFS up to max depth.
        // Only handle patterns with exactly one variable-hop edge for now.
        if pattern.hops.len() != 1 {
            return Err(CypherError::Exec("variable-length hops only supported in single-hop patterns".into()));
        }
        let (edge_pat, end_pat) = &pattern.hops[0];
        let HopSpec::Variable(min_opt, max_opt) = &edge_pat.hops else {
            unreachable!()
        };
        let min = min_opt.unwrap_or(1) as usize;
        let max = max_opt.unwrap_or(10) as usize; // default max 10 for safety

        let start_candidates = self.resolve_node_pattern(&pattern.start, &seed)?;
        let mut results = Vec::new();

        for (start_node, mut b) in start_candidates {
            if let Some(v) = &pattern.start.var {
                b.insert(v.clone(), Value::Node(start_node.clone()));
            }

            // BFS
            let mut frontier = vec![(start_node.id, 0usize, vec![start_node.id])];
            while let Some((cur_id, depth, path)) = frontier.pop() {
                if depth > max { continue; }
                let edges = self.edges_for_direction(cur_id, edge_pat.direction)?;
                for edge in edges {
                    let next_id = if edge_pat.direction == Direction::Incoming { edge.source } else { edge.target };
                    if path.contains(&next_id) { continue; } // no cycles
                    let next_node = match self.graph.get_node(next_id)
                        .map_err(|e| CypherError::Graph(e.to_string()))? {
                        Some(n) => n, None => continue,
                    };
                    let new_depth = depth + 1;
                    let mut new_path = path.clone();
                    new_path.push(next_id);

                    if new_depth >= min && self.node_matches_pattern(&next_node, end_pat) {
                        let mut nb = b.clone();
                        if let Some(ev) = &end_pat.var {
                            nb.insert(ev.clone(), Value::Node(next_node.clone()));
                        }
                        if let Some(pv) = &pattern.path_var {
                            nb.insert(pv.clone(), Value::Path(new_path.clone()));
                        }
                        results.push(nb);
                    }
                    if new_depth < max {
                        frontier.push((next_id, new_depth, new_path));
                    }
                }
            }
        }
        Ok(results)
    }

    // ── CREATE ────────────────────────────────────────────────────────────────

    fn execute_create(&mut self, c: &CreateClause, b: &mut Bindings) -> Result<(usize, usize)> {
        let mut nodes = 0;
        let mut edges = 0;
        for pattern in &c.patterns {
            let (n, e) = self.create_pattern(pattern, b)?;
            nodes += n; edges += e;
        }
        Ok((nodes, edges))
    }

    fn create_pattern(&mut self, pattern: &Pattern, b: &mut Bindings) -> Result<(usize, usize)> {
        let mut nodes = 0;
        let mut edges = 0;

        // Create start node if not already bound
        let start_id = self.create_or_resolve_node(&pattern.start, b)?;
        if pattern.start.var.is_none() || !b.contains_key(pattern.start.var.as_deref().unwrap_or("")) {
            nodes += 1;
        }

        let mut prev_id = start_id;
        for (edge_pat, node_pat) in &pattern.hops {
            let next_id = self.create_or_resolve_node(node_pat, b)?;
            nodes += 1;

            // Create the edge
            let (source, target) = match edge_pat.direction {
                Direction::Incoming => (next_id, prev_id),
                _                   => (prev_id, next_id),
            };

            let label = edge_pat.types.first().cloned().unwrap_or_else(|| "RELATED".into());
            let props = self.eval_prop_map(&edge_pat.props, b)?;
            self.graph.add_edge(source, target, &label, props)
                .map_err(|e| CypherError::Graph(e.to_string()))?;
            edges += 1;

            if let Some(ev) = &edge_pat.var {
                // store edge ref in bindings — skip for now (no edge type in Value yet)
                let _ = ev;
            }
            prev_id = next_id;
        }
        Ok((nodes, edges))
    }

    fn create_or_resolve_node(&mut self, np: &NodePattern, b: &mut Bindings) -> Result<NodeId> {
        // If already bound to an existing node, reuse it
        if let Some(var) = &np.var {
            if let Some(Value::Node(n)) = b.get(var) {
                return Ok(n.id);
            }
        }
        let label = np.labels.first().cloned().unwrap_or_else(|| "Node".into());
        let props = self.eval_prop_map(&np.props, b)?;
        let id = self.graph.add_node(&label, props).map_err(|e| CypherError::Graph(e.to_string()))?;
        if let Some(var) = &np.var {
            let node = self.graph.get_node(id)
                .map_err(|e| CypherError::Graph(e.to_string()))?
                .ok_or_else(|| CypherError::Exec("just-created node missing".into()))?;
            b.insert(var.clone(), Value::Node(node));
        }
        Ok(id)
    }

    // ── MERGE ─────────────────────────────────────────────────────────────────

    fn execute_merge(&mut self, c: &CreateClause, b: &mut Bindings) -> Result<(usize, usize)> {
        // MERGE = find if exists, create if not
        let mut nodes = 0;
        let mut edges = 0;
        for pattern in &c.patterns {
            // Try to match first
            let dummy_match = MatchClause { patterns: vec![pattern.clone()], where_expr: None };
            let existing = self.execute_match(&dummy_match, b.clone())?;
            if existing.is_empty() {
                let (n, e) = self.create_pattern(pattern, b)?;
                nodes += n; edges += e;
            }
        }
        Ok((nodes, edges))
    }

    // ── DELETE ────────────────────────────────────────────────────────────────

    fn execute_delete(&mut self, d: &DeleteClause, b: &Bindings, _detach: bool) -> Result<(usize, usize)> {
        let mut nodes = 0;
        let mut edges = 0;
        for expr in &d.exprs {
            match self.eval_expr(expr, b)? {
                Value::Node(n) => {
                    self.graph.delete_node(n.id).map_err(|e| CypherError::Graph(e.to_string()))?;
                    nodes += 1;
                }
                Value::Edge(e) => {
                    self.graph.delete_edge(e.source, e.target).map_err(|e| CypherError::Graph(e.to_string()))?;
                    edges += 1;
                }
                _ => return Err(CypherError::Exec("DELETE requires a node or edge".into())),
            }
        }
        Ok((nodes, edges))
    }

    // ── SET ───────────────────────────────────────────────────────────────────

    fn execute_set(&mut self, s: &SetClause, b: &mut Bindings) -> Result<usize> {
        let mut count = 0;
        for item in &s.items {
            match item {
                SetItem::Property { var, key, value } => {
                    let val = self.eval_expr(value, b)?;
                    if let Some(Value::Node(node)) = b.get(var).cloned() {
                        let mut props = node.data.properties.clone();
                        props.insert(key.clone(), value_to_prop(val));
                        self.graph.update_node(node.id, &node.data.label, props.clone())
                            .map_err(|e| CypherError::Graph(e.to_string()))?;
                        // Refresh binding
                        if let Some(n) = self.graph.get_node(node.id)
                            .map_err(|e| CypherError::Graph(e.to_string()))? {
                            b.insert(var.clone(), Value::Node(n));
                        }
                        count += 1;
                    }
                }
                SetItem::Labels { .. } => {
                    // Label changes not yet supported
                }
            }
        }
        Ok(count)
    }

    // ── REMOVE ────────────────────────────────────────────────────────────────

    fn execute_remove(&mut self, r: &RemoveClause, b: &mut Bindings) -> Result<()> {
        for item in &r.items {
            match item {
                RemoveItem::Property { var, key } => {
                    if let Some(Value::Node(node)) = b.get(var).cloned() {
                        let mut props = node.data.properties.clone();
                        props.remove(key);
                        self.graph.update_node(node.id, &node.data.label, props)
                            .map_err(|e| CypherError::Graph(e.to_string()))?;
                    }
                }
                RemoveItem::Label { .. } => {}
            }
        }
        Ok(())
    }

    // ── RETURN ────────────────────────────────────────────────────────────────

    fn execute_return(&self, ret: &ReturnClause, bindings_set: &mut Vec<Bindings>) -> Result<QueryResult> {
        // Compute rows
        let mut rows: Vec<Row> = bindings_set
            .iter()
            .map(|b| self.project_return(b, &ret.items))
            .collect::<Result<Vec<_>>>()?;

        // DISTINCT
        if ret.distinct {
            let mut seen = std::collections::HashSet::new();
            rows.retain(|r| {
                let key = format!("{:?}", r.iter().collect::<std::collections::BTreeMap<_, _>>());
                seen.insert(key)
            });
        }

        // ORDER BY
        if !ret.order_by.is_empty() {
            let order_by = ret.order_by.clone();
            let bindings_ref = &bindings_set;
            // We sort rows together with their binding for eval
            let mut indexed: Vec<(usize, Row)> = rows.into_iter().enumerate().collect();
            indexed.sort_by(|(ai, _), (bi, _)| {
                let ba = bindings_ref.get(*ai).cloned().unwrap_or_default();
                let bb = bindings_ref.get(*bi).cloned().unwrap_or_default();
                for item in &order_by {
                    let va = self.eval_expr(&item.expr, &ba).unwrap_or(Value::Null);
                    let vb = self.eval_expr(&item.expr, &bb).unwrap_or(Value::Null);
                    let ord = va.partial_cmp_val(&vb).unwrap_or(std::cmp::Ordering::Equal);
                    let ord = if item.descending { ord.reverse() } else { ord };
                    if ord != std::cmp::Ordering::Equal { return ord; }
                }
                std::cmp::Ordering::Equal
            });
            rows = indexed.into_iter().map(|(_, r)| r).collect();
        }

        // SKIP
        if let Some(skip_expr) = &ret.skip {
            let skip = match self.eval_expr(skip_expr, &HashMap::new())? {
                Value::Int(n) => n as usize,
                _ => return Err(CypherError::Type("SKIP requires integer".into())),
            };
            if skip < rows.len() { rows = rows[skip..].to_vec(); } else { rows.clear(); }
        }

        // LIMIT
        if let Some(limit_expr) = &ret.limit {
            let limit = match self.eval_expr(limit_expr, &HashMap::new())? {
                Value::Int(n) => n as usize,
                _ => return Err(CypherError::Type("LIMIT requires integer".into())),
            };
            rows.truncate(limit);
        }

        // Column names from first row or return items
        let columns = ret.items.iter().map(|item| {
            item.alias.clone().unwrap_or_else(|| match &item.expr {
                Expr::Var(v) => v.clone(),
                Expr::Prop(v, k) => format!("{}.{}", v, k),
                Expr::Call(f, _) => f.clone(),
                _ => "?".into(),
            })
        }).collect();

        Ok(QueryResult { columns, rows, nodes_affected: 0, edges_affected: 0 })
    }

    fn project_return(&self, b: &Bindings, items: &[ReturnItem]) -> Result<Row> {
        let mut row = Row::new();
        for item in items {
            if matches!(item.expr, Expr::Star) {
                for (k, v) in b { row.insert(k.clone(), v.clone()); }
                continue;
            }
            let val = self.eval_expr(&item.expr, b)?;
            let col = item.alias.clone().unwrap_or_else(|| match &item.expr {
                Expr::Var(v)      => v.clone(),
                Expr::Prop(v, k)  => format!("{}.{}", v, k),
                Expr::Call(f, _)  => f.clone(),
                _                 => "col".into(),
            });
            row.insert(col, val);
        }
        Ok(row)
    }

    // ── WITH ──────────────────────────────────────────────────────────────────

    fn execute_with(&self, w: &WithClause, bindings_set: Vec<Bindings>) -> Result<Vec<Bindings>> {
        let mut next = Vec::new();
        for b in &bindings_set {
            let row = self.project_return(b, &w.items)?;
            // Convert projected row back to bindings
            let mut nb = Bindings::new();
            for (k, v) in row { nb.insert(k, v); }
            next.push(nb);
        }
        if let Some(cond) = &w.where_expr {
            next.retain(|b| self.eval_expr(cond, b).map(|v| v.truthy()).unwrap_or(false));
        }
        Ok(next)
    }

    // ── Expression evaluator ──────────────────────────────────────────────────

    fn eval_expr(&self, expr: &Expr, b: &Bindings) -> Result<Value> {
        match expr {
            Expr::Null       => Ok(Value::Null),
            Expr::Bool(v)    => Ok(Value::Bool(*v)),
            Expr::Int(n)     => Ok(Value::Int(*n)),
            Expr::Float(f)   => Ok(Value::Float(*f)),
            Expr::Str(s)     => Ok(Value::Str(s.clone())),
            Expr::Star       => Ok(Value::Null), // handled above
            Expr::List(items) => {
                let vals = items.iter().map(|e| self.eval_expr(e, b)).collect::<Result<Vec<_>>>()?;
                Ok(Value::List(vals))
            }
            Expr::Map(m) => {
                let mut out = HashMap::new();
                for (k, v) in m { out.insert(k.clone(), self.eval_expr(v, b)?); }
                Ok(Value::Map(out))
            }
            Expr::Var(name) => {
                Ok(b.get(name).cloned().unwrap_or(Value::Null))
            }
            Expr::Prop(var, key) => {
                match b.get(var) {
                    Some(Value::Node(n)) => Ok(prop_to_value(n.data.properties.get(key))),
                    Some(Value::Edge(e)) => Ok(prop_to_value(e.data.properties.get(key))),
                    Some(Value::Map(m))  => Ok(m.get(key).cloned().unwrap_or(Value::Null)),
                    _                    => Ok(Value::Null),
                }
            }
            Expr::BinOp(op, l, r) => {
                let lv = self.eval_expr(l, b)?;
                // short-circuit
                match op {
                    BinOp::And => if !lv.truthy() { return Ok(Value::Bool(false)); }
                    BinOp::Or  => if  lv.truthy() { return Ok(Value::Bool(true)); }
                    _ => {}
                }
                let rv = self.eval_expr(r, b)?;
                Ok(apply_binop(*op, lv, rv)?)
            }
            Expr::Not(inner) => {
                let v = self.eval_expr(inner, b)?;
                Ok(Value::Bool(!v.truthy()))
            }
            Expr::IsNull(inner, expect_non_null) => {
                let v = self.eval_expr(inner, b)?;
                let is_null = matches!(v, Value::Null);
                Ok(Value::Bool(if *expect_non_null { !is_null } else { is_null }))
            }
            Expr::In(needle, haystack) => {
                let n = self.eval_expr(needle, b)?;
                let h = self.eval_expr(haystack, b)?;
                match h {
                    Value::List(items) => Ok(Value::Bool(items.iter().any(|i| values_eq(i, &n)))),
                    _                  => Ok(Value::Bool(false)),
                }
            }
            Expr::StringOp(op, l, r) => {
                let lv = self.eval_expr(l, b)?;
                let rv = self.eval_expr(r, b)?;
                match (lv.as_str(), rv.as_str()) {
                    (Some(ls), Some(rs)) => Ok(Value::Bool(match op {
                        StringOp::Contains   => ls.contains(rs),
                        StringOp::StartsWith => ls.starts_with(rs),
                        StringOp::EndsWith   => ls.ends_with(rs),
                    })),
                    _ => Ok(Value::Bool(false)),
                }
            }
            Expr::Call(name, args) => self.call_function(name, args, b),
            Expr::Case { input, branches, default } => {
                let input_val = if let Some(e) = input { Some(self.eval_expr(e, b)?) } else { None };
                for (cond, then) in branches {
                    let matches = if let Some(ref iv) = input_val {
                        values_eq(iv, &self.eval_expr(cond, b)?)
                    } else {
                        self.eval_expr(cond, b)?.truthy()
                    };
                    if matches { return self.eval_expr(then, b); }
                }
                if let Some(d) = default { self.eval_expr(d, b) } else { Ok(Value::Null) }
            }
        }
    }

    // ── Built-in functions ────────────────────────────────────────────────────

    fn call_function(&self, name: &str, args: &[Expr], b: &Bindings) -> Result<Value> {
        let vals: Vec<Value> = args.iter().map(|e| self.eval_expr(e, b)).collect::<Result<Vec<_>>>()?;
        match name {
            "id" => match vals.first() {
                Some(Value::Node(n)) => Ok(Value::Str(n.id.to_string())),
                Some(Value::Edge(e)) => Ok(Value::Str(format!("{}->{}", e.source, e.target))),
                _ => Ok(Value::Null),
            },
            "labels" => match vals.first() {
                Some(Value::Node(n)) => Ok(Value::List(vec![Value::Str(n.data.label.clone())])),
                _ => Ok(Value::Null),
            },
            "type" => match vals.first() {
                Some(Value::Edge(e)) => Ok(Value::Str(e.data.label.clone())),
                _ => Ok(Value::Null),
            },
            "properties" => match vals.first() {
                Some(Value::Node(n)) => {
                    let mut m = HashMap::new();
                    for (k, v) in &n.data.properties { m.insert(k.clone(), prop_to_value(Some(v))); }
                    Ok(Value::Map(m))
                }
                _ => Ok(Value::Null),
            },
            "count" => Ok(Value::Int(vals.len() as i64)),
            "size"  => match vals.first() {
                Some(Value::List(l)) => Ok(Value::Int(l.len() as i64)),
                Some(Value::Str(s))  => Ok(Value::Int(s.len() as i64)),
                _ => Ok(Value::Int(0)),
            },
            "tostring" | "tostring()" => match vals.first() {
                Some(v) => Ok(Value::Str(format!("{:?}", v))),
                _ => Ok(Value::Null),
            },
            "tointeger" => match vals.first() {
                Some(Value::Int(n))   => Ok(Value::Int(*n)),
                Some(Value::Float(f)) => Ok(Value::Int(*f as i64)),
                Some(Value::Str(s))   => Ok(s.parse::<i64>().map(Value::Int).unwrap_or(Value::Null)),
                _ => Ok(Value::Null),
            },
            "tofloat" => match vals.first() {
                Some(Value::Float(f)) => Ok(Value::Float(*f)),
                Some(Value::Int(n))   => Ok(Value::Float(*n as f64)),
                Some(Value::Str(s))   => Ok(s.parse::<f64>().map(Value::Float).unwrap_or(Value::Null)),
                _ => Ok(Value::Null),
            },
            "abs"  => match vals.first() {
                Some(Value::Int(n))   => Ok(Value::Int(n.abs())),
                Some(Value::Float(f)) => Ok(Value::Float(f.abs())),
                _ => Ok(Value::Null),
            },
            "ceil"  => match vals.first() { Some(Value::Float(f)) => Ok(Value::Float(f.ceil())), _ => Ok(Value::Null) },
            "floor" => match vals.first() { Some(Value::Float(f)) => Ok(Value::Float(f.floor())), _ => Ok(Value::Null) },
            "round" => match vals.first() { Some(Value::Float(f)) => Ok(Value::Float(f.round())), _ => Ok(Value::Null) },
            "sqrt"  => match vals.first() { Some(Value::Float(f)) => Ok(Value::Float(f.sqrt())), _ => Ok(Value::Null) },
            "head"  => match vals.first() { Some(Value::List(l)) => Ok(l.first().cloned().unwrap_or(Value::Null)), _ => Ok(Value::Null) },
            "last"  => match vals.first() { Some(Value::List(l)) => Ok(l.last().cloned().unwrap_or(Value::Null)), _ => Ok(Value::Null) },
            "tail"  => match vals.first() {
                Some(Value::List(l)) => Ok(Value::List(l.get(1..).unwrap_or(&[]).to_vec())),
                _ => Ok(Value::Null),
            },
            "reverse" => match vals.first() {
                Some(Value::List(l)) => { let mut r = l.clone(); r.reverse(); Ok(Value::List(r)) }
                Some(Value::Str(s))  => Ok(Value::Str(s.chars().rev().collect())),
                _ => Ok(Value::Null),
            },
            "coalesce" => Ok(vals.into_iter().find(|v| !matches!(v, Value::Null)).unwrap_or(Value::Null)),
            "exists" => Ok(Value::Bool(!matches!(vals.first(), Some(Value::Null) | None))),
            "keys" => match vals.first() {
                Some(Value::Node(n)) => Ok(Value::List(n.data.properties.keys().map(|k| Value::Str(k.clone())).collect())),
                Some(Value::Map(m))  => Ok(Value::List(m.keys().map(|k| Value::Str(k.clone())).collect())),
                _ => Ok(Value::Null),
            },
            "nodes" => match vals.first() {
                Some(Value::Path(p)) => Ok(Value::List(p.iter().map(|id| Value::Str(id.to_string())).collect())),
                _ => Ok(Value::Null),
            },
            "length" => match vals.first() {
                Some(Value::Path(p)) => Ok(Value::Int((p.len() as i64).saturating_sub(1))),
                Some(Value::List(l)) => Ok(Value::Int(l.len() as i64)),
                Some(Value::Str(s))  => Ok(Value::Int(s.len() as i64)),
                _ => Ok(Value::Int(0)),
            },
            "toupper" => match vals.first() { Some(Value::Str(s)) => Ok(Value::Str(s.to_uppercase())), _ => Ok(Value::Null) },
            "tolower" => match vals.first() { Some(Value::Str(s)) => Ok(Value::Str(s.to_lowercase())), _ => Ok(Value::Null) },
            "trim"    => match vals.first() { Some(Value::Str(s)) => Ok(Value::Str(s.trim().to_owned())), _ => Ok(Value::Null) },
            "ltrim"   => match vals.first() { Some(Value::Str(s)) => Ok(Value::Str(s.trim_start().to_owned())), _ => Ok(Value::Null) },
            "rtrim"   => match vals.first() { Some(Value::Str(s)) => Ok(Value::Str(s.trim_end().to_owned())), _ => Ok(Value::Null) },
            "split"   => match (vals.get(0), vals.get(1)) {
                (Some(Value::Str(s)), Some(Value::Str(d))) => {
                    Ok(Value::List(s.split(d.as_str()).map(|p| Value::Str(p.to_owned())).collect()))
                }
                _ => Ok(Value::Null),
            },
            "substring" => match (vals.get(0), vals.get(1)) {
                (Some(Value::Str(s)), Some(Value::Int(start))) => {
                    let st = *start as usize;
                    let end = vals.get(2).and_then(|v| if let Value::Int(n) = v { Some(*n as usize) } else { None });
                    let slice = if let Some(len) = end {
                        &s[st.min(s.len())..(st + len).min(s.len())]
                    } else {
                        &s[st.min(s.len())..]
                    };
                    Ok(Value::Str(slice.to_owned()))
                }
                _ => Ok(Value::Null),
            },
            _ => Err(CypherError::Exec(format!("unknown function: {}", name))),
        }
    }

    // ── Helpers ───────────────────────────────────────────────────────────────

    fn full_node_scan(&self) -> Result<Vec<Node>> {
        // Without a label, we can't efficiently scan.
        // Return empty for now — callers should provide labels.
        // A real system would maintain a "all nodes" list.
        Ok(Vec::new())
    }

    fn eval_prop_map(&self, map: &PropMap, b: &Bindings) -> Result<PropertyMap> {
        let mut out = PropertyMap::new();
        for (k, v) in map {
            out.insert(k.clone(), value_to_prop(self.eval_expr(v, b)?));
        }
        Ok(out)
    }
}

// ── Free helpers ─────────────────────────────────────────────────────────────

fn prop_to_value(p: Option<&Property>) -> Value {
    match p {
        None                     => Value::Null,
        Some(Property::Null)     => Value::Null,
        Some(Property::Bool(b))  => Value::Bool(*b),
        Some(Property::Int(n))   => Value::Int(*n),
        Some(Property::Float(f)) => Value::Float(f.into_inner()),
        Some(Property::String(s)) => Value::Str(s.clone()),
        Some(Property::Bytes(_)) => Value::Null,
        Some(Property::List(l))  => Value::List(l.iter().map(|p| prop_to_value(Some(p))).collect()),
        Some(Property::Map(m))   => {
            Value::Map(m.iter().map(|(k, v)| (k.clone(), prop_to_value(Some(v)))).collect())
        }
    }
}

fn value_to_prop(v: Value) -> Property {
    match v {
        Value::Null       => Property::Null,
        Value::Bool(b)    => Property::Bool(b),
        Value::Int(n)     => Property::Int(n),
        Value::Float(f)   => Property::Float(OrderedFloat(f)),
        Value::Str(s)     => Property::String(s),
        Value::List(l)    => Property::List(l.into_iter().map(value_to_prop).collect()),
        _                 => Property::Null,
    }
}

fn values_eq(a: &Value, b: &Value) -> bool {
    match (a, b) {
        (Value::Null, Value::Null)       => true,
        (Value::Bool(x), Value::Bool(y)) => x == y,
        (Value::Int(x),  Value::Int(y))  => x == y,
        (Value::Float(x),Value::Float(y))=> x == y,
        (Value::Int(x),  Value::Float(y))=> (*x as f64) == *y,
        (Value::Float(x),Value::Int(y))  => *x == (*y as f64),
        (Value::Str(x),  Value::Str(y))  => x == y,
        _                                => false,
    }
}

fn apply_binop(op: BinOp, l: Value, r: Value) -> Result<Value> {
    use BinOp::*;
    match op {
        And => Ok(Value::Bool(l.truthy() && r.truthy())),
        Or  => Ok(Value::Bool(l.truthy() || r.truthy())),
        Xor => Ok(Value::Bool(l.truthy() ^ r.truthy())),
        Eq  => Ok(Value::Bool(values_eq(&l, &r))),
        Neq => Ok(Value::Bool(!values_eq(&l, &r))),
        Lt  => Ok(Value::Bool(l.partial_cmp_val(&r).map_or(false, |o| o.is_lt()))),
        Gt  => Ok(Value::Bool(l.partial_cmp_val(&r).map_or(false, |o| o.is_gt()))),
        Lte => Ok(Value::Bool(l.partial_cmp_val(&r).map_or(false, |o| o.is_le()))),
        Gte => Ok(Value::Bool(l.partial_cmp_val(&r).map_or(false, |o| o.is_ge()))),
        Add => match (&l, &r) {
            (Value::Int(a),   Value::Int(b))   => Ok(Value::Int(a + b)),
            (Value::Float(a), Value::Float(b)) => Ok(Value::Float(a + b)),
            (Value::Int(a),   Value::Float(b)) => Ok(Value::Float(*a as f64 + b)),
            (Value::Float(a), Value::Int(b))   => Ok(Value::Float(a + *b as f64)),
            (Value::Str(a),   Value::Str(b))   => Ok(Value::Str(format!("{}{}", a, b))),
            (Value::List(a),  Value::List(b))  => { let mut v = a.clone(); v.extend(b.clone()); Ok(Value::List(v)) }
            _ => Err(CypherError::Type(format!("cannot add {:?} + {:?}", l, r))),
        },
        Sub => numeric_binop(l, r, |a, b| a - b, |a, b| a - b),
        Mul => numeric_binop(l, r, |a, b| a * b, |a, b| a * b),
        Div => {
            match (&l, &r) {
                (_, Value::Int(0)) =>
                    Err(CypherError::Exec("division by zero".into())),
                (_, Value::Float(f)) if *f == 0.0 =>
                    Err(CypherError::Exec("division by zero".into())),
                _ => numeric_binop(l, r, |a, b| a / b, |a, b| a / b),
            }
        }
        Mod => numeric_binop(l, r, |a, b| a % b, |a, b| a % b),
        Pow => match (&l, &r) {
            (Value::Float(a), Value::Float(b)) => Ok(Value::Float(a.powf(*b))),
            (Value::Int(a), Value::Int(b)) => Ok(Value::Float((*a as f64).powf(*b as f64))),
            _ => Err(CypherError::Type("pow requires numbers".into())),
        },
    }
}

fn numeric_binop(
    l: Value, r: Value,
    int_op: impl Fn(i64, i64) -> i64,
    float_op: impl Fn(f64, f64) -> f64,
) -> Result<Value> {
    match (l, r) {
        (Value::Int(a),   Value::Int(b))   => Ok(Value::Int(int_op(a, b))),
        (Value::Float(a), Value::Float(b)) => Ok(Value::Float(float_op(a, b))),
        (Value::Int(a),   Value::Float(b)) => Ok(Value::Float(float_op(a as f64, b))),
        (Value::Float(a), Value::Int(b))   => Ok(Value::Float(float_op(a, b as f64))),
        (l, r) => Err(CypherError::Type(format!("numeric op requires numbers, got {:?} and {:?}", l, r))),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::parser::Parser;
    use pg_graph::PersonalGraph;
    use pg_core::props;

    fn engine() -> PersonalGraph {
        PersonalGraph::in_memory().unwrap()
    }

    fn exec(g: &mut PersonalGraph, q: &str) -> QueryResult {
        let query = Parser::new(q).unwrap().parse().unwrap();
        CypherEngine::new(g).execute(&query).unwrap()
    }

    #[test]
    fn create_and_match() {
        let mut g = engine();
        exec(&mut g, r#"CREATE (n:Person {name: "Alice", age: 30})"#);
        exec(&mut g, r#"CREATE (n:Person {name: "Bob", age: 25})"#);

        let result = exec(&mut g, "MATCH (n:Person) RETURN n.name");
        assert_eq!(result.rows.len(), 2);
    }

    #[test]
    fn match_where() {
        let mut g = engine();
        exec(&mut g, r#"CREATE (n:Person {name: "Alice", age: 30})"#);
        exec(&mut g, r#"CREATE (n:Person {name: "Bob", age: 17})"#);

        let result = exec(&mut g, "MATCH (n:Person) WHERE n.age >= 18 RETURN n.name");
        assert_eq!(result.rows.len(), 1);
        assert_eq!(result.rows[0].get("n.name"), Some(&Value::Str("Alice".into())));
    }

    #[test]
    fn create_edge_and_traverse() {
        let mut g = engine();
        exec(&mut g, r#"CREATE (a:Person {name: "Alice"})"#);
        exec(&mut g, r#"CREATE (b:Person {name: "Bob"})"#);

        // Get Alice's ID
        let r = exec(&mut g, "MATCH (a:Person) WHERE a.name = 'Alice' RETURN a");
        let alice_id = match r.rows[0].get("a").unwrap() {
            Value::Node(n) => n.id,
            _ => panic!(),
        };
        let r2 = exec(&mut g, "MATCH (b:Person) WHERE b.name = 'Bob' RETURN b");
        let bob_id = match r2.rows[0].get("b").unwrap() {
            Value::Node(n) => n.id,
            _ => panic!(),
        };

        g.add_edge(alice_id, bob_id, "KNOWS", pg_core::props! {}).unwrap();

        let result = exec(&mut g, "MATCH (a:Person)-[:KNOWS]->(b:Person) RETURN a.name, b.name");
        assert_eq!(result.rows.len(), 1);
    }

    #[test]
    fn delete_node() {
        let mut g = engine();
        exec(&mut g, r#"CREATE (n:Thing {x: 1})"#);
        assert_eq!(g.node_count().unwrap(), 1);

        exec(&mut g, "MATCH (n:Thing) DELETE n");
        assert_eq!(g.node_count().unwrap(), 0);
    }

    #[test]
    fn set_property() {
        let mut g = engine();
        exec(&mut g, r#"CREATE (n:Person {name: "Alice", age: 30})"#);
        exec(&mut g, "MATCH (n:Person) WHERE n.name = 'Alice' SET n.age = 31");

        let r = exec(&mut g, "MATCH (n:Person) WHERE n.name = 'Alice' RETURN n.age");
        assert_eq!(r.rows[0].get("n.age"), Some(&Value::Int(31)));
    }

    #[test]
    fn order_and_limit() {
        let mut g = engine();
        for i in [5i64, 1, 3, 2, 4] {
            exec(&mut g, &format!("CREATE (n:Num {{v: {}}})", i));
        }
        let r = exec(&mut g, "MATCH (n:Num) RETURN n.v ORDER BY n.v ASC LIMIT 3");
        assert_eq!(r.rows.len(), 3);
        assert_eq!(r.rows[0].get("n.v"), Some(&Value::Int(1)));
        assert_eq!(r.rows[2].get("n.v"), Some(&Value::Int(3)));
    }

    #[test]
    fn builtin_functions() {
        let mut g = engine();
        exec(&mut g, r#"CREATE (n:X {name: "hello"})"#);
        let r = exec(&mut g, "MATCH (n:X) RETURN toupper(n.name)");
        assert_eq!(r.rows[0].get("toupper"), Some(&Value::Str("HELLO".into())));
    }
}
