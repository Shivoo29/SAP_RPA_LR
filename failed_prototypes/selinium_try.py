from selenium import webdriver
import time

# Path to the Edge WebDriver executable
edge_driver_path = '"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"'  # Update this path

# Initialize WebDriver for Microsoft Edge
options = webdriver.EdgeOptions()
options.use_chromium = True
driver = webdriver.Edge(executable_path=edge_driver_path, options=options)

# Open the SAP portal
driver.get('https://epp.fremont.lamrc.net/irj/portal?&EPPAP13_0')

# Wait for the page to load (adjust the sleep time as needed)
time.sleep(10)  # Wait for 10 seconds to ensure the page loads

# Print the title of the page to verify it opened correctly
print(driver.title)

# Close the browser
driver.quit()