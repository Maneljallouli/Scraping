FROM python:3.11-slim
ENV DEBIAN_FRONTEND=noninteractive
# Installer les dépendances système nécessaires
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    curl \
    gnupg \
    ca-certificates \
    libglib2.0-0 \
    libnss3 \
    libfontconfig1 \
    libx11-6 \
    libxkbfile1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxrandr2 \
    libasound2 \
    libatk1.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libpango-1.0-0 \
    libxss1 \
    libxtst6 \
    && rm -rf /var/lib/apt/lists/*
# Installer Google Chrome stable
RUN wget -q -O /tmp/google-chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get update && apt-get install -y /tmp/google-chrome.deb unzip curl \
    && rm /tmp/google-chrome.deb
# Installer la dernière version stable de Chromedriver
RUN CHROMEDRIVER_VERSION=$(curl -sS https://chromedriver.storage.googleapis.com/LATEST_RELEASE) \
    && wget -O /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip" \
    && unzip /tmp/chromedriver.zip -d /usr/local/bin/ \
    && chmod +x /usr/local/bin/chromedriver \
    && rm /tmp/chromedriver.zip
# Copier les fichiers dans le conteneur
WORKDIR /app
COPY requirements.txt /app/requirements.txt
COPY . /app
# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt
# Exposer le port FastAPI
EXPOSE 8000
# Démarrer FastAPI avec uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
