import time
import chromedriver_autoinstaller
chromedriver_autoinstaller.install()

from typing import Dict
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------- CONFIG ----------------------
LINKEDIN_USERNAME = "jallouli.manel.44@gmail.com"
LINKEDIN_PASSWORD = "Manel_linkedin@@123"
LI_AT_COOKIE = None  # sera mis à jour automatiquement

# ---------------------- LOGIN AUTOMATIQUE ----------------------
def get_li_at(interactive=False) -> str:
    """Récupère automatiquement le cookie li_at. 
    Si interactive=True, le navigateur est visible pour gérer 2FA ou captcha."""
    global LI_AT_COOKIE
    chrome_options = Options()
    if not interactive:
        chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-logging")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")

    driver = webdriver.Chrome(options=chrome_options)
    driver.get("https://www.linkedin.com/login")
    time.sleep(2)

    try:
        # Login avec username/password
        driver.find_element(By.ID, "username").send_keys(LINKEDIN_USERNAME)
        driver.find_element(By.ID, "password").send_keys(LINKEDIN_PASSWORD)
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        time.sleep(5)

        # Vérification de succès
        if "feed" not in driver.current_url:
            if interactive:
                print("⚠️ Checkpoint détecté, résolvez manuellement dans le navigateur...")
                input("Appuyez sur Entrée après validation...")
            else:
                raise Exception("Checkpoint ou 2FA détecté, login headless impossible")
        
        # Récupérer le cookie li_at
        li_at_cookie = driver.get_cookie("li_at")["value"]
        LI_AT_COOKIE = li_at_cookie
        print("✅ Cookie li_at récupéré avec succès")
        driver.quit()
        return li_at_cookie

    except Exception as e:
        driver.quit()
        raise Exception(f"Impossible de récupérer li_at : {e}")

# ---------------------- SCRAPING ----------------------
def scrape_linkedin_profile(profile_url: str) -> Dict:
    global LI_AT_COOKIE
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-logging")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")

    driver = webdriver.Chrome(options=chrome_options)
    driver.get("https://www.linkedin.com/")
    time.sleep(2)

    # ---------------------- Auth via cookie ----------------------
    if LI_AT_COOKIE is None:
        LI_AT_COOKIE = get_li_at(interactive=False)

    driver.add_cookie({
        "name": "li_at",
        "value": LI_AT_COOKIE,
        "domain": ".linkedin.com"
    })
    driver.get(profile_url)
    time.sleep(4)

    # Scroll jusqu’en bas
    last_height = driver.execute_script("return document.body.scrollHeight")
    for _ in range(30):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    # Extraction des sections
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
    try:
        profile_data = scrape_linkedin_profile(linkedin)
    except Exception as e:
        return {"error": str(e)}
    return {
        "contact_id": contactId,
        "linkedin_profile": linkedin,
        "scraped_data": profile_data
    }

@app.post("/refresh-cookie")
def refresh_cookie(interactive: bool = Query(False)):
    """Renouvelle le cookie li_at automatiquement ou en mode interactif"""
    try:
        new_li_at = get_li_at(interactive=interactive)
        return {"li_at": new_li_at}
    except Exception as e:
        return {"error": str(e)}
