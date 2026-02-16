# Pushing CORAAL to Hugging Face Hub


## Download

All files available here: https://lingtools.uoregon.edu/coraal/
```
wget -i https://tinyurl.com/coraalfiles --no-check-certificate
```

Extract
```
./extract_coraal.sh
```

NOTE: I also had to download the metadata files from the above link, and put inside each component's folder.


## Setup

1. Install required packages:
```bash
pip install -r requirements.txt
```

2. Login to Hugging Face:
```bash
huggingface-cli login
```
Enter your Hugging Face token when prompted.

3. Edit the script:
Open `push_to_huggingface.py` and update:
- `REPO_ID = "your-username/coraal"` → Change to your HF username
- `PRIVATE = False` → Set to `True` if you want a private dataset
- `TEST_MODE = True` → Set to `False` if you want upload a subset for testing/debugging

4. Run the script:
```bash
python3 push_to_huggingface.py
```

## Dataset Structure

The dataset is organized with each CORAAL component (ATL, DCA, DCB, DTA, LES, PRV, ROC, VLD) as a separate **config/subset**. Each config has a "test" split containing all samples for that component.

### Loading the Dataset

```python
from datasets import load_dataset

# Load a specific component
dataset = load_dataset("your-username/coraal", "ATL")

# Access the test split
test_data = dataset["test"]
```

### Columns

Each sample includes:

- **audio**: Audio file (WAV format, original sampling rate preserved)
- **text**: Concatenated transcript text (pauses, sound labels like `[<laugh>]`, descriptors like `(breathy)`, and redactions removed)
- **file_id**: Full filename without extension (e.g., "ATL_se0_ag1_f_01_1")
- **Metadata columns**: All columns from the component's metadata file (varies by component)

Common metadata columns include:
- Gender, Age, Age.Group, Year.of.Birth, Year.of.Interview
- Education, Edu.Group, Occupation
- CORAAL.Spkr, Primary.Spkr, Guardian birthplaces, etc.

**Note**: Each component has its own metadata schema based on its metadata file, so available columns may differ between components.

## Notes

- The script processes all 8 CORAAL components as separate configs
- Each component preserves its original metadata columns
- Text is cleaned of pauses, sound labels, descriptors, and redactions
- Audio files are included in their original format and sampling rate
- Total dataset size is ~160 hours of audio across all components
