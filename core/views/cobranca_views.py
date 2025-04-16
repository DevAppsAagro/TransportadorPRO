from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

import json
import logging

from core.models.cobranca_config import AsaasConfig
from core.models.frete import Frete
from core.services.cobranca_service import CobrancaService

logger = logging.getLogger(__name__)

@login_required
def configurar_cobranca(request):
    """
    View para configurar a integração com o sistema de cobranças.
    Permite ao usuário configurar sua chave de API e outras configurações.
    Suporta criação automática de subcontas.
    """
    try:
        config = AsaasConfig.objects.get(usuario=request.user)
    except AsaasConfig.DoesNotExist:
        config = AsaasConfig(usuario=request.user)
    
    # Verificar se é uma requisição AJAX para criação automática de subconta
    if request.method == 'POST' and request.headers.get('Content-Type') == 'application/json':
        import json
        try:
            data = json.loads(request.body)
            if data.get('auto_create'):
                # Verificar se o usuário tem empresa cadastrada
                cobranca_service = CobrancaService(request.user)
                if not cobranca_service.usuario_tem_empresa_completa(request.user):
                    # Usuário não tem empresa cadastrada ou dados incompletos
                    return JsonResponse({
                        'success': False, 
                        'error': 'Dados da empresa incompletos', 
                        'redirect': '/configuracoes/empresa/'
                    })
                
                # A subconta já foi criada no __init__ do CobrancaService se os dados estiverem completos
                return JsonResponse({'success': True})
        except Exception as e:
            logger.error(f"Erro ao criar subconta automaticamente: {str(e)}")
            error_message = str(e)
            # Verifica se o erro é relacionado ao campo companyType
            if 'companyType' in error_message:
                error_message = 'Não foi possível criar a subconta automaticamente devido a restrições da API. Por favor, configure manualmente sua chave de API no sistema de cobranças ou entre em contato com o suporte.'
            
            return JsonResponse({
                'success': False, 
                'error': error_message,
                'manual_config': True
            })
    
    # Requisição normal de formulário
    elif request.method == 'POST':
        api_key = request.POST.get('api_key')
        is_sandbox = request.POST.get('is_sandbox') == 'on'
        
        config.api_key = api_key
        config.is_sandbox = is_sandbox
        config.save()
        
        messages.success(request, 'Configuração de cobranças salva com sucesso!')
        return redirect('core:configurar_cobranca')
    
    return render(request, 'core/configuracoes/cobrancas.html', {'config': config})

@login_required
def gerar_cobranca_frete(request, frete_id):
    """
    View para gerar uma cobrança para um frete.
    """
    frete = get_object_or_404(Frete, id=frete_id, caminhao__usuario=request.user)
    
    # Verificar se já existe cobrança
    if frete.asaas_cobranca_id:
        messages.warning(request, 'Este frete já possui uma cobrança gerada.')
        return redirect('core:frete_detalhes', id=frete.id)
    
    # Verificar se tem cliente associado
    if not frete.cliente:
        messages.error(request, 'Este frete não possui um cliente associado. Adicione um cliente antes de gerar a cobrança.')
        return redirect('core:frete_detalhes', id=frete.id)
    
    # Verificar se tem data de vencimento
    if not hasattr(frete, 'data_vencimento') or not frete.data_vencimento:
        # Usar data de chegada + 7 dias como data de vencimento
        if frete.data_chegada:
            data_vencimento = frete.data_chegada + timezone.timedelta(days=7)
        else:
            data_vencimento = timezone.now().date() + timezone.timedelta(days=7)
    else:
        data_vencimento = frete.data_vencimento
    
    try:
        # Verificar se o usuário tem configuração do sistema de cobranças
        try:
            cobranca_config = AsaasConfig.objects.get(usuario=request.user)
        except AsaasConfig.DoesNotExist:
            messages.error(request, 'Você precisa configurar sua integração com o sistema de cobranças antes de gerar cobranças.')
            return redirect('core:configurar_cobranca')
        
        # Inicializar serviço de cobranças
        cobranca_service = CobrancaService(request.user)
        
        # Criar cobrança
        resultado = cobranca_service.criar_cobranca(frete, data_vencimento)
        
        # Sucesso
        messages.success(request, 'Cobrança gerada com sucesso!')
        return redirect('core:frete_detalhes', id=frete.id)
    
    except Exception as e:
        messages.error(request, f'Erro ao gerar cobrança: {str(e)}')
        return redirect('core:frete_detalhes', id=frete.id)

@login_required
def atualizar_status_cobranca(request, frete_id):
    """
    View para atualizar o status de uma cobrança.
    """
    frete = get_object_or_404(Frete, id=frete_id, caminhao__usuario=request.user)
    
    if not frete.asaas_cobranca_id:
        messages.error(request, 'Este frete não possui uma cobrança para atualizar.')
        return redirect('core:frete_detalhes', id=frete.id)
    
    try:
        # Inicializar serviço de cobranças
        cobranca_service = CobrancaService(request.user)
        
        # Atualizar status
        sucesso = cobranca_service.atualizar_status_cobranca(frete)
        
        if sucesso:
            messages.success(request, f'Status da cobrança atualizado para: {frete.get_cobranca_status_display()}')
        else:
            messages.warning(request, 'Não foi possível atualizar o status da cobrança.')
        
        return redirect('core:frete_detalhes', id=frete.id)
    
    except Exception as e:
        messages.error(request, f'Erro ao atualizar status da cobrança: {str(e)}')
        return redirect('core:frete_detalhes', id=frete.id)

@login_required
def cancelar_cobranca(request, frete_id):
    """
    View para cancelar uma cobrança.
    """
    frete = get_object_or_404(Frete, id=frete_id, caminhao__usuario=request.user)
    
    if not frete.asaas_cobranca_id:
        messages.error(request, 'Este frete não possui uma cobrança para cancelar.')
        return redirect('core:frete_detalhes', id=frete.id)
    
    try:
        # Inicializar serviço de cobranças
        cobranca_service = CobrancaService(request.user)
        
        # Cancelar cobrança
        sucesso = cobranca_service.cancelar_cobranca(frete)
        
        if sucesso:
            messages.success(request, 'Cobrança cancelada com sucesso!')
        else:
            messages.warning(request, 'Não foi possível cancelar a cobrança.')
        
        return redirect('core:frete_detalhes', id=frete.id)
    
    except Exception as e:
        messages.error(request, f'Erro ao cancelar cobrança: {str(e)}')
        return redirect('core:frete_detalhes', id=frete.id)

@csrf_exempt
def webhook_cobranca(request):
    """
    Webhook para receber notificações do sistema de cobranças.
    Atualiza o status das cobranças quando há mudanças (pagamento, cancelamento, etc).
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido'}, status=405)
    
    # Verificar token de segurança (deve ser configurado no sistema de cobranças e no settings.py)
    token = request.headers.get('cobranca-access-token') or request.headers.get('asaas-access-token')
    if token != getattr(settings, 'COBRANCA_WEBHOOK_TOKEN', None):
        logger.warning(f"Tentativa de acesso ao webhook com token inválido: {token}")
        return JsonResponse({'error': 'Token inválido'}, status=403)
    
    try:
        # Processar payload
        payload = json.loads(request.body)
        event = payload.get('event')
        payment = payload.get('payment', {})
        payment_id = payment.get('id')
        
        logger.info(f"Webhook recebido: event={event}, payment_id={payment_id}")
        
        if not payment_id:
            return JsonResponse({'error': 'ID de pagamento não encontrado'}, status=400)
        
        # Buscar frete associado à cobrança
        try:
            frete = Frete.objects.get(asaas_cobranca_id=payment_id)
        except Frete.DoesNotExist:
            logger.warning(f"Cobrança {payment_id} não encontrada no sistema")
            return JsonResponse({'error': 'Cobrança não encontrada'}, status=404)
        
        # Atualizar status da cobrança
        frete.asaas_status = payment.get('status', 'PENDING')
        
        # Se foi pago, atualizar data de recebimento
        if payment.get('status') in ('RECEIVED', 'CONFIRMED'):
            if not frete.data_recebimento:
                frete.data_recebimento = timezone.now().date()
        
        frete.save()
        logger.info(f"Status da cobrança do frete {frete.id} atualizado para {frete.asaas_status}")
        
        return JsonResponse({'success': True})
    
    except Exception as e:
        logger.error(f"Erro ao processar webhook: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def listar_cobrancas(request):
    """
    View para listar todas as cobranças do usuário.
    """
    # Buscar fretes com cobranças
    fretes_com_cobranca = Frete.objects.filter(
        caminhao__usuario=request.user,
        asaas_cobranca_id__isnull=False
    ).order_by('-asaas_data_criacao')
    
    return render(request, 'core/cobrancas/listar.html', {
        'fretes': fretes_com_cobranca
    })
