# NBA-Game-Predictor
This project scrapes, processes, and analyzes NBA game data to predict future game outcomes using machine learning with an accuracy of 64%. It combines web scraping, data cleaning, and predictive modeling into a fully automated data pipeline, from raw HTML to trained model accuracy.


---

## Overview

The project has three main components:

### 1. Data Scraping (`src/scraper.py`)
- Scrapes NBA standings and game box scores from [Basketball Reference](https://www.basketball-reference.com/).
- Saves HTML files to `src/data/standings/` and `src/data/scores/`.
- Uses Playwright and BeautifulSoup for asynchronous scraping.

### 2. Data Parsing (`src/parser.py`)
- Reads and parses the scraped HTML files.
- Extracts team statistics and merges basic and advanced box scores.
- Adds season, date, home/away, and win/loss data.
- Outputs a clean dataset: `nba_games.csv`.

### 3. Prediction Model (`src/predictor.py`)
- Prepares and processes data for machine learning.
- Uses a Ridge Classifier with sequential feature selection.
- Performs season-by-season backtesting to measure prediction accuracy.

---

## Technologies Used
- Python 3.10+
- Playwright
- BeautifulSoup4
- pandas
- scikit-learn
- asyncio

---

## How to Run

1. **Install dependencies:**
   - Run:
     ```bash
     pip install -r requirements.txt
     ```

2. **Scrape the data (running this program will take a long time):**
   - Run:
     ```bash
     python3 src/scraper.py
     ```

3. **Parse and clean the data:**
   - Run:
     ```bash
     python3 src/parser.py
     ```

4. **Train and test the model:**
   - Run:
     ```bash
     python3 src/predictor.py
     ```

5. **Note:**  
   The `src/data/standings` and `src/data/scores` folders must exist before running the scripts. 
