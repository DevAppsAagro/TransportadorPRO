#!/bin/bash
set -e

echo "Instalando dependências..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Coletando arquivos estáticos..."
mkdir -p staticfiles
python manage.py collectstatic --noinput

echo "Build concluído com sucesso!"
