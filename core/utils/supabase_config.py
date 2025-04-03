import os
import uuid
import logging
from django.conf import settings
from supabase import create_client, Client

logger = logging.getLogger(__name__)

def get_supabase_client(use_service_role=True) -> Client:
    """
    Cria e retorna um cliente Supabase
    
    Args:
        use_service_role: Se True, usa a chave de serviço (service_role) que tem mais permissões
    """
    url = settings.SUPABASE_URL
    
    # Depuração para ambiente Vercel
    logger.info(f"SUPABASE_URL: {'Configurado' if url else 'Não configurado'}")
    logger.info(f"SUPABASE_KEY: {'Configurado' if hasattr(settings, 'SUPABASE_KEY') and settings.SUPABASE_KEY else 'Não configurado'}")
    logger.info(f"SUPABASE_SERVICE_KEY: {'Configurado' if hasattr(settings, 'SUPABASE_SERVICE_KEY') and settings.SUPABASE_SERVICE_KEY else 'Não configurado'}")
    logger.info(f"SUPABASE_STORAGE_BUCKET: {getattr(settings, 'SUPABASE_STORAGE_BUCKET', 'não definido')}")
    
    # Usar chave de serviço se disponível
    if use_service_role and hasattr(settings, 'SUPABASE_SERVICE_KEY'):
        key = settings.SUPABASE_SERVICE_KEY
        logger.info("Usando chave de serviço (service_role) do Supabase")
    else:
        key = settings.SUPABASE_KEY
        logger.info("Usando chave normal do Supabase")
    
    if not url or not key:
        logger.error("Supabase URL or Key not configured")
        raise ValueError("Supabase configuration missing")
    
    try:
        # Criar cliente Supabase sem o argumento proxy
        client = create_client(url, key)
        return client
    except TypeError as e:
        if "proxy" in str(e):
            logger.warning("Erro com argumento 'proxy', tentando método alternativo")
            # Se o erro for relacionado ao argumento proxy, tente importar diretamente
            try:
                from supabase import Client as SupabaseClient
                client = SupabaseClient(url, key)
                return client
            except Exception as inner_e:
                logger.error(f"Erro ao criar cliente alternativo: {str(inner_e)}")
                raise
        else:
            logger.error(f"Erro ao criar cliente Supabase: {str(e)}")
            raise

def upload_file(file_data, file_name, auth_token=None, content_type=None):
    """
    Faz upload de um arquivo para o Supabase Storage e retorna a URL pública.
    
    Args:
        file_data: Dados binários do arquivo ou objeto UploadedFile do Django
        file_name: Nome do arquivo no bucket
        auth_token: Token de autenticação (não usado, mantido para compatibilidade)
        content_type: Tipo de conteúdo do arquivo
        
    Returns:
        URL pública do arquivo ou None em caso de erro
    """
    try:
        # Obter nome do bucket das configurações
        bucket_name = getattr(settings, 'SUPABASE_STORAGE_BUCKET', 'logos')
        
        # Criar nome único para o arquivo
        file_ext = os.path.splitext(file_name)[1]
        
        # Determinar o prefixo para o bucket logos
        prefix = "company_logos"
        
        # Criar caminho do arquivo com prefixo
        unique_file_name = f"{prefix}/{uuid.uuid4()}{file_ext}"
        
        logger.info(f"Iniciando upload do arquivo para o bucket {bucket_name} com caminho {unique_file_name}")
        
        # Verificar se as configurações do Supabase estão disponíveis
        if not settings.SUPABASE_URL:
            logger.error("SUPABASE_URL não está configurado")
            return None
            
        if not settings.SUPABASE_SERVICE_KEY and not settings.SUPABASE_KEY:
            logger.error("Nenhuma chave do Supabase está configurada")
            return None
        
        # Inicializar cliente Supabase com chave de serviço
        try:
            supabase = get_supabase_client(use_service_role=True)
        except ValueError as e:
            logger.error(f"Erro ao criar cliente Supabase: {str(e)}")
            # Tentar com a chave normal se a chave de serviço falhar
            try:
                logger.info("Tentando com a chave normal do Supabase")
                supabase = get_supabase_client(use_service_role=False)
            except ValueError as e:
                logger.error(f"Erro ao criar cliente Supabase com chave normal: {str(e)}")
                return None
        
        # Verificar se file_data é um objeto UploadedFile do Django ou dados binários
        if hasattr(file_data, 'read') and callable(file_data.read):
            # É um objeto de arquivo, usar .read() para obter os dados
            file_content = file_data.read()
            
            # Usar o content_type do arquivo se não for fornecido
            if not content_type and hasattr(file_data, 'content_type'):
                content_type = file_data.content_type
        else:
            # Já são dados binários
            file_content = file_data
        
        # Verificar se temos dados para upload
        if not file_content:
            logger.error("Nenhum conteúdo de arquivo para upload")
            return None
            
        # Verificar se temos content_type
        if not content_type:
            # Tentar inferir do nome do arquivo
            if file_ext.lower() in ['.jpg', '.jpeg']:
                content_type = 'image/jpeg'
            elif file_ext.lower() == '.png':
                content_type = 'image/png'
            elif file_ext.lower() == '.gif':
                content_type = 'image/gif'
            else:
                content_type = 'application/octet-stream'
                
        logger.info(f"Fazendo upload com content_type: {content_type}")
        
        # Upload do arquivo
        try:
            result = supabase.storage.from_(bucket_name).upload(
                path=unique_file_name,
                file=file_content,
                file_options={"contentType": content_type}
            )
            
            if result:
                # Gerar URL pública
                public_url = supabase.storage.from_(bucket_name).get_public_url(unique_file_name)
                logger.info(f"Upload concluído com sucesso. URL: {public_url}")
                return public_url
            else:
                logger.error("Falha no upload: resposta inválida")
                return None
        except Exception as e:
            logger.error(f"Erro durante o upload para o Supabase: {str(e)}")
            return None
            
    except Exception as e:
        logger.error(f"Erro ao fazer upload para o Supabase: {str(e)}")
        return None

def remove_file(url):
    """
    Remove um arquivo do Supabase Storage.
    
    Args:
        url: URL pública do arquivo a ser removido
        
    Returns:
        True se o arquivo foi removido com sucesso, False caso contrário
    """
    try:
        if not url:
            return True
            
        # Obter nome do bucket das configurações
        bucket_name = getattr(settings, 'SUPABASE_STORAGE_BUCKET', 'logos')
        
        # Extrair caminho do arquivo da URL
        # A URL será algo como: https://hejhbdkofhkdnzokjklr.supabase.co/storage/v1/object/public/logos/company_logos/uuid.png
        # Precisamos extrair: company_logos/uuid.png
        
        # Primeiro, extrair a parte após o bucket_name
        parts = url.split(f"{bucket_name}/")
        if len(parts) < 2:
            logger.error(f"Não foi possível extrair o caminho do arquivo da URL: {url}")
            return False
            
        file_path = parts[1]
        
        logger.info(f"Removendo arquivo {file_path} do bucket {bucket_name}")
        
        # Inicializar cliente Supabase com chave de serviço
        supabase = get_supabase_client(use_service_role=True)
        
        # Remover arquivo
        supabase.storage.from_(bucket_name).remove([file_path])
        logger.info(f"Arquivo removido com sucesso: {file_path}")
        
        return True
    except Exception as e:
        logger.error(f"Erro ao remover arquivo do Supabase: {str(e)}")
        return False