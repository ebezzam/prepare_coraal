#!/usr/bin/env python3
"""
Push CORAAL dataset to Hugging Face Hub.
Creates a dataset with audio files and concatenated transcript text.

Required packages:
    pip install datasets huggingface-hub soundfile
    
    # On macOS (required for audio encoding):
    brew install ffmpeg
    
    # Then install torch and torchcodec:
    pip install torch torchcodec

Or install from requirements_hf.txt:
    brew install ffmpeg  # macOS
    pip install -r requirements_hf.txt

Setup:
    1. Create a Hugging Face account at https://huggingface.co/join
    2. Create an access token at https://huggingface.co/settings/tokens
       - Click "New token"
       - Select "Write" permissions
       - Copy the token
    3. Login with the token:
       huggingface-cli login
       (or set HF_TOKEN environment variable)
    4. Update REPO_ID in this script to your username/dataset-name
"""

import os
import re
import csv
from pathlib import Path
from datasets import Dataset, DatasetDict, Audio, Features, Value


def extract_text_from_txt(txt_path):
    """
    Extract and concatenate all transcript text from a CORAAL .txt file.
    Excludes pauses and metadata, returns a single concatenated string.
    """
    texts = []
    
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
                    
                    # Remove brackets but keep the text inside
                    content = re.sub(r'[\[\]]', '', content)
                    
                    # Remove angle brackets and their content (like <laugh>, <ts>)
                    content = re.sub(r'<[^>]+>', '', content)
                    
                    # Remove redactions entirely (like /RD-NAME-2/)
                    content = re.sub(r'/RD-[^/]+/', '', content)
                    
                    # Remove descriptors in parentheses (like (breathy))
                    content = re.sub(r'\([a-zA-Z]+\)', '', content)
                    
                    # Clean up whitespace
                    content = ' '.join(content.split())
                    
                    if content:
                        texts.append(content)
    
    except Exception as e:
        print(f"Error reading {txt_path}: {e}")
        return ""
    
    return ' '.join(texts)


def load_metadata(component_dir, component):
    """
    Load metadata from the component's metadata file.
    Returns a dictionary mapping CORAAL.File to metadata row.
    """
    # Find metadata file (pattern: COMPONENT_metadata_*.txt)
    metadata_files = list(Path(component_dir).glob(f'{component}_metadata_*.txt'))
    
    if not metadata_files:
        print(f"ERROR: No metadata file found for {component}")
        print(f"  Searched in: {component_dir}")
        print(f"  Looking for pattern: {component}_metadata_*.txt")
        print(f"  Files in directory: {[f.name for f in Path(component_dir).glob('*.txt')][:5]}")
        return {}
    
    metadata_file = metadata_files[0]
    print(f"  Found metadata: {metadata_file.name}")
    metadata_dict = {}
    
    try:
        with open(metadata_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                file_id = row.get('CORAAL.File', '')
                if file_id:
                    metadata_dict[file_id] = row
        
        if not metadata_dict:
            print(f"  ERROR: No valid metadata entries found in {metadata_file.name}")
            print(f"  Check that the file has a 'CORAAL.File' column")
        else:
            print(f"  Loaded {len(metadata_dict)} metadata entries")
            
    except Exception as e:
        print(f"  ERROR reading metadata file {metadata_file}: {e}")
        return {}
    
    return metadata_dict


def parse_filename(filename):
    """
    Parse CORAAL filename to extract file_id.
    Format: COMPONENT_seX_agY_GENDER_ID_SESSION.ext
    Example: ATL_se0_ag1_f_01_1.wav -> ATL_se0_ag1_f_01
    """
    base = Path(filename).stem
    # Extract the file_id without the session number at the end
    # e.g., ATL_se0_ag1_f_01_1 -> ATL_se0_ag1_f_01
    parts = base.rsplit('_', 1)
    if len(parts) == 2:
        file_id = parts[0]
    else:
        file_id = base
    
    return file_id


def collect_dataset_samples(base_dir='.', max_per_component=None):
    """
    Collect all audio files and their corresponding transcripts.
    Returns a dictionary mapping component names to lists of samples.
    
    Args:
        base_dir: Base directory containing component folders
        max_per_component: Maximum samples per component (None = all samples)
    """
    components = ['ATL', 'DCA', 'DCB', 'DTA', 'LES', 'PRV', 'ROC', 'VLD']
    
    all_samples = {}
    
    for component in components:
        component_dir = os.path.join(base_dir, component)
        
        if not os.path.isdir(component_dir):
            print(f"Warning: {component} directory not found, skipping...")
            continue
        
        # Load metadata for this component
        metadata_dict = load_metadata(component_dir, component)        
        if not metadata_dict:
            print(f"  WARNING: No metadata loaded for {component}, samples will have no metadata columns")
        
        # Find all audio files
        wav_files = list(Path(component_dir).glob('*.wav'))
        
        # Limit samples if in test mode
        if max_per_component is not None:
            wav_files = wav_files[:max_per_component]
        
        total_in_dir = len(list(Path(component_dir).glob('*.wav')))
        if max_per_component is not None and total_in_dir > max_per_component:
            print(f"Processing {component}: {len(wav_files)} audio files (limited from {total_in_dir})")
        else:
            print(f"Processing {component}: {len(wav_files)} audio files")
        
        samples = []
        
        for wav_file in wav_files:
            # Get corresponding txt file
            txt_file = wav_file.with_suffix('.txt')
            
            if not txt_file.exists():
                print(f"Warning: No transcript found for {wav_file.name}")
                continue
            
            # Extract text
            text = extract_text_from_txt(txt_file)
            
            # Parse filename to get file_id (use full stem for metadata lookup)
            full_file_id = Path(wav_file).stem
            
            # Get metadata for this file using the full file_id
            file_metadata = metadata_dict.get(full_file_id, {})
            
            if not file_metadata and metadata_dict:
                # Debug: show what we're looking for vs what's available
                print(f"  Warning: No metadata found for {full_file_id}")
                sample_keys = list(metadata_dict.keys())[:3]
                print(f"    Sample metadata keys: {sample_keys}")
            
            # Create sample with text, file_id, and all metadata columns
            sample = {
                'audio': str(wav_file),
                'text': text,
                'file_id': full_file_id,
            }
            
            # Add all metadata columns
            if file_metadata:
                sample.update(file_metadata)
            
            samples.append(sample)
        
        if samples:
            all_samples[component] = samples
    
    return all_samples


def create_datasets(all_samples):
    """
    Create HuggingFace Datasets from the collected samples, one per component.
    Returns a dictionary mapping component names to their datasets.
    Each component will be a separate config/subset with its own metadata schema.
    """
    component_datasets = {}
    
    for component, samples in all_samples.items():
        if not samples:
            continue
        
        # Get all unique column names from samples for this component
        all_keys = set()
        for sample in samples:
            all_keys.update(sample.keys())
        
        # Define features dynamically based on what's in this component's data
        features = {
            'audio': Audio(sampling_rate=None),
            'text': Value('string'),
            'file_id': Value('string'),
        }
        
        # Add all other columns as string features
        for key in all_keys:
            if key not in features:
                features[key] = Value('string')
        
        # Create dataset for this component
        dataset = Dataset.from_list(samples, features=Features(features))
        
        component_datasets[component] = dataset
        
        print(f"  Created config '{component}' with {len(dataset)} samples and {len(features)} columns")
    
    return component_datasets


def push_dataset_to_hub(component_datasets, repo_id, token=None, private=False):
    """
    Push the dataset to Hugging Face Hub.
    Each component is pushed as a separate config/subset with a 'test' split.
    
    Args:
        component_datasets: Dictionary mapping component names to Dataset objects
        repo_id: Repository ID on HuggingFace (e.g., "username/coraal")
        token: HuggingFace token (optional, will use HF_TOKEN env var if not provided)
        private: Whether to make the repository private
    """
    print(f"\nPushing dataset to {repo_id}...")
    total_samples = sum(len(ds) for ds in component_datasets.values())
    print(f"Total samples: {total_samples} across {len(component_datasets)} configs")
    print(f"Private: {private}")
    print(f"Configs: {', '.join(component_datasets.keys())}")
    
    for component, dataset in component_datasets.items():
        print(f"\n  Pushing config '{component}'...")
        # Wrap in DatasetDict with 'test' split
        dataset_dict = DatasetDict({"test": dataset})
        
        dataset_dict.push_to_hub(
            repo_id,
            config_name=component,
            token=token,
            private=private
        )
        print(f"    ✓ Config '{component}' pushed ({len(dataset)} samples)")
    
    print(f"\n✓ All configs successfully pushed to https://huggingface.co/datasets/{repo_id}")
    print(f"  Load with: load_dataset('{repo_id}', 'COMPONENT_NAME')")
    print(f"  Available configs: {', '.join(component_datasets.keys())}")


def main():
    """Main function to create and push the CORAAL dataset."""
    
    print("=" * 70)
    print("CORAAL Dataset → Hugging Face Hub")
    print("=" * 70)
    
    # Configuration (change accordingly!)
    REPO_ID = "bezzam/coraal"
    PRIVATE = False  # Set to True if you want a private dataset
    TOKEN = None  # Will use HF_TOKEN environment variable if None
    TEST_MODE = False  # Set to False to upload full dataset
    TEST_SAMPLES_PER_COMPONENT = 2  # Number of samples per component in test mode
    
    print(f"\nConfiguration:")
    print(f"  Repository: {REPO_ID}")
    print(f"  Private: {PRIVATE}")
    print(f"  Test Mode: {TEST_MODE}")
    if TEST_MODE:
        print(f"  Samples per component: {TEST_SAMPLES_PER_COMPONENT}")
    print()
    
    # Collect samples
    print("Step 1: Collecting audio files and transcripts...")
    max_samples = TEST_SAMPLES_PER_COMPONENT if TEST_MODE else None
    all_samples = collect_dataset_samples('.', max_per_component=max_samples)
    
    if not all_samples:
        print("Error: No samples collected. Check that audio and txt files exist.")
        return
    
    total_count = sum(len(samples) for samples in all_samples.values())
    print(f"✓ Collected {total_count} samples across {len(all_samples)} components\n")
    
    # Show sample data for each component
    print("Sample data for each component:")
    print("=" * 70)
    for component, samples in all_samples.items():
        if samples:
            first_sample = samples[0]
            # Get metadata columns (exclude audio, text, file_id)
            metadata_cols = [k for k in first_sample.keys() if k not in ['audio', 'text', 'file_id']]
            
            print(f"\n{component}:")
            print(f"  File ID: {first_sample['file_id']}")
            print(f"  Text preview: {first_sample['text'][:500]}...")
            print(f"  Metadata columns ({len(metadata_cols)}): {', '.join(metadata_cols[:10])}")
            if len(metadata_cols) > 10:
                print(f"    ... and {len(metadata_cols) - 10} more")
    print("\n" + "=" * 70 + "\n")
    
    # Create datasets
    print("Step 2: Creating HuggingFace Datasets...")
    component_datasets = create_datasets(all_samples)
    print(f"✓ Created {len(component_datasets)} dataset configs")
    print()
    
    # Push to hub
    print("Step 3: Pushing to Hugging Face Hub...")
    
    if REPO_ID == "your-username/coraal":
        print("\n⚠️  WARNING: Please update REPO_ID in the script!")
        print("   Change 'your-username/coraal' to your actual HuggingFace username/repo")
        print("\nTo push the dataset, run:")
        print("  1. Update REPO_ID in this script")
        print("  2. Login to HuggingFace: huggingface-cli login")
        print("  3. Run this script again")
        print("\nDataset is ready but not pushed.")
        return
    
    try:
        push_dataset_to_hub(component_datasets, REPO_ID, token=TOKEN, private=PRIVATE)
    except Exception as e:
        print(f"\n✗ Error pushing to hub: {e}")
        print("\nMake sure you:")
        print("  1. Have logged in: huggingface-cli login")
        print("  2. Have write access to the repository")
        print("  3. Have the correct repo_id format: 'username/dataset-name'")


if __name__ == '__main__':
    main()
