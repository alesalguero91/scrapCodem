#!/usr/bin/env bash
set -o errexit

echo "🚀 Iniciando build optimizado para Render..."

# Instalar Chrome y dependencias del sistema
echo "📦 Instalando Chrome y dependencias..."
apt-get update
apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    libxss1 \
    libappindicator1 \
    libindicator7 \
    fonts-liberation \
    libnss3 \
    libnspr4 \
    libdbus-1-3 \
    libx11-6 \
    libxcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libxss1 \
    libxtst6 \
    libasound2

# Instalar Chrome
echo "🌐 Instalando Google Chrome..."
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list
apt-get update
apt-get install -y google-chrome-stable

# Limpiar cache para reducir tamaño
echo "🧹 Limpiando cache..."
apt-get clean
rm -rf /var/lib/apt/lists/*

# Instalar dependencias de Python
echo "🐍 Instalando dependencias Python..."
pip install --upgrade pip
pip install --no-cache-dir -r requirements.txt

# Configuración de Django
echo "⚙️ Configurando Django..."
python manage.py collectstatic --no-input --clear
python manage.py migrate --no-input

echo "✅ Build completado exitosamente!"