from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_frete'),
    ]

    operations = [
        migrations.AddField(
            model_name='frete',
            name='valor_comissao_motorista',
            field=models.DecimalField(
                max_digits=10,
                decimal_places=2,
                verbose_name='Valor da Comissão do Motorista',
                default=0
            ),
        ),
    ]