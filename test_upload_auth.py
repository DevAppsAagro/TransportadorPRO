"""
Script para testar o upload de arquivos para o Supabase com autenticação
"""
import os
import sys
import base64
import uuid
from dotenv import load_dotenv
from io import BytesIO

# Adicionar o diretório raiz ao path para poder importar os módulos do projeto
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'transportador_pro.settings')

# Configurar Django
import django
django.setup()

# Importar bibliotecas Supabase
from supabase import create_client, Client

# Carregar variáveis de ambiente
load_dotenv()

print("===== TESTE DE UPLOAD COM AUTENTICAÇÃO =====")

# Obter credenciais do Supabase
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')
bucket_name = 'logos'

# Inicializar cliente Supabase
supabase = create_client(supabase_url, supabase_key)

# Dados de autenticação (substitua por um usuário válido do seu sistema)
email = "teste@exemplo.com"
password = "senha123"

# Tentar fazer login
try:
    print(f"Tentando autenticar com o email: {email}")
    response = supabase.auth.sign_in_with_password({"email": email, "password": password})
    session = response.session
    
    if not session:
        print("[ERRO] Falha na autenticação")
        # Tentar criar um usuário de teste
        print("Tentando criar um usuário de teste...")
        response = supabase.auth.sign_up({"email": email, "password": password})
        session = response.session
        
        if not session:
            print("[ERRO] Não foi possível criar um usuário de teste")
            sys.exit(1)
    
    print(f"[OK] Autenticado com sucesso!")
    
    # Obter token de acesso
    access_token = session.access_token
    print(f"Token de acesso: {access_token[:10]}...")
    
    # Criar um pequeno arquivo de teste
    file_ext = ".png"
    file_name = f"test_logo{file_ext}"
    
    # Imagem de teste em base64 (um pequeno quadrado colorido)
    base64_image = "iVBORw0KGgoAAAANSUhEUgAAABQAAAAUCAYAAACNiR0NAAAABGdBTUEAALGPC/xhBQAAAAlwSFlzAAAOwgAADsIBFShKgAAAABl0RVh0U29mdHdhcmUAcGFpbnQubmV0IDQuMC4yMfEgaZUAAABkSURBVDhPY/j//z9VMZjBQG1DwQYCMdUMhRkGxFQzFGwYzFCqGQo2DIapZijYMBimqqFgA4GYaoaCDQNiqhkKNgyGqWYo2DAYppqhYMNgmGqGgg0DYqoZCjYMhqlmKKUYqAYAIYFY5DzF7IQAAAAASUVORK5CYII="
    
    # Decodifica a imagem base64
    image_data = base64.b64decode(base64_image)
    
    # Criar caminho único para o arquivo
    unique_path = f"company_logos/{uuid.uuid4()}{file_ext}"
    
    print(f"Tentando upload do arquivo para {unique_path}...")
    
    # Fazer upload do arquivo com autenticação
    result = supabase.storage.from_(bucket_name).upload(
        path=unique_path,
        file=image_data,
        file_options={"contentType": "image/png"}
    )
    
    if result:
        # Gerar URL pública
        public_url = supabase.storage.from_(bucket_name).get_public_url(unique_path)
        print(f"[OK] Upload bem-sucedido!")
        print(f"URL pública: {public_url}")
        
        # Testar remoção do arquivo
        print("\nTentando remover o arquivo...")
        supabase.storage.from_(bucket_name).remove([unique_path])
        print("[OK] Arquivo removido com sucesso!")
    else:
        print("[ERRO] Falha no upload")
    
except Exception as e:
    print(f"[ERRO] {str(e)}")

print("\n=======================================")
