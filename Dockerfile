# Utilise une image Python officielle compatible avec Chrome
FROM python:3.10-slim

# Installer Chrome et les dépendances
RUN apt-get update && apt-get install -y \
    wget unzip curl gnupg \
    && wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Installer les dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier ton code
COPY . /app
WORKDIR /app

# Exposer le port pour FastAPI
EXPOSE 8000

# Lancer FastAPI (modifie le nom du fichier si besoin)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
