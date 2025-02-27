from django.db import models
from django.utils import timezone
from decimal import Decimal
from core.models.conjunto import Conjunto

class EstimativaPneus(models.Model):
    conjunto = models.ForeignKey(Conjunto, on_delete=models.CASCADE, related_name='estimativas_pneus')
    data_estimativa = models.DateField(default=timezone.now)
    custo_total_km = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Quantidades de pneus
    qtd_pneus_dianteiros = models.PositiveIntegerField(default=2)
    qtd_pneus_traseiros = models.PositiveIntegerField(default=8)
    qtd_pneus_carreta = models.PositiveIntegerField(default=12)
    
    # Preços dos pneus
    preco_pneu_dianteiro = models.DecimalField(max_digits=10, decimal_places=2)
    preco_pneu_traseiro = models.DecimalField(max_digits=10, decimal_places=2)
    preco_pneu_carreta = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Quilometragem estimada
    km_vida_util_dianteiro = models.PositiveIntegerField(help_text='Quilometragem estimada para pneus dianteiros')
    km_vida_util_traseiro = models.PositiveIntegerField(help_text='Quilometragem estimada para pneus traseiros')
    km_vida_util_carreta = models.PositiveIntegerField(help_text='Quilometragem estimada para pneus da carreta')
    
    # Custos de recapagem
    custo_recapagem_dianteiro = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    custo_recapagem_traseiro = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    custo_recapagem_carreta = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Número de recapagens possíveis
    num_recapagens_dianteiro = models.PositiveIntegerField(default=1)
    num_recapagens_traseiro = models.PositiveIntegerField(default=2)
    num_recapagens_carreta = models.PositiveIntegerField(default=2)
    
    class Meta:
        verbose_name = 'Estimativa de Pneus'
        verbose_name_plural = 'Estimativas de Pneus'
    
    def __str__(self):
        return f'Estimativa de Pneus - Conjunto {self.conjunto} - {self.data_estimativa}'
    
    @property
    def is_active(self):
        # Verifica se existe uma estimativa mais recente para o mesmo conjunto
        estimativa_mais_recente = EstimativaPneus.objects.filter(
            conjunto=self.conjunto,
            data_estimativa__gt=self.data_estimativa
        ).exists()
        return not estimativa_mais_recente
    
    def calcular_custo_por_km_dianteiro(self):
        custo_total = (self.preco_pneu_dianteiro + 
                      (self.custo_recapagem_dianteiro * self.num_recapagens_dianteiro))
        km_total = self.km_vida_util_dianteiro * (1 + self.num_recapagens_dianteiro)
        return (custo_total / Decimal(km_total)) * self.qtd_pneus_dianteiros
    
    def calcular_custo_por_km_traseiro(self):
        custo_total = (self.preco_pneu_traseiro + 
                      (self.custo_recapagem_traseiro * self.num_recapagens_traseiro))
        km_total = self.km_vida_util_traseiro * (1 + self.num_recapagens_traseiro)
        return (custo_total / Decimal(km_total)) * self.qtd_pneus_traseiros
    
    def calcular_custo_por_km_carreta(self):
        custo_total = (self.preco_pneu_carreta + 
                      (self.custo_recapagem_carreta * self.num_recapagens_carreta))
        km_total = self.km_vida_util_carreta * (1 + self.num_recapagens_carreta)
        return (custo_total / Decimal(km_total)) * self.qtd_pneus_carreta
    
    def calcular_custo_pneus(self):
        # Calcula o custo por km para cada tipo de pneu
        def calcular_custo_por_tipo(qtd, preco, km_vida_util, custo_recapagem, num_recapagens):
            custo_total = qtd * preco  # Custo inicial dos pneus
            custo_total += qtd * custo_recapagem * num_recapagens  # Custo total das recapagens
            km_total = km_vida_util * (1 + num_recapagens)  # Quilometragem total considerando recapagens
            return {
                'custo_total': custo_total,
                'km_total': km_total,
                'custo_por_km': custo_total / km_total if km_total > 0 else 0
            }
        
        # Calcula para cada tipo de pneu
        dianteiros = calcular_custo_por_tipo(
            self.qtd_pneus_dianteiros,
            self.preco_pneu_dianteiro,
            self.km_vida_util_dianteiro,
            self.custo_recapagem_dianteiro,
            self.num_recapagens_dianteiro
        )
        
        traseiros = calcular_custo_por_tipo(
            self.qtd_pneus_traseiros,
            self.preco_pneu_traseiro,
            self.km_vida_util_traseiro,
            self.custo_recapagem_traseiro,
            self.num_recapagens_traseiro
        )
        
        carreta = calcular_custo_por_tipo(
            self.qtd_pneus_carreta,
            self.preco_pneu_carreta,
            self.km_vida_util_carreta,
            self.custo_recapagem_carreta,
            self.num_recapagens_carreta
        )
        
        # Calcula o custo total por quilômetro
        custo_total_km = dianteiros['custo_por_km'] + traseiros['custo_por_km'] + carreta['custo_por_km']
        
        # Atualiza o campo custo_total_km do modelo
        self.custo_total_km = custo_total_km
        self.save()
        
        return {
            'dianteiros': dianteiros,
            'traseiros': traseiros,
            'carreta': carreta,
            'custo_total_km': custo_total_km
        }
    
    def calcular_custo_total_por_km(self):
        return (self.calcular_custo_por_km_dianteiro() +
                self.calcular_custo_por_km_traseiro() +
                self.calcular_custo_por_km_carreta())
    
    def save(self, *args, **kwargs):
        self.custo_total_km = self.calcular_custo_total_por_km()
        super().save(*args, **kwargs)