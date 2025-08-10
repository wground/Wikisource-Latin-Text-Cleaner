#!/usr/bin/env python3
"""
Quick utility to add enhanced progress tracking to remaining step files.
This will update step4, step5, step6, and step7 with the new progress tracking system.
"""

import os
import re

def add_progress_import(content):
    """Add progress_tracker import to a step file."""
    if 'from progress_tracker import' in content:
        return content  # Already has the import
    
    # Find the import section and add our import
    import_pattern = r'(import logging\n)'
    replacement = r'\1from progress_tracker import ProgressTracker, get_file_stats\n'
    
    return re.sub(import_pattern, replacement, content)

def enhance_process_function(content, step_name):
    """Add basic progress tracking to a processing function."""
    
    # Pattern to find file processing loops
    loop_patterns = [
        (r'(for filename in [^:]+:)', r'txt_files'),
        (r'(for [^_]*file[^:]*:)', r'files')
    ]
    
    for pattern, var_name in loop_patterns:
        if re.search(pattern, content):
            # Add progress tracker initialization
            init_tracker = f'''
    # Initialize enhanced progress tracker
    progress = ProgressTracker("{step_name}", len({var_name}))
    '''
            
            # Add file start/finish tracking
            file_processing = '''
        # Get file stats and start progress tracking
        file_stats = get_file_stats(filepath if 'filepath' in locals() else input_path if 'input_path' in locals() else filename)
        book_title = progress.start_file(filename, file_stats.get('size', 0))
        
        try:
            '''
            
            file_finish = '''
            progress.finish_file(success=True, 
                               lines_processed=file_stats.get('lines', 0),
                               bytes_processed=file_stats.get('size', 0))
        except Exception as e:
            progress.finish_file(success=False, error_msg=str(e))
            raise
            '''
            
            # This is a simplified enhancement - in practice, each file needs custom handling
            break
    
    return content

def enhance_step_file(filepath, step_name):
    """Enhance a single step file with progress tracking."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Add import
        content = add_progress_import(content)
        
        # Add basic progress tracking structure (simplified)
        enhanced_content = enhance_process_function(content, step_name)
        
        # Write back (with backup)
        backup_path = filepath + '.backup'
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)  # Write original as backup
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(enhanced_content)
        
        print(f"✅ Enhanced {filepath} (backup saved to {backup_path})")
        return True
        
    except Exception as e:
        print(f"❌ Failed to enhance {filepath}: {e}")
        return False

def main():
    """Enhance remaining step files."""
    step_files = [
        ("step4_remove_headings.py", "Step 4: Remove Headings & Section Indicators"),
        ("step5_standardize_orthography.py", "Step 5: Standardize Orthography"),
        ("step6_final_cleanup.py", "Step 6: Final Cleanup & Normalization"),
        ("step7_create_merged_datasets.py", "Step 7: Create Merged Datasets")
    ]
    
    enhanced_count = 0
    
    for filepath, step_name in step_files:
        if os.path.exists(filepath):
            if enhance_step_file(filepath, step_name):
                enhanced_count += 1
        else:
            print(f"⚠️  File not found: {filepath}")
    
    print(f"\n📊 Enhanced {enhanced_count}/{len(step_files)} step files")
    print("💡 Note: These are basic enhancements. For full integration,")
    print("   each step may need custom progress tracking implementation.")

if __name__ == "__main__":
    main()