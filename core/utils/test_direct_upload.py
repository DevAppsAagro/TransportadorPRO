"""
Script para testar o upload direto para o Supabase usando a API REST
"""
import os
import sys
import base64
import logging
from dotenv import load_dotenv

# Adicionar o diretório raiz ao path para permitir importações relativas
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from core.utils.supabase_config import upload_file

# Configurar logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

def test_direct_upload():
    """Testa o upload direto para o Supabase"""
    print("\n===== TESTE DE UPLOAD DIRETO PARA SUPABASE =====")
    print(f"URL: {os.getenv('SUPABASE_URL')}")
    print(f"Key: {'*' * 8 + os.getenv('SUPABASE_KEY')[-4:] if os.getenv('SUPABASE_KEY') else 'Não configurada'}")
    print(f"Bucket: {os.getenv('SUPABASE_STORAGE_BUCKET', 'logos')}")
    print("===============================================\n")
    
    # Criar um pequeno arquivo de teste
    test_file_name = f"test_logo_direct_{os.urandom(4).hex()}.png"
    
    # Imagem de teste em base64 (um pequeno quadrado colorido)
    base64_image = "iVBORw0KGgoAAAANSUhEUgAAABQAAAAUCAYAAACNiR0NAAAABGdBTUEAALGPC/xhBQAAAAlwSFlzAAAOwgAADsIBFShKgAAAABl0RVh0U29mdHdhcmUAcGFpbnQubmV0IDQuMC4yMfEgaZUAAABkSURBVDhPY/j//z9VMZjBQG1DwQYCMdUMhRkGxFQzFGwYzFCqGQo2DIapZijYMBimqqFgA4GYaoaCDQNiqhkKNgyGqWYo2DAYppqhYMNgmGqGgg0DYqoZCjYMhqlmKKUYqAYAIYFY5DzF7IQAAAAASUVORK5CYII="
    
    # Decodifica a imagem base64
    image_data = base64.b64decode(base64_image)
    
    print(f"Tentando fazer upload do arquivo '{test_file_name}'...")
    
    # Fazer upload usando a função upload_file
    file_url = upload_file(
        file_data=image_data,
        file_name=test_file_name,
        content_type="image/png"
    )
    
    if file_url:
        print(f"[OK] Upload bem-sucedido!")
        print(f"URL pública: {file_url}")
        print("\nTeste o acesso à URL no navegador para confirmar que o arquivo está acessível.")
    else:
        print("[ERRO] Falha no upload.")
        print("\nVerifique:")
        print("1. Se o bucket 'logos' existe no Supabase")
        print("2. Se você está usando a chave de API correta")
        print("3. Se as políticas de acesso estão configuradas corretamente")

if __name__ == "__main__":
    test_direct_upload()
