import time
import os

import chromedriver_autoinstaller
# Installe automatiquement le ChromeDriver compatible
chromedriver_autoinstaller.install()

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

# Récupération des identifiants depuis les variables d’environnement
LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")

# Endpoint racine pour tester si le service est actif
@app.get("/")
def root():
    return {
        "message": "Service Scraping LinkedIn actif. Utilisez /scrape avec contactId et linkedin."
    }

# Endpoint healthcheck
@app.get("/health")
def health():
    return {"status": "alive"}


def scrape_linkedin_profile(profile_url: str) -> Dict:
    chrome_options = Options()
    # Mode headless compatible Docker
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-logging")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_argument("--remote-debugging-port=9222")

    driver = webdriver.Chrome(options=chrome_options)
    driver.get("https://www.linkedin.com/login")
    time.sleep(2)

    # Saisir email
    email_input = driver.find_element(By.ID, "username")
    email_input.send_keys(LINKEDIN_EMAIL)

    # Saisir mot de passe
    password_input = driver.find_element(By.ID, "password")
    password_input.send_keys(LINKEDIN_PASSWORD)

    # Cliquer sur "Se connecter"
    driver.find_element(By.XPATH, "//button[@type='submit']").click()
    time.sleep(5)

    # Aller sur le profil
    driver.get(profile_url)
    time.sleep(5)

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


@app.get("/scrape")
def scrape(contactId: str = Query(...), linkedin: str = Query(...)):
    print(f"🔗 Scraping LinkedIn profile for contact ID: {contactId}")
    profile_data = scrape_linkedin_profile(linkedin)
    return {
        "contact_id": contactId,
        "linkedin_profile": linkedin,
        "scraped_data": profile_data
    }
