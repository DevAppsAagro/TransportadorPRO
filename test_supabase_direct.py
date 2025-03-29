"""
Script para testar o upload para o Supabase diretamente, sem depender do Django
"""
import os
import base64
import logging
import uuid
from dotenv import load_dotenv
from supabase import create_client, Client

# Configurar logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

def test_direct_upload():
    """Testa o upload para o Supabase diretamente"""
    print("\n===== TESTE DE UPLOAD DIRETO PARA SUPABASE =====")
    
    # Obter credenciais do Supabase
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    bucket_name = os.getenv('SUPABASE_STORAGE_BUCKET', 'logos')
    
    if not supabase_url or not supabase_key:
        print("[ERRO] Credenciais do Supabase não encontradas no arquivo .env")
        print("Certifique-se de que as variáveis SUPABASE_URL e SUPABASE_KEY estão definidas")
        return
    
    print(f"URL: {supabase_url}")
    print(f"Key: {'*' * 8 + supabase_key[-4:] if supabase_key else 'Não configurada'}")
    print(f"Bucket: {bucket_name}")
    print("=======================================\n")
    
    try:
        # Inicializar cliente Supabase
        supabase = create_client(supabase_url, supabase_key)
        
        # Verificar se o bucket existe
        buckets = supabase.storage.list_buckets()
        bucket_exists = any(bucket.name == bucket_name for bucket in buckets)
        
        if bucket_exists:
            print(f"[OK] Bucket '{bucket_name}' encontrado")
        else:
            print(f"[AVISO] Bucket '{bucket_name}' não encontrado. Tentando criar...")
            try:
                supabase.storage.create_bucket(bucket_name, {'public': True})
                print(f"[OK] Bucket '{bucket_name}' criado com sucesso")
            except Exception as e:
                print(f"[ERRO] Falha ao criar bucket: {str(e)}")
                print("Você precisa criar o bucket manualmente no painel do Supabase")
        
        # Criar um pequeno arquivo de teste
        file_ext = ".png"
        file_name = f"company_logos/{uuid.uuid4()}{file_ext}"
        
        # Imagem de teste em base64 (um pequeno quadrado colorido)
        base64_image = "iVBORw0KGgoAAAANSUhEUgAAABQAAAAUCAYAAACNiR0NAAAABGdBTUEAALGPC/xhBQAAAAlwSFlzAAAOwgAADsIBFShKgAAAABl0RVh0U29mdHdhcmUAcGFpbnQubmV0IDQuMC4yMfEgaZUAAABkSURBVDhPY/j//z9VMZjBQG1DwQYCMdUMhRkGxFQzFGwYzFCqGQo2DIapZijYMBimqqFgA4GYaoaCDQNiqhkKNgyGqWYo2DAYppqhYMNgmGqGgg0DYqoZCjYMhqlmKKUYqAYAIYFY5DzF7IQAAAAASUVORK5CYII="
        
        # Decodifica a imagem base64
        image_data = base64.b64decode(base64_image)
        
        print(f"Tentando fazer upload do arquivo '{file_name}'...")
        
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
            print("\nTeste o acesso à URL no navegador para confirmar que o arquivo está acessível.")
        else:
            print("[ERRO] Falha no upload: resposta inválida")
    
    except Exception as e:
        print(f"[ERRO] Falha ao fazer upload: {str(e)}")
        print("\nVerifique:")
        print("1. Se o bucket 'logos' existe no Supabase")
        print("2. Se você está usando a chave de API correta")
        print("3. Se as políticas de acesso estão configuradas corretamente")
        print("   - Leitura pública para todos")
        print("   - Escrita/atualização/exclusão apenas para usuários autenticados")

if __name__ == "__main__":
    test_direct_upload()
