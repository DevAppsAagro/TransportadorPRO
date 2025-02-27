from django.db import models
from django.conf import settings

class Carreta(models.Model):
    STATUS_CHOICES = [
        ('ATIVO', 'Ativo'),
        ('MANUTENCAO', 'Em Manutenção'),
        ('VENDIDO', 'Vendido'),
        ('INATIVO', 'Inativo')
    ]

    placa = models.CharField('Placa', max_length=8, unique=True)
    marca = models.CharField('Marca', max_length=50)
    modelo = models.CharField('Modelo', max_length=50)
    ano = models.IntegerField('Ano')
    chassi = models.CharField('Chassi', max_length=17, unique=True)
    renavam = models.CharField('Renavam', max_length=11, unique=True)
    valor_compra = models.DecimalField('Valor de Compra', max_digits=10, decimal_places=2)
    vida_util = models.IntegerField('Vida Útil (anos)')
    valor_residual = models.DecimalField('Valor Residual', max_digits=10, decimal_places=2)
    capacidade_carga = models.DecimalField('Capacidade de Carga (kg)', max_digits=8, decimal_places=2)
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='ATIVO')
    quilometragem = models.DecimalField('Quilometragem Atual', max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField('Data de Criação', auto_now_add=True)
    updated_at = models.DateTimeField('Data de Atualização', auto_now=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='Usuário')

    class Meta:
        verbose_name = 'Carreta'
        verbose_name_plural = 'Carretas'
        ordering = ['placa']

    def __str__(self):
        return f'{self.marca} {self.modelo} - {self.placa}'