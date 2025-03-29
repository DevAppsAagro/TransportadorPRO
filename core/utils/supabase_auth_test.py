"""
Script para testar a autenticação e upload no Supabase
Para usar:
1. Configure suas chaves do Supabase no arquivo .env ou diretamente neste script
2. Adicione um e-mail e senha válidos para teste
3. Execute: python supabase_auth_test.py
"""
import os
import sys
import logging
from supabase import create_client, Client
from dotenv import load_dotenv
import base64
import json

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

# Credenciais de teste - SUBSTITUA COM CREDENCIAIS VÁLIDAS
TEST_EMAIL = "seu_email@exemplo.com"
TEST_PASSWORD = "sua_senha_segura"

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

def test_auth(supabase):
    """Testa a autenticação no Supabase"""
    try:
        print(f"\nTentando autenticar com o e-mail: {TEST_EMAIL}")
        
        # Tenta fazer login
        response = supabase.auth.sign_in_with_password({
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if response and hasattr(response, 'user') and response.user:
            print(f"[OK] Autenticação bem-sucedida!")
            print(f"Usuário: {response.user.email}")
            
            # Obtém o token de acesso
            access_token = response.session.access_token
            return True, access_token
        else:
            print("[ERRO] Falha na autenticação")
            print(f"Resposta: {response}")
            return False, None
            
    except Exception as e:
        print(f"[ERRO] Erro ao autenticar: {str(e)}")
        return False, None

def test_file_upload(supabase, access_token=None):
    """Testa o upload de um arquivo de teste para o Supabase"""
    try:
        # Cria um pequeno arquivo de teste (uma imagem base64 simples)
        test_file_name = "test_logo.png"
        # Imagem de teste em base64 (um pequeno quadrado colorido)
        base64_image = "iVBORw0KGgoAAAANSUhEUgAAABQAAAAUCAYAAACNiR0NAAAABGdBTUEAALGPC/xhBQAAAAlwSFlzAAAOwgAADsIBFShKgAAAABl0RVh0U29mdHdhcmUAcGFpbnQubmV0IDQuMC4yMfEgaZUAAABkSURBVDhPY/j//z9VMZjBQG1DwQYCMdUMhRkGxFQzFGwYzFCqGQo2DIapZijYMBimqqFgA4GYaoaCDQNiqhkKNgyGqWYo2DAYppqhYMNgmGqGgg0DYqoZCjYMhqlmKKUYqAYAIYFY5DzF7IQAAAAASUVORK5CYII="
        
        # Decodifica a imagem base64
        image_data = base64.b64decode(base64_image)
        
        print(f"\nTentando fazer upload do arquivo de teste '{test_file_name}'...")
        
        # Se tiver token de acesso, configura a autenticação
        if access_token:
            supabase.auth.set_session(access_token)
        
        # Faz o upload do arquivo
        response = supabase.storage.from_(BUCKET_NAME).upload(
            path=test_file_name,
            file=image_data,
            file_options={"contentType": "image/png"}
        )
        
        if response:
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

def test_anon_upload(supabase):
    """Testa o upload sem autenticação"""
    print("\n--- Teste de upload sem autenticação ---")
    return test_file_upload(supabase)

def test_auth_upload(supabase):
    """Testa o upload com autenticação"""
    print("\n--- Teste de upload com autenticação ---")
    auth_success, access_token = test_auth(supabase)
    if not auth_success:
        return False
    
    return test_file_upload(supabase, access_token)

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
    
    # Tenta upload sem autenticação
    anon_success = test_anon_upload(supabase)
    
    # Tenta upload com autenticação (se houver credenciais)
    auth_success = False
    if TEST_EMAIL != "seu_email@exemplo.com" and TEST_PASSWORD != "sua_senha_segura":
        auth_success = test_auth_upload(supabase)
    else:
        print("\n[AVISO] Credenciais de teste não configuradas. Pulando teste com autenticação.")
    
    print("\n===== RESUMO DOS TESTES =====")
    print("[OK] Conexão com Supabase: OK")
    print(f"[{'OK' if anon_success else 'ERRO'}] Upload sem autenticação: {'OK' if anon_success else 'FALHA'}")
    
    if TEST_EMAIL != "seu_email@exemplo.com":
        print(f"[{'OK' if auth_success else 'ERRO'}] Upload com autenticação: {'OK' if auth_success else 'FALHA'}")
    
    print("============================\n")
    
    if anon_success:
        print("Seu bucket está configurado para permitir uploads anônimos.")
    elif auth_success:
        print("Seu bucket requer autenticação para uploads (recomendado para segurança).")
    else:
        print("Nenhum método de upload funcionou. Verifique:")
        print("1. Se o bucket 'logos' existe no Supabase")
        print("2. Se as policies estão configuradas corretamente")
        print("3. Se as credenciais de teste são válidas (para o teste com autenticação)")

if __name__ == "__main__":
    main()
