# ---- Étape 1 : image Python de base ----
FROM python:3.10-slim

# ---- Étape 2 : installation de Chrome et dépendances ----
RUN apt-get update && apt-get install -y \
    wget gnupg unzip curl fonts-liberation libnss3 libxss1 libasound2 libatk-bridge2.0-0 libgtk-3-0 \
    && mkdir -p /usr/share/keyrings \
    && wget -q -O- https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-linux-signing-keyring.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-linux-signing-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# ---- Étape 3 : installation des dépendances Python ----
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- Étape 4 : copie du code ----
COPY . /app
WORKDIR /app

# ---- Étape 5 : exposition du port ----
EXPOSE 8000

# ---- Étape 6 : commande de lancement ----
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
