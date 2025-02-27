from django.db import models
from decimal import Decimal
from django.utils import timezone
from core.models.conjunto import Conjunto

class EstimativaCustoFixo(models.Model):
    data_estimativa = models.DateField(default=timezone.now)
    conjunto = models.ForeignKey(Conjunto, on_delete=models.CASCADE)
    custo_total_dia = models.DecimalField(max_digits=10, decimal_places=4, default=Decimal('0.0000'))
    
    def __str__(self):
        return f"Estimativa de Custo Fixo - {self.conjunto} - {self.data_estimativa}"
    
    def save(self, *args, **kwargs):
        is_new = not self.pk
        super().save(*args, **kwargs)
        
        # Só calcular o custo total se não for uma nova estimativa
        # Para novas estimativas, o cálculo será feito após adicionar os itens
        if not is_new:
            self.calcular_custo_total_por_dia()
    
    def calcular_custo_total_por_dia(self):
        if not self.pk:  # Se a estimativa ainda não foi salva
            return Decimal('0.0000')
        
        total = Decimal('0.0000')
        for item in self.itens.all():
            total += item.valor_por_dia
        
        self.custo_total_dia = total
        # Evitar recursão infinita e atualizar o valor no banco
        EstimativaCustoFixo.objects.filter(pk=self.pk).update(custo_total_dia=total)
        
        return total
    
    @property
    def is_active(self):
        """Verifica se esta é a estimativa mais recente para este conjunto"""
        estimativas_mais_recentes = EstimativaCustoFixo.objects.filter(
            conjunto=self.conjunto,
            data_estimativa__gt=self.data_estimativa
        ).exists()
        return not estimativas_mais_recentes


class ItemCustoFixo(models.Model):
    TIPO_CHOICES = [
        ('ANUAL', 'Anual'),
        ('MENSAL', 'Mensal'),
    ]
    
    estimativa = models.ForeignKey(EstimativaCustoFixo, on_delete=models.CASCADE, related_name='itens')
    descricao = models.CharField(max_length=100)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, default='ANUAL')
    valor_total = models.DecimalField(max_digits=10, decimal_places=2)
    valor_por_dia = models.DecimalField(max_digits=10, decimal_places=4, default=Decimal('0.0000'))
    
    def __str__(self):
        return f"{self.descricao} - {self.get_tipo_display()}"
    
    def save(self, *args, **kwargs):
        self.calcular_valor_por_dia()
        super().save(*args, **kwargs)
        
        # Atualizar o custo total da estimativa
        if self.estimativa and self.estimativa.pk:
            try:
                self.estimativa.calcular_custo_total_por_dia()
            except Exception:
                # Evitar que erros na atualização do custo total impeçam o salvamento do item
                pass
    
    def calcular_valor_por_dia(self):
        if self.tipo == 'ANUAL':
            self.valor_por_dia = self.valor_total / Decimal('365')
        elif self.tipo == 'MENSAL':
            self.valor_por_dia = self.valor_total / Decimal('30')
        return self.valor_por_dia
