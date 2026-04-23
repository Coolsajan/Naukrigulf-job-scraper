import time
import random
import pandas as pd
from apify import Actor
from seleniumbase import Driver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

async def main():
    async with Actor:
        # 1. Setup Input (Allows you to change the URL from the Apify UI)
        actor_input = await Actor.get_input() or {}
        listing_url = actor_input.get("url", "https://www.naukrigulf.com/data-science-jobs-in-uae")

        # 2. Initialize Undetectable Driver for Server Environment
        # uc=True is essential for bypassing bot detection
        # headless=True is required for running on Apify servers
        driver = Driver(uc=True, headless=True) 
        full_data = []

        try:
            Actor.log.info(f"Opening listing page: {listing_url}")
            driver.get(listing_url)
            driver.maximize_window()
            time.sleep(random.uniform(3, 5))

            # Wait for job links to appear
            wait = WebDriverWait(driver, 20)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.tuple-wrap a.info-position")))
            
            link_elements = driver.find_elements(By.CSS_SELECTOR, "div.tuple-wrap a.info-position")
            job_urls = [link.get_attribute("href") for link in link_elements]
            
            Actor.log.info(f"Found {len(job_urls)} jobs. Starting extraction...")

            for i, url in enumerate(job_urls):
                Actor.log.info(f"[{i+1}] Navigating to: {url}")
                driver.get(url)
                
                # Wait for the job description to load
                time.sleep(random.uniform(4, 7)) 
                
                try:
                    wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "job-description")))
                    description = driver.find_element(By.CLASS_NAME, "job-description").text
                    
                    profile_items = driver.find_elements(By.CSS_SELECTOR, "div.candidate-profile div.col")
            
                    # Store data in a dictionary
                    job_data = {
                        "job_index": i,
                        "url": url,
                        "Description": description
                    }
                    
                    for item in profile_items:
                        try:
                            header = item.find_element(By.CLASS_NAME, "head").text.strip()
                            value = item.find_element(By.CLASS_NAME, "value").text.strip()
                            job_data[header] = value
                        except:
                            continue 

                    # Save to local list for DataFrame creation later
                    full_data.append(job_data)
                    
                    # 3. Push to Apify Dataset (Immediate persistence)
                    await Actor.push_data(job_data)
                    
                except Exception as e:
                    Actor.log.error(f"Failed job {i}: {str(e)}")
                    driver.execute_script("window.scrollBy(0, 300);")
                    time.sleep(2)

            # 4. Create DataFrame and Output as JSON
            if full_data:
                df = pd.DataFrame(full_data)
                # Setting index like your .T (transpose) logic
                df = df.fillna("")
                result_json = df.set_index("job_index").to_dict(orient="index")
                
                # Save the final structured JSON to the Key-Value Store
                await Actor.set_value("OUTPUT", result_json)
                Actor.log.info("Successfully saved DataFrame to Key-Value Store as 'OUTPUT'")

        finally:
            driver.quit()
            Actor.log.info("Scraper finished.")

# Standard entry point for Apify Actors
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
