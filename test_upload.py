"""
Script para testar o upload para o Supabase usando a implementação atualizada
"""
import os
import sys
import base64
import logging
import django
from dotenv import load_dotenv

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'transportadorpro.settings')
django.setup()

# Importar após configurar o Django
from core.utils.supabase_config import upload_file, get_supabase_client

# Configurar logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

def test_upload():
    """Testa o upload para o Supabase"""
    print("\n===== TESTE DE UPLOAD PARA SUPABASE =====")
    
    # Verificar configurações do Supabase
    from django.conf import settings
    print(f"URL: {settings.SUPABASE_URL}")
    print(f"Key: {'*' * 8 + settings.SUPABASE_KEY[-4:] if hasattr(settings, 'SUPABASE_KEY') else 'Não configurada'}")
    print(f"Bucket: {getattr(settings, 'SUPABASE_STORAGE_BUCKET', 'logos')}")
    print("=======================================\n")
    
    # Criar um pequeno arquivo de teste
    test_file_name = f"test_logo_{os.urandom(4).hex()}.png"
    
    # Imagem de teste em base64 (um pequeno quadrado colorido)
    base64_image = "iVBORw0KGgoAAAANSUhEUgAAABQAAAAUCAYAAACNiR0NAAAABGdBTUEAALGPC/xhBQAAAAlwSFlzAAAOwgAADsIBFShKgAAAABl0RVh0U29mdHdhcmUAcGFpbnQubmV0IDQuMC4yMfEgaZUAAABkSURBVDhPY/j//z9VMZjBQG1DwQYCMdUMhRkGxFQzFGwYzFCqGQo2DIapZijYMBimqqFgA4GYaoaCDQNiqhkKNgyGqWYo2DAYppqhYMNgmGqGgg0DYqoZCjYMhqlmKKUYqAYAIYFY5DzF7IQAAAAASUVORK5CYII="
    
    # Decodifica a imagem base64
    image_data = base64.b64decode(base64_image)
    
    print(f"Tentando fazer upload do arquivo '{test_file_name}'...")
    
    # Verificar se o bucket existe
    try:
        supabase = get_supabase_client()
        bucket_name = getattr(settings, 'SUPABASE_STORAGE_BUCKET', 'logos')
        buckets = supabase.storage.list_buckets()
        bucket_exists = any(bucket.name == bucket_name for bucket in buckets)
        
        if bucket_exists:
            print(f"[OK] Bucket '{bucket_name}' encontrado")
        else:
            print(f"[AVISO] Bucket '{bucket_name}' não encontrado. Tentando criar...")
            supabase.storage.create_bucket(bucket_name, {'public': True})
            print(f"[OK] Bucket '{bucket_name}' criado com sucesso")
    except Exception as e:
        print(f"[ERRO] Falha ao verificar/criar bucket: {str(e)}")
        print("Você precisa criar o bucket manualmente no painel do Supabase")
    
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
        print("   - Leitura pública para todos")
        print("   - Escrita/atualização/exclusão apenas para usuários autenticados")

if __name__ == "__main__":
    test_upload()
