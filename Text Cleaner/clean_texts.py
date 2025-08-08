#!/usr/bin/env python3
import os
import re
import string

def clean_text(text):
    # First, remove lines containing "Exported from Wikisource"
    lines = text.split('\n')
    lines = [line for line in lines if 'Exported from Wikisource' not in line]
    
    # Remove everything from "About this digital edition" line onwards
    filtered_lines = []
    for line in lines:
        if line.strip().startswith('About this digital edition'):
            break
        filtered_lines.append(line)
    
    # Rejoin the filtered lines
    text = '\n'.join(filtered_lines)
    
    # Remove all numbers (0-9) and periods that follow them
    text = re.sub(r'[0-9]+\.?', '', text)
    
    # Convert all capital letters to lowercase
    text = text.lower()
    
    # Replace diacritics (macrons, acute accents, grave accents) with their standard versions
    diacritic_replacements = {
        # Macrons
        'ā': 'a', 'ē': 'e', 'ī': 'i', 'ō': 'o', 'ū': 'u',
        'Ā': 'a', 'Ē': 'e', 'Ī': 'i', 'Ō': 'o', 'Ū': 'u',
        # Acute accents
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u', 'ý': 'y',
        'Á': 'a', 'É': 'e', 'Í': 'i', 'Ó': 'o', 'Ú': 'u', 'Ý': 'y',
        # Grave accents
        'à': 'a', 'è': 'e', 'ì': 'i', 'ò': 'o', 'ù': 'u',
        'À': 'a', 'È': 'e', 'Ì': 'i', 'Ò': 'o', 'Ù': 'u'
    }
    for diacritic, standard in diacritic_replacements.items():
        text = text.replace(diacritic, standard)
    
    # Replace ligatures
    text = text.replace('æ', 'a')
    text = text.replace('Æ', 'a')
    text = text.replace('œ', 'oe')
    text = text.replace('Œ', 'oe')
    
    # Remove Roman numerals at the beginning of lines and periods not following letters
    def remove_roman_numerals_and_periods(text):
        lines = text.split('\n')
        cleaned_lines = []
        
        # Roman numeral pattern: matches valid Roman numerals at the beginning of lines
        # This pattern ensures we only match actual Roman numerals, not regular words
        # It matches Roman numerals followed by word boundaries (space, period, end of line)
        roman_pattern = r'^(?=[IVXLCDM])(?:M{0,3}(?:CM|CD|D?C{0,3})(?:XC|XL|L?X{0,3})(?:IX|IV|V?I{0,3}))(?=\s|\.|\s*$)\.?\s*'
        
        for line in lines:
            # Remove Roman numerals at the start of lines
            cleaned_line = re.sub(roman_pattern, '', line, flags=re.IGNORECASE)
            
            # Remove periods that are not following a letter (standalone periods or after spaces/punctuation)
            cleaned_line = re.sub(r'(?<![a-zA-Z])\.', '', cleaned_line)
            
            cleaned_lines.append(cleaned_line)
        
        return '\n'.join(cleaned_lines)
    
    text = remove_roman_numerals_and_periods(text)
    
    # Replace all instances of v with u and j with i
    text = text.replace('v', 'u')
    text = text.replace('j', 'i')
    
    # Keep only specific punctuation: . : , ; ' " ! ?
    # Remove all other punctuation
    allowed_punctuation = set('.,:;\'"!?')
    text = ''.join(char for char in text if char.isalpha() or char.isspace() or char in allowed_punctuation)
    
    # Remove paragraph indentations and whitespace sequences larger than 2 spaces
    # First remove indentations at the beginning of lines
    text = re.sub(r'^\s+', '', text, flags=re.MULTILINE)
    # Then remove whitespace sequences larger than 2 spaces
    text = re.sub(r' {3,}', '  ', text)
    
    # Remove blank lines
    text = re.sub(r'\n\s*\n', '\n', text)
    
    return text

def main():
    input_folder = "Texts to be Cleaned"
    output_folder = "Cleaned Texts"
    
    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # Check if input folder exists
    if not os.path.exists(input_folder):
        print(f"Error: '{input_folder}' folder not found!")
        return
    
    # Process all .txt files in the input folder
    txt_files = [f for f in os.listdir(input_folder) if f.endswith('.txt')]
    
    if not txt_files:
        print(f"No .txt files found in '{input_folder}' folder!")
        return
    
    print(f"Processing {len(txt_files)} text files...")
    
    for filename in txt_files:
        input_path = os.path.join(input_folder, filename)
        output_path = os.path.join(output_folder, filename)
        
        try:
            # Read the original file
            with open(input_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Clean the text
            cleaned_content = clean_text(content)
            
            # Write the cleaned text to output folder
            with open(output_path, 'w', encoding='utf-8') as file:
                file.write(cleaned_content)
            
            print(f"Cleaned: {filename}")
            
        except Exception as e:
            print(f"Error processing {filename}: {e}")
    
    print(f"All files processed! Cleaned texts saved to '{output_folder}' folder.")

if __name__ == "__main__":
    main()