#!/bin/bash
echo "Iniciando deploy no Vercel..."

# Instalar dependências
pip install -r requirements.txt

# Coletar arquivos estáticos
python manage.py collectstatic --noinput

echo "Deploy concluído!"
