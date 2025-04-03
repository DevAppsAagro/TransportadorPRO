from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.db.models import Count

from ..models import AbastecimentoPendente, Abastecimento, Contato
from ..views.motoristas import is_admin


@login_required
@user_passes_test(is_admin)
def listar_abastecimentos_pendentes(request):
    """Lista todos os abastecimentos pendentes para aprovação"""
    # Filtrar por status se especificado
    status = request.GET.get('status', 'PENDENTE')
    
    if status and status in ['PENDENTE', 'APROVADO', 'REJEITADO', 'TODOS']:
        if status == 'TODOS':
            abastecimentos = AbastecimentoPendente.objects.filter(
                caminhao__usuario=request.user
            ).order_by('-data_solicitacao')
        else:
            abastecimentos = AbastecimentoPendente.objects.filter(
                caminhao__usuario=request.user,
                status=status
            ).order_by('-data_solicitacao')
    else:
        abastecimentos = AbastecimentoPendente.objects.filter(
            caminhao__usuario=request.user,
            status='PENDENTE'
        ).order_by('-data_solicitacao')
    
    # Filtrar por motorista se especificado
    motorista_id = request.GET.get('motorista')
    if motorista_id:
        abastecimentos = abastecimentos.filter(motorista_id=motorista_id)
    
    # Filtrar por caminhão se especificado
    caminhao_id = request.GET.get('caminhao')
    if caminhao_id:
        abastecimentos = abastecimentos.filter(caminhao_id=caminhao_id)
    
    # Filtrar por datas se especificado
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    if data_inicio and data_fim:
        abastecimentos = abastecimentos.filter(data__range=[data_inicio, data_fim])
    
    return render(request, 'core/abastecimentos_pendentes/lista.html', {
        'abastecimentos': abastecimentos,
        'status_selecionado': status
    })


@login_required
@user_passes_test(is_admin)
def detalhe_abastecimento_pendente(request, id):
    """Exibe os detalhes de um abastecimento pendente"""
    abastecimento = get_object_or_404(
        AbastecimentoPendente, 
        pk=id,
        caminhao__usuario=request.user
    )
    
    return render(request, 'core/abastecimentos_pendentes/detalhe.html', {
        'abastecimento': abastecimento
    })


@login_required
@user_passes_test(is_admin)
def aprovar_abastecimento(request, id):
    """Aprova um abastecimento pendente e cria o registro no sistema"""
    abastecimento_pendente = get_object_or_404(
        AbastecimentoPendente, 
        pk=id,
        caminhao__usuario=request.user,
        status='PENDENTE'
    )
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Extrair dados do formulário
                id_motorista = request.POST.get('motorista')
                situacao = request.POST.get('situacao')
                data_vencimento = request.POST.get('data_vencimento')
                data_pagamento = request.POST.get('data_pagamento', None)
                
                # Validar dados
                if not id_motorista or not situacao or not data_vencimento:
                    messages.error(request, 'Todos os campos obrigatórios devem ser preenchidos!')
                    return redirect('core:aprovar_abastecimento', id=id)
                
                # Obter objetos relacionados
                motorista = get_object_or_404(Contato, id=id_motorista, tipo='MOTORISTA')
                
                # Criar o abastecimento no sistema
                abastecimento = Abastecimento.objects.create(
                    caminhao=abastecimento_pendente.caminhao,
                    posto=abastecimento_pendente.posto,
                    data=abastecimento_pendente.data,
                    situacao=situacao,
                    tipo_combustivel=abastecimento_pendente.combustivel,  # Transferindo o tipo de combustível
                    litros=abastecimento_pendente.litros,
                    valor_litro=abastecimento_pendente.valor_litro,
                    motorista=motorista,
                    km_abastecimento=abastecimento_pendente.km_atual,
                    data_vencimento=data_vencimento,
                    data_pagamento=data_pagamento if data_pagamento else None,
                    frete=abastecimento_pendente.frete  # Transferindo o frete associado
                )
                
                # Atualizar o status do abastecimento pendente
                abastecimento_pendente.status = 'APROVADO'
                abastecimento_pendente.save()
                
                messages.success(request, 'Abastecimento aprovado com sucesso!')
                return redirect('core:listar_abastecimentos_pendentes')
                
        except Exception as e:
            messages.error(request, f'Erro ao aprovar abastecimento: {str(e)}')
    
    # Obter motoristas para o formulário de confirmação
    motoristas = Contato.objects.filter(tipo='MOTORISTA', usuario=request.user)
    
    return render(request, 'core/abastecimentos_pendentes/confirmar_aprovacao.html', {
        'abastecimento': abastecimento_pendente,
        'motoristas': motoristas
    })


@login_required
@user_passes_test(is_admin)
def rejeitar_abastecimento(request, id):
    """Rejeita um abastecimento pendente"""
    abastecimento_pendente = get_object_or_404(
        AbastecimentoPendente, 
        pk=id,
        caminhao__usuario=request.user,
        status='PENDENTE'
    )
    
    if request.method == 'POST':
        motivo_rejeicao = request.POST.get('motivo_rejeicao', '')
        
        try:
            # Atualizar o status e o motivo da rejeição
            abastecimento_pendente.status = 'REJEITADO'
            abastecimento_pendente.motivo_rejeicao = motivo_rejeicao
            abastecimento_pendente.save()
            
            messages.success(request, 'Abastecimento rejeitado com sucesso!')
            return redirect('core:listar_abastecimentos_pendentes')
            
        except Exception as e:
            messages.error(request, f'Erro ao rejeitar abastecimento: {str(e)}')
    
    return render(request, 'core/abastecimentos_pendentes/confirmar_rejeicao.html', {
        'abastecimento': abastecimento_pendente
    })


@login_required
@user_passes_test(is_admin)
def estatisticas_abastecimentos_pendentes(request):
    """Exibe estatísticas sobre os abastecimentos pendentes"""
    # Total por status
    pendentes = AbastecimentoPendente.objects.filter(
        caminhao__usuario=request.user,
        status='PENDENTE'
    ).count()
    
    aprovados = AbastecimentoPendente.objects.filter(
        caminhao__usuario=request.user,
        status='APROVADO'
    ).count()
    
    rejeitados = AbastecimentoPendente.objects.filter(
        caminhao__usuario=request.user,
        status='REJEITADO'
    ).count()
    
    # Total por caminhão
    total_por_caminhao = AbastecimentoPendente.objects.filter(
        caminhao__usuario=request.user
    ).values('caminhao__placa').annotate(total=Count('id')).order_by('-total')
    
    # Total por motorista
    total_por_motorista = AbastecimentoPendente.objects.filter(
        caminhao__usuario=request.user
    ).values('motorista__first_name', 'motorista__last_name').annotate(total=Count('id')).order_by('-total')
    
    return render(request, 'core/abastecimentos_pendentes/estatisticas.html', {
        'pendentes': pendentes,
        'aprovados': aprovados,
        'rejeitados': rejeitados,
        'total_por_caminhao': total_por_caminhao,
        'total_por_motorista': total_por_motorista
    })
