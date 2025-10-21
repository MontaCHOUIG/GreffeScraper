from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time, csv, re
from urllib.parse import urlparse, parse_qs

BASE = "https://lannuaire.service-public.gouv.fr"
SEARCH_URL = BASE + "/recherche?whoWhat=Greffe+des+associations&page={}"

def get_detail_links(driver, page):
    url = SEARCH_URL.format(page)
    print(f"Navigating to page {page}: {url}")
    driver.get(url)
    time.sleep(5)  # Increased wait time to avoid rate limiting
    
    print(f"Page title: {driver.title}")
    
    # Check for error messages or access restrictions
    body_text = driver.find_element(By.TAG_NAME, "body").text
    if "renforce temporairement son dispositif" in body_text or "accès" in body_text.lower():
        print("⚠️  Warning: Website may be blocking access. Waiting longer...")
        time.sleep(60)
        driver.get(url)
        time.sleep(5)
    
    links = []
    try:
        # Find all links with data-test="searchResult-link"
        elements = driver.find_elements(By.CSS_SELECTOR, "a[data-test='searchResult-link']")
        print(f"Found {len(elements)} result links")
        
        for elem in elements:
            href = elem.get_attribute("href")
            if href and href not in links:
                links.append(href)
    except Exception as e:
        print(f"Error finding links: {e}")
    
    return links

def parse_detail(driver, url):
    driver.get(url)
    time.sleep(3)  # Increased wait time
    
    # Check for error/blocking page
    body_text = driver.find_element(By.TAG_NAME, "body").text
    if "renforce temporairement son dispositif" in body_text:
        print("  ⚠️  Page blocked, waiting and retrying...")
        time.sleep(60)
        driver.get(url)
        time.sleep(5)
        body_text = driver.find_element(By.TAG_NAME, "body").text
    
    # Get name from h1
    name = ""
    try:
        h1 = driver.find_element(By.TAG_NAME, "h1")
        name = h1.text.strip()
        # Skip if we got the error message
        if "renforce temporairement" in name:
            name = "ERROR: Page blocked"
    except NoSuchElementException:
        pass
    
    # Get phone from page text - improved regex
    phone = ""
    phone_match = re.search(r"(?:Téléphone|Tel)[:\s]+([+\d\s\.]{10,})", body_text, re.IGNORECASE)
    if phone_match:
        phone = phone_match.group(1).strip()
    else:
        # Try alternative pattern for direct phone numbers
        phone_match = re.search(r"((?:0|\+33)[1-9](?:[\s\.]?\d{2}){4})", body_text)
        if phone_match:
            phone = phone_match.group(1).strip()
    
    # Get email - avoid the share link
    email = ""
    try:
        # Look for actual contact emails, not share links
        email_elems = driver.find_elements(By.CSS_SELECTOR, "a[href^='mailto:']")
        for elem in email_elems:
            href = elem.get_attribute("href")
            # Skip the share email link
            if "?subject=Service-Public.fr" not in href:
                email = href.replace("mailto:", "")
                break
    except NoSuchElementException:
        pass
    
    # Get coordinates from map link
    lat = lon = ""
    try:
        map_link = driver.find_element(By.CSS_SELECTOR, "a[href*='openstreetmap']")
        map_href = map_link.get_attribute("href")
        qs = parse_qs(urlparse(map_href).query)
        lat = qs.get("mlat", [""])[0]
        lon = qs.get("mlon", [""])[0]
    except NoSuchElementException:
        pass
    
    # Get address
    addr = ""
    try:
        # Find header containing "Lieu"
        headers = driver.find_elements(By.TAG_NAME, "h2") + driver.find_elements(By.TAG_NAME, "h3")
        for header in headers:
            if "Lieu" in header.text:
                # Get next p tag
                try:
                    addr_elem = header.find_element(By.XPATH, "./following-sibling::p[1]")
                    addr = addr_elem.text.strip()
                    break
                except NoSuchElementException:
                    pass
    except NoSuchElementException:
        pass
    
    # Extract region and city from URL
    parsed = urlparse(url)
    path_parts = parsed.path.strip("/").split("/")
    region = path_parts[0] if len(path_parts) > 0 else ""
    city = path_parts[1] if len(path_parts) > 1 else ""
    
    return {
        "name": name,
        "address": addr,
        "phone": phone,
        "email": email,
        "region": region,
        "city": city,
        "lat": lat,
        "lon": lon,
        "url": url
    }

def main():
    # Setup Chrome driver
    options = webdriver.ChromeOptions()
    # options.add_argument('--headless')  # Temporarily disable headless to debug
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    driver = webdriver.Chrome(options=options)
    
    try:
        all_data = []
        for page in range(1, 20):  # Increased to get all pages (198 results / ~10 per page = ~20 pages)
            print(f"\n{'='*60}")
            print(f"SCRAPING PAGE {page}")
            print(f"{'='*60}")
            
            links = get_detail_links(driver, page)
            if not links:
                print(f"No links found on page {page}. Stopping.")
                break
            
            print(f"Page {page}: found {len(links)} links")
            
            for i, link in enumerate(links, 1):
                print(f"  [{i}/{len(links)}] Processing: {link}")
                data = parse_detail(driver, link)
                
                # Skip entries that failed
                if "ERROR" in data.get("name", ""):
                    print(f"  ⚠️  Skipping blocked entry")
                    continue
                    
                all_data.append(data)
                print(f"  ✓ {data['name']}")
                time.sleep(2)  # Increased delay between requests
            
            # Longer delay between pages to avoid rate limiting
            print(f"\nWaiting before next page...")
            time.sleep(5)
        
        if not all_data:
            print("No data collected. CSV file will not be created.")
            return
        
        with open("greffes.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(all_data[0].keys()))
            writer.writeheader()
            writer.writerows(all_data)
        print(f"Successfully wrote {len(all_data)} records to greffes.csv")
    
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
