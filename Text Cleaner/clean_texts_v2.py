#!/usr/bin/env python3
"""
Clean Texts v2.0 - Advanced Latin Text Cleaning Pipeline
Comprehensive text cleaning system for Latin texts to prepare them for LLM training.

This script orchestrates the entire cleaning pipeline:
1. Remove very short files (fragmentary/index files)
2. Sort by period (classical/post-classical) and genre (prose/poetry)  
3. Clean content (remove metadata, non-Latin material)
4. Remove structural headings and section indicators
5. Standardize orthography (diacritics, j->i, v->u, lowercase)
6. Final cleanup (whitespace, remaining artifacts)
7. Create merged datasets for different training scenarios

Author: Willow Groundwater-Schuldt & Claude Code 🫸💥🫷
Version: 2.0
"""

import os
import sys
import time
import logging
import argparse
import subprocess
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('text_cleaning.log')
    ]
)
logger = logging.getLogger(__name__)

def run_step(script_name, step_description):
    """Run a single step of the pipeline."""
    logger.info(f"\n{'='*60}")
    logger.info(f"Starting: {step_description}")
    logger.info(f"Running: {script_name}")
    logger.info('='*60)
    
    start_time = time.time()
    
    try:
        # Run the step script
        result = subprocess.run([sys.executable, script_name], 
                              capture_output=True, text=True, check=True)
        
        # Log the output
        if result.stdout:
            logger.info("Script output:")
            for line in result.stdout.strip().split('\n'):
                logger.info(f"  {line}")
                
        elapsed = time.time() - start_time
        logger.info(f"✓ Completed: {step_description} ({elapsed:.1f}s)")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"✗ Failed: {step_description}")
        logger.error(f"Error code: {e.returncode}")
        if e.stdout:
            logger.error(f"Stdout: {e.stdout}")
        if e.stderr:
            logger.error(f"Stderr: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"✗ Unexpected error in {step_description}: {e}")
        return False

def check_prerequisites():
    """Check that input directory and step scripts exist."""
    logger.info("Checking prerequisites...")
    
    # Check input directory
    input_dir = "Texts to be Cleaned"
    if not os.path.exists(input_dir):
        logger.error(f"Input directory '{input_dir}' not found!")
        return False
    
    # Count input files
    txt_files = [f for f in os.listdir(input_dir) if f.endswith('.txt')]
    logger.info(f"Found {len(txt_files)} .txt files in input directory")
    
    # Check step scripts
    step_scripts = [
        "step1_remove_short_files.py",
        "step2_sort_by_period_genre.py", 
        "step3_clean_content.py",
        "step4_remove_headings.py",
        "step5_standardize_orthography.py",
        "step6_final_cleanup.py",
        "step7_create_merged_datasets.py"
    ]
    
    missing_scripts = []
    for script in step_scripts:
        if not os.path.exists(script):
            missing_scripts.append(script)
    
    if missing_scripts:
        logger.error(f"Missing step scripts: {missing_scripts}")
        return False
    
    logger.info("✓ All prerequisites satisfied")
    return True

def cleanup_intermediate_directories(keep_intermediate=False):
    """Clean up intermediate processing directories."""
    if keep_intermediate:
        logger.info("Keeping intermediate directories as requested")
        return
    
    logger.info("Cleaning up intermediate processing directories...")
    
    intermediate_dirs = [
        "processing_temp",
        "sorted_texts", 
        "content_cleaned",
        "headings_removed",
        "orthography_standardized"
    ]
    
    for dirname in intermediate_dirs:
        if os.path.exists(dirname):
            import shutil
            shutil.rmtree(dirname)
            logger.info(f"Removed intermediate directory: {dirname}")

def print_final_summary():
    """Print a summary of what was created."""
    logger.info("\n" + "="*80)
    logger.info("LATIN TEXT CLEANING PIPELINE - COMPLETION SUMMARY")
    logger.info("="*80)
    
    # Check what was created
    output_dirs = {
        "final_cleaned": "Final cleaned texts (sorted by period/genre)",
        "merged_datasets": "Merged datasets for LLM training",
        "removed_files_backup": "Backup of removed short files"
    }
    
    for dirname, description in output_dirs.items():
        if os.path.exists(dirname):
            if dirname == "merged_datasets":
                # Count datasets in merged_datasets
                subdirs = []
                for root, dirs, files in os.walk(dirname):
                    if any(f.endswith('.txt') for f in files):
                        rel_path = os.path.relpath(root, dirname)
                        file_count = len([f for f in files if f.endswith('.txt')])
                        subdirs.append(f"    {rel_path}: {file_count} files")
                
                logger.info(f"✓ {dirname}/ - {description}")
                for subdir in subdirs:
                    logger.info(subdir)
            else:
                file_count = 0
                for root, dirs, files in os.walk(dirname):
                    file_count += len([f for f in files if f.endswith('.txt')])
                logger.info(f"✓ {dirname}/ - {description} ({file_count} files)")
        else:
            logger.info(f"✗ {dirname}/ - Not created")
    
    logger.info("\nDataset Usage Recommendations:")
    logger.info("- For Classical Latin LLM: Use merged_datasets/classical/combined/")
    logger.info("- For Medieval Latin LLM: Use merged_datasets/post_classical/combined/")
    logger.info("- For Complete Latin LLM: Use merged_datasets/complete_corpus/")
    logger.info("- For Prose-only LLM: Use merged_datasets/prose_only/")
    logger.info("- For Poetry-only LLM: Use merged_datasets/poetry_only/")
    
    stats_file = "merged_datasets/dataset_statistics.txt"
    if os.path.exists(stats_file):
        logger.info(f"\nDetailed statistics available in: {stats_file}")
    
    logger.info(f"\nLog file: text_cleaning.log")
    logger.info("="*80)

def main():
    parser = argparse.ArgumentParser(
        description="Clean Latin texts for LLM training",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Run full pipeline
  %(prog)s --steps 1,2,3      # Run only steps 1-3
  %(prog)s --keep-intermediate # Keep intermediate files
  %(prog)s --min-size 300     # Set minimum file size to 300 bytes
        """
    )
    
    parser.add_argument('--steps', type=str, default='1,2,3,4,5,6,7',
                       help='Comma-separated list of steps to run (default: 1,2,3,4,5,6,7)')
    parser.add_argument('--keep-intermediate', action='store_true',
                       help='Keep intermediate processing directories')
    parser.add_argument('--min-size', type=int, default=200,
                       help='Minimum file size in bytes to keep (default: 200)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Parse steps to run
    try:
        steps_to_run = [int(x.strip()) for x in args.steps.split(',')]
    except ValueError:
        logger.error("Invalid steps format. Use comma-separated numbers like: 1,2,3")
        return 1
    
    logger.info("="*80)
    logger.info("LATIN TEXT CLEANING PIPELINE v2.0")
    logger.info("="*80)
    logger.info(f"Steps to run: {steps_to_run}")
    logger.info(f"Minimum file size: {args.min_size} bytes")
    logger.info(f"Keep intermediate files: {args.keep_intermediate}")
    
    # Check prerequisites
    if not check_prerequisites():
        return 1
    
    # Define pipeline steps
    pipeline_steps = [
        (1, "step1_remove_short_files.py", f"Remove files smaller than {args.min_size} bytes"),
        (2, "step2_sort_by_period_genre.py", "Sort by period and genre"),
        (3, "step3_clean_content.py", "Clean content and remove metadata"),
        (4, "step4_remove_headings.py", "Remove headings and section indicators"),
        (5, "step5_standardize_orthography.py", "Standardize orthography"),
        (6, "step6_final_cleanup.py", "Final cleanup and normalization"),
        (7, "step7_create_merged_datasets.py", "Create merged datasets")
    ]
    
    # Run selected steps
    overall_start = time.time()
    failed_steps = []
    
    for step_num, script, description in pipeline_steps:
        if step_num not in steps_to_run:
            logger.info(f"Skipping step {step_num}: {description}")
            continue
            
        success = run_step(script, f"Step {step_num}: {description}")
        if not success:
            failed_steps.append(step_num)
            logger.error(f"Pipeline failed at step {step_num}")
            break
    
    overall_elapsed = time.time() - overall_start
    
    if failed_steps:
        logger.error(f"\n✗ Pipeline failed at step(s): {failed_steps}")
        logger.error(f"Total runtime: {overall_elapsed:.1f}s")
        return 1
    else:
        logger.info(f"\n✓ Pipeline completed successfully!")
        logger.info(f"Total runtime: {overall_elapsed:.1f}s")
        
        # Cleanup intermediate files unless requested to keep them
        cleanup_intermediate_directories(args.keep_intermediate)
        
        # Print final summary
        print_final_summary()
        
        return 0

if __name__ == "__main__":
    sys.exit(main())