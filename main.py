import time
import json
import os
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
COOKIE_FILE = "li_at_cookie.json"  # fichier pour stocker le cookie

# ---------------------- UTILITAIRES COOKIE ----------------------
def save_cookie(li_at_value: str):
    with open(COOKIE_FILE, "w") as f:
        json.dump({"li_at": li_at_value}, f)

def load_cookie() -> str:
    if os.path.exists(COOKIE_FILE):
        with open(COOKIE_FILE, "r") as f:
            data = json.load(f)
            return data.get("li_at")
    return None

# ---------------------- SCRAPING FUNCTION ----------------------
def scrape_linkedin_profile(profile_url: str) -> Dict:
    li_at_cookie = load_cookie()
    
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
    
    # ---------------------- Connexion avec cookie ----------------------
    if li_at_cookie:
        try:
            driver.get("https://www.linkedin.com/")
            driver.add_cookie({"name": "li_at", "value": li_at_cookie, "domain": ".linkedin.com"})
            driver.get(profile_url)
            time.sleep(4)
            if "login" in driver.current_url:
                print("Cookie expiré, suppression et tentative login...")
                li_at_cookie = None  # pour forcer login
        except Exception as e:
            print("Erreur avec le cookie :", e)
            li_at_cookie = None

    # ---------------------- Connexion username/password si cookie invalide ----------------------
    if not li_at_cookie:
        driver.get("https://www.linkedin.com/login")
        time.sleep(2)
        try:
            username_field = driver.find_element(By.ID, "username")
            password_field = driver.find_element(By.ID, "password")
            username_field.send_keys(LINKEDIN_USERNAME)
            password_field.send_keys(LINKEDIN_PASSWORD)
            driver.find_element(By.XPATH, "//button[@type='submit']").click()
            time.sleep(5)

            # Vérification du login
            if "feed" not in driver.current_url:
                raise Exception("Checkpoint ou 2FA détecté, login automatique impossible")

            # Récupération du cookie li_at après login réussi
            for cookie in driver.get_cookies():
                if cookie['name'] == "li_at":
                    save_cookie(cookie['value'])
                    break

        except Exception as e:
            driver.quit()
            raise Exception(f"Login LinkedIn échoué : {e}")

        # Aller sur le profil après login
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

# ---------------------- ENDPOINT POUR RAFRAÎCHIR COOKIE ----------------------
@app.post("/refresh-cookie")
def refresh_cookie():
    """
    Endpoint pour régénérer le cookie li_at via login interactif si nécessaire.
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless=false")  # Mode interactif pour login manuel si 2FA
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    driver = webdriver.Chrome(options=chrome_options)
    driver.get("https://www.linkedin.com/login")
    time.sleep(2)
    # Ici l'utilisateur peut entrer manuellement username/password et 2FA si nécessaire
    input("Connectez-vous manuellement, puis appuyez sur Entrée...")
    # Sauvegarde du cookie li_at
    for cookie in driver.get_cookies():
        if cookie['name'] == "li_at":
            save_cookie(cookie['value'])
            break
    driver.quit()
    return {"status": "Cookie rafraîchi avec succès"}
