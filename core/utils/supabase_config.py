from supabase import create_client, Client
from django.conf import settings
import logging
import mimetypes

logger = logging.getLogger(__name__)

def get_supabase_client(auth_token: str = None) -> Client:
    url = settings.SUPABASE_URL
    key = settings.SUPABASE_KEY
    
    if not url or not key:
        logger.error("Supabase URL or Key not configured")
        raise ValueError("Supabase configuration missing")
    
    client = create_client(url, key)
    
    if auth_token:
        client.auth.set_session(auth_token)
        # Enable RLS for authenticated users
        client.postgrest.auth(auth_token)
    
    return client

def upload_file(file_data: bytes, file_name: str, auth_token: str = None, content_type: str = None) -> str:
    try:
        supabase = get_supabase_client(auth_token)
        logger.info(f"Iniciando upload do arquivo {file_name}")
        
        # Detect content type if not provided
        if not content_type:
            content_type = mimetypes.guess_type(file_name)[0] or 'application/octet-stream'
        
        # Ensure the bucket exists
        bucket_name = settings.SUPABASE_STORAGE_BUCKET
        
        try:
            # Verifica se o bucket existe
            buckets = supabase.storage.list_buckets()
            bucket_exists = any(bucket.name == bucket_name for bucket in buckets)
            
            if not bucket_exists:
                logger.info(f"Criando bucket {bucket_name}")
                supabase.storage.create_bucket(bucket_name)
        except Exception as e:
            logger.warning(f"Erro ao verificar/criar bucket: {str(e)}")
        
        # Upload the file with proper content type
        response = supabase.storage.from_(bucket_name).upload(
            path=file_name,
            file=file_data,
            file_options={
                "content-type": content_type,
                "upsert": True,
                "cache-control": "3600",
                "x-upsert": "true"
            }
        )
        
        logger.debug(f"Resposta do upload: {response}")
        
        if response:
            # Generate the public URL for the file
            try:
                file_url = supabase.storage.from_(bucket_name).get_public_url(file_name)
                logger.info(f"Upload concluído com sucesso. URL: {file_url}")
                return file_url
            except Exception as e:
                logger.error(f"Erro ao gerar URL pública: {str(e)}")
                return None
        
        logger.error(f"Falha no upload. Resposta inesperada: {response}")
        return None
    except Exception as e:
        logger.error(f"Erro no upload: {str(e)}")
        return None