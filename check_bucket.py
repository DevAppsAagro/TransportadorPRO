"""
Script para verificar se o bucket 'logos' existe no Supabase
"""
import os
from dotenv import load_dotenv
from supabase import create_client

# Carregar variáveis de ambiente
load_dotenv()

# Obter credenciais do Supabase
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')

print(f"URL: {supabase_url}")
print(f"Key: {'*' * 8 + supabase_key[-4:] if supabase_key else 'Não configurada'}")

# Inicializar cliente Supabase
supabase = create_client(supabase_url, supabase_key)

# Listar buckets
print("\nListando buckets disponíveis:")
buckets = supabase.storage.list_buckets()
for bucket in buckets:
    print(f"- {bucket.name} (criado em: {bucket.created_at})")

# Verificar se o bucket 'logos' existe
bucket_name = 'logos'
bucket_exists = any(bucket.name == bucket_name for bucket in buckets)

if bucket_exists:
    print(f"\n[OK] O bucket '{bucket_name}' existe!")
    
    # Listar arquivos no bucket
    print(f"\nListando arquivos no bucket '{bucket_name}':")
    try:
        files = supabase.storage.from_(bucket_name).list()
        if files:
            for file in files:
                print(f"- {file['name']} ({file.get('metadata', {}).get('size', 'N/A')} bytes)")
        else:
            print("Nenhum arquivo encontrado.")
    except Exception as e:
        print(f"[ERRO] Falha ao listar arquivos: {str(e)}")
else:
    print(f"\n[AVISO] O bucket '{bucket_name}' não existe!")
    print("Você precisa criar o bucket manualmente no painel do Supabase.")
    print("Consulte o arquivo guia_configuracao_supabase.md para instruções.")
