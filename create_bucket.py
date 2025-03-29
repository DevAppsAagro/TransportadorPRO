"""
Script para criar o bucket 'logos' no Supabase
"""
import os
from dotenv import load_dotenv
from supabase import create_client

# Carregar variáveis de ambiente
load_dotenv()

# Obter credenciais do Supabase
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY')  # Usar a chave de serviço

if not supabase_url or not supabase_key:
    print("[ERRO] Credenciais do Supabase não encontradas")
    exit(1)

print(f"URL: {supabase_url}")
print(f"Key: {'*' * 8 + supabase_key[-4:] if supabase_key else 'Não configurada'}")

# Inicializar cliente Supabase
supabase = create_client(supabase_url, supabase_key)

# Nome do bucket
bucket_name = 'logos'

# Verificar se o bucket já existe
buckets = supabase.storage.list_buckets()
bucket_exists = any(bucket.name == bucket_name for bucket in buckets)

if bucket_exists:
    print(f"\n[INFO] O bucket '{bucket_name}' já existe!")
else:
    # Criar o bucket
    print(f"\n[INFO] Tentando criar o bucket '{bucket_name}'...")
    try:
        # Formato correto para criar bucket
        result = supabase.storage.create_bucket(bucket_name, {'public': True})
        print(f"[OK] Bucket '{bucket_name}' criado com sucesso!")
    except Exception as e:
        print(f"[ERRO] Falha ao criar bucket: {str(e)}")
        print("\nTente criar o bucket manualmente no painel do Supabase:")
        print("1. Acesse https://app.supabase.com")
        print("2. Selecione seu projeto")
        print("3. Vá para Storage > Buckets")
        print("4. Clique em 'New Bucket' e crie um bucket chamado 'logos'")
        print("5. Marque a opção 'Public bucket' para torná-lo público")
