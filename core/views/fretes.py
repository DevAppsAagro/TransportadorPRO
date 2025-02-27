from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from decimal import Decimal
import logging
from ..models.frete import Frete
from ..models.caminhao import Caminhao
from ..models.contato import Contato
from ..models.carga import Carga
from django.utils import timezone

logger = logging.getLogger(__name__)

@login_required
def fretes(request):
    fretes_list = Frete.objects.all().order_by('-data_saida')
    
    # Calculate metrics that were previously in template filters
    fretes_concluidos = sum(1 for frete in fretes_list if frete.data_chegada)
    fretes_em_andamento = sum(1 for frete in fretes_list if not frete.data_chegada)
    valor_total = sum(frete.valor_total or 0 for frete in fretes_list)
    
    context = {
        'fretes': fretes_list,
        'fretes_concluidos': fretes_concluidos,
        'fretes_em_andamento': fretes_em_andamento,
        'valor_total': valor_total
    }
    
    return render(request, 'core/fretes/fretes.html', context)

@login_required
def frete_detalhes(request, pk):
    frete = get_object_or_404(Frete, pk=pk)
    
    # Buscar despesas relacionadas a este frete
    from ..models.despesa import Despesa
    despesas = Despesa.objects.filter(frete=frete).order_by('data_vencimento')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        data = {
            'id': frete.id,
            'data': frete.data_saida.strftime('%Y-%m-%d') if frete.data_saida else '',
            'origem': frete.origem,
            'destino': frete.destino,
            'valor': float(frete.valor_total),
            'status': frete.status,
            'observacoes': frete.observacoes or ''
        }
        return JsonResponse(data)
    
    context = {
        'frete': frete,
        'despesas': despesas
    }
    
    return render(request, 'core/fretes/frete_detalhes.html', context)

@login_required
def frete_novo(request):
    if request.method == 'POST':
        try:
            logger.info('='*50)
            logger.info('INICIANDO CADASTRO DE NOVO FRETE')
            logger.info('='*50)
            
            # Log dos dados recebidos
            logger.info('DADOS RECEBIDOS DO FORMULÁRIO:')
            for key, value in request.POST.items():
                logger.info(f'{key}: {value}')
            
            # Buscar objetos relacionados
            logger.info('\nBUSCANDO OBJETOS RELACIONADOS:')
            caminhao = Caminhao.objects.get(id=request.POST.get('caminhao'))
            logger.info(f'Caminhão encontrado: {caminhao}')
            
            motorista = Contato.objects.get(id=request.POST.get('motorista'))
            logger.info(f'Motorista encontrado: {motorista}')
            
            cliente = Contato.objects.get(id=request.POST.get('cliente'))
            logger.info(f'Cliente encontrado: {cliente}')
            
            carga = Carga.objects.get(id=request.POST.get('carga'))
            logger.info(f'Carga encontrada: {carga}')
            
            # Log dos valores numéricos
            logger.info('\nPROCESSANDO VALORES NUMÉRICOS:')
            peso_carga = request.POST.get('peso_carga', '0')
            valor_unitario = request.POST.get('valor_unitario', '0')
            valor_total = request.POST.get('valor_total', '0')
            comissao_motorista = request.POST.get('comissao_motorista', '0')
            
            logger.info(f'Peso da carga (bruto): {peso_carga}')
            logger.info(f'Valor unitário (bruto): {valor_unitario}')
            logger.info(f'Valor total (bruto): {valor_total}')
            logger.info(f'Comissão do motorista (bruto): {comissao_motorista}')
            
            # Converter valores para Decimal
            peso_carga = Decimal(peso_carga.replace(',', '.') if peso_carga else '0')
            valor_unitario = Decimal(valor_unitario.replace(',', '.') if valor_unitario else '0')
            valor_total = Decimal(valor_total.replace(',', '.') if valor_total else '0')
            comissao_motorista = Decimal(comissao_motorista.replace(',', '.') if comissao_motorista else '0')
            
            logger.info('\nVALORES CONVERTIDOS PARA DECIMAL:')
            logger.info(f'Peso da carga: {peso_carga}')
            logger.info(f'Valor unitário: {valor_unitario}')
            logger.info(f'Valor total: {valor_total}')
            logger.info(f'Comissão do motorista: {comissao_motorista}')
            
            # Calcular valor total se não foi fornecido
            if valor_total == 0:
                logger.info('\nCALCULANDO VALOR TOTAL:')
                logger.info(f'Fator de multiplicação da carga: {carga.fator_multiplicacao}')
                quantidade_unidades = peso_carga / carga.fator_multiplicacao
                logger.info(f'Quantidade de unidades calculada: {quantidade_unidades}')
                valor_total = quantidade_unidades * valor_unitario
                logger.info(f'Valor total calculado: {valor_total}')
            
            logger.info('\nCRIANDO OBJETO FRETE COM OS SEGUINTES VALORES:')
            frete = Frete(
                caminhao=caminhao,
                motorista=motorista,
                data_saida=request.POST.get('data_saida'),
                peso_carga=peso_carga,
                km_saida=request.POST.get('km_saida'),
                conta_bancaria=request.POST.get('conta_bancaria'),
                data_recebimento=request.POST.get('data_recebimento') or None,
                carga=carga,
                valor_unitario=valor_unitario,
                valor_total=valor_total,
                origem=request.POST.get('origem'),
                destino=request.POST.get('destino'),
                cliente=cliente,
                nota_fiscal=request.POST.get('nota_fiscal'),
                ticket=request.POST.get('ticket'),
                comissao_motorista=comissao_motorista,
                observacoes=request.POST.get('observacoes'),
                data_chegada=request.POST.get('data_chegada') or None,
                km_chegada=request.POST.get('km_chegada') or None,
                valor_acrescimo=Decimal(request.POST.get('valor_acrescimo', '0').replace(',', '.')),
                valor_desconto=Decimal(request.POST.get('valor_desconto', '0').replace(',', '.'))
            )
            
            logger.info('\nSALVANDO FRETE NO BANCO DE DADOS...')
            frete.save()
            logger.info('FRETE SALVO COM SUCESSO!')
            logger.info('='*50)
            
            messages.success(request, 'Frete cadastrado com sucesso!')
            return redirect('core:fretes')
        except Exception as e:
            logger.error('='*50)
            logger.error('ERRO AO CADASTRAR FRETE:')
            logger.error(str(e))
            logger.error('='*50)
            messages.error(request, f'Erro ao cadastrar frete: {str(e)}')
    
    caminhoes = Caminhao.objects.all()
    motoristas = Contato.objects.filter(tipo='MOTORISTA')
    clientes = Contato.objects.filter(tipo='CLIENTE')
    cargas = Carga.objects.all()
    return render(request, 'core/fretes/frete_form.html', {
        'caminhoes': caminhoes,
        'motoristas': motoristas,
        'clientes': clientes,
        'cargas': cargas,
        'titulo': 'Novo Frete'
    })

@login_required
def frete_editar(request, pk):
    frete = get_object_or_404(Frete, pk=pk)
    
    if request.method == 'POST':
        try:
            logger.info('Iniciando edição de frete')
            
            # Log dos dados recebidos
            logger.info(f'Dados do POST: {request.POST}')
            
            # Buscar objetos relacionados
            caminhao = Caminhao.objects.get(id=request.POST.get('caminhao'))
            motorista = Contato.objects.get(id=request.POST.get('motorista'))
            cliente = Contato.objects.get(id=request.POST.get('cliente'))
            carga = Carga.objects.get(id=request.POST.get('carga'))
            
            # Log dos valores numéricos
            peso_carga = request.POST.get('peso_carga', '0')
            valor_unitario = request.POST.get('valor_unitario', '0')
            valor_total = request.POST.get('valor_total', '0')
            comissao_motorista = request.POST.get('comissao_motorista', '0')
            
            logger.info(f'Peso da carga: {peso_carga}')
            logger.info(f'Valor unitário: {valor_unitario}')
            logger.info(f'Valor total: {valor_total}')
            logger.info(f'Comissão do motorista: {comissao_motorista}')
            
            # Converter valores para Decimal
            peso_carga = Decimal(peso_carga.replace(',', '.') if peso_carga else '0')
            valor_unitario = Decimal(valor_unitario.replace(',', '.') if valor_unitario else '0')
            valor_total = Decimal(valor_total.replace(',', '.') if valor_total else '0')
            comissao_motorista = Decimal(comissao_motorista.replace(',', '.') if comissao_motorista else '0')
            
            # Calcular valor total se não foi fornecido
            if valor_total == 0:
                quantidade_unidades = peso_carga / carga.fator_multiplicacao
                valor_total = quantidade_unidades * valor_unitario
                logger.info(f'Valor total calculado: {valor_total}')
            
            frete.caminhao = caminhao
            frete.motorista = motorista
            frete.data_saida = request.POST.get('data_saida')
            frete.peso_carga = peso_carga
            frete.km_saida = request.POST.get('km_saida')
            frete.conta_bancaria = request.POST.get('conta_bancaria')
            frete.data_recebimento = request.POST.get('data_recebimento') or None
            frete.carga = carga
            frete.valor_unitario = valor_unitario
            frete.valor_total = valor_total
            frete.origem = request.POST.get('origem')
            frete.destino = request.POST.get('destino')
            frete.cliente = cliente
            frete.nota_fiscal = request.POST.get('nota_fiscal')
            frete.ticket = request.POST.get('ticket')
            frete.comissao_motorista = comissao_motorista
            frete.observacoes = request.POST.get('observacoes')
            frete.data_chegada = request.POST.get('data_chegada') or None
            frete.km_chegada = request.POST.get('km_chegada') or None
            frete.valor_acrescimo = Decimal(request.POST.get('valor_acrescimo', '0').replace(',', '.'))
            frete.valor_desconto = Decimal(request.POST.get('valor_desconto', '0').replace(',', '.'))
            
            logger.info('Salvando frete...')
            frete.save()
            logger.info('Frete salvo com sucesso!')
            
            messages.success(request, 'Frete atualizado com sucesso!')
            return redirect('core:fretes')
        except Exception as e:
            logger.error(f'Erro ao atualizar frete: {str(e)}')
            messages.error(request, f'Erro ao atualizar frete: {str(e)}')
    
    caminhoes = Caminhao.objects.all()
    motoristas = Contato.objects.filter(tipo='MOTORISTA')
    clientes = Contato.objects.filter(tipo='CLIENTE')
    cargas = Carga.objects.all()
    return render(request, 'core/fretes/frete_form.html', {
        'frete': frete,
        'caminhoes': caminhoes,
        'motoristas': motoristas,
        'clientes': clientes,
        'cargas': cargas,
        'titulo': 'Editar Frete'
    })

@login_required
def frete_excluir(request, pk):
    frete = get_object_or_404(Frete, pk=pk)
    try:
        logger.info('Excluindo frete...')
        frete.delete()
        logger.info('Frete excluído com sucesso!')
        messages.success(request, 'Frete excluído com sucesso!')
    except Exception as e:
        logger.error(f'Erro ao excluir frete: {str(e)}')
        messages.error(request, f'Erro ao excluir frete: {str(e)}')
    return redirect('core:fretes')

@login_required
def frete_receber(request, pk):
    frete = get_object_or_404(Frete, pk=pk)
    if request.method == 'POST':
        try:
            logger.info('Registrando recebimento de frete...')
            frete.data_recebimento = request.POST.get('data_recebimento')
            frete.valor_acrescimo = Decimal(request.POST.get('valor_acrescimo', '0').replace(',', '.'))
            frete.valor_desconto = Decimal(request.POST.get('valor_desconto', '0').replace(',', '.'))
            frete.save()
            logger.info('Recebimento registrado com sucesso!')
            messages.success(request, 'Recebimento registrado com sucesso!')
        except Exception as e:
            logger.error(f'Erro ao registrar recebimento: {str(e)}')
            messages.error(request, f'Erro ao registrar recebimento: {str(e)}')
    return redirect('core:frete_detalhes', pk=pk)