from django.db import models
from django.contrib.auth.models import User
from .caminhao import Caminhao
from .contato import Contato
from .frete import Frete

# Definição das opções de combustível
COMBUSTIVEL_CHOICES = [
    ('DIESEL_S10', 'Diesel S10'),
    ('DIESEL_S500', 'Diesel S500'),
]

class AbastecimentoPendente(models.Model):
    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente'),
        ('APROVADO', 'Aprovado'),
        ('REJEITADO', 'Rejeitado')
    ]
    
    SITUACAO_CHOICES = [
        ('EM_PERCURSO', 'Em Percurso'),
        ('FINAL_FRETE', 'Final de Frete'),
    ]
    
    # Relacionamentos
    motorista = models.ForeignKey(User, on_delete=models.CASCADE, related_name='abastecimentos_pendentes')
    caminhao = models.ForeignKey(Caminhao, on_delete=models.CASCADE)
    posto = models.ForeignKey(
        Contato,
        on_delete=models.CASCADE,
        limit_choices_to={'tipo': 'POSTO'}
    )
    frete = models.ForeignKey(
        Frete,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Frete Associado'
    )
    
    # Dados do abastecimento
    data = models.DateField('Data')
    combustivel = models.CharField('Combustível', max_length=20, choices=COMBUSTIVEL_CHOICES)
    litros = models.DecimalField('Litros', max_digits=10, decimal_places=2)
    valor_litro = models.DecimalField('Valor por Litro', max_digits=10, decimal_places=2)
    valor_total = models.DecimalField('Valor Total', max_digits=10, decimal_places=2)
    km_atual = models.IntegerField('Quilometragem Atual')
    situacao = models.CharField('Situação', max_length=20, choices=SITUACAO_CHOICES, default='EM_PERCURSO', null=True, blank=True)
    data_vencimento = models.DateField('Data de Vencimento', null=True, blank=True)
    data_pagamento = models.DateField('Data de Pagamento', null=True, blank=True)
    
    # Metadados
    comprovante = models.ImageField('Comprovante', upload_to='comprovantes/', null=True, blank=True)
    observacao = models.TextField('Observação', blank=True, null=True)
    data_solicitacao = models.DateTimeField('Data da Solicitação', auto_now_add=True)
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='PENDENTE')
    motivo_rejeicao = models.TextField('Motivo da Rejeição', blank=True, null=True)
    
    class Meta:
        verbose_name = 'Abastecimento Pendente'
        verbose_name_plural = 'Abastecimentos Pendentes'
        ordering = ['-data_solicitacao']
    
    def __str__(self):
        return f"Abastecimento de {self.caminhao.placa} em {self.data} - {self.get_status_display()}"
