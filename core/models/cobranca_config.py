from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import os

def get_encryption_key():
    """
    Gera uma chave de criptografia a partir da SECRET_KEY do Django
    """
    # Usar a SECRET_KEY do Django como senha para gerar a chave
    password = settings.SECRET_KEY.encode()
    # Usar um salt fixo para garantir que a mesma chave seja gerada em cada execução
    salt = b'transportadorpro_salt'
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    
    key = base64.urlsafe_b64encode(kdf.derive(password))
    return key

def encrypt_api_key(api_key):
    """
    Criptografa a chave de API usando Fernet (criptografia simétrica)
    """
    if not api_key:
        return ''
        
    key = get_encryption_key()
    f = Fernet(key)
    encrypted_data = f.encrypt(api_key.encode())
    return base64.urlsafe_b64encode(encrypted_data).decode()

def decrypt_api_key(encrypted_api_key):
    """
    Descriptografa a chave de API
    """
    if not encrypted_api_key:
        return ''
        
    try:
        key = get_encryption_key()
        f = Fernet(key)
        decrypted_data = f.decrypt(base64.urlsafe_b64decode(encrypted_api_key.encode()))
        return decrypted_data.decode()
    except Exception as e:
        # Em caso de erro na descriptografia, retornar string vazia
        return ''

class AsaasConfig(models.Model):
    """
    Configuração da integração com o sistema de cobranças para cada usuário.
    Cada transportadora terá sua própria subconta no sistema de cobranças.
    """
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='asaas_config', verbose_name='Usuário')
    api_key = models.CharField(max_length=512, verbose_name="Chave de API do Sistema de Cobranças (criptografada)")
    is_sandbox = models.BooleanField(default=False, verbose_name="Ambiente de Testes")
    taxa_sistema = models.DecimalField(max_digits=10, decimal_places=2, default=9.99, 
                                      verbose_name="Taxa do Sistema (R$)")
    asaas_account_key = models.CharField(max_length=255, verbose_name="Chave da Conta Asaas", blank=True, null=True)
    
    # Campos para split de pagamento
    wallet_id = models.CharField(max_length=255, verbose_name="Wallet ID (Split)", null=True, blank=True)
    
    # Configuração para obrigar o usuário a gerar cobrança ao cadastrar fretes
    obrigar_cobranca = models.BooleanField(default=False, verbose_name="Obrigar geração de cobrança", 
                                         help_text="Se marcado, o usuário será obrigado a gerar cobrança ao cadastrar fretes")
    
    # Campos de controle
    data_criacao = models.DateTimeField('Data de Criação', auto_now_add=True)
    data_atualizacao = models.DateTimeField('Data de Atualização', auto_now=True)
    
    class Meta:
        verbose_name = "Configuração de Cobranças"
        verbose_name_plural = "Configurações de Cobranças"
    
    def __str__(self):
        return f"Configuração de Cobranças de {self.usuario.username}"
    
    def save(self, *args, **kwargs):
        """Sobrescreve o método save para criptografar a chave de API antes de salvar"""
        # Se a chave de API não estiver vazia e não parecer já estar criptografada
        if self.api_key and not self.api_key.startswith('gAAAAA'):
            self.api_key = encrypt_api_key(self.api_key)
        super().save(*args, **kwargs)
    
    def get_api_key(self):
        """Retorna a chave de API descriptografada"""
        return decrypt_api_key(self.api_key)
    
    @property
    def api_url(self):
        """Retorna a URL da API do sistema de cobranças com base no ambiente (sandbox ou produção)"""
        if self.is_sandbox:
            return "https://sandbox.asaas.com/api/v3"
        return "https://api.asaas.com/api/v3"
