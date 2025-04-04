from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
from .caminhao import Caminhao
from .contato import Contato
from .frete import Frete
# Importação circular, mas necessária para o tipo de anotação
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .abastecimento_pendente import AbastecimentoPendente

class Abastecimento(models.Model):
    SITUACAO_CHOICES = [
        ('EM_PERCURSO', 'Em Percurso'),
        ('FINAL_FRETE', 'Final de Frete'),
    ]
    
    TIPO_COMBUSTIVEL_CHOICES = [
        ('DIESEL_S10', 'Diesel S10'),
        ('DIESEL_S500', 'Diesel S500'),
    ]

    data = models.DateField('Data do Abastecimento')
    data_vencimento = models.DateField('Data de Vencimento')
    data_pagamento = models.DateField('Data de Pagamento', null=True, blank=True)
    caminhao = models.ForeignKey(
        Caminhao,
        on_delete=models.PROTECT,
        verbose_name='Caminhão'
    )
    frete = models.ForeignKey(
        Frete,
        on_delete=models.SET_NULL,
        verbose_name='Frete',
        null=True,
        blank=True
    )
    situacao = models.CharField(
        'Situação',
        max_length=20,
        choices=SITUACAO_CHOICES
    )
    tipo_combustivel = models.CharField(
        'Tipo de Combustível',
        max_length=20,
        choices=TIPO_COMBUSTIVEL_CHOICES,
        default='DIESEL_S10',
        null=True,
        blank=True
    )
    litros = models.DecimalField(
        'Litros',
        max_digits=10,
        decimal_places=2
    )
    valor_litro = models.DecimalField(
        'R$/Litro',
        max_digits=10,
        decimal_places=2
    )
    motorista = models.ForeignKey(
        Contato,
        on_delete=models.PROTECT,
        verbose_name='Motorista',
        related_name='abastecimentos_motorista',
        limit_choices_to={'tipo': 'MOTORISTA'},
        null=True,
        blank=True
    )
    motorista_user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        verbose_name='Motorista (Usuário)',
        related_name='abastecimentos_motorista_user',
        null=True,
        blank=True
    )
    posto = models.ForeignKey(
        Contato,
        on_delete=models.PROTECT,
        verbose_name='Posto',
        related_name='abastecimentos_posto',
        limit_choices_to={'tipo': 'POSTO'}
    )
    km_abastecimento = models.IntegerField('KM do Abastecimento')
    total_valor = models.DecimalField(
        'Valor Total',
        max_digits=10,
        decimal_places=2,
        editable=False
    )
    origem_pendente = models.BooleanField(
        'Origem Pendente',
        default=False,
        help_text='Indica se o abastecimento foi criado a partir de um abastecimento pendente'
    )
    abastecimento_pendente = models.OneToOneField(
        'AbastecimentoPendente',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='abastecimento_aprovado',
        verbose_name='Abastecimento Pendente Original'
    )

    def save(self, *args, **kwargs):
        self.total_valor = self.litros * self.valor_litro
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Abastecimento {self.caminhao} - {self.data}'

    class Meta:
        verbose_name = 'Abastecimento'
        verbose_name_plural = 'Abastecimentos'
        ordering = ['-data']