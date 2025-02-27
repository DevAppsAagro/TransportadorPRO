from django.db import models
from decimal import Decimal
from .caminhao import Caminhao
from .contato import Contato
from .frete import Frete

class Abastecimento(models.Model):
    SITUACAO_CHOICES = [
        ('EM_PERCURSO', 'Em Percurso'),
        ('FINAL_FRETE', 'Final de Frete'),
    ]

    data = models.DateField('Data do Abastecimento')
    data_vencimento = models.DateField('Data de Vencimento')
    data_pagamento = models.DateField('Data de Pagamento', null=True, blank=True)
    caminhao = models.ForeignKey(
        Caminhao,
        on_delete=models.PROTECT,
        verbose_name='Caminhão'
    )
    situacao = models.CharField(
        'Situação',
        max_length=20,
        choices=SITUACAO_CHOICES
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
        limit_choices_to={'tipo': 'MOTORISTA'}
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

    def save(self, *args, **kwargs):
        self.total_valor = self.litros * self.valor_litro
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Abastecimento {self.data} - {self.caminhao}'

    class Meta:
        verbose_name = 'Abastecimento'
        verbose_name_plural = 'Abastecimentos'
        ordering = ['-data']

    def __str__(self):
        return f'Abastecimento {self.caminhao} - {self.data}'