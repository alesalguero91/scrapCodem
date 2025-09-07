#!/usr/bin/env bash
set -o errexit

echo "🚀 Iniciando build para Render..."

# Instalar Chromium (más confiable que Chrome en Render)
apt-get update
apt-get install -y --no-install-recommends \
    chromium \
    chromium-common \
    chromium-driver \
    libxss1 \
    libnss3 \
    libasound2 \
    libx11-6 \
    libxcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1

# Limpiar cache
apt-get clean
rm -rf /var/lib/apt/lists/*

# Instalar dependencias Python
pip install --upgrade pip
pip install -r requirements.txt

# Configurar static files
python manage.py collectstatic --no-input

echo "✅ Build completado! Chromium instalado correctamente."