import time
import chromedriver_autoinstaller
from typing import Dict
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --------- STATIC CREDENTIALS ----------
LINKEDIN_USERNAME = "jallouli.manel.44@gmail.com"
LINKEDIN_PASSWORD = "Manel_linkedin@@123"
# --------------------------------------

chromedriver_autoinstaller.install()  # installe automatiquement le ChromeDriver compatible

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Route racine
@app.get("/")
@app.head("/")
def root():
    return {"status": "OK", "message": "Service is running"}

# Création du driver Chrome
def create_driver() -> webdriver.Chrome:
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-logging")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_argument("--remote-debugging-port=9222")
    chrome_options.add_argument("--no-zygote")
    chrome_options.add_argument("--single-process")
    chrome_options.add_argument("--disable-setuid-sandbox")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(60)
    return driver

# Login LinkedIn
def linkedin_login(driver: webdriver.Chrome, timeout: int = 25) -> bool:
    try:
        driver.get("https://www.linkedin.com/login")
    except (TimeoutException, WebDriverException):
        pass

    wait = WebDriverWait(driver, timeout)
    try:
        wait.until(EC.presence_of_element_located((By.ID, "username")))

        username_el = driver.find_element(By.ID, "username")
        password_el = driver.find_element(By.ID, "password")

        username_el.clear()
        username_el.send_keys(LINKEDIN_USERNAME)
        password_el.clear()
        password_el.send_keys(LINKEDIN_PASSWORD)

        submit = driver.find_element(By.XPATH, "//button[@type='submit']")
        submit.click()

        # Vérification login réussi
        try:
            wait.until(EC.url_contains("/feed"))
        except TimeoutException:
            time.sleep(3)
            if "login" in driver.current_url.lower():
                return False
        return True

    except Exception:
        return False

# Scroll jusqu'en bas
def scroll_to_end(driver, max_attempts=30, wait=1):
    last_height = driver.execute_script("return document.body.scrollHeight")
    for _ in range(max_attempts):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(wait)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

# Extraction des sections
def get_section_titles(driver, section_title_text):
    try:
        wait = WebDriverWait(driver, 6)
        wait.until(EC.presence_of_element_located((By.XPATH, f"//section[.//*[contains(text(), '{section_title_text}')]]")))
    except TimeoutException:
        pass

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
            except Exception:
                continue
        return results if results else [f"No content found in {section_title_text}"]
    except NoSuchElementException:
        return [f"{section_title_text} section not found"]
    except Exception:
        return [f"{section_title_text} section not found"]

# Fonction principale de scraping
def scrape_linkedin_profile(profile_url: str) -> Dict:
    driver = create_driver()
    try:
        logged = linkedin_login(driver, timeout=25)
        if not logged:
            driver.quit()
            return {
                "error": "login_failed",
                "message": "Unable to log in with provided credentials (MFA/captcha/blocked?)."
            }

        try:
            driver.get(profile_url)
        except (TimeoutException, WebDriverException):
            pass

        time.sleep(3)
        scroll_to_end(driver, max_attempts=25, wait=1)

        profile_data = {
            "about": get_section_titles(driver, "À propos"),
            "experience": get_section_titles(driver, "Expérience"),
            "education": get_section_titles(driver, "Formation"),
            "certifications": get_section_titles(driver, "Licences et certifications"),
            "skills": get_section_titles(driver, "Compétences"),
        }
        return profile_data

    finally:
        try:
            driver.quit()
        except Exception:
            pass

# Endpoint FastAPI
@app.get("/scrape")
def scrape(contactId: str = Query(...), linkedin: str = Query(...)):
    print(f"🔗 Scraping LinkedIn profile for contact ID: {contactId}")
    result = scrape_linkedin_profile(linkedin)
    return {
        "contact_id": contactId,
        "linkedin_profile": linkedin,
        "scraped_data": result
    }
