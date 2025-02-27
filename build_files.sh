#!/bin/bash
set -e

echo "Verificando ambiente..."
which python || echo "Python não encontrado"
which pip || echo "Pip não encontrado"

echo "Instalando dependências..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo "Coletando arquivos estáticos..."
mkdir -p staticfiles
python manage.py collectstatic --noinput

echo "Build concluído com sucesso!"
