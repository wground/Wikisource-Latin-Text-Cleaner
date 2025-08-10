#!/usr/bin/env python3
"""
Detailed Progress Logger
Provides comprehensive moment-by-moment logging for the entire text cleaning pipeline.
Shows detailed information about what books are being processed, what operations are happening,
and comprehensive reviews at the end of each step.

Author: Willow Groundwater-Schuldt & Claude Code 🫸💥🫷
"""

import time
import logging
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

class DetailedProgressLogger:
    """Enhanced progress logger that provides moment-by-moment processing details."""
    
    def __init__(self, step_name: str, step_description: str, total_files: int = 0):
        """Initialize the detailed progress logger."""
        self.step_name = step_name
        self.step_description = step_description
        self.total_files = total_files
        self.current_file_index = 0
        self.step_start_time = time.time()
        self.current_book_start_time = None
        self.current_book_name = None
        
        # Detailed statistics
        self.stats = {
            'files_processed': 0,
            'files_skipped': 0,
            'files_failed': 0,
            'lines_processed': 0,
            'lines_added': 0,
            'lines_removed': 0,
            'bytes_processed': 0,
            'bytes_saved': 0,
            'operations_performed': 0,
            'patterns_matched': 0,
            'expansions_made': 0,
            'classifications_made': 0,
            'errors_encountered': 0
        }
        
        # Detailed operation log
        self.operation_log = []
        self.book_summaries = []
        
        # Configure detailed logging
        self.logger = logging.getLogger(f"detailed_{step_name}")
        
        # Print step start header
        self._print_step_header()
    
    def _print_step_header(self):
        """Print comprehensive step start header."""
        print("\n" + "=" * 100)
        print(f"🚀 STARTING STEP: {self.step_name.upper()}")
        print(f"📋 Description: {self.step_description}")
        print("=" * 100)
        print(f"📊 Total files to process: {self.total_files}")
        print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 Expected completion: {self._estimate_completion_time()}")
        print("-" * 100)
    
    def _estimate_completion_time(self) -> str:
        """Estimate completion time based on file count."""
        if self.total_files == 0:
            return "Unknown"
        
        # Rough estimate: 1-3 seconds per file depending on step
        avg_time_per_file = {
            'step1': 0.5,  # File filtering is fast
            'step2': 1.0,  # Classification takes medium time
            'step3': 2.0,  # Content cleaning is slower
            'step4': 1.0,  # Heading removal is medium
            'step5': 1.5,  # Orthography standardization is medium-slow
            'step6': 0.8,  # Final cleanup is medium-fast
            'step7': 2.5   # Dataset creation is slowest
        }.get(self.step_name, 1.0)
        
        estimated_seconds = self.total_files * avg_time_per_file
        estimated_completion = datetime.now() + timedelta(seconds=estimated_seconds)
        return estimated_completion.strftime('%H:%M:%S')
    
    def start_book_processing(self, filename: str, file_path: str = None) -> str:
        """Start processing a new book with detailed information."""
        self.current_file_index += 1
        self.current_book_start_time = time.time()
        self.current_book_name = filename
        
        # Extract meaningful book title
        book_title = self._extract_meaningful_title(filename)
        
        # Get file information
        file_info = self._get_file_info(file_path) if file_path else {}
        
        # Progress percentage
        progress_pct = (self.current_file_index / self.total_files * 100) if self.total_files > 0 else 0
        
        # Print detailed book start information
        print(f"\n📖 BOOK {self.current_file_index}/{self.total_files} ({progress_pct:.1f}%)")
        print(f"   📚 Title: {book_title}")
        print(f"   📄 File: {filename}")
        
        if file_info:
            print(f"   📊 Size: {file_info.get('size_display', 'Unknown')}")
            print(f"   📝 Lines: {file_info.get('lines', 'Unknown')}")
            print(f"   🏷️  Type: {file_info.get('file_type', 'Unknown')}")
        
        print(f"   🕐 Started: {datetime.now().strftime('%H:%M:%S')}")
        
        return book_title
    
    def log_operation(self, operation: str, details: str = "", success: bool = True, count: int = 0):
        """Log a specific operation with detailed information."""
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]  # Include milliseconds
        
        if success:
            status_icon = "✅"
            self.stats['operations_performed'] += 1
        else:
            status_icon = "❌"
            self.stats['errors_encountered'] += 1
        
        # Update relevant counters
        if count > 0:
            if 'pattern' in operation.lower() or 'match' in operation.lower():
                self.stats['patterns_matched'] += count
            elif 'expand' in operation.lower():
                self.stats['expansions_made'] += count
            elif 'classif' in operation.lower():
                self.stats['classifications_made'] += count
        
        # Format the log message
        log_msg = f"      {status_icon} {timestamp} | {operation}"
        if details:
            log_msg += f" | {details}"
        if count > 0:
            log_msg += f" | Count: {count}"
        
        print(log_msg)
        
        # Store in operation log
        self.operation_log.append({
            'timestamp': timestamp,
            'operation': operation,
            'details': details,
            'success': success,
            'count': count,
            'book': self.current_book_name
        })
    
    def log_text_analysis(self, original_text: str, processed_text: str, analysis_type: str):
        """Log detailed text analysis showing before/after comparisons."""
        orig_lines = len(original_text.split('\n'))
        proc_lines = len(processed_text.split('\n'))
        
        orig_chars = len(original_text)
        proc_chars = len(processed_text)
        
        lines_changed = proc_lines - orig_lines
        chars_changed = proc_chars - orig_chars
        
        print(f"      📊 {analysis_type} Analysis:")
        print(f"         📝 Lines: {orig_lines} → {proc_lines} ({lines_changed:+d})")
        print(f"         🔤 Characters: {orig_chars:,} → {proc_chars:,} ({chars_changed:+,})")
        
        if orig_chars > 0:
            change_pct = (chars_changed / orig_chars) * 100
            print(f"         📈 Change: {change_pct:+.2f}%")
        
        # Update statistics
        self.stats['lines_processed'] += orig_lines
        if lines_changed > 0:
            self.stats['lines_added'] += lines_changed
        elif lines_changed < 0:
            self.stats['lines_removed'] += abs(lines_changed)
        
        self.stats['bytes_processed'] += orig_chars
        if chars_changed < 0:
            self.stats['bytes_saved'] += abs(chars_changed)
    
    def log_pattern_matching(self, pattern_name: str, matches_found: int, sample_matches: List[str] = None):
        """Log detailed pattern matching results."""
        if matches_found == 0:
            print(f"      🔍 {pattern_name}: No matches found")
            return
        
        print(f"      🎯 {pattern_name}: {matches_found} matches found")
        
        if sample_matches and len(sample_matches) > 0:
            print(f"         📋 Sample matches:")
            for i, match in enumerate(sample_matches[:3]):  # Show first 3 matches
                # Truncate long matches
                display_match = match[:50] + "..." if len(match) > 50 else match
                print(f"         • {display_match}")
        
        self.stats['patterns_matched'] += matches_found
    
    def log_classification_result(self, book_title: str, classification: Dict[str, str], confidence: str = ""):
        """Log classification results with detailed breakdown."""
        print(f"      🏷️  Classification Results:")
        for category, value in classification.items():
            print(f"         {category.title()}: {value}")
        
        if confidence:
            print(f"         Confidence: {confidence}")
        
        self.stats['classifications_made'] += 1
    
    def log_file_operation(self, operation: str, source_path: str = "", dest_path: str = "", success: bool = True):
        """Log file operations like moves, copies, deletions."""
        if success:
            print(f"      📂 {operation}")
            if source_path and dest_path:
                print(f"         From: {source_path}")
                print(f"         To: {dest_path}")
            elif source_path:
                print(f"         File: {source_path}")
        else:
            print(f"      ❌ Failed: {operation}")
            if source_path:
                print(f"         File: {source_path}")
    
    def finish_book_processing(self, success: bool = True, summary: str = "", 
                             lines_processed: int = 0, operations_count: int = 0, error_msg: str = ""):
        """Finish processing current book with detailed summary."""
        if not self.current_book_start_time:
            return
        
        elapsed_time = time.time() - self.current_book_start_time
        book_title = self._extract_meaningful_title(self.current_book_name)
        
        # Update statistics
        if success:
            self.stats['files_processed'] += 1
        else:
            self.stats['files_failed'] += 1
        
        if lines_processed > 0:
            self.stats['lines_processed'] += lines_processed
        
        # Print completion summary
        if success:
            print(f"   ✅ COMPLETED: {book_title}")
            print(f"      ⏱️  Processing time: {elapsed_time:.2f} seconds")
            
            if operations_count > 0:
                print(f"      🔧 Operations performed: {operations_count}")
            
            if lines_processed > 0:
                lines_per_sec = lines_processed / elapsed_time if elapsed_time > 0 else 0
                print(f"      📈 Processing rate: {lines_per_sec:.1f} lines/sec")
            
            if summary:
                print(f"      📋 Summary: {summary}")
        else:
            print(f"   ❌ FAILED: {book_title}")
            print(f"      ⏱️  Time before failure: {elapsed_time:.2f} seconds")
            if error_msg:
                print(f"      💬 Error: {error_msg}")
        
        # Store book summary
        self.book_summaries.append({
            'title': book_title,
            'filename': self.current_book_name,
            'success': success,
            'elapsed_time': elapsed_time,
            'lines_processed': lines_processed,
            'operations_count': operations_count,
            'summary': summary,
            'error': error_msg
        })
        
        # Reset current book tracking
        self.current_book_start_time = None
        self.current_book_name = None
    
    def skip_book(self, reason: str = ""):
        """Mark current book as skipped with reason."""
        book_title = self._extract_meaningful_title(self.current_book_name) if self.current_book_name else "Unknown"
        
        print(f"   ⏭️  SKIPPED: {book_title}")
        if reason:
            print(f"      💬 Reason: {reason}")
        
        self.stats['files_skipped'] += 1
        
        # Store in summaries
        self.book_summaries.append({
            'title': book_title,
            'filename': self.current_book_name,
            'success': False,
            'skipped': True,
            'reason': reason
        })
    
    def print_step_summary(self):
        """Print comprehensive step completion summary with detailed review."""
        total_elapsed = time.time() - self.step_start_time
        
        print("\n" + "=" * 100)
        print(f"🏁 STEP COMPLETED: {self.step_name.upper()}")
        print("=" * 100)
        
        # Basic statistics
        print(f"📊 PROCESSING STATISTICS:")
        print(f"   ✅ Files processed: {self.stats['files_processed']}")
        if self.stats['files_skipped'] > 0:
            print(f"   ⏭️  Files skipped: {self.stats['files_skipped']}")
        if self.stats['files_failed'] > 0:
            print(f"   ❌ Files failed: {self.stats['files_failed']}")
        
        total_files = self.stats['files_processed'] + self.stats['files_skipped'] + self.stats['files_failed']
        success_rate = (self.stats['files_processed'] / total_files * 100) if total_files > 0 else 0
        print(f"   📈 Success rate: {success_rate:.1f}%")
        
        # Content statistics
        if self.stats['lines_processed'] > 0:
            print(f"\n📝 CONTENT STATISTICS:")
            print(f"   📄 Lines processed: {self.stats['lines_processed']:,}")
            if self.stats['lines_added'] > 0:
                print(f"   ➕ Lines added: {self.stats['lines_added']:,}")
            if self.stats['lines_removed'] > 0:
                print(f"   ➖ Lines removed: {self.stats['lines_removed']:,}")
        
        if self.stats['bytes_processed'] > 0:
            print(f"   💾 Bytes processed: {self.stats['bytes_processed']:,}")
            if self.stats['bytes_saved'] > 0:
                print(f"   💰 Bytes saved: {self.stats['bytes_saved']:,}")
        
        # Operation statistics
        if self.stats['operations_performed'] > 0:
            print(f"\n🔧 OPERATION STATISTICS:")
            print(f"   ⚙️  Total operations: {self.stats['operations_performed']:,}")
            if self.stats['patterns_matched'] > 0:
                print(f"   🎯 Patterns matched: {self.stats['patterns_matched']:,}")
            if self.stats['expansions_made'] > 0:
                print(f"   📝 Expansions made: {self.stats['expansions_made']:,}")
            if self.stats['classifications_made'] > 0:
                print(f"   🏷️  Classifications made: {self.stats['classifications_made']:,}")
        
        # Performance statistics
        print(f"\n⏱️  PERFORMANCE STATISTICS:")
        print(f"   🕐 Total time: {total_elapsed:.2f} seconds ({total_elapsed/60:.1f} minutes)")
        
        if self.stats['files_processed'] > 0:
            avg_time = total_elapsed / self.stats['files_processed']
            files_per_minute = (self.stats['files_processed'] / total_elapsed) * 60
            print(f"   📊 Average per file: {avg_time:.2f} seconds")
            print(f"   🚀 Processing rate: {files_per_minute:.1f} files/minute")
        
        # Top processed books (by processing time)
        print(f"\n📚 BOOK PROCESSING SUMMARY:")
        successful_books = [b for b in self.book_summaries if b.get('success', False)]
        failed_books = [b for b in self.book_summaries if not b.get('success', False) and not b.get('skipped', False)]
        skipped_books = [b for b in self.book_summaries if b.get('skipped', False)]
        
        if successful_books:
            print(f"   ✅ Successfully processed {len(successful_books)} books:")
            # Show top 5 by processing time
            top_books = sorted(successful_books, key=lambda x: x.get('elapsed_time', 0), reverse=True)[:5]
            for book in top_books:
                elapsed = book.get('elapsed_time', 0)
                lines = book.get('lines_processed', 0)
                print(f"      📖 {book['title'][:50]:<50} ({elapsed:.2f}s, {lines} lines)")
        
        if failed_books:
            print(f"   ❌ Failed books ({len(failed_books)}):")
            for book in failed_books[:5]:  # Show first 5 failures
                error = book.get('error', 'Unknown error')[:80]
                print(f"      📖 {book['title'][:40]:<40} | {error}")
        
        if skipped_books:
            print(f"   ⏭️  Skipped books ({len(skipped_books)}):")
            for book in skipped_books[:5]:  # Show first 5 skipped
                reason = book.get('reason', 'No reason given')[:60]
                print(f"      📖 {book['title'][:40]:<40} | {reason}")
        
        # Final completion message
        print(f"\n🎯 STEP REVIEW:")
        if success_rate >= 90:
            print("   🌟 Excellent! Step completed with high success rate.")
        elif success_rate >= 70:
            print("   👍 Good! Step completed successfully with minor issues.")
        elif success_rate >= 50:
            print("   ⚠️  Acceptable! Step completed but with notable issues to review.")
        else:
            print("   🚨 Poor! Step completed but requires immediate attention.")
        
        print(f"\n🔄 Ready to proceed to next step: {total_elapsed:.1f}s elapsed")
        print("=" * 100)
        
        return self.stats
    
    def _extract_meaningful_title(self, filename: str) -> str:
        """Extract a meaningful, readable title from filename."""
        # Remove file extensions
        title = filename.replace('.txt', '').replace('.txt_1', '').replace('.txt_2', '')
        
        # Handle specific patterns for Latin texts
        if '_liber' in title:
            parts = title.split('_liber')
            if len(parts) >= 2:
                book = parts[0].replace('_', ' ').title()
                liber = parts[1].replace('_', ' ').strip()
                return f"{book} - Book {liber}"
        
        if title.startswith('Ab Urbe Condita'):
            # Special handling for Livy
            if 'Periochae' in title:
                return title.replace('_', ' ').replace(' - ', ': ')
            else:
                return title.replace('_', ' ')
        
        # Handle other common patterns
        title = title.replace('_', ' ')
        
        # Smart capitalization
        words = title.split()
        formatted_words = []
        
        # Roman numerals and common abbreviations
        roman_numerals = {'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 
                         'XI', 'XII', 'XIII', 'XIV', 'XV', 'XX', 'XXX', 'XL', 'L', 
                         'C', 'CI', 'CII', 'CIII'}
        
        for word in words:
            if word.upper() in roman_numerals or word in ['I', 'II', 'III']:
                formatted_words.append(word.upper())
            elif len(word) <= 2:  # Short prepositions, etc.
                formatted_words.append(word.lower())
            else:
                formatted_words.append(word.capitalize())
        
        title = ' '.join(formatted_words)
        
        # Limit length for display
        if len(title) > 70:
            title = title[:67] + "..."
        
        return title
    
    def _get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get comprehensive file information."""
        try:
            stat = os.stat(file_path)
            size = stat.st_size
            
            # Format size display
            if size > 1024 * 1024:
                size_display = f"{size/(1024*1024):.1f} MB"
            elif size > 1024:
                size_display = f"{size/1024:.1f} KB"
            else:
                size_display = f"{size} bytes"
            
            # Count lines efficiently
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = sum(1 for _ in f)
            
            # Determine file type based on content
            file_type = "Text file"
            if file_path.endswith('.txt'):
                file_type = "Latin text"
            
            return {
                'size': size,
                'size_display': size_display,
                'lines': lines,
                'file_type': file_type
            }
        
        except Exception as e:
            return {
                'size': 0,
                'size_display': 'Unknown',
                'lines': 0,
                'file_type': 'Unknown',
                'error': str(e)
            }

# Convenience functions for easy integration
def create_detailed_logger(step_name: str, step_description: str, total_files: int = 0) -> DetailedProgressLogger:
    """Create a new detailed progress logger for a step."""
    return DetailedProgressLogger(step_name, step_description, total_files)

def log_major_milestone(message: str, level: str = "info"):
    """Log a major milestone or important event."""
    timestamp = datetime.now().strftime('%H:%M:%S')
    
    if level == "success":
        print(f"\n🎉 {timestamp} | MILESTONE: {message}")
    elif level == "warning":
        print(f"\n⚠️  {timestamp} | WARNING: {message}")
    elif level == "error":
        print(f"\n❌ {timestamp} | ERROR: {message}")
    else:
        print(f"\n📢 {timestamp} | {message}")