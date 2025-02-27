"""
Arquivo específico para deploy no Vercel
"""
import os
from transportador_pro.wsgi import application

# Adiciona suporte para Vercel
app = application
