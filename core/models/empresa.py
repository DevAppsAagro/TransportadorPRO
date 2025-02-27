from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
import os

class Empresa(models.Model):
    # Usuário proprietário
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Usuário')
    # Informações Básicas
    razao_social = models.CharField('Razão Social', max_length=255)
    nome_fantasia = models.CharField('Nome Fantasia', max_length=255, blank=True)
    logo = models.URLField('Logo', blank=True, null=True)
    cnpj = models.CharField('CNPJ', max_length=18, unique=True)
    inscricao_estadual = models.CharField('Inscrição Estadual', max_length=30, blank=True)
    inscricao_municipal = models.CharField('Inscrição Municipal', max_length=30, blank=True)
    
    # Endereço
    cep = models.CharField('CEP', max_length=9)
    logradouro = models.CharField('Logradouro', max_length=255)
    numero = models.CharField('Número', max_length=10)
    complemento = models.CharField('Complemento', max_length=100, blank=True)
    bairro = models.CharField('Bairro', max_length=100)
    cidade = models.CharField('Cidade', max_length=100)
    estado = models.CharField('Estado', max_length=2)
    
    # Contato
    telefone = models.CharField('Telefone', max_length=15)
    celular = models.CharField('Celular', max_length=15, blank=True)
    email = models.EmailField('E-mail')
    site = models.URLField('Site', blank=True)
    
    # Informações Adicionais
    rntrc = models.CharField('RNTRC', max_length=50, blank=True)
    antt = models.CharField('ANTT', max_length=50, blank=True)
    observacoes = models.TextField('Observações', blank=True)
    
    # Campos de controle
    data_criacao = models.DateTimeField('Data de Criação', auto_now_add=True)
    data_atualizacao = models.DateTimeField('Data de Atualização', auto_now=True)
    
    class Meta:
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'
    
    def __str__(self):
        return self.razao_social