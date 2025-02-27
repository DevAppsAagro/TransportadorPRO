#!/bin/bash

# Instala as dependências do projeto
python3 -m pip install -r requirements.txt

# Coleta os arquivos estáticos
python3 manage.py collectstatic --noinput

# Executa as migrações (opcional, dependendo da configuração)
# python3 manage.py migrate
