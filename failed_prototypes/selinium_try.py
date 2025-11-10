from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

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
    driver.quit()
    exit()

# Step 2: Switch to Iframe 1
try:
    # Wait for the page to fully load
    wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
    time.sleep(5)  # Add a delay to allow dynamic content to load
    
    # Locate Iframe 1
    iframe_1 = wait.until(EC.presence_of_element_located((By.ID, "contentAreaFrame")))
    driver.switch_to.frame(iframe_1)
    print("Switched to Iframe 1")
    
    # Locate the nested iframe (isolatedWorkArea)
    nested_iframe = wait.until(EC.presence_of_element_located((By.ID, "isolatedWorkArea")))
    driver.switch_to.frame(nested_iframe)
    print("Switched to Nested Iframe (isolatedWorkArea)")

except Exception as e:
    print("Error while switching to Iframe 1 or Nested Iframe")
    print(e)
    driver.quit()
    exit()

# Step 3: Locate and Interact with Elements Inside the Target <div>
try:
    # Locate the Plant dropdown
    plant_input = wait.until(EC.element_to_be_clickable((By.ID, "aaaa.RpmDashboardView.PlantsDdbk")))
    print(f"Is Plant Input displayed? {plant_input.is_displayed()}")
    print(f"Is Plant Input enabled? {plant_input.is_enabled()}")
    plant_input.click()
    print("Plant Input Found and Clicked")
    
    # Wait for dropdown options to appear and select "ALL"
    all_option = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(text(),'ALL')]")))
    all_option.click()
    print("Dropdown Option 'ALL' Found and Selected")
    
except Exception as e:
    print("Plant Input or Dropdown Option Not Found")
    print(e)
    driver.quit()
    exit()

# Step 4: Enter ERF number
try:
    erf_input = wait.until(EC.element_to_be_clickable((By.ID, "aaaa.RpmDashboardView.ERFNumInp")))
    print(f"Is ERF Input displayed? {erf_input.is_displayed()}")
    print(f"Is ERF Input enabled? {erf_input.is_enabled()}")
    erf_input.clear()
    erf_input.send_keys("633398")
    print("ERF Number Entered")
except Exception as e:
    print("ERF Input Not Found")
    print(e)
    driver.quit()
    exit()

# Step 5: Click Search button
try:
    search_button = wait.until(EC.element_to_be_clickable((By.ID, "aaaa.RpmDashboardView.SearchBtn")))
    print(f"Is Search Button displayed? {search_button.is_displayed()}")
    print(f"Is Search Button enabled? {search_button.is_enabled()}")
    search_button.click()
    print("Search Button Clicked")
except Exception as e:
    print("Search Button Not Found")
    print(e)
    driver.quit()
    exit()

# Step 6: Click on the "1" Link
try:
    one_link = wait.until(EC.element_to_be_clickable((By.ID, "aaaa.RpmDashboardView.ALL_1Lta-text")))
    print(f"Is '1' Link displayed? {one_link.is_displayed()}")
    print(f"Is '1' Link enabled? {one_link.is_enabled()}")
    one_link.click()
    print("'1' Link Found and Clicked")
    
    # Wait for the screen to load
    time.sleep(2)  # Add a delay to allow the screen to load

except Exception as e:
    print("'1' Link Not Found")
    print(e)
    driver.quit()
    exit()

# Step 7: Click on "Update/View ERF" Button
try:
    update_button = wait.until(EC.element_to_be_clickable((By.ID, "aaaa.HeaderView.UpdateBtn")))
    print(f"Is 'Update/View ERF' Button displayed? {update_button.is_displayed()}")
    print(f"Is 'Update/View ERF' Button enabled? {update_button.is_enabled()}")
    update_button.click()
    print("'Update/View ERF' Button Found and Clicked")
    
    # Wait for the final page to load
    time.sleep(2)

except Exception as e:
    print("'Update/View ERF' Button Not Found")
    print(e)
    driver.quit()
    exit()

# Step 8: Extract and Print Final Page Details
try:
    # Extract Short Order Description
    short_order_desc = driver.find_element(By.ID, "aaaa.CreateOrderView.ShortDescInp").get_attribute("value")
    print(f"Short Order Description: {short_order_desc}")
    
    # Extract Internal Order
    internal_order = driver.find_element(By.ID, "aaaa.CreateOrderView.InternalOrderInp").get_attribute("value")
    print(f"Internal Order: {internal_order}")
    
    # Extract Cost Center
    cost_center = driver.find_element(By.ID, "aaaa.CreateOrderView.CostCenterInp").get_attribute("value")
    print(f"Cost Center: {cost_center}")

except Exception as e:
    print("Error while extracting final page details")
    print(e)
    driver.quit()
    exit()

# Close browser
driver.quit()
print("Session closed successfully.")