#!/usr/bin/env python3
"""
Step 1: Remove Very Short Files and Index Files
Identifies and removes fragmentary, index, or table-of-contents files that don't contain
meaningful Latin text content. Enhanced with intelligent index detection and detailed progress tracking.
"""

import os
import re
import shutil
import logging
from typing import Tuple, List
from progress_tracker import ProgressTracker, get_file_stats
from optimized_regex_patterns import PATTERNS

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_directories():
    """Create necessary directories for processing."""
    directories = [
        "processing_temp",
        "removed_files_backup",
        "removed_files_backup/index_files"
    ]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            logger.info(f"Created directory: {directory}")

def detect_index_content(file_path: str) -> Tuple[bool, List[str]]:
    """
    Detect if a file contains index-like content adapted for Latin texts.
    Returns (is_index, list_of_detected_patterns)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Skip header section (standard in our pipeline)
        lines = content.split('\n')
        content_start = 0
        for i, line in enumerate(lines):
            if '----' in line or line.strip().startswith('--'):
                content_start = i + 1
                break
        
        actual_content = '\n'.join(lines[content_start:]).strip()
        
        # Check for index patterns - adapted for Latin texts
        detected_patterns = []
        content_lines = [line.strip() for line in actual_content.split('\n') if line.strip()]
        
        if len(content_lines) == 0:
            return False, []
        
        # Check if most lines look like chapter/book references (Latin-specific)
        chapter_like_lines = 0
        bullet_point_lines = 0
        
        for line in content_lines[:50]:  # Check first 50 lines
            # Latin book/chapter patterns (optimized)
            if PATTERNS.has_latin_chapter_pattern(line):
                chapter_like_lines += 1
                detected_patterns.append(f"Chapter reference: {line[:50]}...")
                
            # Generic table of contents patterns (optimized)
            elif PATTERNS.TOC_PATTERN.match(line) and len(line) < 80:
                chapter_like_lines += 1
                detected_patterns.append(f"Numbered section: {line[:50]}...")
                
            # Bullet point or list patterns
            elif line.startswith('*') and len(line) < 100:
                bullet_point_lines += 1
                detected_patterns.append(f"Bullet point: {line.lstrip('*').strip()[:40]}...")
                
            # Page number patterns (optimized)
            elif PATTERNS.PAGE_PATTERN.match(line):
                detected_patterns.append(f"Page number: {line}")
        
        # Decision logic adapted for Latin corpus
        total_lines = len(content_lines)
        
        # Strong indicators of index content
        if chapter_like_lines > 5 and chapter_like_lines > total_lines * 0.3:
            return True, detected_patterns
            
        # Many short bullet points suggest index
        if bullet_point_lines > 10 and total_lines < 100:
            return True, detected_patterns
            
        # Very short files with mostly structural content
        if total_lines < 30 and (chapter_like_lines + bullet_point_lines) > total_lines * 0.5:
            return True, detected_patterns
            
        # Check for predominantly non-prose content patterns
        non_prose_lines = 0
        for line in content_lines[:30]:  # Check first 30 lines
            # Lines that are mostly punctuation, numbers, or very short
            if (len(line) < 20 and 
                not re.search(r'[a-zA-Z]{4,}', line) and  # Not much actual text
                not line.endswith('.') and  # Doesn't end like prose
                not PATTERNS.LATIN_FUNCTION_WORDS.search(line)):  # No Latin function words (optimized)
                non_prose_lines += 1
        
        if non_prose_lines > total_lines * 0.4 and total_lines < 50:
            return True, detected_patterns
            
        return False, detected_patterns
        
    except Exception as e:
        logger.warning(f"Error detecting index content in {file_path}: {e}")
        return False, []

def analyze_file_sizes(input_folder):
    """Analyze file sizes to determine appropriate threshold."""
    if not os.path.exists(input_folder):
        logger.error(f"Input folder '{input_folder}' not found!")
        return None
    
    file_sizes = []
    txt_files = [f for f in os.listdir(input_folder) if f.endswith('.txt')]
    
    for filename in txt_files:
        filepath = os.path.join(input_folder, filename)
        size = os.path.getsize(filepath)
        file_sizes.append((filename, size))
    
    file_sizes.sort(key=lambda x: x[1])
    
    logger.info(f"Total files: {len(file_sizes)}")
    logger.info(f"Smallest 10 files:")
    for i in range(min(10, len(file_sizes))):
        logger.info(f"  {file_sizes[i][0]}: {file_sizes[i][1]} bytes")
    
    # Calculate statistics
    sizes_only = [size for _, size in file_sizes]
    if sizes_only:
        logger.info(f"Median size: {sorted(sizes_only)[len(sizes_only)//2]} bytes")
        logger.info(f"Average size: {sum(sizes_only)/len(sizes_only):.0f} bytes")
    
    return file_sizes

def remove_short_and_index_files(input_folder, min_size_bytes=200, backup=True):
    """
    Remove files below the minimum size threshold and index/TOC files with enhanced progress tracking.
    
    Args:
        input_folder: Directory containing text files
        min_size_bytes: Minimum file size to keep (default 200 bytes)
        backup: Whether to backup removed files before deletion
    """
    setup_directories()
    
    file_sizes = analyze_file_sizes(input_folder)
    if not file_sizes:
        return
    
    # Initialize enhanced progress tracker with detailed logging
    progress = ProgressTracker(
        "step1", 
        len(file_sizes), 
        "Enhanced File Filtering: Remove short files and intelligently detect index/TOC files"
    )
    
    removed_short_count = 0
    removed_index_count = 0
    kept_count = 0
    total_bytes_removed = 0
    total_bytes_kept = 0
    index_patterns_found = []
    
    for filename, size in file_sizes:
        filepath = os.path.join(input_folder, filename)
        
        # Get detailed file stats
        file_stats = get_file_stats(filepath)
        book_title = progress.start_file(filename, filepath, size)
        
        try:
            remove_reason = None
            remove_type = None
            
            # Log file analysis start
            progress.log_operation("Starting file analysis", f"Size: {size} bytes, Lines: {file_stats.get('lines', 0)}")
            
            # Check if file is too small
            if size < min_size_bytes:
                remove_reason = f"too small ({size} bytes < {min_size_bytes})"
                remove_type = "short"
                progress.log_operation("Size check failed", f"File is below minimum threshold", True, 1)
                
            # Check if file contains index content (only for files that aren't too small)
            else:
                progress.log_operation("Size check passed", f"File meets minimum size requirement ({size} >= {min_size_bytes})")
                progress.log_operation("Starting index detection", "Analyzing content for index/TOC patterns")
                
                is_index, patterns = detect_index_content(filepath)
                if is_index:
                    remove_reason = f"index/TOC content detected ({len(patterns)} patterns)"
                    remove_type = "index"
                    index_patterns_found.extend(patterns[:3])  # Keep sample patterns
                    
                    progress.log_pattern_matching("Index/TOC patterns", len(patterns), patterns[:3])
                    progress.log_operation("Index detection positive", f"Identified as index/TOC file", True, len(patterns))
                else:
                    progress.log_operation("Index detection negative", "No index/TOC patterns detected - keeping file")
            
            # Remove file if it matches removal criteria
            if remove_reason:
                progress.log_operation("File marked for removal", remove_reason)
                
                # Backup the file before removal if requested
                if backup:
                    if remove_type == "index":
                        backup_path = os.path.join("removed_files_backup", "index_files", filename)
                        backup_type = "index file backup"
                    else:
                        backup_path = os.path.join("removed_files_backup", filename)
                        backup_type = "short file backup"
                    
                    progress.log_operation("Creating backup", f"Saving to {backup_type} directory")
                    shutil.copy2(filepath, backup_path)
                    progress.log_file_operation(f"Backup {backup_type}", filepath, backup_path, True)
                
                # Remove the original file
                progress.log_operation("Removing original file", "File will be deleted from input directory")
                os.remove(filepath)
                progress.log_file_operation("Delete file", filepath, "", True)
                
                if remove_type == "short":
                    removed_short_count += 1
                    summary = f"Removed short file ({size} bytes)"
                else:
                    removed_index_count += 1
                    summary = f"Removed index/TOC file with {len(patterns) if 'patterns' in locals() else 0} patterns"
                    
                total_bytes_removed += size
                progress.skip_file(remove_reason)
                
            else:
                # Copy to processing temp directory for next steps
                temp_path = os.path.join("processing_temp", filename)
                
                progress.log_operation("File approved for processing", "Copying to temp directory for next step")
                shutil.copy2(filepath, temp_path)
                progress.log_file_operation("Copy to temp", filepath, temp_path, True)
                
                kept_count += 1
                total_bytes_kept += size
                
                summary = f"Kept file: {size} bytes, {file_stats.get('lines', 0)} lines"
                progress.finish_file(success=True, 
                                   lines_processed=file_stats.get('lines', 0),
                                   bytes_processed=size,
                                   summary=summary)
                progress.update_stat('files_processed', 1)
                
        except Exception as e:
            error_msg = f"Error processing file: {e}"
            progress.log_operation("Processing failed", f"Exception occurred: {str(e)}", False)
            progress.finish_file(success=False, error_msg=error_msg)
            logger.error(f"Failed to process {filename}: {e}")
    
    # Update final statistics
    total_removed = removed_short_count + removed_index_count
    progress.stats['files_processed'] = kept_count
    progress.stats['skipped'] = total_removed
    progress.stats['bytes_processed'] = total_bytes_kept
    
    # Print enhanced summary
    final_stats = progress.print_summary()
    
    # Additional step-specific summary
    logger.info("📋 ENHANCED STEP-SPECIFIC RESULTS")
    logger.info("-" * 80)
    logger.info(f"🗑️  Files removed (too small): {removed_short_count}")
    logger.info(f"📚 Index/TOC files removed: {removed_index_count}")
    logger.info(f"📊 Total files removed: {total_removed}")
    logger.info(f"✅ Files kept for processing: {kept_count}")
    logger.info(f"📁 Kept files copied to: processing_temp/")
    
    if backup and total_removed > 0:
        logger.info(f"💾 Short files backed up to: removed_files_backup/")
        if removed_index_count > 0:
            logger.info(f"📋 Index files backed up to: removed_files_backup/index_files/")
    
    if total_bytes_kept > 0:
        avg_kept_size = total_bytes_kept // kept_count if kept_count > 0 else 0
        logger.info(f"📊 Average kept file size: {avg_kept_size} bytes")
    
    if total_bytes_removed > 0:
        if total_bytes_removed > 1024:
            kb_removed = total_bytes_removed / 1024
            logger.info(f"🧹 Total space freed: {kb_removed:.1f} KB")
        else:
            logger.info(f"🧹 Total space freed: {total_bytes_removed} bytes")
    
    # Show sample index patterns found
    if index_patterns_found:
        logger.info(f"🔍 Sample index patterns detected:")
        for i, pattern in enumerate(index_patterns_found[:5]):
            logger.info(f"   {i+1}. {pattern[:60]}...")
        if len(index_patterns_found) > 5:
            logger.info(f"   ... and {len(index_patterns_found) - 5} more patterns")
    
    return final_stats

def main():
    input_folder = "Texts to be Cleaned"
    
    logger.info("=== Step 1: Enhanced File Filtering ===")
    logger.info("Features: Size filtering + Intelligent index detection")
    
    # Analyze and remove short files and index files with enhanced tracking
    stats = remove_short_and_index_files(input_folder, min_size_bytes=200, backup=True)
    
    if stats and stats['files_processed'] > 0:
        logger.info("🎯 Step 1 completed successfully with enhanced filtering!")
        logger.info("✨ Both short files and index/TOC files have been intelligently detected and removed!")
    else:
        logger.warning("⚠️  Step 1 completed with issues - check output above")

if __name__ == "__main__":
    main()