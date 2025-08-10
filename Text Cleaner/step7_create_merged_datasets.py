#!/usr/bin/env python3
"""
Step 7: Create Merged Datasets
Creates merged datasets combining different periods and genres as requested:
- Classical folder with combined prose/poetry
- Post-classical folder with combined prose/poetry  
- All-periods folder with separate prose, poetry, and combined subfolders
"""

import os
import shutil
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_merged_directories():
    """Create the merged dataset directory structure."""
    base_dir = "merged_datasets"
    directories = [
        # Individual period directories with combined genre subdirectories
        f"{base_dir}/classical/prose",
        f"{base_dir}/classical/poetry", 
        f"{base_dir}/classical/combined",
        
        f"{base_dir}/post_classical/prose",
        f"{base_dir}/post_classical/poetry",
        f"{base_dir}/post_classical/combined",
        
        # All periods combined directories
        f"{base_dir}/all_periods/prose",
        f"{base_dir}/all_periods/poetry", 
        f"{base_dir}/all_periods/combined",
        
        # Genre-specific cross-period directories
        f"{base_dir}/prose_only",
        f"{base_dir}/poetry_only",
        
        # Everything combined
        f"{base_dir}/complete_corpus"
    ]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            logger.info(f"Created directory: {directory}")

def copy_files(source_dir, target_dir):
    """Copy all .txt files from source to target directory."""
    if not os.path.exists(source_dir):
        logger.warning(f"Source directory {source_dir} does not exist")
        return 0
    
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    
    txt_files = [f for f in os.listdir(source_dir) if f.endswith('.txt')]
    copied = 0
    
    for filename in txt_files:
        source_path = os.path.join(source_dir, filename)
        target_path = os.path.join(target_dir, filename)
        
        try:
            shutil.copy2(source_path, target_path)
            copied += 1
        except Exception as e:
            logger.error(f"Error copying {filename}: {e}")
    
    return copied

def create_period_combined_datasets(base_input, base_output):
    """Create combined datasets for each period (classical/post-classical)."""
    periods = ["classical", "post_classical"]
    
    for period in periods:
        logger.info(f"Creating combined dataset for {period}...")
        
        # Copy existing prose and poetry directories
        prose_source = os.path.join(base_input, period, "prose")
        poetry_source = os.path.join(base_input, period, "poetry")
        
        prose_target = os.path.join(base_output, period, "prose")
        poetry_target = os.path.join(base_output, period, "poetry")
        combined_target = os.path.join(base_output, period, "combined")
        
        # Copy to individual directories
        prose_count = copy_files(prose_source, prose_target)
        poetry_count = copy_files(poetry_source, poetry_target)
        
        # Copy to combined directory
        combined_prose_count = copy_files(prose_source, combined_target)
        combined_poetry_count = copy_files(poetry_source, combined_target)
        
        logger.info(f"  {period} - Prose: {prose_count}, Poetry: {poetry_count}")
        logger.info(f"  {period} - Combined: {combined_prose_count + combined_poetry_count}")

def create_cross_period_datasets(base_input, base_output):
    """Create datasets that combine periods but separate genres."""
    logger.info("Creating cross-period datasets...")
    
    # Prose from all periods
    prose_sources = [
        os.path.join(base_input, "classical", "prose"),
        os.path.join(base_input, "post_classical", "prose")
    ]
    
    prose_target = os.path.join(base_output, "prose_only")
    all_periods_prose_target = os.path.join(base_output, "all_periods", "prose")
    
    total_prose = 0
    for source in prose_sources:
        count = copy_files(source, prose_target)
        copy_files(source, all_periods_prose_target)
        total_prose += count
    
    # Poetry from all periods  
    poetry_sources = [
        os.path.join(base_input, "classical", "poetry"),
        os.path.join(base_input, "post_classical", "poetry")
    ]
    
    poetry_target = os.path.join(base_output, "poetry_only")
    all_periods_poetry_target = os.path.join(base_output, "all_periods", "poetry")
    
    total_poetry = 0
    for source in poetry_sources:
        count = copy_files(source, poetry_target)
        copy_files(source, all_periods_poetry_target)
        total_poetry += count
    
    logger.info(f"  Cross-period - Total Prose: {total_prose}, Total Poetry: {total_poetry}")

def create_complete_datasets(base_input, base_output):
    """Create completely merged datasets."""
    logger.info("Creating complete merged datasets...")
    
    # All periods combined (prose + poetry)
    all_sources = [
        os.path.join(base_input, "classical", "prose"),
        os.path.join(base_input, "classical", "poetry"),
        os.path.join(base_input, "post_classical", "prose"),
        os.path.join(base_input, "post_classical", "poetry")
    ]
    
    all_periods_combined_target = os.path.join(base_output, "all_periods", "combined")
    complete_corpus_target = os.path.join(base_output, "complete_corpus")
    
    total_files = 0
    for source in all_sources:
        count = copy_files(source, all_periods_combined_target)
        copy_files(source, complete_corpus_target)
        total_files += count
    
    logger.info(f"  Complete corpus: {total_files} files")

def create_statistics_report(base_output):
    """Generate a statistics report for all created datasets."""
    logger.info("Generating statistics report...")
    
    stats = {}
    
    def count_files_in_dir(directory):
        """Count .txt files in a directory."""
        if os.path.exists(directory):
            return len([f for f in os.listdir(directory) if f.endswith('.txt')])
        return 0
    
    # Count files in each dataset
    datasets = {
        "Classical Prose": "classical/prose",
        "Classical Poetry": "classical/poetry",
        "Classical Combined": "classical/combined",
        "Post-Classical Prose": "post_classical/prose", 
        "Post-Classical Poetry": "post_classical/poetry",
        "Post-Classical Combined": "post_classical/combined",
        "All Periods Prose": "all_periods/prose",
        "All Periods Poetry": "all_periods/poetry", 
        "All Periods Combined": "all_periods/combined",
        "Prose Only": "prose_only",
        "Poetry Only": "poetry_only",
        "Complete Corpus": "complete_corpus"
    }
    
    for name, subdir in datasets.items():
        directory = os.path.join(base_output, subdir)
        count = count_files_in_dir(directory)
        stats[name] = count
    
    # Write statistics to file
    stats_file = os.path.join(base_output, "dataset_statistics.txt")
    with open(stats_file, 'w', encoding='utf-8') as f:
        f.write("Latin Text Datasets - File Count Statistics\n")
        f.write("=" * 50 + "\n\n")
        
        f.write("Period-Specific Datasets:\n")
        f.write(f"  Classical Prose:        {stats['Classical Prose']:>6} files\n")
        f.write(f"  Classical Poetry:       {stats['Classical Poetry']:>6} files\n")
        f.write(f"  Classical Combined:     {stats['Classical Combined']:>6} files\n")
        f.write(f"  Post-Classical Prose:   {stats['Post-Classical Prose']:>6} files\n")
        f.write(f"  Post-Classical Poetry:  {stats['Post-Classical Poetry']:>6} files\n")
        f.write(f"  Post-Classical Combined:{stats['Post-Classical Combined']:>6} files\n\n")
        
        f.write("Cross-Period Datasets:\n")
        f.write(f"  All Periods Prose:      {stats['All Periods Prose']:>6} files\n")
        f.write(f"  All Periods Poetry:     {stats['All Periods Poetry']:>6} files\n")
        f.write(f"  All Periods Combined:   {stats['All Periods Combined']:>6} files\n")
        f.write(f"  Prose Only:             {stats['Prose Only']:>6} files\n")
        f.write(f"  Poetry Only:            {stats['Poetry Only']:>6} files\n\n")
        
        f.write("Complete Dataset:\n")
        f.write(f"  Complete Corpus:        {stats['Complete Corpus']:>6} files\n\n")
        
        f.write("Dataset Descriptions:\n")
        f.write("- Classical: Texts from the Roman Republic/Empire periods\n")
        f.write("- Post-Classical: Medieval and later Latin texts\n")
        f.write("- Prose: Narrative, historical, and philosophical texts\n")
        f.write("- Poetry: Verse texts including epic, lyric, and dramatic\n")
        f.write("- Combined: Both prose and poetry together\n")
        f.write("- Complete Corpus: All texts from all periods and genres\n")
    
    logger.info(f"Statistics report written to {stats_file}")
    
    # Also log the statistics
    logger.info("\n=== Dataset Statistics ===")
    for name, count in stats.items():
        logger.info(f"  {name}: {count} files")

def main():
    base_input = "final_cleaned"
    base_output = "merged_datasets"
    
    logger.info("=== Step 7: Create Merged Datasets ===")
    
    # Setup directory structure
    setup_merged_directories()
    
    # Create various merged datasets
    create_period_combined_datasets(base_input, base_output)
    create_cross_period_datasets(base_input, base_output)
    create_complete_datasets(base_input, base_output)
    
    # Generate statistics report
    create_statistics_report(base_output)
    
    logger.info("Step 7 completed! Merged datasets created successfully.")
    logger.info(f"All datasets available in '{base_output}/' directory")

if __name__ == "__main__":
    main()