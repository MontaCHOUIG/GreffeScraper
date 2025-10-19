from selenium import webdriver
from selenium.webdriver.common.by import By
import time

# Test if selenium is working
options = webdriver.ChromeOptions()
# options.add_argument('--headless')
options.add_argument('--no-sandbox')

driver = webdriver.Chrome(options=options)

try:
    driver.get("https://lannuaire.service-public.gouv.fr/recherche?whoWhat=Greffe+des+associations&page=1")
    time.sleep(3)
    
    print(f"Page title: {driver.title}")
    
    elements = driver.find_elements(By.CSS_SELECTOR, "a[data-test='searchResult-link']")
    print(f"Found {len(elements)} links")
    
    if elements:
        for i, elem in enumerate(elements[:5]):  # Show first 5
            print(f"{i+1}. {elem.text}: {elem.get_attribute('href')}")
    
finally:
    driver.quit()

print("\nSelenium is working correctly!")
