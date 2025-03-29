"""
Script para configurar o bucket do Supabase com as políticas corretas
Este script deve ser executado uma vez para configurar o bucket 'logos'
com as políticas de acesso adequadas.
"""
import os
import sys
import json
import logging
import requests
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

# Configurações do Supabase
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
BUCKET_NAME = os.getenv('SUPABASE_STORAGE_BUCKET', 'logos')

def setup_bucket():
    """Configura o bucket com as políticas corretas"""
    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.error("Supabase URL ou Key não configurados")
        print("\nERRO: Configure as variáveis SUPABASE_URL e SUPABASE_KEY no arquivo .env")
        sys.exit(1)
    
    try:
        # Conectar ao Supabase
        print(f"\nConfigurando políticas para o bucket '{BUCKET_NAME}' no Supabase: {SUPABASE_URL}")
        
        # Configurar headers para as requisições
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json"
        }
        
        # Verificar se o bucket existe
        print(f"\nVerificando se o bucket '{BUCKET_NAME}' existe...")
        buckets_url = f"{SUPABASE_URL}/storage/v1/bucket"
        
        response = requests.get(buckets_url, headers=headers)
        buckets = response.json()
        
        bucket_exists = any(bucket.get('name') == BUCKET_NAME for bucket in buckets)
        
        if not bucket_exists:
            print(f"Bucket '{BUCKET_NAME}' não encontrado. Tentando criar...")
            
            # Criar o bucket
            bucket_data = {
                "id": BUCKET_NAME,
                "name": BUCKET_NAME,
                "public": True
            }
            
            response = requests.post(buckets_url, headers=headers, json=bucket_data)
            
            if response.status_code in [200, 201]:
                print(f"[OK] Bucket '{BUCKET_NAME}' criado com sucesso!")
            else:
                print(f"[ERRO] Falha ao criar bucket: {response.status_code} - {response.text}")
                print("\nTente criar o bucket manualmente no painel do Supabase:")
                print("1. Acesse https://app.supabase.com")
                print("2. Selecione seu projeto")
                print("3. Vá para Storage > Buckets")
                print(f"4. Clique em 'New Bucket' e crie um bucket chamado '{BUCKET_NAME}'")
                print("5. Marque a opção 'Public bucket' para torná-lo público")
        else:
            print(f"[OK] Bucket '{BUCKET_NAME}' já existe!")
        
        # Configurar políticas de acesso
        print("\nConfigurando políticas de acesso...")
        
        # URL para políticas
        policies_url = f"{SUPABASE_URL}/storage/v1/policies"
        
        # 1. Política para leitura pública
        print("\nConfigurando política de leitura pública...")
        read_policy = {
            "name": f"allow_public_read_{BUCKET_NAME}",
            "definition": {
                "role": "anon",
                "bucket_id": BUCKET_NAME,
                "operation": "SELECT",
                "check": "true"
            }
        }
        
        response = requests.post(policies_url, headers=headers, json=read_policy)
        
        if response.status_code in [200, 201, 409]:  # 409 = Conflict (já existe)
            print("[OK] Política de leitura pública configurada!")
        else:
            print(f"[AVISO] Falha ao configurar política de leitura: {response.status_code} - {response.text}")
        
        # 2. Política para escrita autenticada
        print("\nConfigurando política de escrita para usuários autenticados...")
        write_policy = {
            "name": f"allow_auth_write_{BUCKET_NAME}",
            "definition": {
                "role": "authenticated",
                "bucket_id": BUCKET_NAME,
                "operation": "INSERT",
                "check": f"((bucket_id = '{BUCKET_NAME}'::text) AND (auth.role() = 'authenticated'::text))"
            }
        }
        
        response = requests.post(policies_url, headers=headers, json=write_policy)
        
        if response.status_code in [200, 201, 409]:  # 409 = Conflict (já existe)
            print("[OK] Política de escrita para usuários autenticados configurada!")
        else:
            print(f"[AVISO] Falha ao configurar política de escrita: {response.status_code} - {response.text}")
        
        # 3. Política para atualização autenticada
        print("\nConfigurando política de atualização para usuários autenticados...")
        update_policy = {
            "name": f"allow_auth_update_{BUCKET_NAME}",
            "definition": {
                "role": "authenticated",
                "bucket_id": BUCKET_NAME,
                "operation": "UPDATE",
                "check": f"((bucket_id = '{BUCKET_NAME}'::text) AND (auth.role() = 'authenticated'::text))"
            }
        }
        
        response = requests.post(policies_url, headers=headers, json=update_policy)
        
        if response.status_code in [200, 201, 409]:
            print("[OK] Política de atualização para usuários autenticados configurada!")
        else:
            print(f"[AVISO] Falha ao configurar política de atualização: {response.status_code} - {response.text}")
        
        # 4. Política para exclusão autenticada
        print("\nConfigurando política de exclusão para usuários autenticados...")
        delete_policy = {
            "name": f"allow_auth_delete_{BUCKET_NAME}",
            "definition": {
                "role": "authenticated",
                "bucket_id": BUCKET_NAME,
                "operation": "DELETE",
                "check": f"((bucket_id = '{BUCKET_NAME}'::text) AND (auth.role() = 'authenticated'::text))"
            }
        }
        
        response = requests.post(policies_url, headers=headers, json=delete_policy)
        
        if response.status_code in [200, 201, 409]:
            print("[OK] Política de exclusão para usuários autenticados configurada!")
        else:
            print(f"[AVISO] Falha ao configurar política de exclusão: {response.status_code} - {response.text}")
        
        print("\n===== CONFIGURAÇÃO CONCLUÍDA =====")
        print(f"Bucket: {BUCKET_NAME}")
        print("Políticas configuradas:")
        print("- Leitura: Pública (qualquer pessoa pode ler)")
        print("- Escrita/Atualização/Exclusão: Apenas usuários autenticados")
        print("====================================")
        
        print("\nAgora você pode testar o upload de arquivos usando:")
        print("python core/utils/test_direct_upload.py")
        
    except Exception as e:
        print(f"\n[ERRO] Erro durante a configuração: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    setup_bucket()
