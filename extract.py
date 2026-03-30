import os
import re
import json
import subprocess
from pathlib import Path
from pdf2image import convert_from_path
import pytesseract
import pdfplumber
import pandas as pd
from normalize import normalize_api

#data and extraction paths
pdf_folder = Path("data/pdf_data")
ocr_folder= Path("data/ocr_pdfs")
extracted_folder = Path("extracted_data") / "extracted.jsonl"
ocr_folder.mkdir(parents=True, exist_ok=True)
extracted_folder.parent.mkdir(parents=True, exist_ok=True)

api_match = re.compile(r'\bAPI(?:\s*#|\:)?\s*[:\-\s]*([0-9\-]{6,20})', re.I)
latitude_match = re.compile(r'(Latitude|Lat)[:\s]*([-+]?\d{1,3}\.\d+)', re.I)
longitude_match = re.compile(r'(Longitude|Long)[:\s]*([-+]?\d{1,3}\.\d+)', re.I)

coordinate_match = re.compile(r'(\d{1,3}°\s*\d{1,2}\'\s*\d{1,2}(?:\.\d+)?\")')

#coverts the pdf into readable pdf to allow search
def ocrpdf(input_pdf: Path, output_pdf: Path):

    #shellcommand
    cmd = ["ocrmypdf", "--deskew", "--skip-text", str(input_pdf), str(output_pdf)]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        print(f"ocrmypdf failed for {input_pdf}: {e}. Trying without --skip-text.")
        cmd = ["ocrmypdf", "--deskew", str(input_pdf), str(output_pdf)]
        subprocess.run(cmd, check=False)


#extract text
def pdf_text(pdf_path: Path):
    text = ""
    try:
        #open pdf and extract text into a big string
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                text += "\n" + page_text
    except Exception as e:
        print("pdfplumber failed with:", e)
    return text

#incase plumber fails, convert to image and run tesseract
def tesseract_from_pdf(pdf_path: Path):
    text = ""
    images = convert_from_path(str(pdf_path), dpi=300)
    for i, img in enumerate(images):
        page_text = pytesseract.image_to_string(img, lang='eng')
        text += "\n" + page_text
    return text


# turns data into structured text
# use regex-based parsing
def parse_fields(text: str):
    out = {}

    #  API Extraction 

    # 1. labeled apis (clean format)
    api_labeled = re.search(
        r'API\s*(?:NUMBER|No\.?|#)?\s*[:\s]+\s*(33[-\s]?\d{3}[-\s]?\d{5}(?:[-\s]?\d{2})?)',
        text, re.I
    )

    # 2. if can't find api, find api anywhere in document
    api_bare = re.search(
        r'\b(33[-\s]\d{3}[-\s]\d{5}(?:[-\s]\d{2})?)\b',
        text
    )

    # 3 ndic file number (fallback ID if API is missing)
    ndic_match = re.search(r'NDIC\s+File\s+(?:Number|No\.?)\s*[:\s]+(\d{4,6})', text, re.I)
    file_no_match = re.search(r'(?:Well\s+)?File\s+No\.?\s*[:\s]*(\d{4,6})', text, re.I)

    if api_labeled:
        out['api'] = normalize_api(api_labeled.group(1).strip())
    elif api_bare:
        out['api'] = normalize_api(api_bare.group(1).strip())
    else:
        out['api'] = None

    # get ndic number as backup
    if ndic_match:
        out['ndic_file_number'] = ndic_match.group(1).strip()
    elif file_no_match:
        out['ndic_file_number'] = file_no_match.group(1).strip()
    else:
        out['ndic_file_number'] = None

    
    out['well_name'] = "Pending Web Scrape"

    # stim volume
    vol_pattern = r'(?:Acidized|Frac|Volume|Material Used)[\s\S]{0,100}?([\d,]{3,})\s*(?:gal|gallons|bbls|barrels)'
    vol_match = re.search(vol_pattern, text, re.I)
    out['stim_volume'] = float(vol_match.group(1).replace(',', '')) if vol_match else 0.0

    # stim proppant 
    prop_pattern = r'(?:Proppant|Sand|Lbs|Prop)[\s\S]{0,50}?([\d,]{4,})\s*(?:lbs|pounds|#)'
    prop_match = re.search(prop_pattern, text, re.I)
    out['stim_proppant'] = float(prop_match.group(1).replace(',', '')) if prop_match else 0.0

    return out

def main():
    results = []
    pdf_files = sorted(pdf_folder.glob("*.pdf"))
   
    if extracted_folder.exists():
        extracted_folder.unlink()
   
    for pdf_file in pdf_files:
        print("Processing", pdf_file)
        ocr_pdf_path = ocr_folder / pdf_file.name
        ocrpdf(pdf_file, ocr_pdf_path)
        text = pdf_text(ocr_pdf_path)
        if (not text) or len(text) < 50:
            # if it doesnt work, run tesseract on images
            print("Fallback: running pdf2image + pytesseract")
            text = tesseract_from_pdf(ocr_pdf_path)
        parsed = parse_fields(text)
        parsed['source_pdf'] = str(pdf_file)
        results.append(parsed)


        # append to jsonl
        with open(extracted_folder, "a", encoding="utf-8") as f:
            f.write(json.dumps(parsed) + "\n")

        print("Extracted:", {
            "api": parsed.get("api"),
            "well_name": parsed.get("well_name"),
            "latitude": parsed.get("latitude"),
            "longitude": parsed.get("longitude")
        })
    print("Done")

if __name__ == "__main__":
    main()