FROM python:3.11-slim

# Installe Chrome et dépendances nécessaires
RUN apt-get update && apt-get install -y wget gnupg unzip \
    && wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update && apt-get install -y google-chrome-stable \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Crée le dossier d'app
WORKDIR /app
COPY . /app

# Installe les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Expose le port FastAPI (si tu veux tester avec /scrape)
EXPOSE 8080

# Lance le script principal
CMD ["python", "main.py"]
