"""
Script para testar o upload para o Supabase usando a chave de serviço (service_role)
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

def test_service_role_upload():
    """Testa o upload para o Supabase usando a chave de serviço"""
    print("\n===== TESTE DE UPLOAD COM CHAVE DE SERVIÇO =====")
    
    # Obter credenciais do Supabase
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')
    bucket_name = os.getenv('SUPABASE_STORAGE_BUCKET', 'logos')
    
    if not supabase_url:
        print("[ERRO] URL do Supabase não encontrada no arquivo .env")
        return
    
    if not supabase_service_key:
        print("[ERRO] Chave de serviço do Supabase não encontrada no arquivo .env")
        print("Adicione a variável SUPABASE_SERVICE_KEY ao arquivo .env")
        print("Você pode obter esta chave no painel do Supabase em Settings > API")
        return
    
    print(f"URL: {supabase_url}")
    print(f"Key normal: {'*' * 8 + supabase_key[-4:] if supabase_key else 'Não configurada'}")
    print(f"Key de serviço: {'*' * 8 + supabase_service_key[-4:] if supabase_service_key else 'Não configurada'}")
    print(f"Bucket: {bucket_name}")
    print("=======================================\n")
    
    try:
        # Inicializar cliente Supabase com a chave de serviço
        supabase = create_client(supabase_url, supabase_service_key)
        
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
                
                # Configurar políticas de acesso
                print("Configurando políticas de acesso...")
                
                # Nota: A configuração de políticas via API não está disponível na biblioteca Python
                # É necessário configurar as políticas manualmente no painel do Supabase
                print("[AVISO] Configure as políticas de acesso manualmente no painel do Supabase")
                print("Consulte o arquivo guia_configuracao_supabase.md para instruções")
                
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
            
            # Verificar se o arquivo é acessível publicamente
            print("\nVerificando se o arquivo é acessível publicamente...")
            import requests
            response = requests.head(public_url)
            if response.status_code == 200:
                print(f"[OK] Arquivo acessível publicamente (status code: {response.status_code})")
            else:
                print(f"[AVISO] Arquivo pode não ser acessível publicamente (status code: {response.status_code})")
                print("Verifique se o bucket está configurado como público no painel do Supabase")
        else:
            print("[ERRO] Falha no upload: resposta inválida")
    
    except Exception as e:
        print(f"[ERRO] Falha ao fazer upload: {str(e)}")
        print("\nVerifique:")
        print("1. Se você está usando a chave de serviço (service_role) correta")
        print("2. Se o bucket 'logos' existe no Supabase")
        print("3. Se as políticas de acesso estão configuradas corretamente")

if __name__ == "__main__":
    test_service_role_upload()
