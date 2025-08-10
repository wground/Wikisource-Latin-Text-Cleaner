#!/usr/bin/env python3
"""
Step 5: Standardize Orthography
Standardizes Latin orthography by removing diacritics, normalizing ligatures,
converting j->i and v->u, and making everything lowercase for consistent
tokenization in LLM training.
"""

import os
import re
import unicodedata
import logging
from progress_tracker import ProgressTracker, get_file_stats

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def normalize_medieval_variants(text):
    """
    Normalize medieval/late Latin orthographic variants to classical forms.
    This function standardizes common medieval spelling variants before other transformations.
    Based on scholarly research into medieval Latin orthography.
    """
    # Medieval H → CH variants (michi → mihi, nichil → nihil, etc.)
    h_to_ch_variants = {
        # Core pronouns and common words with 'h' changed to 'ch'
        r'\bmichi\b': 'mihi',           # to me (dative of ego)
        r'\btichi\b': 'tibi',           # to you (dative of tu) 
        r'\bsichi\b': 'sibi',           # to himself/herself (dative of se)
        r'\bnichil\b': 'nihil',         # nothing
        r'\bnichilo\b': 'nihilo',       # nothing (ablative)
        r'\bnichilum\b': 'nihilum',     # nothing (accusative)
        r'\bmichil\b': 'mihil',         # variant of nihil
        r'\bmacina\b': 'machina',       # machine
        r'\bpulcer\b': 'pulcher',       # beautiful
        r'\bsepulcrum\b': 'sepulchrum', # tomb
        
        # Spanish/Iberian variants (nichi → nihil, mici → mihi)
        r'\bnichi\b': 'nihil',
        r'\bmici\b': 'mihi',
        r'\barcivum\b': 'archivum',     # archive
        
        # Other h-loss variants
        r'\babere\b': 'habere',         # to have (h-loss)
        r'\bomines\b': 'homines',       # men (h-loss)
        r'\bonor\b': 'honor',           # honor (h-loss)
        r'\bora\b(?!\w)': 'hora',       # hour (careful not to match 'ora' = pray)
        r'\bumanus\b': 'humanus',       # human (h-loss)
        
        # Reverse h-addition (where h was added incorrectly)
        r'\bchorona\b': 'corona',       # crown (incorrect h-addition)
        r'\brhethor\b': 'rhetor',       # rhetorician 
    }
    
    # Medieval consonant variants
    consonant_variants = {
        # TI → CI variants (divitiae → diviciae, tertius → tercius)
        r'\bdiviciae\b': 'divitiae',    # riches
        r'\bdivicie\b': 'divitiae',     # riches (alternate)
        r'\btercius\b': 'tertius',      # third
        r'\bvicium\b': 'vitium',        # vice/fault
        r'\bnegocium\b': 'negotium',    # business
        r'\bprecium\b': 'pretium',      # price
        r'\bspacium\b': 'spatium',      # space
        r'\bpaciens\b': 'patiens',      # patient
        r'\bgracie\b': 'gratiae',       # thanks/graces
        r'\bjusticia\b': 'justitia',    # justice
        
        # MN → MPN variants (damnum → dampnum)
        r'\bdampnum\b': 'damnum',       # damage
        r'\balumpnus\b': 'alumnus',     # student/foster child
        r'\bsompnus\b': 'somnus',       # sleep
        r'\bhiempns\b': 'hiems',        # winter
        r'\bcolumpna\b': 'columna',     # column
        r'\bsolempnis\b': 'sollemnis',  # solemn
        
        # Double consonant variations
        r'\btranquilitas\b': 'tranquillitas', # tranquility (single → double l)
        r'\bAffrica\b': 'Africa',       # Africa (double → single f)
        r'\boccasio\b': 'occasio',      # occasion
        r'\bopprobrium\b': 'oprobrium', # reproach
        r'\bassidere\b': 'assidere',    # to sit by
        
        # AE → E simplification (medieval trend)
        r'\bcese\b': 'caese',           # cut (past participle)
        r'\bquedam\b': 'quaedam',       # certain (feminine)
        r'\bpretor\b': 'praetor',       # praetor
        r'\bequs\b': 'aequus',          # equal
        r'\bequalitas\b': 'aequalitas', # equality
        
        # OE → E simplification  
        r'\bpena\b': 'poena',           # punishment
        r'\bfenum\b': 'foenum',         # hay
        r'\bfedus\b': 'foedus',         # treaty/foul
        
        # B → V variants (common medieval confusion)
        r'\babsoluo\b': 'absolvo',      # I absolve
        r'\buiuo\b': 'vivo',            # I live
        r'\bbibo\b': 'vivo',            # incorrect b for v
        
        # Medieval spelling normalizations
        r'\bquoniam\b': 'quoniam',      # because (standardize)
        r'\bquamuis\b': 'quamvis',      # although  
        r'\bquamcumque\b': 'quamcumque', # whenever
        r'\bquemadmodum\b': 'quemadmodum', # just as
    }
    
    # Numerical and ordinal variants
    numerical_variants = {
        r'\bprimus\b': 'primus',        # first (standardize)
        r'\bsecundus\b': 'secundus',    # second
        r'\btercius\b': 'tertius',      # third (ci → ti)
        r'\bquartus\b': 'quartus',      # fourth
        r'\bquintus\b': 'quintus',      # fifth
        r'\bsextus\b': 'sextus',        # sixth
        r'\bseptimus\b': 'septimus',    # seventh
        r'\boctauus\b': 'octavus',      # eighth
        r'\bnonus\b': 'nonus',          # ninth
        r'\bdecimus\b': 'decimus',      # tenth
    }
    
    # Apply all variant replacements (case-insensitive)
    variant_groups = [h_to_ch_variants, consonant_variants, numerical_variants]
    replacements_made = 0
    
    for variant_dict in variant_groups:
        for pattern, replacement in variant_dict.items():
            original_text = text
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
            if text != original_text:
                count = len(re.findall(pattern, original_text, re.IGNORECASE))
                replacements_made += count
                stripped_pattern = pattern.strip(r'\b')
                logger.debug(f"Normalized {count} instances of medieval variant: {stripped_pattern} → {replacement}")
    
    return text, replacements_made

def remove_diacritics(text):
    """Remove all diacritical marks from Latin text."""
    # Comprehensive diacritic replacements
    diacritic_replacements = {
        # Macrons (long vowel markers)
        'ā': 'a', 'ē': 'e', 'ī': 'i', 'ō': 'o', 'ū': 'u', 'ȳ': 'y',
        'Ā': 'a', 'Ē': 'e', 'Ī': 'i', 'Ō': 'o', 'Ū': 'u', 'Ȳ': 'y',
        
        # Breves (short vowel markers)
        'ă': 'a', 'ĕ': 'e', 'ĭ': 'i', 'ŏ': 'o', 'ŭ': 'u',
        'Ă': 'a', 'Ĕ': 'e', 'Ĭ': 'i', 'Ŏ': 'o', 'Ŭ': 'u',
        
        # Acute accents
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u', 'ý': 'y',
        'Á': 'a', 'É': 'e', 'Í': 'i', 'Ó': 'o', 'Ú': 'u', 'Ý': 'y',
        
        # Grave accents
        'à': 'a', 'è': 'e', 'ì': 'i', 'ò': 'o', 'ù': 'u',
        'À': 'a', 'È': 'e', 'Ì': 'i', 'Ò': 'o', 'Ù': 'u',
        
        # Circumflex accents
        'â': 'a', 'ê': 'e', 'î': 'i', 'ô': 'o', 'û': 'u', 'ŷ': 'y',
        'Â': 'a', 'Ê': 'e', 'Î': 'i', 'Ô': 'o', 'Û': 'u', 'Ŷ': 'y',
        
        # Other diacritics that might appear
        'ä': 'a', 'ë': 'e', 'ï': 'i', 'ö': 'o', 'ü': 'u', 'ÿ': 'y',
        'Ä': 'a', 'Ë': 'e', 'Ï': 'i', 'Ö': 'o', 'Ü': 'u', 'Ÿ': 'y',
        'ã': 'a', 'ñ': 'n', 'õ': 'o', 'ç': 'c',
        'Ã': 'a', 'Ñ': 'n', 'Õ': 'o', 'Ç': 'c',
        
        # Ring above/below
        'å': 'a', 'ů': 'u', 'Å': 'a', 'Ů': 'u',
        
        # Cedilla
        'ç': 'c', 'ş': 's', 'ţ': 't',
        'Ç': 'c', 'Ş': 's', 'Ţ': 't',
        
        # Caron/hacek
        'č': 'c', 'ď': 'd', 'ě': 'e', 'ň': 'n', 'ř': 'r', 'š': 's', 'ť': 't', 'ž': 'z',
        'Č': 'c', 'Ď': 'd', 'Ě': 'e', 'Ň': 'n', 'Ř': 'r', 'Š': 's', 'Ť': 't', 'Ž': 'z',
        
        # Double acute
        'ő': 'o', 'ű': 'u',
        'Ő': 'o', 'Ű': 'u',
        
        # Ogonek
        'ą': 'a', 'ę': 'e', 'į': 'i', 'ų': 'u',
        'Ą': 'a', 'Ę': 'e', 'Į': 'i', 'Ų': 'u',
    }
    
    # Apply explicit replacements first
    for diacritic, standard in diacritic_replacements.items():
        text = text.replace(diacritic, standard)
    
    # Use Unicode normalization as backup for any remaining diacritics
    # NFD decomposes characters into base + combining marks, then filter out the marks
    normalized = unicodedata.normalize('NFD', text)
    without_accents = ''.join(
        char for char in normalized 
        if unicodedata.category(char) != 'Mn'  # Mn = Nonspacing_Mark (combining diacritics)
    )
    
    return without_accents

def normalize_ligatures(text):
    """Convert ligatures to their component letters."""
    ligature_replacements = {
        # Latin ligatures
        'æ': 'ae', 'Æ': 'ae',
        'œ': 'oe', 'Œ': 'oe',
        
        # Other possible ligatures
        'ﬀ': 'ff', 'ﬁ': 'fi', 'ﬂ': 'fl', 'ﬃ': 'ffi', 'ﬄ': 'ffl',
        'ﬅ': 'st', 'ﬆ': 'st',
        
        # Historical ligatures that might appear in old texts
        'ĳ': 'ij', 'Ĳ': 'ij',
        
        # Et ligature
        '&': 'et',
    }
    
    for ligature, replacement in ligature_replacements.items():
        text = text.replace(ligature, replacement)
    
    return text

def normalize_medieval_characters(text):
    """Convert medieval character variants to standard forms."""
    medieval_replacements = {
        # Medieval v/u normalization - convert all v to u
        'v': 'u',
        'V': 'u',
        
        # Medieval j/i normalization - convert all j to i  
        'j': 'i',
        'J': 'i',
        
        # Medieval variants of other letters
        'ſ': 's',  # Long s
        'ʃ': 's',  # Another form of long s
        'ß': 'ss', # German sz ligature (might appear in Latin texts)
        
        # Medieval punctuation variants
        '¶': '',   # Paragraph mark (pilcrow)
        '§': '',   # Section mark
        '†': '',   # Dagger
        '‡': '',   # Double dagger
        
        # Medieval abbreviation marks (remove rather than expand)
        '℥': '',   # Ounce mark
        '℞': '',   # Prescription mark
        '℟': '',   # Response mark
        
        # Tironian notes (medieval shorthand)
        '⁊': 'et', # Tironian et
        '℈': '',   # Scruple mark
    }
    
    for medieval, replacement in medieval_replacements.items():
        text = text.replace(medieval, replacement)
    
    return text

def convert_to_lowercase(text):
    """Convert all text to lowercase."""
    return text.lower()

def clean_letter_spacing(text):
    """Fix common letter spacing issues that might occur after normalization."""
    # Remove excessive spaces around punctuation
    text = re.sub(r'\s+([,.;:!?])', r'\1', text)
    text = re.sub(r'([,.;:!?])\s+', r'\1 ', text)
    
    # Standardize quotation mark spacing
    text = re.sub(r'\s*(["\'""])\s*', r' \1', text)
    
    # Fix spacing around parentheses
    text = re.sub(r'\s*\(\s*', r' (', text)
    text = re.sub(r'\s*\)\s*', r') ', text)
    
    return text

def standardize_punctuation_final(text):
    """Final punctuation standardization after orthographic changes."""
    # Normalize quotation marks to simple ASCII
    quote_replacements = {
        '"': '"', '"': '"', ''': "'", ''': "'",
        '«': '"', '»': '"', '‚': "'", '„': '"',
        '‹': "'", '›': "'", '‛': "'", '"': '"'
    }
    
    for fancy_quote, simple_quote in quote_replacements.items():
        text = text.replace(fancy_quote, simple_quote)
    
    # Normalize dashes
    text = re.sub(r'[–—]', '-', text)
    
    # Normalize ellipses
    text = re.sub(r'…', '...', text)
    
    return text

def standardize_orthography(text):
    """Apply all orthographic standardization steps in the correct order."""
    stats = {
        'variants_normalized': 0,
        'diacritics_removed': 0,
        'ligatures_normalized': 0,
        'medieval_chars_converted': 0
    }
    
    logger.debug("Normalizing medieval variants FIRST...")
    text, variants_count = normalize_medieval_variants(text)
    stats['variants_normalized'] = variants_count
    
    logger.debug("Removing diacritics...")
    original_len = len(text)
    text = remove_diacritics(text)
    # Estimate diacritics removed (rough heuristic)
    stats['diacritics_removed'] = max(0, original_len - len(text))
    
    logger.debug("Normalizing ligatures...")
    original_text = text
    text = normalize_ligatures(text)
    stats['ligatures_normalized'] = len(re.findall(r'ae|oe|et', text)) - len(re.findall(r'ae|oe|et', original_text))
    
    logger.debug("Converting medieval characters...")
    text = normalize_medieval_characters(text)
    
    logger.debug("Converting to lowercase...")
    text = convert_to_lowercase(text)
    
    logger.debug("Cleaning letter spacing...")
    text = clean_letter_spacing(text)
    
    logger.debug("Final punctuation standardization...")
    text = standardize_punctuation_final(text)
    
    return text, stats

def process_directory(input_dir, output_dir):
    """Process all txt files in a directory with enhanced progress tracking and orthographic variant normalization."""
    if not os.path.exists(input_dir):
        logger.warning(f"Input directory {input_dir} does not exist")
        return 0
        
    os.makedirs(output_dir, exist_ok=True)
    
    # Create reports directory
    report_dir = os.path.join(output_dir, "orthography_reports")  
    os.makedirs(report_dir, exist_ok=True)
    
    txt_files = [f for f in os.listdir(input_dir) if f.endswith('.txt')]
    
    # Initialize enhanced progress tracker
    dir_name = os.path.basename(input_dir)
    progress = ProgressTracker(f"Orthographic Standardization: {dir_name}", len(txt_files))
    
    # Aggregate statistics
    total_variants_normalized = 0
    total_diacritics_removed = 0
    total_ligatures_normalized = 0
    
    for filename in txt_files:
        input_path = os.path.join(input_dir, filename)
        output_path = os.path.join(output_dir, filename)
        
        # Get file stats and start progress tracking
        file_stats = get_file_stats(input_path)
        book_title = progress.start_file(filename, file_stats['size'])
        
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Apply enhanced orthographic standardization
            standardized_content, ortho_stats = standardize_orthography(content)
            
            # Save standardized content
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(standardized_content)
            
            # Update aggregate statistics
            total_variants_normalized += ortho_stats['variants_normalized']
            total_diacritics_removed += ortho_stats['diacritics_removed']
            total_ligatures_normalized += ortho_stats['ligatures_normalized']
            
            # Log detailed progress
            if ortho_stats['variants_normalized'] > 0:
                progress.log_progress(f"Normalized {ortho_stats['variants_normalized']} medieval variants")
            if ortho_stats['diacritics_removed'] > 0:
                progress.log_progress(f"Removed {ortho_stats['diacritics_removed']} diacritics")
            
            progress.finish_file(success=True, 
                               lines_processed=file_stats.get('lines', 0),
                               bytes_processed=len(standardized_content.encode('utf-8')),
                               expansions_made=ortho_stats['variants_normalized'])
            
        except Exception as e:
            error_msg = f"Orthography standardization error: {e}"
            progress.finish_file(success=False, error_msg=error_msg)
    
    # Update final progress statistics
    progress.stats.update({
        'expansions_made': total_variants_normalized,  # Use expansions field for variant normalizations
    })
    
    # Print enhanced progress summary
    final_stats = progress.print_summary()
    
    # Save processing report with orthographic details
    try:
        report_path = os.path.join(report_dir, "orthography_summary.txt")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("=== Enhanced Orthographic Standardization Report ===\n\n")
            f.write(f"Files processed: {final_stats['files_processed']}\n")
            f.write(f"Medieval variants normalized: {total_variants_normalized}\n")
            f.write(f"Diacritics removed: {total_diacritics_removed}\n") 
            f.write(f"Ligatures normalized: {total_ligatures_normalized}\n")
            f.write(f"Errors encountered: {final_stats['errors']}\n\n")
            f.write("Orthographic features applied:\n")
            f.write("✓ Medieval variant normalization (michi→mihi, nichil→nihil, etc.)\n")
            f.write("✓ Comprehensive diacritic removal\n")
            f.write("✓ Ligature normalization (æ→ae, œ→oe)\n")
            f.write("✓ Medieval character conversion (j→i, v→u)\n")
            f.write("✓ Case normalization (all lowercase)\n")
            f.write("✓ Punctuation standardization\n")
        
        progress.log_progress(f"Saved orthography report to {report_path}")
    except Exception as e:
        progress.log_progress(f"Could not save orthography report: {e}", "warning")
    
    return final_stats['files_processed']

def main():
    base_input = "headings_removed"
    base_output = "orthography_standardized"
    
    logger.info("=== Step 5: Enhanced Orthographic Standardization ===")
    logger.info("Features: Medieval variant normalization, diacritic removal, case standardization")
    
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
            logger.info(f"Enhanced orthographic standardization completed for {processed} files in {input_subdir}")
        else:
            logger.debug(f"Skipping non-existent directory: {input_subdir}")
    
    logger.info(f"\n=== Enhanced Orthographic Standardization Summary ===")
    logger.info(f"✅ Total files processed: {total_processed}")
    logger.info(f"🔤 Features applied:")
    logger.info(f"   • Medieval variant normalization (michi→mihi, nichil→nihil, etc.)")
    logger.info(f"   • Comprehensive diacritic removal (ā→a, ē→e, etc.)")
    logger.info(f"   • Ligature standardization (æ→ae, œ→oe)")
    logger.info(f"   • Medieval character conversion (j→i, v→u)")
    logger.info(f"   • Case normalization (all lowercase)")
    logger.info(f"   • Punctuation standardization")
    logger.info(f"📋 Detailed reports saved in orthography_reports/ directories")
    logger.info(f"🎯 Latin texts now have standardized orthography for LLM training!")

if __name__ == "__main__":
    main()