"""
Script para testar o upload de arquivos para o Supabase usando a nova implementação
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

# Agora podemos importar a função
from core.utils.supabase_config import upload_file, remove_file

# Carregar variáveis de ambiente
load_dotenv()

print("===== TESTE DE UPLOAD COM NOVA IMPLEMENTAÇÃO =====")

# Criar um pequeno arquivo de teste
file_ext = ".png"
file_name = f"test_logo{file_ext}"

# Imagem de teste em base64 (um pequeno quadrado colorido)
base64_image = "iVBORw0KGgoAAAANSUhEUgAAABQAAAAUCAYAAACNiR0NAAAABGdBTUEAALGPC/xhBQAAAAlwSFlzAAAOwgAADsIBFShKgAAAABl0RVh0U29mdHdhcmUAcGFpbnQubmV0IDQuMC4yMfEgaZUAAABkSURBVDhPY/j//z9VMZjBQG1DwQYCMdUMhRkGxFQzFGwYzFCqGQo2DIapZijYMBimqqFgA4GYaoaCDQNiqhkKNgyGqWYo2DAYppqhYMNgmGqGgg0DYqoZCjYMhqlmKKUYqAYAIYFY5DzF7IQAAAAASUVORK5CYII="

# Decodifica a imagem base64
image_data = base64.b64decode(base64_image)

# Criar um objeto similar ao UploadedFile do Django
class MockUploadedFile:
    def __init__(self, name, content, content_type):
        self.name = name
        self._content = content
        self.content_type = content_type
        self._file = BytesIO(content)
    
    def read(self):
        return self._content

# Criar o objeto de arquivo
mock_file = MockUploadedFile(
    name=file_name,
    content=image_data,
    content_type="image/png"
)

print(f"Tentando upload do arquivo '{file_name}'...")

# Fazer upload do arquivo
public_url = upload_file(
    file_data=mock_file,
    file_name=file_name,
    content_type="image/png"
)

if public_url:
    print(f"[OK] Upload bem-sucedido!")
    print(f"URL pública: {public_url}")
    
    # Testar remoção do arquivo
    print("\nTentando remover o arquivo...")
    if remove_file(public_url):
        print("[OK] Arquivo removido com sucesso!")
    else:
        print("[ERRO] Falha ao remover o arquivo")
else:
    print("[ERRO] Falha no upload")

print("\n=======================================")
