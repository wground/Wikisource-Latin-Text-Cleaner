# Text Cleaner

## Personal Notes

*IMPORTANT NOTICE*: As of August 12. 2025 this project is meaningless-- an intergrated cleaner and processor is now available at [Vicifons Scra[er](https://github.com/wground/Vicifons-Scraper). Literally everything is better over there.
---

## Project Overview

This is a text cleaning and processing project designed to process and clean historical Latin texts scraped from Vicifons (Latin Wikisource). The project works in conjunction with [Vicifons Scraper](https://github.com/wground/Vicifons-Scraper/tree/main) and contains a large collection of texts to be cleaned and multiple Python scripts for automated text processing.

## Directory Structure

### `/Texts to be Cleaned/`
Contains hundreds of historical Latin texts including:
- **Ab Urbe Condita** - Livy's histories (Periochae and main text books)
- **Medieval religious texts** - Various disputations, visions, and religious writings
- **Historical documents** - Letters, councils, and chronicles
- **Classical works** - Achilleis, hymns, and other Latin literature

### Processing Scripts
- `clean_texts_v2.py` - Main text cleaning script (v2)
- `step1_remove_short_files.py` - Remove files below minimum length
- `step2_sort_by_period_genre.py` - Organize texts by historical period/genre
- `step3_clean_content.py` - Core content cleaning operations
- `step4_remove_headings.py` - Strip headers and metadata
- `step5_standardize_orthography.py` - Normalize spelling and orthography
- `step6_final_cleanup.py` - Final formatting and cleanup
- `step7_create_merged_datasets.py` - Combine cleaned texts into datasets
- `step7_optimized_datasets.py` - Optimized dataset creation

### Optimization & Monitoring
- `run_optimized_pipeline.py` - Run the full processing pipeline
- `progress_tracker.py` - Track processing progress
- `detailed_progress_logger.py` - Detailed logging system
- `memory_efficient_processing.py` - Memory optimization utilities
- `gpu_acceleration_opportunities.py` - GPU acceleration options
- `optimized_regex_patterns.py` - Optimized regex patterns for cleaning

### Logging & Testing
- `text_cleaning.log` - Processing log file
- `demo_step3_logging.py` - Demo of step 3 with logging
- `test_detailed_logging.py` - Test suite for logging functionality
- `enhance_remaining_steps.py` - Enhancements for processing steps
