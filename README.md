# Oil Well Data Extraction & Visualization

## Overview

This project is an end-to-end data pipeline that extracts, normalizes, enriches, and visualizes oil well data from multiple sources. It processes unstructured, scanned PDF documents (Completion Reports) using Optical Character Recognition (OCR), merges that data with live geographic and production metadata scraped from the web, and stores the integrated dataset in a normalized MySQL database. Finally, it serves this data to an interactive, frontend Leaflet map.

---

## Project Structure & File Overview

The codebase is modularized to separate heavy processing (OCR) from network-dependent tasks (scraping) and database operations.

### Data Extraction & Processing

| File | Description |
|------|-------------|
| `extract.py` | Loops through all scanned PDFs in `data/pdf_data/`, applies deskewing and OCR using `ocrmypdf` and `pdfplumber` (with a `pytesseract` fallback), and extracts the Universal API Number and Stimulation Volumes. Outputs raw checkpoints to `extracted_data/extracted.jsonl`. |
| `normalize.py` | A utility module containing the `normalize_api()` function. Ensures all API numbers are strictly cleaned into the standard 10-digit North Dakota format (`33-XXX-XXXXX`), regardless of OCR noise or formatting. |
| `web_scrape.py` | The Selenium web-scraping module. Utilizes a headless Chrome WebDriver to search `drillingedge.com` by API number and extracts DOM-based metadata (Latitude, Longitude, Well Status, Well Type, Closest City, and Production Stats). |
| `process_all.py` | Reads `extracted.jsonl`, normalizes the APIs, manages a single persistent Selenium browser session to fetch web data, and merges both sources into a final "Golden Dataset" saved as `extracted_data/final_cleaned_data.json`. |

### Database Management

| File | Description |
|------|-------------|
| `schema.sql` | The SQL script that initializes the `dsci560_wells` database and creates the relational `wells` and `stimulation` tables. |
| `insertsql.py` | Parses the final cleaned JSON file and performs an "UPSERT" (Insert or Update on Duplicate Key) into MySQL to prevent duplicate entries while capturing 1-to-many stimulation stages. |

### Web Application & Visualization

| File | Description |
|------|-------------|
| **Apache Web Server** | Serves as the primary HTTP server (port 80). Configured as a reverse proxy that forwards all incoming browser requests to the Flask application running on 127.0.0.1:5000. |
| `app.py` | The Python Flask backend server. Connects to MySQL, joins the `wells` and `stimulation` tables, and serves data as a JSON REST API at `/api/wells`. Also serves the frontend UI. |
| `index.html` | The frontend UI. Uses Leaflet.js and MarkerCluster to render an interactive map — dynamically plots well markers, color-codes them by well type, handles popup generation, and includes filtering/CSV export controls. |


---

## Setup & Installation

### 1. Install System Dependencies

Required for OCR and PDF processing. Google Chrome must also be installed for the web scraper.
```bash
sudo apt-get update
sudo apt-get install -y ocrmypdf tesseract-ocr poppler-utils ghostscript
```

**Install Google Chrome for Selenium:**
```bash
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install -y ./google-chrome-stable_current_amd64.deb
```

### 2. Create and Activate a Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Python Requirements
```bash
pip install -r requirements.txt
```

---

## Database Setup

Create the SQL database schema before running the pipeline.
```bash
sudo mysql < schema.sql
```

> **Note:** If your MySQL user requires a password, run `mysql -u root -p < schema.sql` instead.

This creates the `dsci560_wells` database containing the `wells` and `stimulation` tables.

---

## Execution Pipeline

Follow these steps **in order** to process data from raw PDFs to the final web map.

### Step 1 — Extract Data from PDFs

> This step takes the longest as it performs image-to-text OCR on all PDFs.

```bash
python3 extract.py
```

**Output:** `extracted_data/extracted.jsonl`

---

### Step 2 — Web Scraping & Data Merging

```bash
python3 process_all.py
```

**Output:** `extracted_data/final_cleaned_data.json`

---

### Step 3 — Insert Data into MySQL

```bash
python3 insertsql.py \
  --file extracted_data/final_cleaned_data.json \
  --user root \
  --password yourpassword \
  --commit
```

> Omit `--password` if your local root user does not require one.

---
### Step 4 — Start the Web Application Start the Flask backend
```bash
python3 app.py
```
The flask server will run internally on
http://127.0.0.1:5000
Ensure apache is on
```bash
sudo systemctl start apache2
```
--- 

## Using the Application 
Open your browser and navigate to: http://<IP_ADDRESS>/

---

### Features

- **Interactive Mapping** — View all oil wells clustered dynamically by region.
- **Detailed Popups** — Click any marker to view technical data including API, location, production stats, and stimulation/frac stages.
- **Raw Data Inspector** — Expand the "Raw JSON" toggle inside any popup to inspect the raw scraped data structure.
- **Filtering** — Use the control panel (top right) to filter wells by Status (Active/Plugged), minimum oil production, or search by API/Name.
- **CSV Export** — Click the green "Export CSV" button to download a spreadsheet of the currently visible (filtered) wells.
