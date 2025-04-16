from django.db import models
from django.contrib.auth.models import User

class Contato(models.Model):
    TIPO_CHOICES = [
        ('FORNECEDOR', 'Fornecedor'),
        ('CLIENTE', 'Cliente'),
        ('FUNCIONARIO', 'Funcionário'),
        ('MOTORISTA', 'Motorista'),
        ('POSTO', 'Posto de Combustível')
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Usuário')
    nome_completo = models.CharField('Nome Completo', max_length=255)
    tipo = models.CharField('Tipo', max_length=20, choices=TIPO_CHOICES)
    
    # Campos importantes para integração com Asaas - obrigatórios para clientes
    # blank=True permite que o campo seja opcional no banco de dados, mas 
    # a validação no formulário garantirá que seja preenchido para clientes
    cpf_cnpj = models.CharField('CPF/CNPJ', max_length=18, blank=True, help_text='Obrigatório para clientes')
    email = models.EmailField('E-mail', blank=True, help_text='Obrigatório para clientes')
    telefone = models.CharField('Telefone', max_length=15, blank=True, help_text='Obrigatório para clientes')
    
    # Endereço
    cep = models.CharField('CEP', max_length=9, blank=True)
    logradouro = models.CharField('Logradouro', max_length=255, blank=True)
    numero = models.CharField('Número', max_length=10, blank=True)
    complemento = models.CharField('Complemento', max_length=100, blank=True)
    bairro = models.CharField('Bairro', max_length=100, blank=True)
    cidade = models.CharField('Cidade', max_length=100, blank=True)
    estado = models.CharField('Estado', max_length=2, blank=True)
    
    # Campos de controle
    data_criacao = models.DateTimeField('Data de Criação', auto_now_add=True)
    data_atualizacao = models.DateTimeField('Data de Atualização', auto_now=True)
    ativo = models.BooleanField('Ativo', default=True)
    
    class Meta:
        verbose_name = 'Contato'
        verbose_name_plural = 'Contatos'
        ordering = ['nome_completo']
    
    def __str__(self):
        return f"{self.nome_completo} ({self.get_tipo_display()})"