# Generated by Django 5.0 on 2025-02-27 04:56

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0016_alter_contato_bairro_alter_contato_cep_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='EstimativaManutencao',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data_estimativa', models.DateField(default=django.utils.timezone.now)),
                ('custo_total_km', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('conjunto', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='estimativas_manutencao', to='core.conjunto')),
            ],
            options={
                'verbose_name': 'Estimativa de Manutenção',
                'verbose_name_plural': 'Estimativas de Manutenção',
                'ordering': ['-data_estimativa'],
            },
        ),
        migrations.CreateModel(
            name='ItemManutencao',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('descricao', models.CharField(max_length=255)),
                ('duracao_km', models.PositiveIntegerField(help_text='Quilometragem estimada para duração desta manutenção')),
                ('custo_total', models.DecimalField(decimal_places=2, max_digits=10)),
                ('custo_por_km', models.DecimalField(blank=True, decimal_places=4, max_digits=10, null=True)),
                ('estimativa', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='itens_manutencao', to='core.estimativamanutencao')),
            ],
            options={
                'verbose_name': 'Item de Manutenção',
                'verbose_name_plural': 'Itens de Manutenção',
            },
        ),
    ]
