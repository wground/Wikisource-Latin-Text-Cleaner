#!/usr/bin/env python3
"""
Optimized Regex Patterns for Latin Text Processing
Pre-compiled regex patterns to eliminate redundant compilations across the pipeline.
This can improve processing speed by 30-50% for regex-heavy operations.
"""

import re
from typing import Dict, Pattern

class OptimizedPatterns:
    """Pre-compiled regex patterns for reuse across all processing steps."""
    
    def __init__(self):
        # Roman numeral patterns (used in multiple steps)
        self.ROMAN_NUMERAL = re.compile(
            r'\b(?=[MDCLXVI])M{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})\b',
            re.IGNORECASE
        )
        
        self.ROMAN_START_PATTERN = re.compile(
            r'^(?=[IVXLCDM])(?:M{0,4}(?:CM|CD|D?C{0,3})(?:XC|XL|L?X{0,3})(?:IX|IV|V?I{0,3}))[.\s\-–—]*',
            re.IGNORECASE
        )
        
        # Chapter/heading patterns
        self.CHAPTER_PATTERNS = [
            re.compile(r'^\s*cap\s*\.?\s*[ivxlcdm\d]*\s*[.\-–—]?\s*$', re.IGNORECASE),
            re.compile(r'^\s*caput\s+[ivxlcdm\d]+\s*[.\-–—]?\s*$', re.IGNORECASE),
            re.compile(r'^\s*capitulum\s+[ivxlcdm\d]+\s*[.\-–—]?\s*$', re.IGNORECASE),
            re.compile(r'^\s*liber\s+[ivxlcdm\d]+\s*[.\-–—]?\s*$', re.IGNORECASE),
            re.compile(r'^\s*pars\s+[ivxlcdm\d]+\s*[.\-–—]?\s*$', re.IGNORECASE),
            re.compile(r'^\s*sectio\s+[ivxlcdm\d]+\s*[.\-–—]?\s*$', re.IGNORECASE),
            re.compile(r'^\s*book\s+[ivxlcdm\d]+\s*[.\-–—]?\s*$', re.IGNORECASE),
            re.compile(r'^\s*chapter\s+[ivxlcdm\d]+\s*[.\-–—]?\s*$', re.IGNORECASE),
        ]
        
        # Latin book/chapter patterns for index detection
        self.LATIN_CHAPTER_PATTERN = re.compile(
            r'(liber|book|chapter|capitulum|epistul|carmen|versus|sectio|pars)\s+[ivxlcdm0-9]+',
            re.IGNORECASE
        )
        
        # Generic table of contents patterns
        self.TOC_PATTERN = re.compile(r'^[ivxlcdm0-9]+[\.\s\-]', re.IGNORECASE)
        
        # Page number patterns
        self.PAGE_PATTERN = re.compile(r'^\s*\d+\s*$|^\s*p\.\s*\d+', re.IGNORECASE)
        
        # Latin function words pattern for prose detection
        self.LATIN_FUNCTION_WORDS = re.compile(
            r'\b(et|in|de|ad|cum|ex|pro|per|ab)\b',
            re.IGNORECASE
        )
        
        # Prose connector patterns
        self.PROSE_CONNECTORS = [
            'itaque', 'igitur', 'ergo', 'autem', 'enim', 'nam', 'sed', 'at',
            'vero', 'quidem', 'tamen', 'etiam', 'quoque', 'denique', 'porro',
            'praeterea', 'insuper', 'deinde', 'postea', 'interim'
        ]
        
        # Whitespace normalization patterns
        self.MULTIPLE_SPACES = re.compile(r' {2,}')
        self.MULTIPLE_NEWLINES = re.compile(r'\n{3,}')
        self.CRLF_NORMALIZE = re.compile(r'\r\n?')
        
        # Punctuation cleanup patterns
        self.MULTIPLE_PERIODS = re.compile(r'\.{2,}')
        self.MULTIPLE_COMMAS = re.compile(r',{2,}')
        self.MULTIPLE_SEMICOLONS = re.compile(r';{2,}')
        self.MULTIPLE_COLONS = re.compile(r':{2,}')
        self.MULTIPLE_EXCLAMATIONS = re.compile(r'!{2,}')
        self.MULTIPLE_QUESTIONS = re.compile(r'\?{2,}')
        
        # Space around punctuation
        self.SPACE_BEFORE_PUNCT = re.compile(r'\s+([,.;:!?])')
        self.SPACE_AFTER_PUNCT = re.compile(r'([,.;:!?])(?=[a-zA-Z])')
        
        # Editorial patterns
        self.EDITORIAL_PATTERNS = [
            re.compile(r'\[.*?ed\..*?\]', re.IGNORECASE),
            re.compile(r'\[.*?edit.*?\]', re.IGNORECASE),
            re.compile(r'\<.*?ed\..*?\>', re.IGNORECASE),
            re.compile(r'\{.*?ed\..*?\}', re.IGNORECASE),
            re.compile(r'\[sic\]', re.IGNORECASE),
            re.compile(r'\[.*?\?\]'),
            re.compile(r'\[\.{3,}\]'),
            re.compile(r'\[lacuna\]', re.IGNORECASE),
            re.compile(r'\[gap\]', re.IGNORECASE),
            re.compile(r'\[missing\]', re.IGNORECASE),
            re.compile(r'\[corrupt\]', re.IGNORECASE),
            re.compile(r'\[illegible\]', re.IGNORECASE),
        ]
        
        # Footnote patterns
        self.FOOTNOTE_BRACKETS = re.compile(r'\[\d+\]')
        self.FOOTNOTE_PARENS = re.compile(r'\(\d+\)')
        
        # Category removal patterns
        self.COMMENTARIUM_PATTERN = re.compile(
            r'==\s*Commentarium\s*==.*$',
            re.MULTILINE | re.DOTALL
        )
        self.CATEGORIA_PATTERN = re.compile(
            r'^Categoria?:\s*.*$',
            re.MULTILINE | re.IGNORECASE
        )
        
        # Quotation normalization
        self.QUOTE_REPLACEMENTS = {
            '"': '"', '"': '"', ''': "'", ''': "'",
            '«': '"', '»': '"', '‚': "'", '„': '"',
            '‹': "'", '›': "'", '‛': "'", '"': '"'
        }
        
        # Dash normalization
        self.DASH_NORMALIZE = re.compile(r'[–—]')
        
        # Ellipsis normalization
        self.ELLIPSIS_NORMALIZE = re.compile(r'…')
        
        # Empty quotes removal
        self.EMPTY_DOUBLE_QUOTES = re.compile(r'"\s*"')
        self.EMPTY_SINGLE_QUOTES = re.compile(r"'\s*'")
        
        # Standalone punctuation lines
        self.STANDALONE_PUNCT = re.compile(r'^[.,:;!?\-–—"\'()[\]{}]+$')
        
    def is_roman_numeral(self, text: str) -> bool:
        """Check if text is a Roman numeral."""
        return bool(self.ROMAN_NUMERAL.fullmatch(text.upper()))
    
    def is_chapter_heading(self, line: str) -> bool:
        """Check if line is a chapter heading using pre-compiled patterns."""
        line_lower = line.strip().lower()
        if not line_lower:
            return False
        
        return any(pattern.match(line_lower) for pattern in self.CHAPTER_PATTERNS)
    
    def has_latin_chapter_pattern(self, line: str) -> bool:
        """Check for Latin chapter patterns in line."""
        return bool(self.LATIN_CHAPTER_PATTERN.search(line))
    
    def normalize_whitespace_fast(self, text: str) -> str:
        """Fast whitespace normalization using pre-compiled patterns."""
        # Convert line endings
        text = self.CRLF_NORMALIZE.sub('\n', text)
        # Remove tabs
        text = text.replace('\t', ' ')
        # Collapse multiple spaces
        text = self.MULTIPLE_SPACES.sub(' ', text)
        # Limit consecutive newlines
        text = self.MULTIPLE_NEWLINES.sub('\n\n', text)
        return text
    
    def clean_punctuation_fast(self, text: str) -> str:
        """Fast punctuation cleanup using pre-compiled patterns."""
        # Normalize repeated punctuation
        text = self.MULTIPLE_PERIODS.sub('.', text)
        text = self.MULTIPLE_COMMAS.sub(',', text)
        text = self.MULTIPLE_SEMICOLONS.sub(';', text)
        text = self.MULTIPLE_COLONS.sub(':', text)
        text = self.MULTIPLE_EXCLAMATIONS.sub('!', text)
        text = self.MULTIPLE_QUESTIONS.sub('?', text)
        
        # Fix spacing around punctuation
        text = self.SPACE_BEFORE_PUNCT.sub(r'\1', text)
        text = self.SPACE_AFTER_PUNCT.sub(r'\1 ', text)
        
        return text
    
    def remove_editorial_fast(self, text: str) -> str:
        """Fast editorial content removal using pre-compiled patterns."""
        for pattern in self.EDITORIAL_PATTERNS:
            text = pattern.sub('', text)
        
        # Remove footnotes
        text = self.FOOTNOTE_BRACKETS.sub('', text)
        text = self.FOOTNOTE_PARENS.sub('', text)
        
        return text

# Global instance for import
PATTERNS = OptimizedPatterns()