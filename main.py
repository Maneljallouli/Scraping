import time
import chromedriver_autoinstaller
chromedriver_autoinstaller.install()  # Installe automatiquement le ChromeDriver compatible

from typing import Dict
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------- CONFIG LOGIN ----------------------
LINKEDIN_USERNAME = "jallouli.manel.44@gmail.com"
LINKEDIN_PASSWORD = "Manel_linkedin@@123"
LI_AT_COOKIE = "AQEDAUilXRIB-m9SAAABmZr3SMoAAAGaJlYtjE4AbDFXE5o10lsEhYHTODo0209dUkkoRL-zq9uet4C1KEKAwP8lmxR3Dj1NBbrBQ1_SqKslfHjIdXnI5_7OrI6kJGp2IcESy_yRA7v062OZUgt5JKiB"

# ---------------------- SCRAPING FUNCTION ----------------------
def scrape_linkedin_profile(profile_url: str) -> Dict:
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")  # Headless moderne
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-logging")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--remote-debugging-port=9222")

    driver = webdriver.Chrome(options=chrome_options)
    driver.get("https://www.linkedin.com/login")
    time.sleep(2)

    # ---------------------- Auth via username/password ----------------------
    try:
        username_field = driver.find_element(By.ID, "username")
        password_field = driver.find_element(By.ID, "password")
        username_field.send_keys(LINKEDIN_USERNAME)
        password_field.send_keys(LINKEDIN_PASSWORD)
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        time.sleep(5)

        if "feed" not in driver.current_url:
            print("Connexion via username/password échouée, tentative avec cookie li_at...")
            driver.get("https://www.linkedin.com/")
            driver.add_cookie({
                "name": "li_at",
                "value": LI_AT_COOKIE,
                "domain": ".linkedin.com"
            })
            driver.get(profile_url)
            time.sleep(4)
    except Exception:
        # Si l'auth par mot de passe échoue, on utilise le cookie
        driver.get("https://www.linkedin.com/")
        driver.add_cookie({
            "name": "li_at",
            "value": LI_AT_COOKIE,
            "domain": ".linkedin.com"
        })
        driver.get(profile_url)
        time.sleep(4)

    # ---------------------- Scroll jusqu’en bas ----------------------
    def scroll_to_end(driver, max_attempts=30, wait=1):
        last_height = driver.execute_script("return document.body.scrollHeight")
        for _ in range(max_attempts):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(wait)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

    scroll_to_end(driver)

    # ---------------------- Extraction des sections ----------------------
    def get_section_titles(section_title_text):
        try:
            section = driver.find_element(By.XPATH, f"//section[.//*[contains(text(), '{section_title_text}')]]")
            items = section.find_elements(By.XPATH, ".//li | .//div[@class='pvs-entity']")
            results = []
            for item in items:
                try:
                    spans = item.find_elements(By.TAG_NAME, "span")
                    if len(spans) >= 2:
                        title = spans[0].text.strip()
                        company = spans[1].text.strip()
                        if title and company:
                            results.append(f"{title} @ {company}")
                        elif title:
                            results.append(title)
                except:
                    continue
            return results if results else [f"No content found in {section_title_text}"]
        except NoSuchElementException:
            return [f"{section_title_text} section not found"]

    profile_data = {
        "about": get_section_titles("À propos"),
        "experience": get_section_titles("Expérience"),
        "education": get_section_titles("Formation"),
        "certifications": get_section_titles("Licences et certifications"),
        "skills": get_section_titles("Compétences"),
    }

    driver.quit()
    return profile_data

# ---------------------- ENDPOINT FASTAPI ----------------------
@app.get("/scrape")
def scrape(contactId: str = Query(...), linkedin: str = Query(...)):
    print(f"🔗 Scraping LinkedIn profile for contact ID: {contactId}")
    profile_data = scrape_linkedin_profile(linkedin)
    return {
        "contact_id": contactId,
        "linkedin_profile": linkedin,
        "scraped_data": profile_data
    }
