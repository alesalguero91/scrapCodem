#!/usr/bin/env bash
set -o errexit

echo "🚀 Iniciando build para Render..."
echo "📦 Instalando dependencias del sistema..."

# Actualizar e instalar dependencias necesarias
apt-get update
apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
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
    libxtst6 \
    libasound2

# Descargar e instalar Chrome directamente
echo "🌐 Instalando Google Chrome..."
curl -o google-chrome-stable.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
apt-get install -y ./google-chrome-stable.deb
rm -f google-chrome-stable.deb

# Verificar instalación
echo "✅ Chrome instalado: $(google-chrome --version)"

# Limpiar cache para ahorrar espacio
apt-get clean
rm -rf /var/lib/apt/lists/*

# Instalar dependencias Python
echo "🐍 Instalando dependencias Python..."
pip install --upgrade pip
pip install -r requirements.txt

# Configurar static files (si es necesario)
python manage.py collectstatic --no-input

echo "🎉 Build completado exitosamente!"