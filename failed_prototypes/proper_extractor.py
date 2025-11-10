from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import json

# Setup
edge_driver_path = r"c:\Program Files\edgedriver_win64\msedgedriver.exe"
options = webdriver.EdgeOptions()
options.use_chromium = True
service = Service(executable_path=edge_driver_path)
driver = webdriver.Edge(service=service, options=options)

# Open SAP portal
driver.get('https://epp.fremont.lamrc.net/irj/portal?&EPPAP13_0')

# Wait for page to load
wait = WebDriverWait(driver, 30)  # Increased timeout to 30 seconds

# Step 1: Click "ERF Dashboard"
try:
    erf_dashboard = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@class='TabText' and text()='ERF Dashboard']")))
    erf_dashboard.click()
    print("ERF Dashboard Found and Clicked")
except Exception as e:
    print("ERF Dashboard Not Found")
    print(e)

# Step 2: Extract and parse HTML content
try:
    # Wait for the page to fully load
    wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
    
    # Extract the HTML content of the page
    html_content = driver.page_source
    
    # Parse the HTML using BeautifulSoup
    soup = BeautifulSoup(html_content, "html.parser")
    
    # Extract structured data
    structured_data = {}
    
    # Extract all buttons
    buttons = soup.find_all("button")
    structured_data["buttons"] = [{"text": button.get_text(strip=True), "id": button.get("id"), "class": button.get("class")} for button in buttons]
    
    # Extract all inputs
    inputs = soup.find_all("input")
    structured_data["inputs"] = [{"type": input.get("type"), "id": input.get("id"), "name": input.get("name"), "class": input.get("class"), "value": input.get("value")} for input in inputs]
    
    # Extract all dropdowns (select elements)
    dropdowns = soup.find_all("select")
    structured_data["dropdowns"] = [{"id": dropdown.get("id"), "name": dropdown.get("name"), "class": dropdown.get("class"), "options": [option.get_text(strip=True) for option in dropdown.find_all("option")]} for dropdown in dropdowns]
    
    # Extract all divs
    divs = soup.find_all("div")
    structured_data["divs"] = [{"text": div.get_text(strip=True), "id": div.get("id"), "class": div.get("class")} for div in divs]
    
    # Save structured data to a JSON file
    with open("structured_erf_dashboard_data.json", "w", encoding="utf-8") as json_file:
        json.dump(structured_data, json_file, ensure_ascii=False, indent=4)
    
    print("Structured HTML content successfully extracted and saved to 'structured_erf_dashboard_data.json'")
except Exception as e:
    print("Failed to extract and structure HTML content")
    print(e)

# Close browser
driver.quit()