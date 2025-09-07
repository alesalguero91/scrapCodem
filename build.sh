#!/usr/bin/env bash
set -o errexit

echo "🚀 Iniciando build para Render..."

# Instalar dependencias del sistema
apt-get update
apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    libxss1 \
    libnss3 \
    libasound2

# Instalar dependencias Python
pip install --upgrade pip
pip install -r requirements.txt

# Configurar static files
python manage.py collectstatic --no-input

echo "✅ Build completado! WebDriver Manager manejará Chrome automáticamente."