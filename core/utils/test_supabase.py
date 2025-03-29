"""
Script para testar a conexão com o Supabase e o upload de arquivos
Para usar:
1. Configure suas chaves do Supabase no arquivo .env ou diretamente neste script
2. Execute: python test_supabase.py
"""
import os
import sys
import logging
from supabase import create_client, Client
from dotenv import load_dotenv
import base64

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

def get_supabase_client() -> Client:
    """Cria e retorna um cliente Supabase"""
    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.error("Supabase URL ou Key não configurados")
        print("\nERRO: Configure as variáveis SUPABASE_URL e SUPABASE_KEY no arquivo .env ou diretamente neste script")
        sys.exit(1)
        
    try:
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        return client
    except Exception as e:
        logger.error(f"Erro ao criar cliente Supabase: {str(e)}")
        raise

def test_connection():
    """Testa a conexão com o Supabase"""
    try:
        supabase = get_supabase_client()
        print("\n[OK] Conexão com Supabase estabelecida com sucesso!")
        return True, supabase
    except Exception as e:
        print(f"\n[ERRO] Erro ao conectar com Supabase: {str(e)}")
        return False, None

def test_file_upload(supabase):
    """Testa o upload de um arquivo de teste para o Supabase"""
    try:
        # Cria um pequeno arquivo de teste (uma imagem base64 simples)
        test_file_name = "test_logo.png"
        # Imagem de teste em base64 (um pequeno quadrado colorido)
        base64_image = "iVBORw0KGgoAAAANSUhEUgAAABQAAAAUCAYAAACNiR0NAAAABGdBTUEAALGPC/xhBQAAAAlwSFlzAAAOwgAADsIBFShKgAAAABl0RVh0U29mdHdhcmUAcGFpbnQubmV0IDQuMC4yMfEgaZUAAABkSURBVDhPY/j//z9VMZjBQG1DwQYCMdUMhRkGxFQzFGwYzFCqGQo2DIapZijYMBimqqFgA4GYaoaCDQNiqhkKNgyGqWYo2DAYppqhYMNgmGqGgg0DYqoZCjYMhqlmKKUYqAYAIYFY5DzF7IQAAAAASUVORK5CYII="
        
        # Decodifica a imagem base64
        image_data = base64.b64decode(base64_image)
        
        print(f"\nTentando fazer upload do arquivo de teste '{test_file_name}'...")
        
        # Faz o upload do arquivo - corrigindo o formato dos parâmetros
        response = supabase.storage.from_(BUCKET_NAME).upload(
            path=test_file_name,
            file=image_data,
            file_options={"contentType": "image/png"}
        )
        
        if response and hasattr(response, 'data'):
            # Gera a URL pública
            file_url = supabase.storage.from_(BUCKET_NAME).get_public_url(test_file_name)
            print(f"[OK] Upload concluído com sucesso!")
            print(f"URL pública: {file_url}")
            return True
        else:
            print("[ERRO] Falha no upload: resposta inválida")
            if response:
                print(f"Resposta: {response}")
            return False
            
    except Exception as e:
        print(f"[ERRO] Erro ao fazer upload do arquivo: {str(e)}")
        return False

def main():
    """Função principal para testar todas as funcionalidades"""
    print("\n===== TESTE DE CONFIGURAÇÃO DO SUPABASE =====")
    print(f"URL: {SUPABASE_URL}")
    print(f"Key: {'*' * 8 + SUPABASE_KEY[-4:] if SUPABASE_KEY else 'Não configurada'}")
    print(f"Bucket: {BUCKET_NAME}")
    print("============================================\n")
    
    # Testa a conexão
    success, supabase = test_connection()
    if not success:
        return
    
    # Testa o upload de arquivo
    upload_success = test_file_upload(supabase)
    
    print("\n===== RESUMO DOS TESTES =====")
    print("[OK] Conexão com Supabase: OK")
    if upload_success:
        print("[OK] Upload de arquivo: OK")
        print("============================\n")
        print("Sua configuração do Supabase está funcionando corretamente!")
        print("Você pode usar o sistema de upload de logos com segurança.")
    else:
        print("[ERRO] Upload de arquivo: FALHA")
        print("============================\n")
        print("Verifique se o bucket 'logos' existe e se as policies estão configuradas corretamente.")
        print("Lembre-se de que você precisa criar o bucket manualmente no painel do Supabase.")

if __name__ == "__main__":
    main()
