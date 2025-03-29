"""
Script simples para testar o upload para o bucket 'logos' existente no Supabase
"""
import os
import base64
import uuid
from dotenv import load_dotenv
from supabase import create_client

# Carregar variáveis de ambiente
load_dotenv()

# Obter credenciais do Supabase
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')
supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')
bucket_name = 'logos'

print(f"URL: {supabase_url}")
print(f"Bucket: {bucket_name}")

# Criar um pequeno arquivo de teste
file_ext = ".png"
file_name = f"test_logo_{uuid.uuid4()}{file_ext}"

# Imagem de teste em base64 (um pequeno quadrado colorido)
base64_image = "iVBORw0KGgoAAAANSUhEUgAAABQAAAAUCAYAAACNiR0NAAAABGdBTUEAALGPC/xhBQAAAAlwSFlzAAAOwgAADsIBFShKgAAAABl0RVh0U29mdHdhcmUAcGFpbnQubmV0IDQuMC4yMfEgaZUAAABkSURBVDhPY/j//z9VMZjBQG1DwQYCMdUMhRkGxFQzFGwYzFCqGQo2DIapZijYMBimqqFgA4GYaoaCDQNiqhkKNgyGqWYo2DAYppqhYMNgmGqGgg0DYqoZCjYMhqlmKKUYqAYAIYFY5DzF7IQAAAAASUVORK5CYII="

# Decodifica a imagem base64
image_data = base64.b64decode(base64_image)

print(f"\nTentando upload com chave normal...")
try:
    # Inicializar cliente Supabase com chave normal
    supabase = create_client(supabase_url, supabase_key)
    
    # Fazer upload do arquivo
    result = supabase.storage.from_(bucket_name).upload(
        path=file_name,
        file=image_data,
        file_options={"contentType": "image/png"}
    )
    
    if result:
        # Gerar URL pública
        public_url = supabase.storage.from_(bucket_name).get_public_url(file_name)
        print(f"[OK] Upload bem-sucedido!")
        print(f"URL pública: {public_url}")
    else:
        print("[ERRO] Falha no upload com chave normal")
except Exception as e:
    print(f"[ERRO] Falha no upload com chave normal: {str(e)}")

print(f"\nTentando upload com chave de serviço...")
try:
    # Inicializar cliente Supabase com chave de serviço
    supabase = create_client(supabase_url, supabase_service_key)
    
    # Criar um novo nome de arquivo para o segundo teste
    file_name_service = f"test_logo_service_{uuid.uuid4()}{file_ext}"
    
    # Fazer upload do arquivo
    result = supabase.storage.from_(bucket_name).upload(
        path=file_name_service,
        file=image_data,
        file_options={"contentType": "image/png"}
    )
    
    if result:
        # Gerar URL pública
        public_url = supabase.storage.from_(bucket_name).get_public_url(file_name_service)
        print(f"[OK] Upload bem-sucedido com chave de serviço!")
        print(f"URL pública: {public_url}")
    else:
        print("[ERRO] Falha no upload com chave de serviço")
except Exception as e:
    print(f"[ERRO] Falha no upload com chave de serviço: {str(e)}")
