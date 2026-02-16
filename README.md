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

The script creates a dataset with the following columns:

- **audio**: Audio file (WAV format)
- **text**: Concatenated transcript text (pauses and metadata removed)
- **file_id**: Full filename without extension (e.g., "ATL_se0_ag1_f_01_1")
- **component**: Dataset component (ATL, DCA, DCB, DTA, LES, PRV, ROC, VLD)
- **session**: Session identifier (e.g., "se0")
- **age_group**: Age group (e.g., "ag1")
- **gender**: Gender (f/m)
- **speaker_id**: Speaker ID number
- **recording_number**: Recording session number

## Notes

- The script processes all 8 CORAAL components
- Text is cleaned of pauses, metadata, and special markers
- Audio files are included in their original format and sampling rate
- Total dataset size will be ~160 hours of audio
