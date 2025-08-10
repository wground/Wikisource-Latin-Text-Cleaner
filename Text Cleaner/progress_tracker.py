#!/usr/bin/env python3
"""
Enhanced Progress Tracking Utility
Provides detailed real-time progress information with book names, statistics,
and performance metrics across all text cleaning steps.
Now integrated with DetailedProgressLogger for comprehensive moment-by-moment tracking.
"""

import time
import logging
import os
from pathlib import Path
from detailed_progress_logger import DetailedProgressLogger, log_major_milestone

class ProgressTracker:
    """Enhanced progress tracker for text cleaning operations."""
    
    def __init__(self, step_name, total_files=0, step_description="Processing text files"):
        """Initialize progress tracker with detailed logging."""
        self.step_name = step_name
        self.total_files = total_files
        self.current_file = 0
        self.start_time = time.time()
        self.current_book_start = None
        
        # Initialize detailed progress logger
        self.detailed_logger = DetailedProgressLogger(step_name, step_description, total_files)
        
        # Statistics tracking (kept for backward compatibility)
        self.stats = {
            'files_processed': 0,
            'lines_processed': 0,
            'bytes_processed': 0,
            'expansions_made': 0,
            'categories_removed': 0,
            'errors': 0,
            'skipped': 0
        }
        
        # Configure enhanced logging with book names
        self.logger = logging.getLogger(f"{step_name}")
        
        # Log the start milestone
        log_major_milestone(f"Started {step_name}: {step_description}", "success")
    
    def print_start_header(self):
        """Print enhanced start header with step information."""
        self.logger.info("=" * 80)
        self.logger.info(f"📚 {self.step_name.upper()}")
        self.logger.info("=" * 80)
        if self.total_files > 0:
            self.logger.info(f"📊 Processing {self.total_files} files")
        self.logger.info(f"🕐 Started at: {time.strftime('%H:%M:%S', time.localtime(self.start_time))}")
        self.logger.info("-" * 80)
    
    def start_file(self, filename, file_path=None, file_size=None):
        """Start processing a new file with detailed logging."""
        self.current_file += 1
        self.current_book_start = time.time()
        
        # Use detailed logger for comprehensive book start logging
        book_title = self.detailed_logger.start_book_processing(filename, file_path)
        
        # Keep legacy logging for backward compatibility
        progress_pct = ""
        if self.total_files > 0:
            pct = (self.current_file / self.total_files) * 100
            progress_pct = f"({self.current_file}/{self.total_files}, {pct:.1f}%)"
        
        size_info = ""
        if file_size:
            if file_size > 1024:
                size_info = f", {file_size//1024}KB"
            else:
                size_info = f", {file_size}B"
        
        return book_title
    
    def extract_book_title(self, filename):
        """Extract readable book title from filename."""
        # Remove file extensions
        title = filename.replace('.txt', '').replace('.txt_1', '').replace('.txt_2', '')
        
        # Handle common patterns
        if '_liber' in title:
            parts = title.split('_liber')
            if len(parts) >= 2:
                book = parts[0].replace('_', ' ').title()
                liber = parts[1].replace('_', ' ').strip()
                return f"{book} - Book {liber}"
        
        # Handle other patterns
        title = title.replace('_', ' ')
        
        # Capitalize first letter of each major word
        words = title.split()
        formatted_words = []
        for word in words:
            if len(word) > 3 or word in ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X']:
                formatted_words.append(word.title())
            else:
                formatted_words.append(word.lower())
        
        title = ' '.join(formatted_words)
        
        # Limit length for display
        if len(title) > 60:
            title = title[:57] + "..."
        
        return title
    
    def finish_file(self, success=True, lines_processed=0, bytes_processed=0, 
                   expansions_made=0, categories_removed=0, error_msg=None, summary=""):
        """Finish processing current file with detailed logging."""
        if self.current_book_start:
            elapsed = time.time() - self.current_book_start
            
            # Update statistics
            if success:
                self.stats['files_processed'] += 1
                self.stats['lines_processed'] += lines_processed
                self.stats['bytes_processed'] += bytes_processed
                self.stats['expansions_made'] += expansions_made
                self.stats['categories_removed'] += categories_removed
                
                # Use detailed logger for comprehensive finish logging
                operations_count = expansions_made + categories_removed
                self.detailed_logger.finish_book_processing(
                    success=True, 
                    summary=summary,
                    lines_processed=lines_processed,
                    operations_count=operations_count
                )
                
                # Keep legacy logging for backward compatibility
                details = []
                if lines_processed > 0:
                    details.append(f"{lines_processed} lines")
                if bytes_processed > 0:
                    if bytes_processed > 1024:
                        details.append(f"{bytes_processed//1024}KB")
                    else:
                        details.append(f"{bytes_processed}B")
                if expansions_made > 0:
                    details.append(f"{expansions_made} expansions")
                if categories_removed > 0:
                    details.append(f"{categories_removed} categories removed")
                
                detail_str = ", ".join(details)
                if detail_str:
                    detail_str = f" | {detail_str}"
                
            else:
                self.stats['errors'] += 1
                # Use detailed logger for failure logging
                self.detailed_logger.finish_book_processing(
                    success=False, 
                    error_msg=error_msg,
                    lines_processed=lines_processed
                )
            
            self.current_book_start = None
    
    def skip_file(self, reason=""):
        """Mark file as skipped with detailed logging."""
        self.stats['skipped'] += 1
        
        # Use detailed logger
        self.detailed_logger.skip_book(reason)
        
        # Keep legacy logging
        reason_str = f": {reason}" if reason else ""
        self.logger.info(f"   ⏭️  Skipped{reason_str}")
    
    def update_stat(self, stat_name, increment=1):
        """Update a specific statistic."""
        if stat_name in self.stats:
            self.stats[stat_name] += increment
    
    def log_progress(self, message, level="info"):
        """Log a progress message."""
        if level == "debug":
            self.logger.debug(f"   🔍 {message}")
        elif level == "warning":
            self.logger.warning(f"   ⚠️  {message}")
        elif level == "error":
            self.logger.error(f"   ❌ {message}")
        else:
            self.logger.info(f"   📝 {message}")
    
    def log_operation(self, operation: str, details: str = "", success: bool = True, count: int = 0):
        """Log a detailed operation with the detailed logger."""
        self.detailed_logger.log_operation(operation, details, success, count)
    
    def log_text_analysis(self, original_text: str, processed_text: str, analysis_type: str):
        """Log detailed text analysis showing before/after."""
        self.detailed_logger.log_text_analysis(original_text, processed_text, analysis_type)
    
    def log_pattern_matching(self, pattern_name: str, matches_found: int, sample_matches=None):
        """Log pattern matching results with samples."""
        self.detailed_logger.log_pattern_matching(pattern_name, matches_found, sample_matches)
    
    def log_classification_result(self, book_title: str, classification: dict, confidence: str = ""):
        """Log classification results."""
        self.detailed_logger.log_classification_result(book_title, classification, confidence)
    
    def log_file_operation(self, operation: str, source_path: str = "", dest_path: str = "", success: bool = True):
        """Log file operations."""
        self.detailed_logger.log_file_operation(operation, source_path, dest_path, success)
    
    def print_summary(self):
        """Print comprehensive summary using detailed logger."""
        # Use detailed logger for comprehensive summary
        detailed_stats = self.detailed_logger.print_step_summary()
        
        # Sync our stats with detailed logger stats for backward compatibility
        self.stats.update({
            'files_processed': detailed_stats.get('files_processed', self.stats['files_processed']),
            'files_skipped': detailed_stats.get('files_skipped', self.stats['skipped']),
            'errors': detailed_stats.get('files_failed', self.stats['errors']),
            'lines_processed': detailed_stats.get('lines_processed', self.stats['lines_processed']),
            'bytes_processed': detailed_stats.get('bytes_processed', self.stats['bytes_processed']),
            'expansions_made': detailed_stats.get('expansions_made', self.stats['expansions_made'])
        })
        
        # Log step completion milestone
        log_major_milestone(f"Completed {self.step_name} with {self.stats['files_processed']} files processed", "success")
        
        return self.stats

def get_file_line_count(filepath):
    """Efficiently count lines in a file."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            return sum(1 for _ in f)
    except:
        return 0

def get_file_stats(filepath):
    """Get comprehensive file statistics."""
    try:
        stat = os.stat(filepath)
        line_count = get_file_line_count(filepath)
        return {
            'size': stat.st_size,
            'lines': line_count
        }
    except:
        return {'size': 0, 'lines': 0}