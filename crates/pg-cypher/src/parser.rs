//! Recursive-descent Cypher parser.

use crate::ast::*;
use crate::lexer::{Lexer, Token};
use crate::{CypherError, Result};
use std::collections::BTreeMap;

pub struct Parser {
    tokens: Vec<Token>,
    pos: usize,
}

impl Parser {
    pub fn new(src: &str) -> Result<Self> {
        let tokens = Lexer::new(src).tokenize()?;
        Ok(Self { tokens, pos: 0 })
    }

    pub fn parse(&mut self) -> Result<Query> {
        let mut clauses = Vec::new();
        while !self.at_end() {
            // skip optional semicolons between statements
            while self.peek() == &Token::Semicolon { self.advance(); }
            if self.at_end() { break; }
            clauses.push(self.parse_clause()?);
        }
        Ok(Query { clauses })
    }

    // ── Clause dispatch ──────────────────────────────────────────────────────

    fn parse_clause(&mut self) -> Result<Clause> {
        match self.peek().clone() {
            Token::Match => {
                self.advance();
                let clause = self.parse_match_body()?;
                Ok(Clause::Match(clause))
            }
            Token::Optional => {
                self.advance();
                self.expect(Token::Match)?;
                let clause = self.parse_match_body()?;
                Ok(Clause::OptionalMatch(clause))
            }
            Token::Create => {
                self.advance();
                let patterns = self.parse_pattern_list()?;
                Ok(Clause::Create(CreateClause { patterns }))
            }
            Token::Merge => {
                self.advance();
                let patterns = self.parse_pattern_list()?;
                Ok(Clause::Merge(CreateClause { patterns }))
            }
            Token::Detach => {
                self.advance();
                self.expect(Token::Delete)?;
                let exprs = self.parse_expr_list()?;
                Ok(Clause::DetachDelete(DeleteClause { exprs }))
            }
            Token::Delete => {
                self.advance();
                let exprs = self.parse_expr_list()?;
                Ok(Clause::Delete(DeleteClause { exprs }))
            }
            Token::Set => {
                self.advance();
                Ok(Clause::Set(self.parse_set_clause()?))
            }
            Token::Remove => {
                self.advance();
                Ok(Clause::Remove(self.parse_remove_clause()?))
            }
            Token::Return => {
                self.advance();
                Ok(Clause::Return(self.parse_return_clause()?))
            }
            Token::With => {
                self.advance();
                Ok(Clause::With(self.parse_with_clause()?))
            }
            Token::Unwind => {
                self.advance();
                let expr = self.parse_expr(0)?;
                self.expect(Token::As)?;
                let var = self.expect_ident()?;
                Ok(Clause::Unwind(UnwindClause { expr, var }))
            }
            other => Err(CypherError::Parse(format!("unexpected clause start: {:?}", other))),
        }
    }

    // ── MATCH body ───────────────────────────────────────────────────────────

    fn parse_match_body(&mut self) -> Result<MatchClause> {
        let patterns = self.parse_pattern_list()?;
        let where_expr = if self.peek() == &Token::Where {
            self.advance();
            Some(self.parse_expr(0)?)
        } else {
            None
        };
        Ok(MatchClause { patterns, where_expr })
    }

    // ── Pattern list  p1, p2, … ──────────────────────────────────────────────

    fn parse_pattern_list(&mut self) -> Result<Vec<Pattern>> {
        let mut patterns = Vec::new();
        patterns.push(self.parse_pattern()?);
        while self.peek() == &Token::Comma {
            self.advance();
            patterns.push(self.parse_pattern()?);
        }
        Ok(patterns)
    }

    fn parse_pattern(&mut self) -> Result<Pattern> {
        // optional path variable:  p = (a)-[:T]->(b)
        let path_var = if matches!(self.peek(), Token::Ident(_)) && self.peek_ahead(1) == &Token::Eq {
            let v = self.expect_ident()?;
            self.advance(); // =
            Some(v)
        } else {
            None
        };

        // optional shortestPath(…) wrapper
        let is_shortest = matches!(self.peek(), Token::ShortestPath | Token::AllShortestPaths);
        if is_shortest {
            self.advance();
            self.expect(Token::LParen)?;
        }

        let start = self.parse_node_pattern()?;
        let mut hops = Vec::new();

        while self.is_edge_start() {
            let edge = self.parse_edge_pattern()?;
            let node = self.parse_node_pattern()?;
            hops.push((edge, node));
        }

        if is_shortest {
            self.expect(Token::RParen)?;
        }

        Ok(Pattern { start, hops, path_var })
    }

    fn is_edge_start(&self) -> bool {
        matches!(self.peek(), Token::Minus | Token::Arrow | Token::LeftArrow)
    }

    // (var:Label1:Label2 {key: value})
    fn parse_node_pattern(&mut self) -> Result<NodePattern> {
        self.expect(Token::LParen)?;

        // Variable: any bare identifier before labels/props/closing paren.
        // Examples: (n), (n:Label), (n:Label {k:v}), (:Label), ()
        let var = if matches!(self.peek(), Token::Ident(_)) {
            Some(self.expect_ident()?)
        } else {
            None
        };

        let mut labels = Vec::new();
        while self.peek() == &Token::Colon {
            self.advance();
            labels.push(self.expect_ident()?);
        }

        let props = if self.peek() == &Token::LBrace {
            self.parse_prop_map()?
        } else {
            BTreeMap::new()
        };

        self.expect(Token::RParen)?;
        Ok(NodePattern { var, labels, props })
    }

    // -[var:TYPE*min..max {props}]->   or  <-[...]- or -[...]-
    fn parse_edge_pattern(&mut self) -> Result<EdgePattern> {
        let direction = match self.peek().clone() {
            Token::LeftArrow => { self.advance(); Direction::Incoming }
            Token::Minus     => { self.advance(); Direction::Either }
            Token::Arrow     => {
                // shouldn't happen at start but handle gracefully
                self.advance(); Direction::Outgoing
            }
            _ => return Err(CypherError::Parse("expected edge start".into())),
        };

        // optional bracket part [...]
        let (var, types, props, hops) = if self.peek() == &Token::LBracket {
            self.advance();

            let var = if matches!(self.peek(), Token::Ident(_)) { Some(self.expect_ident()?) } else { None };

            let mut types = Vec::new();
            while self.peek() == &Token::Colon {
                self.advance();
                types.push(self.expect_ident()?);
                if self.peek() == &Token::Pipe { self.advance(); }
            }

            let hops = if self.peek() == &Token::Star {
                self.advance();
                let min = if matches!(self.peek(), Token::Int(_)) {
                    Some(self.expect_int()? as u32)
                } else { None };
                let max = if self.peek() == &Token::DotDot {
                    self.advance();
                    if matches!(self.peek(), Token::Int(_)) {
                        Some(self.expect_int()? as u32)
                    } else { None }
                } else { None };
                HopSpec::Variable(min, max)
            } else {
                HopSpec::One
            };

            let props = if self.peek() == &Token::LBrace { self.parse_prop_map()? } else { BTreeMap::new() };

            self.expect(Token::RBracket)?;
            (var, types, props, hops)
        } else {
            (None, Vec::new(), BTreeMap::new(), HopSpec::One)
        };

        // closing direction
        let direction = match self.peek().clone() {
            Token::Arrow  => { self.advance(); if direction == Direction::Incoming { Direction::Incoming } else { Direction::Outgoing } }
            Token::Minus  => { self.advance(); direction }
            _             => direction,
        };

        Ok(EdgePattern { var, types, props, direction, hops })
    }

    // {key: expr, key2: expr2}
    fn parse_prop_map(&mut self) -> Result<PropMap> {
        self.expect(Token::LBrace)?;
        let mut map = BTreeMap::new();
        while self.peek() != &Token::RBrace {
            let key = self.expect_ident()?;
            self.expect(Token::Colon)?;
            let val = self.parse_expr(0)?;
            map.insert(key, val);
            if self.peek() == &Token::Comma { self.advance(); }
        }
        self.expect(Token::RBrace)?;
        Ok(map)
    }

    // ── SET clause ───────────────────────────────────────────────────────────

    fn parse_set_clause(&mut self) -> Result<SetClause> {
        let mut items = Vec::new();
        items.push(self.parse_set_item()?);
        while self.peek() == &Token::Comma {
            self.advance();
            items.push(self.parse_set_item()?);
        }
        Ok(SetClause { items })
    }

    fn parse_set_item(&mut self) -> Result<SetItem> {
        let var = self.expect_ident()?;
        self.expect(Token::Dot)?;
        let key = self.expect_ident()?;
        self.expect(Token::Eq)?;
        let value = self.parse_expr(0)?;
        Ok(SetItem::Property { var, key, value })
    }

    // ── REMOVE clause ────────────────────────────────────────────────────────

    fn parse_remove_clause(&mut self) -> Result<RemoveClause> {
        let mut items = Vec::new();
        loop {
            let var = self.expect_ident()?;
            if self.peek() == &Token::Dot {
                self.advance();
                let key = self.expect_ident()?;
                items.push(RemoveItem::Property { var, key });
            } else if self.peek() == &Token::Colon {
                self.advance();
                let label = self.expect_ident()?;
                items.push(RemoveItem::Label { var, label });
            }
            if self.peek() == &Token::Comma { self.advance(); } else { break; }
        }
        Ok(RemoveClause { items })
    }

    // ── RETURN clause ────────────────────────────────────────────────────────

    fn parse_return_clause(&mut self) -> Result<ReturnClause> {
        let distinct = if self.peek() == &Token::Distinct { self.advance(); true } else { false };
        let items = self.parse_return_items()?;
        let order_by = self.parse_optional_order_by()?;
        let skip  = if self.peek() == &Token::Skip  { self.advance(); Some(self.parse_expr(0)?) } else { None };
        let limit = if self.peek() == &Token::Limit { self.advance(); Some(self.parse_expr(0)?) } else { None };
        Ok(ReturnClause { distinct, items, order_by, skip, limit })
    }

    fn parse_with_clause(&mut self) -> Result<WithClause> {
        let items = self.parse_return_items()?;
        let where_expr = if self.peek() == &Token::Where { self.advance(); Some(self.parse_expr(0)?) } else { None };
        let order_by = self.parse_optional_order_by()?;
        let skip  = if self.peek() == &Token::Skip  { self.advance(); Some(self.parse_expr(0)?) } else { None };
        let limit = if self.peek() == &Token::Limit { self.advance(); Some(self.parse_expr(0)?) } else { None };
        Ok(WithClause { items, where_expr, order_by, skip, limit })
    }

    fn parse_return_items(&mut self) -> Result<Vec<ReturnItem>> {
        let mut items = Vec::new();
        // RETURN *
        if self.peek() == &Token::Star {
            self.advance();
            return Ok(vec![ReturnItem { expr: Expr::Star, alias: None }]);
        }
        items.push(self.parse_return_item()?);
        while self.peek() == &Token::Comma {
            self.advance();
            items.push(self.parse_return_item()?);
        }
        Ok(items)
    }

    fn parse_return_item(&mut self) -> Result<ReturnItem> {
        let expr = self.parse_expr(0)?;
        let alias = if self.peek() == &Token::As {
            self.advance();
            Some(self.expect_ident()?)
        } else {
            None
        };
        Ok(ReturnItem { expr, alias })
    }

    fn parse_optional_order_by(&mut self) -> Result<Vec<OrderItem>> {
        if self.peek() != &Token::Order { return Ok(Vec::new()); }
        self.advance();
        self.expect(Token::By)?;
        let mut items = Vec::new();
        items.push(self.parse_order_item()?);
        while self.peek() == &Token::Comma {
            self.advance();
            items.push(self.parse_order_item()?);
        }
        Ok(items)
    }

    fn parse_order_item(&mut self) -> Result<OrderItem> {
        let expr = self.parse_expr(0)?;
        let descending = match self.peek() {
            Token::Desc => { self.advance(); true }
            Token::Asc  => { self.advance(); false }
            _           => false,
        };
        Ok(OrderItem { expr, descending })
    }

    // ── Expression parser (Pratt-style) ──────────────────────────────────────

    fn parse_expr_list(&mut self) -> Result<Vec<Expr>> {
        let mut exprs = Vec::new();
        exprs.push(self.parse_expr(0)?);
        while self.peek() == &Token::Comma {
            self.advance();
            exprs.push(self.parse_expr(0)?);
        }
        Ok(exprs)
    }

    /// min_bp = minimum binding power (Pratt parsing).
    fn parse_expr(&mut self, min_bp: u8) -> Result<Expr> {
        let mut lhs = self.parse_prefix()?;

        loop {
            let tok = self.peek().clone();

            // postfix: IS [NOT] NULL
            if tok == Token::Is {
                self.advance();
                let negated = if self.peek() == &Token::Not { self.advance(); true } else { false };
                self.expect(Token::Null)?;
                lhs = Expr::IsNull(Box::new(lhs), !negated);
                continue;
            }

            // infix operators
            let Some((lbp, rbp, binop)) = infix_binding_power(&tok) else { break; };
            if lbp < min_bp { break; }
            self.advance();

            // String ops: n.name CONTAINS "foo"
            let rhs = self.parse_expr(rbp)?;
            lhs = Expr::BinOp(binop, Box::new(lhs), Box::new(rhs));
        }

        Ok(lhs)
    }

    fn parse_prefix(&mut self) -> Result<Expr> {
        match self.peek().clone() {
            Token::Int(n)  => { self.advance(); Ok(Expr::Int(n)) }
            Token::Float(f) => { self.advance(); Ok(Expr::Float(f)) }
            Token::Str(s)  => { self.advance(); Ok(Expr::Str(s)) }
            Token::True    => { self.advance(); Ok(Expr::Bool(true)) }
            Token::False   => { self.advance(); Ok(Expr::Bool(false)) }
            Token::Null    => { self.advance(); Ok(Expr::Null) }
            Token::Star    => { self.advance(); Ok(Expr::Star) }
            Token::Minus   => {
                self.advance();
                let expr = self.parse_expr(90)?;
                Ok(Expr::BinOp(BinOp::Sub, Box::new(Expr::Int(0)), Box::new(expr)))
            }
            Token::Not     => {
                self.advance();
                let expr = self.parse_expr(70)?;
                Ok(Expr::Not(Box::new(expr)))
            }
            Token::LParen  => {
                self.advance();
                let expr = self.parse_expr(0)?;
                self.expect(Token::RParen)?;
                Ok(expr)
            }
            Token::LBracket => {
                self.advance();
                let mut items = Vec::new();
                while self.peek() != &Token::RBracket {
                    items.push(self.parse_expr(0)?);
                    if self.peek() == &Token::Comma { self.advance(); }
                }
                self.advance();
                Ok(Expr::List(items))
            }
            Token::LBrace => {
                let map = self.parse_prop_map()?;
                Ok(Expr::Map(map))
            }
            Token::Ident(name) => {
                let name = name.clone();
                self.advance();

                // Function call?
                if self.peek() == &Token::LParen {
                    self.advance();
                    let mut args = Vec::new();
                    // count(*) special case
                    if self.peek() == &Token::Star {
                        self.advance();
                        args.push(Expr::Star);
                    } else {
                        while self.peek() != &Token::RParen {
                            args.push(self.parse_expr(0)?);
                            if self.peek() == &Token::Comma { self.advance(); }
                        }
                    }
                    self.expect(Token::RParen)?;
                    return Ok(Expr::Call(name.to_lowercase(), args));
                }

                // Property access?
                if self.peek() == &Token::Dot {
                    self.advance();
                    let prop = self.expect_ident()?;
                    return Ok(Expr::Prop(name, prop));
                }

                Ok(Expr::Var(name))
            }
            // CASE
            Token::Case => {
                self.advance();
                let input = if !matches!(self.peek(), Token::When) {
                    Some(Box::new(self.parse_expr(0)?))
                } else {
                    None
                };
                let mut branches = Vec::new();
                while self.peek() == &Token::When {
                    self.advance();
                    let cond = self.parse_expr(0)?;
                    self.expect(Token::Then)?;
                    let then = self.parse_expr(0)?;
                    branches.push((cond, then));
                }
                let default = if self.peek() == &Token::Else {
                    self.advance();
                    Some(Box::new(self.parse_expr(0)?))
                } else { None };
                self.expect(Token::End)?;
                Ok(Expr::Case { input, branches, default })
            }
            other => Err(CypherError::Parse(format!("unexpected expression token: {:?}", other))),
        }
    }

    // ── Helpers ───────────────────────────────────────────────────────────────

    fn peek(&self) -> &Token {
        self.tokens.get(self.pos).unwrap_or(&Token::Eof)
    }
    fn peek_ahead(&self, n: usize) -> &Token {
        self.tokens.get(self.pos + n).unwrap_or(&Token::Eof)
    }
    fn advance(&mut self) -> Token {
        let t = self.tokens.get(self.pos).cloned().unwrap_or(Token::Eof);
        self.pos += 1;
        t
    }
    fn at_end(&self) -> bool {
        matches!(self.peek(), Token::Eof)
    }
    fn expect(&mut self, want: Token) -> Result<()> {
        let got = self.advance();
        if got == want { Ok(()) }
        else { Err(CypherError::Parse(format!("expected {:?}, got {:?}", want, got))) }
    }
    fn expect_ident(&mut self) -> Result<String> {
        match self.advance() {
            Token::Ident(s) => Ok(s),
            other => Err(CypherError::Parse(format!("expected identifier, got {:?}", other))),
        }
    }
    fn expect_int(&mut self) -> Result<i64> {
        match self.advance() {
            Token::Int(n) => Ok(n),
            other => Err(CypherError::Parse(format!("expected integer, got {:?}", other))),
        }
    }
}

/// Returns (left_bp, right_bp, BinOp) for infix operators, or None.
fn infix_binding_power(tok: &Token) -> Option<(u8, u8, BinOp)> {
    use BinOp::*;
    match tok {
        Token::Or            => Some((10, 11, Or)),
        Token::Xor           => Some((12, 13, Xor)),
        Token::And           => Some((20, 21, And)),
        Token::Eq            => Some((30, 31, Eq)),
        Token::Neq           => Some((30, 31, Neq)),
        Token::Lt            => Some((30, 31, Lt)),
        Token::Gt            => Some((30, 31, Gt)),
        Token::Lte           => Some((30, 31, Lte)),
        Token::Gte           => Some((30, 31, Gte)),
        Token::Plus          => Some((40, 41, Add)),
        Token::Minus         => Some((40, 41, Sub)),
        Token::Star          => Some((50, 51, Mul)),
        Token::Slash         => Some((50, 51, Div)),
        Token::Percent       => Some((50, 51, Mod)),
        Token::Caret         => Some((60, 59, Pow)), // right-assoc
        Token::In            => Some((30, 31, Eq)),  // handled specially later
        _                    => None,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn parse(q: &str) -> Query { Parser::new(q).unwrap().parse().unwrap() }

    #[test]
    fn simple_match_return() {
        let q = parse("MATCH (n:Person) RETURN n");
        assert!(matches!(q.clauses[0], Clause::Match(_)));
        assert!(matches!(q.clauses[1], Clause::Return(_)));
    }

    #[test]
    fn match_with_where() {
        let q = parse("MATCH (n:Person) WHERE n.age > 18 RETURN n.name");
        match &q.clauses[0] {
            Clause::Match(m) => assert!(m.where_expr.is_some()),
            _ => panic!("expected match"),
        }
    }

    #[test]
    fn edge_pattern() {
        let q = parse("MATCH (a)-[:KNOWS]->(b) RETURN a, b");
        match &q.clauses[0] {
            Clause::Match(m) => {
                assert_eq!(m.patterns[0].hops.len(), 1);
                assert_eq!(m.patterns[0].hops[0].0.direction, Direction::Outgoing);
            }
            _ => panic!(),
        }
    }

    #[test]
    fn create_node() {
        let q = parse(r#"CREATE (n:Person {name: "Alice", age: 30})"#);
        assert!(matches!(q.clauses[0], Clause::Create(_)));
    }

    #[test]
    fn order_limit() {
        let q = parse("MATCH (n) RETURN n ORDER BY n.name DESC LIMIT 10");
        match &q.clauses[1] {
            Clause::Return(r) => {
                assert_eq!(r.order_by.len(), 1);
                assert!(r.order_by[0].descending);
                assert!(r.limit.is_some());
            }
            _ => panic!(),
        }
    }

    #[test]
    fn set_property() {
        let q = parse("MATCH (n:Person) WHERE n.name = 'Alice' SET n.age = 31");
        // WHERE is part of the MATCH clause; SET is at clauses[1]
        assert_eq!(q.clauses.len(), 2);
        assert!(matches!(q.clauses[1], Clause::Set(_)));
    }

    #[test]
    fn variable_length_hop() {
        let q = parse("MATCH (a)-[*2..5]->(b) RETURN a");
        match &q.clauses[0] {
            Clause::Match(m) => {
                let hop = &m.patterns[0].hops[0].0;
                assert_eq!(hop.hops, HopSpec::Variable(Some(2), Some(5)));
            }
            _ => panic!(),
        }
    }

    #[test]
    fn count_star() {
        let q = parse("MATCH (n) RETURN count(*)");
        match &q.clauses[1] {
            Clause::Return(r) => {
                assert!(matches!(r.items[0].expr, Expr::Call(..)));
            }
            _ => panic!(),
        }
    }
}
