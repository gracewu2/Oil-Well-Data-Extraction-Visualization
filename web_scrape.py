import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from normalize import normalize_api
from selenium.webdriver.support import expected_conditions as EC

from selenium.webdriver.support.ui import WebDriverWait

BASE_SEARCH_URL = "https://www.drillingedge.com/search"
BASE_URL = "https://www.drillingedge.com"

# create headless Chrome browser 
def create_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--start-maximized")

    driver = webdriver.Chrome(options=options)
    return driver


from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def search_well(driver, api):
    # Standardize the API (remove dashes for the search box)
    api_clean = api.replace("-", "") 
    
    # Start at the base search page
    driver.get("https://www.drillingedge.com/search")
    # wait for page to load 
    wait = WebDriverWait(driver, 15)

    try:
        # 1. Find the API input box and type the number
        # (Assuming the input box has the name "api_no" based on the URL structure)
        search_box = wait.until(EC.presence_of_element_located((By.NAME, "api_no")))
        search_box.clear()
        search_box.send_keys(api_clean)

        # 2. Click the specific "Search Database" button you inspected
        search_button = driver.find_element(By.XPATH, "//input[@type='submit' and @value='Search Database']")
        search_button.click()

        # 3. Wait for the results to load and grab the link to the well
        link_xpath = "//table[contains(@class, 'interest_table')]//a[contains(@href, '/wells/')]"
        well_link = wait.until(EC.presence_of_element_located((By.XPATH, link_xpath)))
        
        return well_link.get_attribute("href")
        
    except Exception as e:
        print(f"Manual search simulation failed for {api}: {e}")
        return None

 # extract data   
def scrape_well_page(driver, url):
    # open well page 
    driver.get(url)
    time.sleep(3)
    # grab all visible text 
    page_text = driver.find_element(By.TAG_NAME, "body").text

    data = {
        "well_name": "Unknown",
        "well_status": "N/A",
        "well_type": "N/A",
        "closest_city": "N/A",
        "latitude": 0.0,
        "longitude": 0.0,
        "barrels_oil": 0.0,
        "barrels_gas": 0.0
    }

    # 1. Resilient extraction using text offsets (Handles smashed text)
    def get_val(header, end_trigger):
        if header in page_text:
            part = page_text.split(header)[-1].split(end_trigger)[0].strip()
            return part
        return "N/A"

    data["well_name"] = get_val("Well Name", "API No.")
    data["well_status"] = get_val("Well Status", "Well Type")
    data["well_type"] = get_val("Well Type", "Township")
    data["closest_city"] = get_val("Closest City", "Latitude")
    
    # 2. Extract Latitude and Longitude
    coords = re.search(r'Latitude / Longitude\s*([-+]?\d+\.\d+),\s*([-+]?\d+\.\d+)', page_text)
    if coords:
        data["latitude"] = float(coords.group(1))
        data["longitude"] = float(coords.group(2))

    # 3. Grabbing Monthly production (Bypassing paywall)
    oil = re.search(r'([\d,]+)\s*Barrels of Oil', page_text)
    gas = re.search(r'([\d,]+)\s*MCF of Gas', page_text)
    data["barrels_oil"] = float(oil.group(1).replace(',', '')) if oil else 0.0
    data["barrels_gas"] = float(gas.group(1).replace(',', '')) if gas else 0.0

    return data

def get_well_data(api, driver):  # accept driver instead of creating one
    try:
        # find well page 
        well_url = search_well(driver, api)
        if not well_url:
            print("No well found")
            return None
        print("Scraping:", well_url)
        data = scrape_well_page(driver, well_url)
        return data
    except Exception as e:
        print(f"Error scraping {api}: {e}")
        return None


if __name__ == "__main__":
    #replace with json list
    test_api = "33-053-02102"
    data = get_well_data(test_api)
    print(data)