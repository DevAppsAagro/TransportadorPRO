#!/bin/bash

# Instala as dependências do projeto
pip install -r requirements.txt

# Coleta os arquivos estáticos
python manage.py collectstatic --noinput

# Executa as migrações (opcional, dependendo da configuração)
# python manage.py migrate
