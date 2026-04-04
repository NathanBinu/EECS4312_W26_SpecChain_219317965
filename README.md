# EECS4312_W26_SpecChain

<!-- ## instructions:
Please update to include: 
- App name
- Data collection method
- Original dataset
- Final cleaned dataset
- Exact commands to run pipeline

# example
Application: [Calm]

Dataset:
- reviews_raw.jsonl contains the collected reviews.
- reviews_clean.jsonl contains the cleaned dataset.
- The cleaned dataset contains 842 reviews.

Repository Structure:
- data/ contains datasets and review groups
- personas/ contains persona files
- spec/ contains specifications
- tests/ contains validation tests
- metrics/ contains all metric files
- src/ contains executable Python scripts
- reflection/ contains the final reflection

How to Run:
1. python src/00_validate_repo.py
2. python src/02_clean.py
3. python src/run_all.py
4. Open metrics/metrics_summary.json for comparison results -->

<!-- --------------------------------------------------------------------------- -->

## Application
MindDoc: Mental Health Support  
Package ID: de.moodpath.android

## Data Collection Method
The dataset was collected using the Google Play Scraper API via `google-play-scraper`.  
Reviews were retrieved programmatically and stored in JSONL format.

## Dataset
- `data/reviews_raw.jsonl` contains the collected reviews.
- `data/reviews_clean.jsonl` contains the cleaned dataset.
- The cleaned dataset contains **2584 reviews**.

## Repository Structure
- `data/` contains datasets and review groups  
- `personas/` contains persona files  
- `spec/` contains specifications  
- `tests/` contains validation tests  
- `metrics/` contains all metric files  
- `src/` contains executable Python scripts  
- `reflection/` contains the final reflection  

## Environment Setup
This project was developed using a Python virtual environment.

### Create and activate virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### Install dependencies
```bash
pip install google-play-scraper nltk emoji inflect requests python-dotenv
```

### Download NLTK resources
Run the following in Python:
```python
import nltk
nltk.download("stopwords")
nltk.download("wordnet")
nltk.download("omw-1.4")
exit()
```

## API Setup
The automated pipeline uses the Groq API.  
Create a `.env` file in the project root and add:
```
GROQ_API_KEY=your_api_key_here
```

## How to Run

1. Validate repository structure:
```bash
python src/00_validate_repo.py
```

2. Clean dataset:
```bash
python src/02_clean.py
```

3. Run full automated pipeline:
```bash
python src/run_all.py
```

4. View results:
```
metrics/metrics_summary.json
```