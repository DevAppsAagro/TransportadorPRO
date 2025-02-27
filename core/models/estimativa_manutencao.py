from django.db import models
from django.utils import timezone
from decimal import Decimal
from core.models.conjunto import Conjunto

class EstimativaManutencao(models.Model):
    conjunto = models.ForeignKey(Conjunto, on_delete=models.CASCADE, related_name='estimativas_manutencao')
    data_estimativa = models.DateField(default=timezone.now)
    custo_total_km = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    
    class Meta:
        verbose_name = 'Estimativa de Manutenção'
        verbose_name_plural = 'Estimativas de Manutenção'
        ordering = ['-data_estimativa']
    
    def __str__(self):
        return f'Estimativa de Manutenção - Conjunto {self.conjunto} - {self.data_estimativa}'
    
    @property
    def is_active(self):
        """
        Verifica se esta é a estimativa mais recente para o conjunto.
        Apenas a estimativa mais recente é considerada ativa.
        """
        estimativa_mais_recente = EstimativaManutencao.objects.filter(
            conjunto=self.conjunto,
            data_estimativa__gt=self.data_estimativa
        ).exists()
        return not estimativa_mais_recente
    
    @classmethod
    def get_active_for_conjunto(cls, conjunto_id):
        """
        Retorna a estimativa ativa (mais recente) para um determinado conjunto
        """
        try:
            return cls.objects.filter(conjunto_id=conjunto_id).order_by('-data_estimativa').first()
        except cls.DoesNotExist:
            return None
    
    def calcular_custo_total_por_km(self):
        """Calcula o custo total por km somando todos os itens de manutenção"""
        if not self.pk:  # Se a estimativa ainda não foi salva
            return Decimal('0.0000')
        
        itens = self.itens_manutencao.all()
        total = sum(item.custo_por_km for item in itens)
        return total
    
    def save(self, *args, **kwargs):
        # Primeiro salvamos a estimativa para garantir que ela tenha um ID
        is_new = not self.pk
        super().save(*args, **kwargs)
        
        # Só calculamos o custo total se não for uma nova estimativa ou se já tiver itens
        if not is_new:
            self.custo_total_km = self.calcular_custo_total_por_km()
            # Evitamos uma recursão infinita usando update
            type(self).objects.filter(pk=self.pk).update(custo_total_km=self.custo_total_km)


class ItemManutencao(models.Model):
    estimativa = models.ForeignKey(EstimativaManutencao, on_delete=models.CASCADE, related_name='itens_manutencao')
    descricao = models.CharField(max_length=255)
    duracao_km = models.PositiveIntegerField(help_text='Quilometragem estimada para duração desta manutenção')
    custo_total = models.DecimalField(max_digits=10, decimal_places=2)
    custo_por_km = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    
    class Meta:
        verbose_name = 'Item de Manutenção'
        verbose_name_plural = 'Itens de Manutenção'
    
    def __str__(self):
        return f'{self.descricao} - R${self.custo_total}'
    
    def calcular_custo_por_km(self):
        """Calcula o custo por km para este item de manutenção"""
        if self.duracao_km > 0:
            return self.custo_total / Decimal(self.duracao_km)
        return Decimal('0.0000')
    
    def save(self, *args, **kwargs):
        self.custo_por_km = self.calcular_custo_por_km()
        super().save(*args, **kwargs)
        
        # Não atualizamos a estimativa aqui para evitar recursão
        # A atualização do custo total da estimativa é feita nas views
