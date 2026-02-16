#!/usr/bin/env python3
"""
Verify CORAAL corpus statistics: word counts and duration in hours.
"""

import os
import re
from pathlib import Path
from collections import defaultdict


def count_words_from_txt(txt_path):
    """Count words from a CORAAL .txt file, excluding pauses and metadata."""
    word_count = 0
    
    try:
        with open(txt_path, 'r', encoding='utf-8') as f:
            # Skip header line
            next(f)
            
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) >= 4:
                    content = parts[3]  # Content column
                    
                    # Skip pause lines
                    if content.startswith('(pause'):
                        continue
                    
                    # Skip empty content
                    if not content or content == '':
                        continue
                    
                    # Remove brackets and markup
                    # [text], </text>, /text/, <text>, etc.
                    content = re.sub(r'[<\[\]/]', ' ', content)
                    
                    # Remove redaction markers like /RD-NAME-1/
                    content = re.sub(r'/RD-[A-Z]+-\d+/', '', content)
                    
                    # Split by whitespace and count
                    words = content.split()
                    # Filter out empty strings and special markers
                    words = [w for w in words if w and not w.startswith('RD-')]
                    word_count += len(words)
    
    except Exception as e:
        print(f"Error reading {txt_path}: {e}")
    
    return word_count


def get_duration_from_textgrid(textgrid_path):
    """Extract the maximum time (duration) from a TextGrid file."""
    try:
        with open(textgrid_path, 'r', encoding='utf-8') as f:
            for line in f:
                # Look for xmax = value at the file level (not in intervals)
                if line.strip().startswith('xmax ='):
                    # Extract the number
                    match = re.search(r'xmax\s*=\s*([\d.]+)', line)
                    if match:
                        return float(match.group(1))
        return 0.0
    except Exception as e:
        print(f"Error reading {textgrid_path}: {e}")
        return 0.0


def analyze_corpus(base_dir='.'):
    """Analyze all CORAAL components and calculate statistics."""
    
    components = ['ATL', 'DCA', 'DCB', 'DTA', 'LES', 'PRV', 'ROC', 'VLD']
    
    results = {}
    
    for component in components:
        component_dir = os.path.join(base_dir, component)
        
        if not os.path.isdir(component_dir):
            print(f"Warning: {component} directory not found")
            continue
        
        total_words = 0
        total_seconds = 0
        
        # Process all .txt files
        txt_files = list(Path(component_dir).glob('*.txt'))
        textgrid_files = list(Path(component_dir).glob('*.TextGrid'))
        
        for txt_file in txt_files:
            words = count_words_from_txt(txt_file)
            total_words += words
        
        for textgrid_file in textgrid_files:
            duration = get_duration_from_textgrid(textgrid_file)
            total_seconds += duration
        
        total_hours = total_seconds / 3600
        
        results[component] = {
            'words': total_words,
            'hours': total_hours,
            'txt_files': len(txt_files),
            'textgrid_files': len(textgrid_files)
        }
    
    return results


def main():
    """Main function to run the analysis and display results."""
    
    print("Analyzing CORAAL corpus...")
    print("=" * 70)
    
    results = analyze_corpus()
    
    # Expected values from PDF
    expected = {
        'ATL': {'hours': 8.62, 'words': 93525},
        'DCA': {'hours': 34.02, 'words': 333537},
        'DCB': {'hours': 46.04, 'words': 515189},
        'DTA': {'hours': 25.12, 'words': 240767},
        'LES': {'hours': 8.44, 'words': 102171},
        'PRV': {'hours': 13.95, 'words': 156176},
        'ROC': {'hours': 11.80, 'words': 126140},
        'VLD': {'hours': 11.49, 'words': 111973}
    }
    
    print(f"\n{'Component':<10} {'Hours (Calc)':<15} {'Hours (PDF)':<15} {'Diff':<10}")
    print(f"{'':10} {'Words (Calc)':<15} {'Words (PDF)':<15} {'Diff':<10}")
    print("-" * 70)
    
    for component in ['ATL', 'DCA', 'DCB', 'DTA', 'LES', 'PRV', 'ROC', 'VLD']:
        if component in results:
            calc = results[component]
            exp = expected[component]
            
            hours_diff = calc['hours'] - exp['hours']
            words_diff = calc['words'] - exp['words']
            
            print(f"{component:<10} {calc['hours']:>14.2f} {exp['hours']:>14.2f} {hours_diff:>9.2f}")
            print(f"{'':10} {calc['words']:>14,} {exp['words']:>14,} {words_diff:>9,}")
            print(f"{'':10} ({calc['txt_files']} txt files, {calc['textgrid_files']} TextGrid files)")
            print()
    
    # Summary
    total_calc_hours = sum(r['hours'] for r in results.values())
    total_calc_words = sum(r['words'] for r in results.values())
    total_exp_hours = sum(e['hours'] for e in expected.values())
    total_exp_words = sum(e['words'] for e in expected.values())
    
    print("=" * 70)
    print(f"{'TOTAL':<10} {total_calc_hours:>14.2f} {total_exp_hours:>14.2f} {total_calc_hours - total_exp_hours:>9.2f}")
    print(f"{'':10} {total_calc_words:>14,} {total_exp_words:>14,} {total_calc_words - total_exp_words:>9,}")


if __name__ == '__main__':
    main()
