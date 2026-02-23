//! Cypher lexer — converts a query string into a flat token stream.

use crate::{CypherError, Result};

#[derive(Debug, Clone, PartialEq)]
pub enum Token {
    // ── Keywords ──────────────────────────────────────────────────
    Match, Optional, Where, Return, Create, Merge,
    Delete, Detach, Set, Remove, With, Unwind,
    Order, By, Skip, Limit, Distinct,
    Asc, Desc, As,
    And, Or, Xor, Not,
    True, False, Null,
    In, Is, Contains, Starts, Ends,
    ShortestPath, AllShortestPaths,
    Case, When, Then, Else, End,
    // ── Identifiers & literals ────────────────────────────────────
    Ident(String),
    Int(i64),
    Float(f64),
    Str(String),
    // ── Punctuation ───────────────────────────────────────────────
    LParen, RParen,
    LBracket, RBracket,
    LBrace, RBrace,
    Comma, Colon, Semicolon, Dot,
    DotDot, // ..  (used in [*..n])
    Pipe,
    Star,
    // ── Operators ─────────────────────────────────────────────────
    Eq, Neq, Lt, Gt, Lte, Gte,
    Plus, Minus, Slash, Percent, Caret,
    Arrow,      // ->
    LeftArrow,  // <-
    Dash,       // -  (undirected edge)
    // ── End ───────────────────────────────────────────────────────
    Eof,
}

pub struct Lexer<'a> {
    src: &'a [u8],
    pos: usize,
}

impl<'a> Lexer<'a> {
    pub fn new(src: &'a str) -> Self {
        Self { src: src.as_bytes(), pos: 0 }
    }

    pub fn tokenize(mut self) -> Result<Vec<Token>> {
        let mut tokens = Vec::new();
        loop {
            let tok = self.next_token()?;
            let done = tok == Token::Eof;
            tokens.push(tok);
            if done { break; }
        }
        Ok(tokens)
    }

    fn peek(&self) -> Option<u8> { self.src.get(self.pos).copied() }
    fn peek2(&self) -> Option<u8> { self.src.get(self.pos + 1).copied() }
    fn advance(&mut self) -> u8 { let c = self.src[self.pos]; self.pos += 1; c }

    fn skip_whitespace_and_comments(&mut self) {
        loop {
            // whitespace
            while self.peek().map_or(false, |c| c.is_ascii_whitespace()) {
                self.advance();
            }
            // // line comment
            if self.peek() == Some(b'/') && self.peek2() == Some(b'/') {
                while self.peek().map_or(false, |c| c != b'\n') { self.advance(); }
                continue;
            }
            // /* block comment */
            if self.peek() == Some(b'/') && self.peek2() == Some(b'*') {
                self.advance(); self.advance();
                while self.pos + 1 < self.src.len() {
                    if self.src[self.pos] == b'*' && self.src[self.pos+1] == b'/' {
                        self.advance(); self.advance(); break;
                    }
                    self.advance();
                }
                continue;
            }
            break;
        }
    }

    fn next_token(&mut self) -> Result<Token> {
        self.skip_whitespace_and_comments();
        let pos = self.pos;

        let c = match self.peek() {
            None => return Ok(Token::Eof),
            Some(c) => c,
        };

        // ── String literals ───────────────────────────────────────
        if c == b'\'' || c == b'"' {
            return self.lex_string(c);
        }

        // ── Backtick-quoted identifiers ───────────────────────────
        if c == b'`' {
            self.advance();
            let start = self.pos;
            while self.peek().map_or(false, |c| c != b'`') { self.advance(); }
            let s = std::str::from_utf8(&self.src[start..self.pos]).unwrap().to_owned();
            self.advance(); // consume closing `
            return Ok(Token::Ident(s));
        }

        // ── Numbers ───────────────────────────────────────────────
        if c.is_ascii_digit() || (c == b'-' && self.peek2().map_or(false, |d| d.is_ascii_digit())) {
            return self.lex_number();
        }

        // ── Identifiers & keywords ────────────────────────────────
        if c.is_ascii_alphabetic() || c == b'_' {
            return Ok(self.lex_ident_or_keyword());
        }

        // ── Two-char operators ────────────────────────────────────
        self.advance();
        match c {
            b'(' => Ok(Token::LParen),
            b')' => Ok(Token::RParen),
            b'[' => Ok(Token::LBracket),
            b']' => Ok(Token::RBracket),
            b'{' => Ok(Token::LBrace),
            b'}' => Ok(Token::RBrace),
            b',' => Ok(Token::Comma),
            b':' => Ok(Token::Colon),
            b';' => Ok(Token::Semicolon),
            b'|' => Ok(Token::Pipe),
            b'*' => Ok(Token::Star),
            b'+' => Ok(Token::Plus),
            b'/' => Ok(Token::Slash),
            b'%' => Ok(Token::Percent),
            b'^' => Ok(Token::Caret),
            b'.' => {
                if self.peek() == Some(b'.') { self.advance(); Ok(Token::DotDot) }
                else { Ok(Token::Dot) }
            }
            b'=' => Ok(Token::Eq),
            b'<' => {
                if self.peek() == Some(b'=') { self.advance(); Ok(Token::Lte) }
                else if self.peek() == Some(b'>') { self.advance(); Ok(Token::Neq) }
                else if self.peek() == Some(b'-') { self.advance(); Ok(Token::LeftArrow) }
                else { Ok(Token::Lt) }
            }
            b'>' => {
                if self.peek() == Some(b'=') { self.advance(); Ok(Token::Gte) }
                else { Ok(Token::Gt) }
            }
            b'-' => {
                if self.peek() == Some(b'>') { self.advance(); Ok(Token::Arrow) }
                else { Ok(Token::Minus) }
            }
            b'!' => {
                if self.peek() == Some(b'=') { self.advance(); Ok(Token::Neq) }
                else {
                    Err(CypherError::Lex { pos, msg: format!("unexpected '!'") })
                }
            }
            other => Err(CypherError::Lex {
                pos,
                msg: format!("unexpected character '{}'", other as char),
            }),
        }
    }

    fn lex_string(&mut self, quote: u8) -> Result<Token> {
        self.advance(); // opening quote
        let mut buf = String::new();
        loop {
            match self.peek() {
                None => return Err(CypherError::Lex { pos: self.pos, msg: "unterminated string".into() }),
                Some(c) if c == quote => { self.advance(); break; }
                Some(b'\\') => {
                    self.advance();
                    match self.advance() {
                        b'n'  => buf.push('\n'),
                        b't'  => buf.push('\t'),
                        b'r'  => buf.push('\r'),
                        b'\'' => buf.push('\''),
                        b'"'  => buf.push('"'),
                        b'\\' => buf.push('\\'),
                        other => { buf.push('\\'); buf.push(other as char); }
                    }
                }
                Some(c) => { self.advance(); buf.push(c as char); }
            }
        }
        Ok(Token::Str(buf))
    }

    fn lex_number(&mut self) -> Result<Token> {
        let start = self.pos;
        if self.peek() == Some(b'-') { self.advance(); }
        while self.peek().map_or(false, |c| c.is_ascii_digit()) { self.advance(); }
        // Don't treat `..` (range) as a decimal point
        let is_float = self.peek() == Some(b'.') && self.peek2() != Some(b'.');
        if is_float {
            self.advance();
            while self.peek().map_or(false, |c| c.is_ascii_digit()) { self.advance(); }
            // optional exponent
            if self.peek().map_or(false, |c| c == b'e' || c == b'E') {
                self.advance();
                if self.peek().map_or(false, |c| c == b'+' || c == b'-') { self.advance(); }
                while self.peek().map_or(false, |c| c.is_ascii_digit()) { self.advance(); }
            }
            let s = std::str::from_utf8(&self.src[start..self.pos]).unwrap();
            Ok(Token::Float(s.parse().map_err(|e| CypherError::Lex {
                pos: start, msg: format!("bad float: {e}"),
            })?))
        } else {
            let s = std::str::from_utf8(&self.src[start..self.pos]).unwrap();
            Ok(Token::Int(s.parse().map_err(|e| CypherError::Lex {
                pos: start, msg: format!("bad int: {e}"),
            })?))
        }
    }

    fn lex_ident_or_keyword(&mut self) -> Token {
        let start = self.pos;
        while self.peek().map_or(false, |c| c.is_ascii_alphanumeric() || c == b'_') {
            self.advance();
        }
        let raw = std::str::from_utf8(&self.src[start..self.pos]).unwrap();
        match raw.to_lowercase().as_str() {
            "match"            => Token::Match,
            "optional"         => Token::Optional,
            "where"            => Token::Where,
            "return"           => Token::Return,
            "create"           => Token::Create,
            "merge"            => Token::Merge,
            "delete"           => Token::Delete,
            "detach"           => Token::Detach,
            "set"              => Token::Set,
            "remove"           => Token::Remove,
            "with"             => Token::With,
            "unwind"           => Token::Unwind,
            "order"            => Token::Order,
            "by"               => Token::By,
            "skip"             => Token::Skip,
            "limit"            => Token::Limit,
            "distinct"         => Token::Distinct,
            "asc"              => Token::Asc,
            "desc"             => Token::Desc,
            "as"               => Token::As,
            "and"              => Token::And,
            "or"               => Token::Or,
            "xor"              => Token::Xor,
            "not"              => Token::Not,
            "true"             => Token::True,
            "false"            => Token::False,
            "null"             => Token::Null,
            "in"               => Token::In,
            "is"               => Token::Is,
            "contains"         => Token::Contains,
            "starts"           => Token::Starts,
            "ends"             => Token::Ends,
            "shortestpath"     => Token::ShortestPath,
            "allshortestpaths" => Token::AllShortestPaths,
            "case"             => Token::Case,
            "when"             => Token::When,
            "then"             => Token::Then,
            "else"             => Token::Else,
            "end"              => Token::End,
            _                  => Token::Ident(raw.to_owned()),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn basic_match() {
        let tokens = Lexer::new("MATCH (n:Person) RETURN n").tokenize().unwrap();
        assert_eq!(tokens[0], Token::Match);
        assert_eq!(tokens[1], Token::LParen);
        assert_eq!(tokens[2], Token::Ident("n".into()));
        assert_eq!(tokens[3], Token::Colon);
        assert_eq!(tokens[4], Token::Ident("Person".into()));
    }

    #[test]
    fn arrow_tokens() {
        let tokens = Lexer::new("(a)-[:KNOWS]->(b)").tokenize().unwrap();
        assert!(tokens.contains(&Token::Arrow));
        assert!(tokens.contains(&Token::LeftArrow) == false);
    }

    #[test]
    fn string_literal() {
        let tokens = Lexer::new(r#""hello world""#).tokenize().unwrap();
        assert_eq!(tokens[0], Token::Str("hello world".into()));
    }

    #[test]
    fn numbers() {
        let tokens = Lexer::new("42 3.14").tokenize().unwrap();
        assert_eq!(tokens[0], Token::Int(42));
        assert_eq!(tokens[1], Token::Float(3.14));
    }

    #[test]
    fn line_comment() {
        let tokens = Lexer::new("MATCH // ignore this\n(n) RETURN n").tokenize().unwrap();
        assert_eq!(tokens[0], Token::Match);
        assert_eq!(tokens[1], Token::LParen);
    }
}
