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
from django.contrib.auth.models import User
from django.db.models import Sum, Count, Q, DecimalField, Case, When, Value
from django.db.models.functions import Coalesce

logger = logging.getLogger(__name__)

@login_required
def fretes(request):
    # Verificar se há um filtro de status na URL
    status_filter = request.GET.get('status', None)
    
    # Filtrar fretes pelo usuário logado através do caminhão e pré-carregar relações
    fretes_query = Frete.objects.filter(caminhao__usuario=request.user).select_related(
        'caminhao', 'motorista', 'motorista_user', 'cliente', 'carga'
    )
    
    # Aplicar filtro de status se existir
    if status_filter:
        fretes_query = fretes_query.filter(status=status_filter)
    
    # Ordenar por data de saída (mais recentes primeiro)
    fretes_list = fretes_query.order_by('-data_saida')
    
    # Calculate metrics using more efficient methods
    from django.db.models import Sum, Count, Q, DecimalField, Case, When, Value
    from django.db.models.functions import Coalesce
    
    # Get counts and sums directly from the database
    metrics = {
        'fretes_concluidos': Frete.objects.filter(caminhao__usuario=request.user, status_andamento='FINALIZADO').count(),
        'fretes_em_andamento': Frete.objects.filter(caminhao__usuario=request.user, status_andamento='EM_ANDAMENTO').count(),
        'valor_total': Frete.objects.filter(caminhao__usuario=request.user).aggregate(
            total=Coalesce(Sum('valor_total'), Value(0), output_field=DecimalField(max_digits=10, decimal_places=2))
        )['total'],
        'valor_recebido': Frete.objects.filter(caminhao__usuario=request.user, status='PAGO').aggregate(
            total=Coalesce(Sum('valor_total'), Value(0), output_field=DecimalField(max_digits=10, decimal_places=2))
        )['total'],
        'valor_a_receber': Frete.objects.filter(caminhao__usuario=request.user, status='PENDENTE').aggregate(
            total=Coalesce(Sum('valor_total'), Value(0), output_field=DecimalField(max_digits=10, decimal_places=2))
        )['total'],
        'valor_vencido': Frete.objects.filter(caminhao__usuario=request.user, status='VENCIDO').aggregate(
            total=Coalesce(Sum('valor_total'), Value(0), output_field=DecimalField(max_digits=10, decimal_places=2))
        )['total'],
        'valor_vence_hoje': Frete.objects.filter(caminhao__usuario=request.user, status='VENCE_HOJE').aggregate(
            total=Coalesce(Sum('valor_total'), Value(0), output_field=DecimalField(max_digits=10, decimal_places=2))
        )['total']
    }
    
    # Adicionar contadores por status para os novos cards
    status_counts = {
        'contador_pendente': Frete.objects.filter(caminhao__usuario=request.user, status='PENDENTE').count(),
        'contador_vence_hoje': Frete.objects.filter(caminhao__usuario=request.user, status='VENCE_HOJE').count(),
        'contador_vencido': Frete.objects.filter(caminhao__usuario=request.user, status='VENCIDO').count(),
        'contador_pago': Frete.objects.filter(caminhao__usuario=request.user, status='PAGO').count(),
    }
    
    context = {
        'fretes': fretes_list,
        'fretes_concluidos': metrics['fretes_concluidos'],
        'fretes_em_andamento': metrics['fretes_em_andamento'],
        'valor_total': metrics['valor_total'],
        'valor_recebido': metrics['valor_recebido'],
        'valor_a_receber': metrics['valor_a_receber'],
        'valor_vencido': metrics['valor_vencido'],
        'valor_vence_hoje': metrics['valor_vence_hoje'],
        # Adicionar totais para os novos cards
        'total_pendente': metrics['valor_a_receber'],
        'total_vence_hoje': metrics['valor_vence_hoje'],
        'total_vencido': metrics['valor_vencido'],
        'total_pago': metrics['valor_recebido'],
        # Adicionar contadores para os novos cards
        'contador_pendente': status_counts['contador_pendente'],
        'contador_vence_hoje': status_counts['contador_vence_hoje'],
        'contador_vencido': status_counts['contador_vencido'],
        'contador_pago': status_counts['contador_pago'],
        # Adicionar o status de filtro atual para destacar o botão correto
        'status_filter': status_filter
    }
    
    return render(request, 'core/fretes/fretes.html', context)

@login_required
def frete_detalhes(request, id):
    # Garantir que o usuário só possa ver seus próprios fretes
    frete = get_object_or_404(Frete, pk=id, caminhao__usuario=request.user)
    
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
def registrar_recebimento_frete(request, id):
    """Registra o recebimento do frete e atualiza seu status para 'PAGO'."""
    # Garantir que o usuário só possa atualizar seus próprios fretes
    frete = get_object_or_404(Frete, pk=id, caminhao__usuario=request.user)
    
    if request.method == 'POST':
        data_recebimento = request.POST.get('data_recebimento')
        
        if data_recebimento:
            from datetime import datetime
            # Converter a string de data para objeto date
            data_recebimento = datetime.strptime(data_recebimento, '%Y-%m-%d').date()
            
            # Atualizar o frete
            frete.data_recebimento = data_recebimento
            frete.status = 'PAGO'
            frete.save()
            
            messages.success(request, 'Recebimento do frete registrado com sucesso!')
        else:
            messages.error(request, 'Data de recebimento inválida.')
    
    return redirect('core:frete_detalhes', id=id)

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
            
            # Se o motorista_user foi selecionado, usá-lo; caso contrário, usar o motorista (contato)
            motorista_user_id = request.POST.get('motorista_user')
            motorista_id = request.POST.get('motorista')
            
            motorista = None
            motorista_user = None
            
            if motorista_user_id and motorista_user_id != '':
                motorista_user = User.objects.get(id=motorista_user_id)
                logger.info(f'Motorista (usuário) encontrado: {motorista_user}')
            elif motorista_id and motorista_id != '':
                motorista = Contato.objects.get(id=motorista_id)
                logger.info(f'Motorista (contato) encontrado: {motorista}')
            else:
                logger.error('Nenhum motorista selecionado!')
                raise ValueError('É necessário selecionar um motorista.')
            
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
                motorista_user=motorista_user,
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
    
    # Filtrar opções apenas do usuário atual
    caminhoes = Caminhao.objects.filter(usuario=request.user)
    motoristas = Contato.objects.filter(tipo='MOTORISTA', usuario=request.user)
    # Buscar apenas motoristas que são usuários criados pelo usuário atual
    motoristas_users = User.objects.filter(
        perfil__tipo_usuario='MOTORISTA',
        perfil__criado_por=request.user
    )
    clientes = Contato.objects.filter(tipo='CLIENTE', usuario=request.user)
    cargas = Carga.objects.filter(usuario=request.user)
    
    return render(request, 'core/fretes/frete_form.html', {
        'caminhoes': caminhoes,
        'motoristas': motoristas,
        'motoristas_users': motoristas_users,
        'clientes': clientes,
        'cargas': cargas,
        'titulo': 'Novo Frete'
    })

@login_required
def frete_editar(request, id):
    # Garantir que o usuário só possa editar seus próprios fretes
    frete = get_object_or_404(Frete, pk=id, caminhao__usuario=request.user)
    
    if request.method == 'POST':
        try:
            logger.info('Iniciando edição de frete')
            
            # Log dos dados recebidos
            logger.info(f'Dados do POST: {request.POST}')
            
            # Buscar objetos relacionados
            logger.info('\nBUSCANDO OBJETOS RELACIONADOS:')
            caminhao = Caminhao.objects.get(id=request.POST.get('caminhao'))
            
            # Se o motorista_user foi selecionado, usá-lo; caso contrário, usar o motorista (contato)
            motorista_user_id = request.POST.get('motorista_user')
            motorista_id = request.POST.get('motorista')
            
            motorista = None
            motorista_user = None
            
            if motorista_user_id and motorista_user_id != '':
                motorista_user = User.objects.get(id=motorista_user_id)
                logger.info(f'Motorista (usuário) encontrado: {motorista_user}')
            elif motorista_id and motorista_id != '':
                motorista = Contato.objects.get(id=motorista_id)
                logger.info(f'Motorista (contato) encontrado: {motorista}')
            else:
                logger.error('Nenhum motorista selecionado!')
                raise ValueError('É necessário selecionar um motorista.')
            
            cliente = Contato.objects.get(id=request.POST.get('cliente'))
            logger.info(f'Cliente encontrado: {cliente}')
            
            carga = Carga.objects.get(id=request.POST.get('carga'))
            logger.info(f'Carga encontrada: {carga}')
            
            # Log dos valores numéricos
            logger.info('\nPROCESSANDO VALORES NUMÉRICOS:')
            peso_carga = request.POST.get('peso_carga', '')
            valor_unitario = request.POST.get('valor_unitario', '')
            valor_total = request.POST.get('valor_total', '')
            comissao_motorista = request.POST.get('comissao_motorista', '')
            
            logger.info(f'Peso da carga: {peso_carga}')
            logger.info(f'Valor unitário: {valor_unitario}')
            logger.info(f'Valor total: {valor_total}')
            logger.info(f'Comissão do motorista: {comissao_motorista}')
            
            # Verificar se os campos estão vazios e manter os valores originais se estiverem
            if not peso_carga.strip():
                peso_carga = str(frete.peso_carga)
                logger.info(f'Usando valor original para peso da carga: {peso_carga}')
            
            if not valor_unitario.strip():
                valor_unitario = str(frete.valor_unitario)
                logger.info(f'Usando valor original para valor unitário: {valor_unitario}')
            
            if not valor_total.strip():
                valor_total = str(frete.valor_total)
                logger.info(f'Usando valor original para valor total: {valor_total}')
            
            if not comissao_motorista.strip():
                comissao_motorista = str(frete.comissao_motorista)
                logger.info(f'Usando valor original para comissão do motorista: {comissao_motorista}')
            
            # Converter valores para Decimal
            peso_carga = Decimal(peso_carga.replace(',', '.'))
            valor_unitario = Decimal(valor_unitario.replace(',', '.'))
            valor_total = Decimal(valor_total.replace(',', '.'))
            comissao_motorista = Decimal(comissao_motorista.replace(',', '.'))
            
            # Calcular valor total se não foi fornecido
            if valor_total == 0:
                quantidade_unidades = peso_carga / carga.fator_multiplicacao
                valor_total = quantidade_unidades * valor_unitario
                logger.info(f'Valor total calculado: {valor_total}')
            
            # Atualizar o objeto frete
            frete.caminhao = caminhao
            frete.motorista = motorista
            frete.motorista_user = motorista_user
            frete.data_saida = request.POST.get('data_saida')
            frete.peso_carga = peso_carga
            frete.km_saida = request.POST.get('km_saida')
            frete.conta_bancaria = request.POST.get('conta_bancaria')
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
            
            # Calcular valor da comissão do motorista
            frete.valor_comissao_motorista = (frete.valor_total * frete.comissao_motorista) / 100
            
            # Verificar se há data de chegada e Km de chegada
            if request.POST.get('data_chegada'):
                frete.data_chegada = request.POST.get('data_chegada')
                frete.km_chegada = request.POST.get('km_chegada')
            
            # Verificar se há data de recebimento
            if request.POST.get('data_recebimento'):
                frete.data_recebimento = request.POST.get('data_recebimento')
            else:
                frete.data_recebimento = None
            
            frete.save()
            messages.success(request, 'Frete atualizado com sucesso!')
            return redirect('core:fretes')
        except Exception as e:
            logger.error(f'Erro ao atualizar frete: {str(e)}')
            messages.error(request, f'Erro ao atualizar frete: {str(e)}')
    
    # Filtrar opções apenas do usuário atual
    caminhoes = Caminhao.objects.filter(usuario=request.user)
    motoristas = Contato.objects.filter(tipo='MOTORISTA', usuario=request.user)
    # Buscar apenas motoristas que são usuários criados pelo usuário atual
    motoristas_users = User.objects.filter(
        perfil__tipo_usuario='MOTORISTA',
        perfil__criado_por=request.user
    )
    clientes = Contato.objects.filter(tipo='CLIENTE', usuario=request.user)
    cargas = Carga.objects.filter(usuario=request.user)
    
    return render(request, 'core/fretes/frete_form.html', {
        'frete': frete,
        'caminhoes': caminhoes,
        'motoristas': motoristas,
        'motoristas_users': motoristas_users,
        'clientes': clientes,
        'cargas': cargas,
        'titulo': 'Editar Frete'
    })

@login_required
def alterar_status_frete(request, id):
    # Garantir que o usuário só possa alterar o status de seus próprios fretes
    frete = get_object_or_404(Frete, pk=id, caminhao__usuario=request.user)
    
    if request.method == 'POST':
        try:
            status_andamento = request.POST.get('status_andamento')
            
            # Validar o status
            if status_andamento not in ['EM_ANDAMENTO', 'FINALIZADO']:
                raise ValueError('Status inválido')
            
            # Atualizar o status
            frete.status_andamento = status_andamento
            frete.save()
            
            messages.success(request, 'Status do frete atualizado com sucesso!')
            return redirect('core:frete_detalhes', id=frete.id)
        except Exception as e:
            messages.error(request, f'Erro ao atualizar status do frete: {str(e)}')
            return redirect('core:frete_detalhes', id=frete.id)
    
    # Se não for POST, redirecionar para a página de detalhes
    return redirect('core:frete_detalhes', id=frete.id)

@login_required
def frete_excluir(request, id):
    # Garantir que o usuário só possa excluir seus próprios fretes
    frete = get_object_or_404(Frete, pk=id, caminhao__usuario=request.user)
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
def frete_receber(request, id):
    # Garantir que o usuário só possa receber seus próprios fretes
    frete = get_object_or_404(Frete, pk=id, caminhao__usuario=request.user)
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
    return redirect('core:frete_detalhes', id=id)

@login_required
def frete_print(request, id):
    """
    Versão de impressão dos detalhes do frete.
    """
    # Garantir que o usuário só possa ver seus próprios fretes
    frete = get_object_or_404(Frete, pk=id, caminhao__usuario=request.user)
    
    # Buscar despesas relacionadas a este frete
    from ..models.despesa import Despesa
    despesas = Despesa.objects.filter(frete=frete).order_by('data_vencimento')
    
    # Busca a empresa do usuário
    from ..models.empresa import Empresa
    empresa = Empresa.objects.filter(usuario=request.user).first()
    
    context = {
        'frete': frete,
        'despesas': despesas,
        'empresa': empresa,
    }
    
    return render(request, 'core/fretes/frete_print.html', context)