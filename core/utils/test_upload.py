"""
Script simplificado para testar o upload de arquivos para o Supabase
Assume que o bucket já existe e está configurado corretamente
"""
import os
import sys
import base64
import logging
from supabase import create_client
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

def test_upload():
    """Testa o upload de um arquivo para o Supabase"""
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("\nERRO: Configure as variáveis SUPABASE_URL e SUPABASE_KEY no arquivo .env")
        sys.exit(1)
    
    print("\n===== TESTE DE UPLOAD PARA SUPABASE =====")
    print(f"URL: {SUPABASE_URL}")
    print(f"Key: {'*' * 8 + SUPABASE_KEY[-4:] if SUPABASE_KEY else 'Não configurada'}")
    print(f"Bucket: {BUCKET_NAME}")
    print("==========================================\n")
    
    try:
        # Conectar ao Supabase usando a service key
        print("Conectando ao Supabase...")
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("[OK] Conexão estabelecida com sucesso!")
        
        # Criar um pequeno arquivo de teste
        test_file_name = f"test_logo_{os.urandom(4).hex()}.png"
        # Imagem de teste em base64 (um pequeno quadrado colorido)
        base64_image = "iVBORw0KGgoAAAANSUhEUgAAABQAAAAUCAYAAACNiR0NAAAABGdBTUEAALGPC/xhBQAAAAlwSFlzAAAOwgAADsIBFShKgAAAABl0RVh0U29mdHdhcmUAcGFpbnQubmV0IDQuMC4yMfEgaZUAAABkSURBVDhPY/j//z9VMZjBQG1DwQYCMdUMhRkGxFQzFGwYzFCqGQo2DIapZijYMBimqqFgA4GYaoaCDQNiqhkKNgyGqWYo2DAYppqhYMNgmGqGgg0DYqoZCjYMhqlmKKUYqAYAIYFY5DzF7IQAAAAASUVORK5CYII="
        
        # Decodifica a imagem base64
        image_data = base64.b64decode(base64_image)
        
        print(f"\nTentando fazer upload do arquivo '{test_file_name}'...")
        
        # Método 1: Usando o cliente padrão
        try:
            print("\nMétodo 1: Usando o cliente padrão do Supabase")
            response = supabase.storage.from_(BUCKET_NAME).upload(
                path=test_file_name,
                file=image_data,
                file_options={"contentType": "image/png"}
            )
            
            if response:
                file_url = supabase.storage.from_(BUCKET_NAME).get_public_url(test_file_name)
                print(f"[OK] Upload bem-sucedido!")
                print(f"URL pública: {file_url}")
                method1_success = True
            else:
                print(f"[ERRO] Falha no upload: resposta inválida")
                method1_success = False
                
        except Exception as e:
            print(f"[ERRO] Método 1 falhou: {str(e)}")
            method1_success = False
        
        # Método 2: Usando a API direta (ignorando RLS)
        try:
            if not method1_success:
                print("\nMétodo 2: Usando a API direta (ignorando RLS)")
                test_file_name = f"test_logo_direct_{os.urandom(4).hex()}.png"
                
                from supabase.storage import StorageClient
                storage = StorageClient(
                    supabase.supabase_url, 
                    {"Authorization": f"Bearer {supabase.supabase_key}"}
                )
                
                result = storage.from_(BUCKET_NAME).upload(
                    path=test_file_name,
                    file=image_data,
                    file_options={"contentType": "image/png"}
                )
                
                if result:
                    file_url = supabase.storage.from_(BUCKET_NAME).get_public_url(test_file_name)
                    print(f"[OK] Upload bem-sucedido com o método alternativo!")
                    print(f"URL pública: {file_url}")
                    method2_success = True
                else:
                    print(f"[ERRO] Método 2 falhou: resposta inválida")
                    method2_success = False
        except Exception as e:
            print(f"[ERRO] Método 2 falhou: {str(e)}")
            method2_success = False
        
        # Resumo
        print("\n===== RESUMO DO TESTE =====")
        print(f"Método 1 (Cliente padrão): {'OK' if method1_success else 'FALHA'}")
        if not method1_success:
            print(f"Método 2 (API direta): {'OK' if method2_success else 'FALHA'}")
        print("===========================\n")
        
        if method1_success or method2_success:
            print("CONCLUSÃO: O upload de arquivos para o Supabase está funcionando!")
            print("\nPróximos passos:")
            print("1. Verifique se a URL pública está acessível no navegador")
            print("2. Implemente o upload de logos na sua aplicação")
        else:
            print("CONCLUSÃO: Nenhum método de upload funcionou.")
            print("\nVerifique:")
            print("1. Se o bucket 'logos' existe no Supabase")
            print("2. Se você está usando a chave de API correta (service key, não anon key)")
            print("3. Se as políticas de acesso estão configuradas corretamente")
            print("\nPara configurar manualmente no painel do Supabase:")
            print("1. Acesse https://app.supabase.com")
            print("2. Selecione seu projeto")
            print("3. Vá para Storage > Buckets")
            print(f"4. Crie um bucket chamado '{BUCKET_NAME}' (se não existir)")
            print("5. Marque a opção 'Public bucket' para torná-lo público")
            print("6. Vá para Storage > Policies")
            print("7. Configure políticas para permitir leitura pública e escrita autenticada")
        
    except Exception as e:
        print(f"\n[ERRO] Erro durante o teste: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    test_upload()
