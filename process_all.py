import json
import re
from web_scrape import get_well_data, create_driver
from normalize import normalize_api
import time

def parse_stimulation(text):
    # Search for "Acidized" or "Fracture" followed by a number and "gal" or "barrels"
    # This covers the 'Volume' requirement
    vol_match = re.search(r'(?:Acidized|Fracture|Volume|total)\s*[\w\s]*?\s*([\d,]+)\s*(?:gal|barrels|bbls)', text, re.I)
    
    # Search for "Proppant" or "Lbs" followed by a number
    prop_match = re.search(r'(?:Proppant|Lbs|Prop|Sand)\s*[\w\s]*?\s*([\d,]+)', text, re.I)
    
    volume = float(vol_match.group(1).replace(',', '')) if vol_match else 0.0
    proppant = float(prop_match.group(1).replace(',', '')) if prop_match else 0.0
    
    return volume, proppant


def main():
    final_results = []
    # avoid duplicates
    seen_apis = set()

    driver = create_driver()  # create once

    try:
        # read extracted data
        with open('extracted_data/extracted.jsonl', 'r') as f:
            # for each pdf
            for line in f:
                # get pdf data
                pdf_data = json.loads(line)
                api = pdf_data.get('api')
                api = normalize_api(api)

                if not api or api in seen_apis:
                    continue

                seen_apis.add(api)
                print(f"--- Processing {api} ---")

                # call web scraper 
                web_data = get_well_data(api, driver) or {}  # pass driver in

                # merge pdf & scraped data
                clean_entry = {
                    "api": api,
                    "well_name": web_data.get("well_name") or pdf_data.get("well_name"),
                    "latitude": web_data.get("latitude") or 0.0,
                    "longitude": web_data.get("longitude") or 0.0,
                    "status": web_data.get("well_status", "N/A"),
                    "well_type": web_data.get("well_type", "N/A"),
                    "closest_city": web_data.get("closest_city", "N/A"),
                    "oil_prod": web_data.get("barrels_oil", 0.0),
                    "gas_prod": web_data.get("barrels_gas", 0.0),
                    "stim_volume": pdf_data.get("stim_volume", 0.0),
                    "stim_proppant": pdf_data.get("stim_proppant", 0.0)
                }

                final_results.append(clean_entry)
                time.sleep(2)  

    finally:
        driver.quit()  # quit once at the end

    with open('extracted_data/final_cleaned_data.json', 'w') as f:
        json.dump(final_results, f, indent=4)
    print("\nDone!")

if __name__ == "__main__":
    main()