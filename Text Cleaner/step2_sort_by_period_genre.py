#!/usr/bin/env python3
"""
Step 2: Sort Files by Period and Genre
Enhanced classification system that eliminates unknowns through multi-layered
analysis of titles, authors, content, and linguistic features.
Based on computational philology research and Latin literary analysis.
"""

import os
import re
import shutil
import logging
from progress_tracker import ProgressTracker, get_file_stats

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Enhanced classification data structures
POETRY_TITLE_INDICATORS = [
    'carmen', 'carmina', 'elegia', 'elegiae', 'versus', 'aeneis', 
    'metamorphoses', 'ecloga', 'eclogae', 'georgica', 'bucolica',
    'satirae', 'satira', 'hymnus', 'hymni', 'odes', 'ode', 'epigram',
    'epigramma', 'liber carminum', 'fasti', 'tristia', 'heroides'
]

PROSE_TITLE_INDICATORS = [
    'historia', 'historiae', 'oratio', 'orationes', 'epistola', 'epistolae',
    'commentarii', 'annales', 'bellum', 'bella', 'de ', 'ad ', 'vita', 'vitae',
    'dialogus', 'tractatus', 'institutio', 'naturalis historia', 'confessiones',
    'civitate dei', 'tusculanae', 'rhetorica', 'philosophia', 'grammatica'
]

MIXED_TITLE_INDICATORS = [
    'comoedia', 'tragoedia', 'fabula', 'drama', 'theatrum'
]

# Author-based genre classification (known literary preferences)
AUTHOR_GENRE_HINTS = {
    # Primarily poetry
    'vergilius': 'poetry', 'ovidius': 'poetry', 'horatius': 'poetry',
    'catullus': 'poetry', 'propertius': 'poetry', 'tibullus': 'poetry',
    'lucretius': 'poetry', 'martialis': 'poetry', 'juvenalis': 'poetry',
    'persius': 'poetry', 'statius': 'poetry', 'lucanus': 'poetry',
    'silius': 'poetry', 'valerius flaccus': 'poetry', 'prudentius': 'poetry',
    
    # Primarily prose  
    'cicero': 'prose', 'caesar': 'prose', 'livius': 'prose', 'tacitus': 'prose',
    'plinius': 'prose', 'quintilianus': 'prose', 'suetonius': 'prose',
    'sallustius': 'prose', 'nepos': 'prose', 'curtius': 'prose',
    'augustinus': 'prose', 'hieronymus': 'prose', 'ambrosius': 'prose',
    
    # Mixed (both prose and poetry)
    'seneca': 'mixed', 'apuleius': 'mixed', 'boethius': 'mixed'
}

# Chronological classification of authors
CLASSICAL_AUTHORS = [
    'cicero', 'caesar', 'livius', 'vergilius', 'ovidius', 'horatius',
    'catullus', 'propertius', 'tibullus', 'lucretius', 'sallustius',
    'nepos', 'tacitus', 'plinius', 'quintilianus', 'suetonius',
    'juvenalis', 'martialis', 'persius', 'statius', 'lucanus',
    'silius', 'valerius flaccus', 'curtius', 'seneca', 'apuleius'
]

LATE_CLASSICAL_AUTHORS = [
    'augustinus', 'hieronymus', 'ambrosius', 'prudentius', 'boethius',
    'cassiodorus', 'isidorus', 'gregorius magnus'
]

MEDIEVAL_AUTHORS = [
    'beda', 'alcuinus', 'rabanus maurus', 'hincmarus', 'lupus',
    'thomas aquinas', 'anselmus', 'bernardus', 'abelardus'
]

# Vocabulary indicators for period classification
CLASSICAL_VOCABULARY = [
    'imperium', 'consulatus', 'senatus', 'populus romanus', 'res publica',
    'caesar', 'augustus', 'pontifex maximus', 'triumphus', 'forum'
]

MEDIEVAL_VOCABULARY = [
    'christianus', 'ecclesia', 'sanctus', 'monachus', 'abbas', 'episcopus',
    'baptismus', 'sacramentum', 'martyrium', 'confessio', 'divinus',
    'benedictus', 'dominus', 'iesu', 'christi', 'maria', 'angelus'
]

# Prose connectors (more frequent in prose than poetry)
PROSE_CONNECTORS = [
    'itaque', 'igitur', 'ergo', 'autem', 'enim', 'nam', 'sed', 'at',
    'vero', 'quidem', 'tamen', 'etiam', 'quoque', 'denique', 'porro',
    'praeterea', 'insuper', 'deinde', 'postea', 'interim'
]

def setup_output_directories():
    """Create the enhanced output directory structure."""
    directories = [
        "sorted_texts",
        "sorted_texts/classical",
        "sorted_texts/classical/prose",
        "sorted_texts/classical/poetry", 
        "sorted_texts/classical/mixed",
        "sorted_texts/post_classical",
        "sorted_texts/post_classical/prose",
        "sorted_texts/post_classical/poetry",
        "sorted_texts/post_classical/mixed",
        "sorted_texts/classification_reports"  # For detailed classification logs
    ]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            logger.info(f"Created directory: {directory}")

def parse_file_metadata(filepath):
    """
    Extract metadata from file header.
    Returns dict with 'title', 'source', 'category', 'text_type'
    """
    metadata = {
        'title': None,
        'source': None,  
        'category': None,
        'text_type': None
    }
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            # Read first few lines to get metadata
            lines = []
            for i, line in enumerate(f):
                lines.append(line.strip())
                if i > 10:  # Only need first few lines for metadata
                    break
        
        for line in lines:
            if line.startswith('Title:'):
                metadata['title'] = line.replace('Title:', '').strip()
            elif line.startswith('Source:'):
                metadata['source'] = line.replace('Source:', '').strip()
            elif line.startswith('Category:'):
                metadata['category'] = line.replace('Category:', '').strip()
            elif line.startswith('Text Type:'):
                metadata['text_type'] = line.replace('Text Type:', '').strip()
            elif line.startswith('--'):
                break  # End of metadata section
                
    except Exception as e:
        logger.warning(f"Error reading metadata from {filepath}: {e}")
    
    return metadata

def classify_period_enhanced(title, category, content_sample=None):
    """
    Enhanced period classification using multiple indicators.
    Never returns 'unknown' - makes educated guesses based on available evidence.
    """
    confidence_score = {'classical': 0, 'post_classical': 0}
    
    # Start with existing category-based classification (highest confidence)
    if category:
        category_lower = category.lower()
        
        classical_indicators = [
            'latinitas_romana', 'romana', 'classical', 'republic', 'empire',
            'augustus', 'imperial', 'golden age', 'silver age'
        ]
        
        postclassical_indicators = [
            'latinitas_mediaevalis', 'mediaevalis', 'medieval', 'saeculum_',
            'christian', 'christiana', 'patristic', 'carolingian', 'scholastic'
        ]
        
        for indicator in classical_indicators:
            if indicator in category_lower:
                confidence_score['classical'] += 5  # High confidence from category
                
        for indicator in postclassical_indicators:
            if indicator in category_lower:
                confidence_score['post_classical'] += 5
    
    # Author-based classification
    if title:
        title_lower = title.lower()
        
        # Check for classical authors
        for author in CLASSICAL_AUTHORS:
            if author in title_lower:
                confidence_score['classical'] += 3
                logger.debug(f"Classical author '{author}' found in title")
                
        # Check for late classical authors
        for author in LATE_CLASSICAL_AUTHORS:
            if author in title_lower:
                confidence_score['post_classical'] += 3
                logger.debug(f"Late classical author '{author}' found in title")
                
        # Check for medieval authors
        for author in MEDIEVAL_AUTHORS:
            if author in title_lower:
                confidence_score['post_classical'] += 3
                logger.debug(f"Medieval author '{author}' found in title")
    
    # Content-based analysis (if available)
    if content_sample:
        content_lower = content_sample.lower()
        
        # Count classical vocabulary indicators
        classical_count = sum(1 for word in CLASSICAL_VOCABULARY if word in content_lower)
        if classical_count > 0:
            confidence_score['classical'] += min(classical_count * 0.5, 2)
            
        # Count medieval vocabulary indicators
        medieval_count = sum(1 for word in MEDIEVAL_VOCABULARY if word in content_lower)
        if medieval_count > 0:
            confidence_score['post_classical'] += min(medieval_count * 0.5, 2)
    
    # Fallback logic based on title patterns
    if title and max(confidence_score.values()) == 0:
        title_lower = title.lower()
        
        # Some title patterns suggest classical period
        if any(pattern in title_lower for pattern in ['ab urbe condita', 'bellum', 'historia', 'commentarii']):
            confidence_score['classical'] += 1
            
        # Some patterns suggest post-classical
        if any(pattern in title_lower for pattern in ['sanctus', 'vita', 'martyrium', 'confessio']):
            confidence_score['post_classical'] += 1
    
    # Final decision - if still tied, default to classical (more common in corpus)
    if confidence_score['classical'] >= confidence_score['post_classical']:
        result = 'classical'
        confidence = 'high' if confidence_score['classical'] >= 3 else 'medium' if confidence_score['classical'] >= 1 else 'low'
    else:
        result = 'post_classical'  
        confidence = 'high' if confidence_score['post_classical'] >= 3 else 'medium' if confidence_score['post_classical'] >= 1 else 'low'
    
    # If both scores are 0, make educated guess based on filename patterns
    if max(confidence_score.values()) == 0:
        # Default to classical for well-known classical works, post_classical for religious content
        if title:
            title_lower = title.lower()
            if any(term in title_lower for term in ['aeneis', 'metamorphoses', 'cicero', 'caesar']):
                result = 'classical'
                confidence = 'low'
            elif any(term in title_lower for term in ['saint', 'sanctus', 'church', 'god', 'jesus']):
                result = 'post_classical'
                confidence = 'low'
            else:
                # Ultimate fallback - classical is more common in typical Latin corpora
                result = 'classical'
                confidence = 'very_low'
    
    return result, confidence

def classify_genre_enhanced(title, filepath, content_sample=None):
    """
    Enhanced genre classification that eliminates unknowns through multi-layered analysis.
    Based on computational philology research and Latin literary patterns.
    """
    confidence_score = {'poetry': 0, 'prose': 0, 'mixed': 0}
    
    # Title-based genre detection (highest confidence indicator)
    if title:
        title_lower = title.lower()
        
        # Enhanced poetry title scoring
        for indicator in POETRY_TITLE_INDICATORS:
            if indicator in title_lower:
                confidence_score['poetry'] += 3
                logger.debug(f"Poetry title indicator '{indicator}' found")
        
        # Enhanced prose title scoring  
        for indicator in PROSE_TITLE_INDICATORS:
            if indicator in title_lower:
                confidence_score['prose'] += 3
                logger.debug(f"Prose title indicator '{indicator}' found")
                
        # Mixed genre indicators
        for indicator in MIXED_TITLE_INDICATORS:
            if indicator in title_lower:
                confidence_score['mixed'] += 3
                logger.debug(f"Mixed genre indicator '{indicator}' found")
        
        # Author-based genre hints
        for author, genre in AUTHOR_GENRE_HINTS.items():
            if author in title_lower:
                if genre == 'poetry':
                    confidence_score['poetry'] += 2
                elif genre == 'prose':
                    confidence_score['prose'] += 2
                else:  # mixed
                    confidence_score['mixed'] += 2
                logger.debug(f"Author '{author}' suggests genre '{genre}'")
    
    # Enhanced content analysis
    try:
        if content_sample is None and filepath:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                content_start = 0
                for i, line in enumerate(lines):
                    if line.strip().startswith('--'):
                        content_start = i + 1
                        break
                
                # Analyze first 100 lines for better accuracy
                sample_lines = lines[content_start:content_start + 100]
                content_sample = '\n'.join(sample_lines)
        
        if content_sample:
            lines = [line.strip() for line in content_sample.split('\n') if line.strip()]
            
            if len(lines) > 5:  # Need minimum sample
                # Advanced line length analysis
                short_lines = sum(1 for line in lines if 20 <= len(line) <= 80)
                very_short_lines = sum(1 for line in lines if 10 <= len(line) < 30)
                long_lines = sum(1 for line in lines if len(line) > 100)
                
                # Poetry indicators based on line length patterns
                if very_short_lines > len(lines) * 0.3:  # 30%+ very short lines
                    confidence_score['poetry'] += 2
                if short_lines > long_lines * 2:  # Many medium-length lines
                    confidence_score['poetry'] += 1
                    
                # Prose indicators  
                if long_lines > len(lines) * 0.2:  # 20%+ long lines
                    confidence_score['prose'] += 2
                
                # Line ending analysis (poetry often doesn't end with periods)
                non_period_endings = sum(1 for line in lines if line and not line.endswith('.'))
                period_endings = sum(1 for line in lines if line.endswith('.'))
                
                if non_period_endings > period_endings * 2:  # Many non-period endings
                    confidence_score['poetry'] += 1
                if period_endings > non_period_endings:  # More sentence endings
                    confidence_score['prose'] += 1
                
                # Prose connector analysis
                content_lower = content_sample.lower()
                word_count = len(re.findall(r'\w+', content_sample))
                
                if word_count > 0:
                    connector_count = sum(content_lower.count(conn) for conn in PROSE_CONNECTORS)
                    if connector_count > word_count // 100:  # Relative to text length
                        confidence_score['prose'] += 1
                
                # Look for structural poetry indicators
                if re.search(r'\b(carmen|versus|metra|hymn|elegia)\b', content_lower):
                    confidence_score['poetry'] += 1
                    
                # Look for prose structure indicators
                if re.search(r'\b(liber|capitulum|sectio|paragraph|oratio)\b', content_lower):
                    confidence_score['prose'] += 1
                
                # Check for metrical patterns (basic hexameter detection)
                hexameter_patterns = 0
                for line in lines[:20]:  # Check first 20 lines
                    # Very basic check for potential dactylic hexameter length
                    if 30 <= len(line) <= 60 and not line.endswith('.'):
                        hexameter_patterns += 1
                
                if hexameter_patterns > len(lines[:20]) * 0.4:  # 40%+ potential verse lines
                    confidence_score['poetry'] += 1
    
    except Exception as e:
        logger.warning(f"Error in enhanced content analysis for {filepath}: {e}")
    
    # Determine final classification
    max_score = max(confidence_score.values())
    
    # If no clear indicators, make educated guesses based on filename patterns
    if max_score == 0 and title:
        title_lower = title.lower()
        
        # Common classical poetry works
        if any(work in title_lower for work in ['aeneid', 'metamorphoses', 'odes', 'satires', 'elegies']):
            confidence_score['poetry'] += 1
            
        # Common prose works
        elif any(work in title_lower for work in ['history', 'letters', 'orations', 'commentaries', 'tusculan']):
            confidence_score['prose'] += 1
            
        # If still no indicators, check for author names without explicit genre
        else:
            for author in ['catullus', 'tibullus', 'propertius', 'martial']:
                if author in title_lower:
                    confidence_score['poetry'] += 1
                    break
            for author in ['pliny', 'tacitus', 'suetonius']:
                if author in title_lower:
                    confidence_score['prose'] += 1
                    break
    
    # Final decision with confidence assessment
    max_score = max(confidence_score.values())
    
    if confidence_score['poetry'] == max_score and max_score > 0:
        result = 'poetry'
    elif confidence_score['prose'] == max_score and max_score > 0:
        result = 'prose'
    elif confidence_score['mixed'] == max_score and max_score > 0:
        result = 'mixed'
    else:
        # Ultimate fallback - prose is more common in most Latin corpora
        result = 'prose'
        max_score = 0.5  # Low confidence fallback
    
    # Confidence assessment
    if max_score >= 4:
        confidence = 'high'
    elif max_score >= 2:
        confidence = 'medium'
    elif max_score >= 1:
        confidence = 'low'
    else:
        confidence = 'very_low'
    
    return result, confidence

def sort_files(input_folder):
    """Enhanced file sorting with comprehensive classification and detailed progress tracking."""
    setup_output_directories()
    
    if not os.path.exists(input_folder):
        logger.error(f"Input folder '{input_folder}' not found!")
        return
    
    txt_files = [f for f in os.listdir(input_folder) if f.endswith('.txt')]
    
    # Initialize enhanced progress tracker
    progress = ProgressTracker("Step 2: Enhanced Genre & Period Classification", len(txt_files))
    
    # Enhanced statistics tracking
    stats = {
        'classical': {'prose': 0, 'poetry': 0, 'mixed': 0},
        'post_classical': {'prose': 0, 'poetry': 0, 'mixed': 0},
        'errors': 0,
        'confidence_levels': {
            'high': 0, 'medium': 0, 'low': 0, 'very_low': 0
        }
    }
    
    # Detailed classification report
    classification_report = []
    
    for filename in txt_files:
        filepath = os.path.join(input_folder, filename)
        file_stats = get_file_stats(filepath)
        book_title = progress.start_file(filename, file_stats['size'])
        
        try:
            metadata = parse_file_metadata(filepath)
            
            # Enhanced period classification
            period, period_confidence = classify_period_enhanced(
                metadata.get('title', filename),
                metadata.get('category'),
                None  # Could add content sample here if needed
            )
            
            # Enhanced genre classification  
            genre = metadata.get('text_type')
            genre_confidence = 'high'  # Default for metadata
            classification_source = "metadata"
            
            if not genre or genre.lower() not in ['prose', 'poetry', 'mixed']:
                # Use enhanced classification
                genre, genre_confidence = classify_genre_enhanced(
                    metadata.get('title', filename),
                    filepath
                )
                classification_source = f"enhanced_analysis"
                progress.log_progress(f"Used enhanced analysis for genre detection")
            else:
                genre = genre.lower()
            
            # Determine output path (no more unknowns!)
            output_path = os.path.join("sorted_texts", period, genre, filename)
            stats[period][genre] += 1
            
            # Track confidence levels
            overall_confidence = 'low' if period_confidence == 'very_low' or genre_confidence == 'very_low' else min(period_confidence, genre_confidence, key=lambda x: ['high', 'medium', 'low', 'very_low'].index(x))
            stats['confidence_levels'][overall_confidence] += 1
            
            # Copy file to appropriate directory
            shutil.copy2(filepath, output_path)
            
            # Record detailed classification info
            classification_info = {
                'filename': filename,
                'period': period,
                'period_confidence': period_confidence,
                'genre': genre, 
                'genre_confidence': genre_confidence,
                'classification_source': classification_source,
                'final_path': f"{period}/{genre}",
                'title': metadata.get('title', 'N/A'),
                'category': metadata.get('category', 'N/A')
            }
            classification_report.append(classification_info)
            
            # Log detailed progress
            progress.log_progress(f"→ {period.title()} {genre.title()} ({overall_confidence} confidence)")
            progress.finish_file(success=True, 
                               lines_processed=file_stats.get('lines', 0),
                               bytes_processed=file_stats['size'])
            
        except Exception as e:
            error_msg = f"Classification error: {e}"
            progress.finish_file(success=False, error_msg=error_msg)
            stats['errors'] += 1
    
    # Update final progress statistics
    progress.stats.update({
        'files_processed': len(txt_files) - stats['errors'],
        'errors': stats['errors']
    })
    
    # Print enhanced progress summary
    final_stats = progress.print_summary()
    
    # Save detailed classification report
    try:
        report_path = os.path.join("sorted_texts", "classification_reports", "detailed_classification.txt")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("=== Enhanced Classification Report ===\n\n")
            f.write(f"Total files processed: {len(txt_files)}\n")
            f.write(f"Errors encountered: {stats['errors']}\n\n")
            
            f.write("=== Confidence Distribution ===\n")
            for level, count in stats['confidence_levels'].items():
                f.write(f"{level.title()} confidence: {count} files\n")
            f.write("\n")
            
            f.write("=== Detailed Classifications ===\n")
            for info in classification_report:
                f.write(f"\nFile: {info['filename']}\n")
                f.write(f"  Title: {info['title']}\n")
                f.write(f"  Category: {info['category']}\n")
                f.write(f"  Final Classification: {info['final_path']}\n")
                f.write(f"  Period Confidence: {info['period_confidence']}\n")  
                f.write(f"  Genre Confidence: {info['genre_confidence']}\n")
                f.write(f"  Source: {info['classification_source']}\n")
        
        progress.log_progress(f"Saved detailed report to {report_path}")
    except Exception as e:
        progress.log_progress(f"Could not save detailed report: {e}", "warning")
    
    # Additional step-specific summary
    logger.info("📋 CLASSIFICATION RESULTS")
    logger.info("-" * 80)
    logger.info(f"📚 Classical Prose: {stats['classical']['prose']}")
    logger.info(f"🎭 Classical Poetry: {stats['classical']['poetry']}")
    logger.info(f"🎪 Classical Mixed: {stats['classical']['mixed']}")
    logger.info(f"📜 Post-Classical Prose: {stats['post_classical']['prose']}")
    logger.info(f"✨ Post-Classical Poetry: {stats['post_classical']['poetry']}")
    logger.info(f"🎨 Post-Classical Mixed: {stats['post_classical']['mixed']}")
    
    logger.info(f"\n🎯 CONFIDENCE DISTRIBUTION")
    logger.info("-" * 80)
    total_successful = len(txt_files) - stats['errors']
    for level, count in stats['confidence_levels'].items():
        percentage = (count / total_successful * 100) if total_successful > 0 else 0
        logger.info(f"{level.title().ljust(10)}: {str(count).rjust(3)} files ({percentage:5.1f}%)")
    
    total_classified = sum(sum(period.values()) for period in [stats['classical'], stats['post_classical']])
    logger.info(f"\n✅ Successfully classified {total_classified} files with NO unknowns!")
    
    return final_stats

def main():
    input_folder = "processing_temp"
    
    logger.info("=== Step 2: Enhanced Classification by Period and Genre ===")
    logger.info("Using multi-layered analysis to eliminate unknown classifications")
    
    stats = sort_files(input_folder)
    
    if stats:
        logger.info("Step 2 completed successfully with enhanced classification!")
        logger.info("All files have been classified - no unknowns remain!")
    else:
        logger.warning("Step 2 completed with errors - check the log above")

if __name__ == "__main__":
    main()