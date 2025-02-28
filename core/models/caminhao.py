from django.db import models
from django.contrib.auth.models import User

class Caminhao(models.Model):
    STATUS_CHOICES = [
        ('ATIVO', 'Ativo'),
        ('MANUTENCAO', 'Em Manutenção'),
        ('VENDIDO', 'Vendido'),
        ('INATIVO', 'Inativo')
    ]
    
    placa = models.CharField(max_length=8, verbose_name='Placa')
    marca = models.CharField(max_length=50, verbose_name='Marca')
    modelo = models.CharField(max_length=50, verbose_name='Modelo')
    ano = models.IntegerField(verbose_name='Ano')
    chassi = models.CharField(max_length=17, verbose_name='Chassi')
    renavam = models.CharField(max_length=11, verbose_name='Renavam')
    valor_compra = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Valor de Compra')
    vida_util = models.IntegerField(verbose_name='Vida Útil (anos)')
    valor_residual = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Valor Residual')
    capacidade_carga = models.DecimalField(max_digits=8, decimal_places=2, verbose_name='Capacidade de Carga (kg)')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ATIVO', verbose_name='Status')
    quilometragem = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Quilometragem Atual')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Usuário')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Data de Criação')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Data de Atualização')
    
    class Meta:
        verbose_name = 'Caminhão'
        verbose_name_plural = 'Caminhões'
        ordering = ['placa']
    
    def __str__(self):
        return f"{self.placa} - {self.marca} {self.modelo}"
    
    def calcular_depreciacao_anual(self):
        """Calcula a depreciação anual do caminhão"""
        if self.vida_util > 0:
            valor_depreciavel = float(self.valor_compra) - float(self.valor_residual)
            return valor_depreciavel / self.vida_util
        return 0
    
    def calcular_valor_atual(self):
        """Calcula o valor atual do caminhão considerando a depreciação"""
        from datetime import datetime
        anos_uso = datetime.now().year - self.ano
        depreciacao_total = self.calcular_depreciacao_anual() * min(anos_uso, self.vida_util)
        return max(float(self.valor_compra) - depreciacao_total, float(self.valor_residual))