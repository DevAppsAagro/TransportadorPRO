from django.db import models
from django.utils import timezone
from .caminhao import Caminhao
from .contato import Contato
from .carga import Carga
from django.contrib.auth.models import User
import logging

logger = logging.getLogger(__name__)

class Frete(models.Model):
    STATUS_ANDAMENTO_CHOICES = [
        ('EM_ANDAMENTO', 'Em Andamento'),
        ('FINALIZADO', 'Finalizado'),
    ]
    caminhao = models.ForeignKey(Caminhao, on_delete=models.PROTECT, verbose_name='Caminhão')
    motorista = models.ForeignKey(Contato, on_delete=models.PROTECT, verbose_name='Motorista', limit_choices_to={'tipo': 'MOTORISTA'}, related_name='fretes_como_motorista', null=True, blank=True)
    motorista_user = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name='Motorista (Usuário)', null=True, blank=True, related_name='fretes_como_motorista_user')
    data_saida = models.DateField(verbose_name='Data de Saída')
    data_chegada = models.DateField(verbose_name='Data de Chegada', null=True, blank=True)
    peso_carga = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Peso da Carga (kg)')
    km_saida = models.IntegerField(verbose_name='Km de Saída')
    km_chegada = models.IntegerField(verbose_name='Km de Chegada', null=True, blank=True)
    conta_bancaria = models.CharField(max_length=100, verbose_name='Conta Bancária', blank=True, null=True)
    data_recebimento = models.DateField(verbose_name='Data de Recebimento', null=True, blank=True)
    carga = models.ForeignKey(Carga, on_delete=models.PROTECT, verbose_name='Tipo de Carga')
    valor_unitario = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Valor Unitário')
    valor_total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Valor Total')
    origem = models.CharField(max_length=100, verbose_name='Origem')
    destino = models.CharField(max_length=100, verbose_name='Destino')
    cliente = models.ForeignKey(Contato, on_delete=models.PROTECT, verbose_name='Cliente', limit_choices_to={'tipo': 'CLIENTE'}, related_name='fretes_como_cliente')
    nota_fiscal = models.CharField(max_length=50, verbose_name='Nota Fiscal')
    ticket = models.CharField(max_length=50, verbose_name='Ticket')
    comissao_motorista = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='Comissão do Motorista (%)')
    valor_comissao_motorista = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Valor da Comissão do Motorista', default=0)
    observacoes = models.TextField(verbose_name='Observações', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    valor_acrescimo = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Valor de Acréscimo', default=0)
    valor_desconto = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Valor de Desconto', default=0)
    status = models.CharField(max_length=20, verbose_name='Status', default='PENDENTE')
    status_andamento = models.CharField(max_length=20, verbose_name='Status de Andamento', choices=STATUS_ANDAMENTO_CHOICES, default='EM_ANDAMENTO')

    class Meta:
        verbose_name = 'Frete'
        verbose_name_plural = 'Fretes'
        ordering = ['-data_saida']

    def __str__(self):
        return f'Frete {self.id} - {self.cliente} - {self.data_saida}'

    @property
    def km_total(self):
        """Calcula o total de quilômetros percorridos."""
        if self.km_chegada and self.km_saida:
            return self.km_chegada - self.km_saida
        return 0
        
    @property
    def valor_por_km(self):
        """Calcula o valor por quilômetro percorrido."""
        km = self.km_total
        if km and km > 0:
            return self.valor_total / km
        return 0

    def save(self, *args, **kwargs):
        logger.info('Salvando frete...')
        logger.info(f'Peso da carga: {self.peso_carga}')
        logger.info(f'Valor unitário: {self.valor_unitario}')
        logger.info(f'Fator de multiplicação: {self.carga.fator_multiplicacao}')
        
        # Calcula o valor total antes de salvar
        if self.peso_carga and self.carga and self.valor_unitario:
            quantidade_unidades = float(self.peso_carga) / float(self.carga.fator_multiplicacao)
            valor_total_calculado = quantidade_unidades * float(self.valor_unitario)
            self.valor_total = valor_total_calculado + float(self.valor_acrescimo) - float(self.valor_desconto)
            logger.info(f'Valor total calculado: {self.valor_total}')
            
            # Calcula o valor da comissão do motorista
            self.valor_comissao_motorista = float(self.valor_total) * (float(self.comissao_motorista) / 100)
            logger.info(f'Valor da comissão do motorista calculado: {self.valor_comissao_motorista}')

        # Atualiza o status com base na data de recebimento
        if self.data_recebimento:
            self.status = 'PAGO'
        else:
            hoje = timezone.now().date()
            if isinstance(self.data_saida, str):
                from datetime import datetime
                self.data_saida = datetime.strptime(self.data_saida, '%Y-%m-%d').date()
            
            if self.data_saida < hoje:
                self.status = 'VENCIDO'
            elif self.data_saida == hoje:
                self.status = 'VENCE_HOJE'
            else:
                self.status = 'PENDENTE'

        logger.info(f'Status do frete: {self.status}')
        super().save(*args, **kwargs)
        logger.info('Frete salvo com sucesso!')