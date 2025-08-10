#!/usr/bin/env python3
# This program's Mrs. Hudson~
"""
Step 3: Enhanced Text Content Cleaning
Removes metadata headers, category sections, source attributions, and intelligently
expands Latin abbreviations while preserving authentic Latin content.
Features gender-aware praenomina expansion and numeral disambiguation.
"""

import os
import re
import logging
from progress_tracker import ProgressTracker, get_file_stats

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Enhanced Latin abbreviation data structures based on classical and medieval sources

# Standard praenomina abbreviations (classical Roman names)
MALE_PRAENOMINA = {
    # Most common (>75% of population)
    'M\\.': 'Marcus',
    'L\\.': 'Lucius', 
    'C\\.': 'Gaius',
    'P\\.': 'Publius',
    'Q\\.': 'Quintus',
    
    # Other common praenomina
    'A\\.': 'Aulus',
    'Ap\\.': 'Appius',
    'Cn\\.': 'Gnaeus',
    'D\\.': 'Decimus',
    'K\\.': 'Kaeso',
    'M\'\.': 'Manius',  # Note: M'. different from M.
    'N\\.': 'Numerius',
    'S\\.': 'Spurius',
    'Ser\\.': 'Servius',
    'Sex\\.': 'Sextus',
    'Sp\\.': 'Spurius',
    'T\\.': 'Titus',
    'Ti\\.': 'Tiberius',
    'Tib\\.': 'Tiberius',
    'V\\.': 'Vibius',
    'Vol\\.': 'Volesus',
}

# Female praenomina (rare, mostly numerical or patronymic)
FEMALE_PRAENOMINA = {
    'Prima': 'Prima',
    'Secunda': 'Secunda', 
    'Tertia': 'Tertia',
    'Quarta': 'Quarta',
    'Quinta': 'Quinta',
    'Sexta': 'Sexta',
    'Septima': 'Septima',
    'Octavia': 'Octavia',
    'Nona': 'Nona',
    'Decima': 'Decima'
}

# Common Latin abbreviations (classical and medieval)
STANDARD_ABBREVIATIONS = {
    # Classical abbreviations
    r'\bq\.': 'que',
    r'\bc\.': 'cum',  
    r'\bet\s+c\.': 'et cetera',
    r'\bi\.\s*e\.': 'id est',
    r'\be\.\s*g\.': 'exempli gratia', 
    r'\bviz\.': 'videlicet',
    r'\bscil\.': 'scilicet',
    r'\bv\.': 'vide',
    r'\bcf\.': 'confer',
    r'\bib\.': 'ibidem',
    r'\bid\.': 'idem',
    r'\bloc\.\s*cit\.': 'loco citato',
    r'\bop\.\s*cit\.': 'opere citato',
    
    # Religious abbreviations (medieval)
    r'\bD\.\s*N\.': 'Dominus Noster',
    r'\bI\.\s*H\.\s*S\.': 'Iesus Hominum Salvator',
    r'\bX\.\s*P\.\s*S\.': 'Christus',
    r'\bD\.\s*M\.': 'Dis Manibus',  # "To the Divine Spirits"
    r'\bR\.\s*I\.\s*P\.': 'Requiescat In Pace',
    r'\bA\.\s*D\.': 'Anno Domini',
    r'\bA\.\s*M\.': 'Ave Maria',
    
    # Common contractions
    r'\bxpts': 'Christus',
    r'\bihs': 'Iesus',
    r'\bdns': 'dominus',
    r'\bsps': 'spiritus',
    r'\bscs': 'sanctus',
    r'\bepa': 'episcopa',
    r'\beps': 'episcopus',
    
    # Ordinals and titles
    r'\bImp\.': 'Imperator',
    r'\bCaes\.': 'Caesar',
    r'\bAug\.': 'Augustus',
    r'\bCos\.': 'Consul',
    r'\bTrib\.': 'Tribunus',
    r'\bPont\.': 'Pontifex',
    r'\bMax\.': 'Maximus',
}

# Roman numeral patterns (to avoid expanding as names)
ROMAN_NUMERAL_PATTERN = r'\b(?=[MDCLXVI])M{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})\b'

# Gender context indicators for praenomina expansion
MASCULINE_CONTEXT_WORDS = [
    'filius', 'pater', 'vir', 'maritus', 'rex', 'dux', 'comes', 'miles',
    'consul', 'imperator', 'caesar', 'augustus', 'pontifex', 'tribunus'
]

FEMININE_CONTEXT_WORDS = [
    'filia', 'mater', 'uxor', 'regina', 'domina', 'matrona', 'virgo',
    'sponsa', 'vidua', 'imperatrix', 'augusta'
]

def remove_metadata_header(text):
    """Remove the metadata header section from the beginning of the text."""
    lines = text.split('\n')
    content_start = 0
    
    # Find the end of metadata (separator line with dashes)
    for i, line in enumerate(lines):
        if line.strip().startswith('--') and len(line.strip()) > 10:
            content_start = i + 1
            break
        elif i > 20:  # If no separator found in first 20 lines, assume no header
            content_start = 0
            break
    
    # Return content after header
    return '\n'.join(lines[content_start:])

def remove_category_sections(text):
    """Enhanced removal of category sections and metadata commonly found at text endings."""
    # Remove entire Commentarium sections (like ==Commentarium==)
    text = re.sub(r'==\s*Commentarium\s*==.*$', '', text, flags=re.MULTILINE | re.DOTALL)
    
    # Remove category lines (handles both Categoria: and Category:)
    text = re.sub(r'^Categoria?:\s*.*$', '', text, flags=re.MULTILINE | re.IGNORECASE)
    
    # Remove multiple consecutive category lines
    text = re.sub(r'(^Categoria?:\s*.*\n?){2,}', '', text, flags=re.MULTILINE | re.IGNORECASE)
    
    # Remove standalone category sections at the end
    text = re.sub(r'\n+(?:Categoria?:\s*.*\n?)+$', '', text, flags=re.IGNORECASE)
    
    return text

def remove_source_attributions(text):
    """Enhanced removal of source attributions and metadata with line-by-line filtering."""
    # First pass: Line-by-line filtering for robust removal
    lines = text.split('\n')
    
    # Remove lines containing "Exported from Wikisource" 
    lines = [line for line in lines if 'Exported from Wikisource' not in line]
    
    # Remove everything from "About this digital edition" line onwards
    filtered_lines = []
    for line in lines:
        if line.strip().startswith('About this digital edition'):
            logger.debug("Found 'About this digital edition' - truncating content here")
            break
        filtered_lines.append(line)
    
    # Rejoin text for further processing
    text = '\n'.join(filtered_lines)
    
    # Second pass: Regex-based cleanup for remaining patterns
    # Remove any remaining Wikisource export references
    text = re.sub(r'.*Exported from Wikisource.*\n?', '', text, flags=re.IGNORECASE)
    
    # Remove any remaining "About this digital edition" sections (backup)
    text = re.sub(r'About this digital edition.*$', '', text, flags=re.MULTILINE | re.DOTALL)
    
    # Apply enhanced category removal
    text = remove_category_sections(text)
    
    # Remove source URLs and references
    text = re.sub(r'Source:\s*https?://.*\n?', '', text, flags=re.IGNORECASE)
    text = re.sub(r'https?://[^\s]+', '', text)
    
    # Remove editorial notes in brackets/parentheses that contain non-Latin
    text = re.sub(r'\[.*?(?:ed\.|edit\.|source|wiki).*?\]', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\(.*?(?:ed\.|edit\.|source|wiki).*?\)', '', text, flags=re.IGNORECASE)
    
    # Remove editor/publisher attribution patterns
    text = re.sub(r'.*(?:von Bunge|Napiersky).*possint.*', '', text, flags=re.IGNORECASE)
    
    # Additional cleanup patterns that might be missed
    # Remove lines that are clearly digital metadata
    lines = text.split('\n')
    clean_lines = []
    
    for line in lines:
        line_lower = line.lower().strip()
        
        # Skip lines that are clearly metadata/digital artifacts
        skip_patterns = [
            'exported by', 'generated by', 'digitized by', 'scanned by',
            'copyright', '©', 'all rights reserved', 'permission',
            'this text was', 'this edition', 'digital edition',
            'ocr', 'optical character', 'text recognition'
        ]
        
        should_skip = False
        for pattern in skip_patterns:
            if pattern in line_lower:
                should_skip = True
                logger.debug(f"Skipping metadata line: {line[:50]}...")
                break
        
        if not should_skip:
            clean_lines.append(line)
    
    return '\n'.join(clean_lines)

def remove_toc_and_navigation(text):
    """Remove table of contents and navigation elements."""
    # Remove TOC markers
    text = re.sub(r'__TOC__', '', text)
    
    # Remove section navigation
    text = re.sub(r'==+.*?==+', '', text)
    text = re.sub(r'===+.*?===+', '', text)
    
    return text

def clean_non_latin_content(text):
    """Remove content that's clearly not Latin text."""
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        
        # Skip empty lines (will be handled later)
        if not line:
            cleaned_lines.append('')
            continue
            
        # Skip lines that are primarily metadata/markup
        if (line.startswith('Title:') or 
            line.startswith('Source:') or 
            line.startswith('Category:') or
            line.startswith('Text Type:') or
            line.startswith('#') or
            line.startswith('{{') or
            line.startswith('}}') or
            line.startswith('[[') or
            line.startswith(']]')):
            continue
            
        # Skip lines with modern language indicators
        modern_indicators = [
            'english', 'deutsch', 'français', 'español', 'italiano',
            'translation', 'note:', 'see also', 'external link',
            'bibliography', 'reference', 'isbn', 'doi:'
        ]
        
        skip_line = False
        line_lower = line.lower()
        for indicator in modern_indicators:
            if indicator in line_lower:
                skip_line = True
                break
        
        if skip_line:
            continue
            
        cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)

def standardize_punctuation(text):
    """Standardize punctuation, keeping only what's appropriate for Latin."""
    # Keep only standard punctuation marks useful for Latin
    allowed_punctuation = set('.,:;!?\'"-()[]')
    
    # Remove excessive punctuation and special characters
    # But preserve basic punctuation structure
    cleaned_chars = []
    
    for char in text:
        if (char.isalpha() or 
            char.isspace() or 
            char in allowed_punctuation or
            char.isdigit()):  # Keep digits for now (Roman numerals), will handle later
            cleaned_chars.append(char)
        # Convert some special punctuation
        elif char in '""''':
            cleaned_chars.append('"')
        elif char in '–—':
            cleaned_chars.append('-')
        # Skip other special characters
    
    text = ''.join(cleaned_chars)
    
    # Clean up excessive punctuation
    text = re.sub(r'\.{2,}', '.', text)  # Multiple periods
    text = re.sub(r',{2,}', ',', text)   # Multiple commas
    text = re.sub(r';{2,}', ';', text)   # Multiple semicolons
    text = re.sub(r':{2,}', ':', text)   # Multiple colons
    
    return text

def is_roman_numeral(text):
    """Check if a text segment is a Roman numeral to avoid expanding as name."""
    return bool(re.fullmatch(ROMAN_NUMERAL_PATTERN, text.upper()))

def detect_gender_context(text_segment, position):
    """
    Detect gender context around a position in text for praenomina expansion.
    Returns 'masculine', 'feminine', or 'unknown'
    """
    # Look in a window around the position for gender indicators
    window_start = max(0, position - 100)
    window_end = min(len(text_segment), position + 100)
    context = text_segment[window_start:window_end].lower()
    
    masculine_count = sum(1 for word in MASCULINE_CONTEXT_WORDS if word in context)
    feminine_count = sum(1 for word in FEMININE_CONTEXT_WORDS if word in context)
    
    if masculine_count > feminine_count:
        return 'masculine'
    elif feminine_count > masculine_count:
        return 'feminine'
    else:
        return 'unknown'

def expand_praenomina_contextually(text):
    """
    Intelligently expand praenomina abbreviations with gender awareness and numeral disambiguation.
    """
    expanded_text = text
    expansions_made = []
    
    # Process each potential praenomina match
    for abbreviation, full_name in MALE_PRAENOMINA.items():
        pattern = r'\b' + abbreviation + r'(?=\s[A-Z])'  # Must be followed by capitalized word (nomen/cognomen)
        matches = list(re.finditer(pattern, expanded_text))
        
        for match in reversed(matches):  # Reverse to maintain positions during replacement
            matched_text = match.group(0)
            position = match.start()
            
            # Skip if it's actually a Roman numeral
            if is_roman_numeral(matched_text.replace('.', '')):
                logger.debug(f"Skipping Roman numeral: {matched_text}")
                continue
            
            # Get context and determine if expansion is appropriate
            context = detect_gender_context(expanded_text, position)
            
            # Expand if context suggests masculine or if context is unknown but common praenomina
            if (context in ['masculine', 'unknown'] and 
                abbreviation in ['M\\.', 'L\\.', 'C\\.', 'P\\.', 'Q\\.']):  # Most common ones
                
                expanded_text = expanded_text[:match.start()] + full_name + expanded_text[match.end():]
                expansions_made.append(f"{matched_text} → {full_name} ({context} context)")
                logger.debug(f"Expanded praenomen: {matched_text} → {full_name} (context: {context})")
    
    return expanded_text, expansions_made

def expand_standard_abbreviations(text):
    """Expand standard Latin abbreviations that are unambiguous."""
    expansions_made = []
    
    for pattern, replacement in STANDARD_ABBREVIATIONS.items():
        matches = list(re.finditer(pattern, text, flags=re.IGNORECASE))
        if matches:
            for match in matches:
                expansions_made.append(f"{match.group(0)} → {replacement}")
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
            logger.debug(f"Expanded abbreviation: {pattern} → {replacement}")
    
    return text, expansions_made

def expand_abbreviations_enhanced(text):
    """
    Enhanced abbreviation expansion with comprehensive Latin abbreviations,
    gender-aware praenomina expansion, and numeral disambiguation.
    """
    logger.debug("Starting enhanced abbreviation expansion...")
    
    # First expand standard abbreviations (safer, unambiguous)
    text, standard_expansions = expand_standard_abbreviations(text)
    
    # Then expand praenomina with context awareness
    text, praenomen_expansions = expand_praenomina_contextually(text)
    
    # Log summary
    total_expansions = len(standard_expansions) + len(praenomen_expansions)
    if total_expansions > 0:
        logger.info(f"Made {total_expansions} abbreviation expansions:")
        for expansion in standard_expansions[:5]:  # Show first 5
            logger.debug(f"  Standard: {expansion}")
        for expansion in praenomen_expansions[:5]:  # Show first 5  
            logger.debug(f"  Praenomen: {expansion}")
        if total_expansions > 10:
            logger.debug(f"  ... and {total_expansions - 10} more")
    
    return text

def clean_text_content_with_logging(text, progress):
    """Apply all enhanced content cleaning steps with detailed progress logging."""
    original_text = text
    
    progress.log_operation("Step 1: Removing metadata header", "Cleaning document headers and metadata")
    text = remove_metadata_header(text)
    progress.log_text_analysis(original_text, text, "Metadata header removal")
    
    step_text = text
    progress.log_operation("Step 2: Removing source attributions", "Cleaning source attributions and categories")
    text = remove_source_attributions(text)
    
    # Count categories removed
    categories_removed = len(re.findall(r'Categoria?:', step_text, re.IGNORECASE)) - len(re.findall(r'Categoria?:', text, re.IGNORECASE))
    if categories_removed > 0:
        progress.log_operation("Categories removed", f"Successfully removed {categories_removed} category sections", True, categories_removed)
    
    step_text = text
    progress.log_operation("Step 3: Removing TOC and navigation", "Cleaning table of contents and navigation elements")
    text = remove_toc_and_navigation(text)
    progress.log_text_analysis(step_text, text, "TOC and navigation removal")
    
    step_text = text
    progress.log_operation("Step 4: Cleaning non-Latin content", "Removing non-Latin text and formatting")
    text = clean_non_latin_content(text)
    progress.log_text_analysis(step_text, text, "Non-Latin content cleaning")
    
    step_text = text
    progress.log_operation("Step 5: Standardizing punctuation", "Normalizing punctuation and spacing")
    text = standardize_punctuation(text)
    if len(step_text) != len(text):
        progress.log_operation("Punctuation standardized", f"Modified {abs(len(step_text) - len(text))} characters")
    
    step_text = text
    progress.log_operation("Step 6: Expanding abbreviations", "Applying enhanced abbreviation expansion")
    
    # Count abbreviations before expansion
    abbrev_before = len(re.findall(r'\b[A-Z]\.(?:\s[A-Z]\.)*', step_text))
    text = expand_abbreviations_enhanced(text)
    abbrev_after = len(re.findall(r'\b[A-Z]\.(?:\s[A-Z]\.)*', text))
    
    expansions_made = abbrev_before - abbrev_after
    if expansions_made > 0:
        progress.log_operation("Abbreviations expanded", f"Expanded {expansions_made} abbreviations", True, expansions_made)
    
    progress.log_operation("Step 7: Final cleanup", "Removing excessive whitespace and normalizing text")
    # Final cleanup - remove excessive whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)  # Max 2 consecutive newlines
    text = re.sub(r'[ \t]+', ' ', text)     # Normalize spaces
    text = text.strip()
    
    # Final analysis
    progress.log_text_analysis(original_text, text, "Complete cleaning pipeline")
    progress.log_operation("Content cleaning completed", f"All {7} cleaning steps applied successfully")
    
    return text

def clean_text_content(text):
    """Apply all enhanced content cleaning steps (legacy version without logging)."""
    logger.debug("Removing metadata header...")
    text = remove_metadata_header(text)
    
    logger.debug("Removing source attributions and categories...")
    text = remove_source_attributions(text)
    
    logger.debug("Removing TOC and navigation...")
    text = remove_toc_and_navigation(text)
    
    logger.debug("Cleaning non-Latin content...")
    text = clean_non_latin_content(text)
    
    logger.debug("Standardizing punctuation...")
    text = standardize_punctuation(text)
    
    logger.debug("Expanding abbreviations with enhanced intelligence...")
    text = expand_abbreviations_enhanced(text)
    
    # Final cleanup - remove excessive whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)  # Max 2 consecutive newlines
    text = re.sub(r'[ \t]+', ' ', text)     # Normalize spaces
    text = text.strip()
    
    return text

def process_directory(input_dir, output_dir):
    """Process all txt files in a directory with enhanced cleaning and detailed progress tracking."""
    if not os.path.exists(input_dir):
        logger.warning(f"Input directory {input_dir} does not exist")
        return 0
        
    os.makedirs(output_dir, exist_ok=True)
    
    # Create cleaning report directory
    report_dir = os.path.join(output_dir, "cleaning_reports")
    os.makedirs(report_dir, exist_ok=True)
    
    txt_files = [f for f in os.listdir(input_dir) if f.endswith('.txt')]
    
    # Initialize enhanced progress tracker for this directory
    dir_name = os.path.basename(input_dir)
    progress = ProgressTracker(
        "step3", 
        len(txt_files), 
        f"Enhanced Content Cleaning: Remove metadata, expand abbreviations, clean non-Latin content for {dir_name}"
    )
    
    # Summary statistics
    total_categories_removed = 0
    total_expansions_made = 0
    total_lines_cleaned = 0
    
    for filename in txt_files:
        input_path = os.path.join(input_dir, filename)
        output_path = os.path.join(output_dir, filename)
        
        # Get file stats and start progress tracking
        file_stats = get_file_stats(input_path)
        progress.start_file(filename, input_path, file_stats['size'])
        
        try:
            progress.log_operation("Loading file content", "Reading original text for processing")
            with open(input_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            original_length = len(original_content)
            original_lines = len(original_content.split('\n'))
            
            progress.log_operation("Content loaded", f"Original: {original_length:,} chars, {original_lines} lines")
            
            # Check for categories before cleaning
            category_count = len(re.findall(r'Categoria?:', original_content, re.IGNORECASE))
            if category_count > 0:
                progress.log_operation("Categories detected", f"Found {category_count} category sections to remove", True, category_count)
            
            # Start comprehensive text cleaning with detailed logging
            progress.log_operation("Starting content cleaning pipeline", "Applying all cleaning transformations")
            
            # Clean the content with enhanced logging
            cleaned_content = clean_text_content_with_logging(original_content, progress)
            
            # Analyze results
            cleaned_length = len(cleaned_content)
            cleaned_lines = len(cleaned_content.split('\n'))
            lines_processed = max(original_lines, cleaned_lines)
            
            # Calculate reduction statistics
            size_reduction = original_length - cleaned_length
            line_change = cleaned_lines - original_lines
            
            progress.log_operation("Analyzing cleaning results", 
                                 f"Size change: {size_reduction:+,} chars, Line change: {line_change:+d}")
            
            # Get actual abbreviation count from the detailed logger stats
            expansions_made = progress.detailed_logger.stats.get('expansions_made', 0)
            categories_removed = progress.detailed_logger.stats.get('categories_removed', 0)
            
            # Save cleaned content
            progress.log_operation("Saving cleaned content", f"Writing to {output_path}")
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(cleaned_content)
            
            progress.log_file_operation("Write cleaned file", "", output_path, True)
            
            # Update tracking statistics
            total_categories_removed += categories_removed
            total_expansions_made += expansions_made
            total_lines_cleaned += lines_processed
            
            # Create detailed summary
            summary_parts = []
            if size_reduction > 0:
                summary_parts.append(f"reduced by {size_reduction:,} chars")
            if categories_removed > 0:
                summary_parts.append(f"{categories_removed} categories removed")
            if expansions_made > 0:
                summary_parts.append(f"{expansions_made} abbreviations expanded")
            
            summary = "Cleaned successfully"
            if summary_parts:
                summary += f": {', '.join(summary_parts)}"
            
            progress.finish_file(success=True, 
                               lines_processed=lines_processed,
                               bytes_processed=cleaned_length,
                               expansions_made=expansions_made,
                               categories_removed=categories_removed,
                               summary=summary)
            
        except Exception as e:
            error_msg = f"Content cleaning error: {e}"
            progress.log_operation("Processing failed", f"Exception during cleaning: {str(e)}", False)
            progress.finish_file(success=False, error_msg=error_msg)
    
    # Update final progress statistics
    progress.stats.update({
        'categories_removed': total_categories_removed,
        'expansions_made': total_expansions_made
    })
    
    # Print enhanced progress summary
    final_stats = progress.print_summary()
    
    # Save processing report
    try:
        report_path = os.path.join(report_dir, "cleaning_summary.txt")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("=== Enhanced Text Cleaning Report ===\n\n")
            f.write(f"Files processed: {final_stats['files_processed']}\n")
            f.write(f"Category sections removed: {total_categories_removed}\n") 
            f.write(f"Abbreviations expanded: {total_expansions_made}\n")
            f.write(f"Lines processed: {total_lines_cleaned:,}\n")
            f.write(f"Errors encountered: {final_stats['errors']}\n\n")
            f.write("Enhanced features applied:\n")
            f.write("✓ Intelligent category section removal\n")
            f.write("✓ Gender-aware praenomina expansion\n")
            f.write("✓ Roman numeral disambiguation\n")
            f.write("✓ Comprehensive Latin abbreviation expansion\n")
            f.write("✓ Enhanced punctuation standardization\n")
            f.write("✓ Line-by-line metadata filtering\n")
        
        progress.log_progress(f"Saved cleaning report to {report_path}")
    except Exception as e:
        progress.log_progress(f"Could not save cleaning report: {e}", "warning")
    
    return final_stats['files_processed']

def main():
    base_input = "sorted_texts"
    base_output = "content_cleaned"
    
    logger.info("=== Step 3: Enhanced Text Content Cleaning ===")
    logger.info("Features: Category removal, intelligent abbreviation expansion, gender-aware praenomina")
    
    # Create output directory structure
    os.makedirs(base_output, exist_ok=True)
    
    # Updated to handle new mixed genre directory structure
    directories_to_process = [
        ("classical/prose", "classical/prose"),
        ("classical/poetry", "classical/poetry"),
        ("classical/mixed", "classical/mixed"),
        ("post_classical/prose", "post_classical/prose"),
        ("post_classical/poetry", "post_classical/poetry"),
        ("post_classical/mixed", "post_classical/mixed"),
    ]
    
    total_processed = 0
    
    for input_subdir, output_subdir in directories_to_process:
        input_dir = os.path.join(base_input, input_subdir)
        output_dir = os.path.join(base_output, output_subdir)
        
        if os.path.exists(input_dir):
            logger.info(f"Processing {input_subdir}...")
            processed = process_directory(input_dir, output_dir)
            total_processed += processed
            logger.info(f"Enhanced cleaning completed for {processed} files in {input_subdir}")
        else:
            logger.debug(f"Skipping non-existent directory: {input_subdir}")
    
    logger.info(f"\n=== Enhanced Cleaning Summary ===")
    logger.info(f"✅ Total files processed: {total_processed}")
    logger.info(f"🧹 Features applied:")
    logger.info(f"   • Category section removal (==Commentarium== and Categoria: lines)")
    logger.info(f"   • Gender-aware praenomina expansion (M. → Marcus, etc.)")
    logger.info(f"   • Roman numeral disambiguation") 
    logger.info(f"   • Comprehensive Latin abbreviation expansion")
    logger.info(f"   • Enhanced punctuation standardization")
    logger.info(f"📋 Detailed reports saved in cleaning_reports/ directories")
    logger.info(f"🎯 Core Latin content is now clean and ready for further processing!")

if __name__ == "__main__":
    main()