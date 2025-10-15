import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# tes fonctions de scraping ici (create_driver, linkedin_login, etc.)

def main():
    from apify_client import ApifyClient
    import json
    import os

    # récupérer l'input depuis Apify
    input_data = os.environ.get("APIFY_INPUT", "{}")
    input_json = json.loads(input_data)
    linkedin_url = input_json.get("linkedin", "")

    result = scrape_linkedin_profile(linkedin_url)
    print(json.dumps(result))

if __name__ == "__main__":
    main()
