#!/usr/bin/env bash
set -o errexit

echo "🚀 Iniciando build en Railway..."

# Instalar dependencias del sistema para Chrome
apt-get update
apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    libxss1 \
    libnss3 \
    libasound2

# Instalar Chrome
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list
apt-get update
apt-get install -y google-chrome-stable

# Instalar dependencias Python
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Build completado! Chrome instalado correctamente."