#!/usr/bin/env python3
"""
Step 4: Remove Chapter/Book Headings and Section Indicators
Removes structural headings like Roman numerals, chapter markers, and book
divisions while preserving inline references and dates.
"""

import os
import re
import logging
from progress_tracker import ProgressTracker, get_file_stats
from optimized_regex_patterns import PATTERNS

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def is_roman_numeral_heading(line):
    """
    Determine if a line contains a Roman numeral being used as a heading.
    Returns True if it appears to be a structural heading, False if it's inline content.
    """
    line = line.strip()
    if not line:
        return False
    
    # Check if the entire line is just a Roman numeral (possibly with punctuation)
    clean_line = re.sub(r'[.\s\-–—]', '', line)
    if PATTERNS.is_roman_numeral(clean_line):
        # Additional checks to confirm it's a heading:
        # 1. Line is very short (headings are typically brief)
        if len(line) < 20:
            return True
        
    # Check for Roman numeral at start of line followed by heading indicators
    if PATTERNS.ROMAN_START_PATTERN.match(line):
        remaining = PATTERNS.ROMAN_START_PATTERN.sub('', line).strip()
        
        # If what remains looks like a heading
        heading_indicators = [
            'liber', 'book', 'cap', 'caput', 'capitulum', 'chapter',
            'pars', 'part', 'sectio', 'section', 'titulus', 'title'
        ]
        
        if not remaining or len(remaining) < 30:  # Very short or empty remainder
            return True
        
        for indicator in heading_indicators:
            if indicator in remaining.lower():
                return True
    
    return False

def is_chapter_heading(line):
    """Identify various forms of chapter/section headings using optimized patterns."""
    return PATTERNS.is_chapter_heading(line)

def is_title_or_author_line(line):
    """Identify title pages and author attribution lines."""
    line = line.strip()
    if not line:
        return False
    
    # Common title/author patterns
    title_patterns = [
        r'^\s*[A-Z\s]+$',  # All caps lines (often titles)
        r'^\s*AUCTORE?\s+',  # "AUCTORE" or "AUCTOR" 
        r'^\s*[Aa]uctore?\s+',  # "auctore"
        r'^\s*[Ss]cripsi?t\s+',  # "scripsit"
        r'^\s*[Cc]omposi?t\s+',  # "composit"
        r'^\s*[Aa]d\s+[A-Z]',  # "Ad [Name]" (dedicatory)
        r'^\s*FINIS\s*$',  # "FINIS"
        r'^\s*EXPLICIT',  # "EXPLICIT"
        r'^\s*INCIPIT',  # "INCIPIT"
    ]
    
    for pattern in title_patterns:
        if re.match(pattern, line):
            # Additional check: if it's all caps and reasonably short, likely a title
            if line.isupper() and len(line) < 100:
                return True
            return True
    
    return False

def remove_arabic_numerals(text):
    """Remove standalone Arabic numerals that are likely page numbers or section numbers."""
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        original_line = line
        line = line.strip()
        
        # Skip lines that are just numbers (likely page numbers)
        if re.match(r'^\s*\d+\s*\.?\s*$', line):
            continue
            
        # Remove numbers at the beginning of lines followed by periods (likely numbering)
        line = re.sub(r'^\s*\d+\.\s*', '', line)
        
        # Remove standalone numbers at end of lines (likely page numbers)
        line = re.sub(r'\s+\d+\s*$', '', line)
        
        cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)

def remove_structural_headings(text):
    """Remove various types of structural headings and markers."""
    lines = text.split('\n')
    cleaned_lines = []
    
    for line_num, line in enumerate(lines):
        original_line = line
        line = line.strip()
        
        # Skip empty lines (will be cleaned up later)
        if not line:
            cleaned_lines.append('')
            continue
        
        # Check for various types of headings
        skip_line = False
        
        # Roman numeral headings
        if is_roman_numeral_heading(line):
            logger.debug(f"Removing Roman numeral heading: {line}")
            skip_line = True
        
        # Chapter/section headings
        elif is_chapter_heading(line):
            logger.debug(f"Removing chapter heading: {line}")
            skip_line = True
        
        # Title/author lines
        elif is_title_or_author_line(line):
            logger.debug(f"Removing title/author line: {line}")
            skip_line = True
        
        # Lines that are mostly punctuation or separators
        elif re.match(r'^[\s\-–—\.=\*#]+$', line):
            logger.debug(f"Removing separator line: {line}")
            skip_line = True
        
        # Very short lines that might be headings (but preserve normal short lines)
        elif len(line) < 3 and not re.match(r'^[a-z]+$', line.lower()):
            logger.debug(f"Removing very short line: {line}")
            skip_line = True
        
        if not skip_line:
            cleaned_lines.append(original_line)
    
    text = '\n'.join(cleaned_lines)
    
    # Remove Arabic numerals
    text = remove_arabic_numerals(text)
    
    return text

def clean_inline_formatting(text):
    """Remove inline formatting that might interfere with training."""
    # Remove bold/italic markup
    text = re.sub(r"'''([^']+)'''", r'\1', text)  # Bold
    text = re.sub(r"''([^']+)''", r'\1', text)    # Italic
    
    # Remove other wiki-style formatting
    text = re.sub(r'\[\[([^\]]+)\]\]', r'\1', text)  # Links
    text = re.sub(r'\{\{[^\}]+\}\}', '', text)       # Templates
    
    return text

def process_file_headings(content):
    """Apply all heading removal steps to file content."""
    logger.debug("Removing structural headings...")
    content = remove_structural_headings(content)
    
    logger.debug("Cleaning inline formatting...")
    content = clean_inline_formatting(content)
    
    return content

def process_directory(input_dir, output_dir):
    """Process all txt files in a directory."""
    if not os.path.exists(input_dir):
        logger.warning(f"Input directory {input_dir} does not exist")
        return 0
        
    os.makedirs(output_dir, exist_ok=True)
    
    txt_files = [f for f in os.listdir(input_dir) if f.endswith('.txt')]
    processed = 0
    
    for filename in txt_files:
        try:
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(output_dir, filename)
            
            with open(input_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            cleaned_content = process_file_headings(content)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(cleaned_content)
            
            logger.debug(f"Removed headings from {filename}")
            processed += 1
            
        except Exception as e:
            logger.error(f"Error processing {filename}: {e}")
    
    return processed

def main():
    base_input = "content_cleaned"
    base_output = "headings_removed"
    
    logger.info("=== Step 4: Remove Headings and Section Indicators ===")
    
    # Create output directory structure
    os.makedirs(base_output, exist_ok=True)
    
    directories_to_process = [
        ("classical/prose", "classical/prose"),
        ("classical/poetry", "classical/poetry"),
        ("post_classical/prose", "post_classical/prose"),
        ("post_classical/poetry", "post_classical/poetry"),
        ("unknown_classification", "unknown_classification")
    ]
    
    total_processed = 0
    
    for input_subdir, output_subdir in directories_to_process:
        input_dir = os.path.join(base_input, input_subdir)
        output_dir = os.path.join(base_output, output_subdir)
        
        logger.info(f"Processing {input_subdir}...")
        processed = process_directory(input_dir, output_dir)
        total_processed += processed
        logger.info(f"Processed {processed} files in {input_subdir}")
    
    logger.info(f"Step 4 completed! Total files processed: {total_processed}")

if __name__ == "__main__":
    main()