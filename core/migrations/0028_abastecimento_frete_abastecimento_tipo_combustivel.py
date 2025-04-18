# Generated by Django 5.0 on 2025-04-03 20:04

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0027_alter_frete_motorista'),
    ]

    operations = [
        migrations.AddField(
            model_name='abastecimento',
            name='frete',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.frete', verbose_name='Frete'),
        ),
        migrations.AddField(
            model_name='abastecimento',
            name='tipo_combustivel',
            field=models.CharField(choices=[('DIESEL_COMUM', 'Diesel Comum'), ('DIESEL_S10', 'Diesel S10'), ('GASOLINA', 'Gasolina'), ('ETANOL', 'Etanol'), ('GNV', 'GNV')], default='DIESEL_S10', max_length=20, verbose_name='Tipo de Combustível'),
        ),
    ]
