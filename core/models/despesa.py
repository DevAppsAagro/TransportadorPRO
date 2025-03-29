from django.db import models
from django.utils import timezone
from datetime import date
from decimal import Decimal
from core.models.categoria import Categoria
from core.models.subcategoria import Subcategoria
from core.models.caminhao import Caminhao
from core.models.carreta import Carreta
from core.models.frete import Frete
from core.models.empresa import Empresa
from core.models.contato import Contato

class Despesa(models.Model):
    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente'),
        ('VENCE_HOJE', 'Vence Hoje'),
        ('VENCIDA', 'Vencida'),
        ('PAGA', 'Paga'),
    ]
    
    data = models.DateField(default=timezone.now)
    data_vencimento = models.DateField()
    data_pagamento = models.DateField(null=True, blank=True)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT)
    subcategoria = models.ForeignKey(Subcategoria, on_delete=models.PROTECT)
    
    # Campos de destino (apenas um será preenchido, dependendo da alocação da categoria)
    caminhao = models.ForeignKey(Caminhao, on_delete=models.PROTECT, null=True, blank=True)
    carreta = models.ForeignKey(Carreta, on_delete=models.PROTECT, null=True, blank=True)
    frete = models.ForeignKey(Frete, on_delete=models.PROTECT, null=True, blank=True)
    empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, null=True, blank=True)
    
    contato = models.ForeignKey(Contato, on_delete=models.PROTECT, null=True, blank=True)
    observacao = models.TextField(blank=True)
    
    def __str__(self):
        return f"Despesa {self.id} - {self.categoria} - {self.valor}"
    
    @property
    def status(self):
        hoje = date.today()
        
        if self.data_pagamento:
            return 'PAGA'
        elif self.data_vencimento == hoje:
            return 'VENCE_HOJE'
        elif self.data_vencimento < hoje:
            return 'VENCIDA'
        else:
            return 'PENDENTE'
    
    @property
    def status_display(self):
        status_dict = dict(self.STATUS_CHOICES)
        return status_dict.get(self.status)
    
    @property
    def dias_atraso(self):
        """Retorna o número de dias em atraso, ou 0 se não estiver atrasada"""
        if self.status == 'VENCIDA':
            hoje = date.today()
            return (hoje - self.data_vencimento).days
        return 0
    
    @property
    def destino_display(self):
        """Retorna uma representação textual do destino da despesa"""
        if self.caminhao:
            return f"Caminhão: {self.caminhao.placa}"
        elif self.carreta:
            return f"Carreta: {self.carreta.placa}"
        elif self.frete:
            return f"Frete: {self.frete.id} - {self.frete.cliente}"
        elif self.empresa:
            return f"Empresa: {self.empresa.razao_social}"
        return "Não definido"
    
    def save(self, *args, **kwargs):
        # Garantir que apenas um destino seja preenchido, baseado na alocação da categoria
        alocacao = self.categoria.alocacao if self.categoria else None
        
        if alocacao == 'VEICULO':
            self.frete = None
            self.empresa = None
        elif alocacao == 'FRETE':
            self.caminhao = None
            self.carreta = None
            self.empresa = None
        elif alocacao == 'ADMINISTRATIVO':
            self.caminhao = None
            self.carreta = None
            self.frete = None
        
        super().save(*args, **kwargs)
