from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_remove_abastecimento_frete_atual_and_more'),
    ]

    operations = [
        migrations.DeleteModel(
            name='EstimativaPneus',
        ),
        migrations.CreateModel(
            name='EstimativaPneus',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data_estimativa', models.DateField(default=django.utils.timezone.now)),
                ('qtd_pneus_dianteiros', models.PositiveIntegerField(default=2)),
                ('qtd_pneus_traseiros', models.PositiveIntegerField(default=8)),
                ('qtd_pneus_carreta', models.PositiveIntegerField(default=12)),
                ('preco_pneu_dianteiro', models.DecimalField(decimal_places=2, max_digits=10)),
                ('preco_pneu_traseiro', models.DecimalField(decimal_places=2, max_digits=10)),
                ('preco_pneu_carreta', models.DecimalField(decimal_places=2, max_digits=10)),
                ('km_vida_util_dianteiro', models.PositiveIntegerField(help_text='Quilometragem estimada para pneus dianteiros')),
                ('km_vida_util_traseiro', models.PositiveIntegerField(help_text='Quilometragem estimada para pneus traseiros')),
                ('km_vida_util_carreta', models.PositiveIntegerField(help_text='Quilometragem estimada para pneus da carreta')),
                ('custo_recapagem_dianteiro', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('custo_recapagem_traseiro', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('custo_recapagem_carreta', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('num_recapagens_dianteiro', models.PositiveIntegerField(default=1)),
                ('num_recapagens_traseiro', models.PositiveIntegerField(default=2)),
                ('num_recapagens_carreta', models.PositiveIntegerField(default=2)),
                ('conjunto', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='estimativas_pneus', to='core.conjunto')),
            ],
            options={
                'verbose_name': 'Estimativa de Pneus',
                'verbose_name_plural': 'Estimativas de Pneus',
            },
        ),
    ]