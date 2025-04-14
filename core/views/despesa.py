from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q
from datetime import date
import json
from decimal import Decimal, InvalidOperation

from core.models.despesa import Despesa
from core.models.categoria import Categoria
from core.models.subcategoria import Subcategoria
from core.models.caminhao import Caminhao
from core.models.carreta import Carreta
from core.models.frete import Frete
from core.models.empresa import Empresa
from core.models.contato import Contato

@login_required
def despesa_list(request):
    """Lista todas as despesas com filtros por status"""
    status_filter = request.GET.get('status', '')
    
    # Filtrar despesas pelo usuário logado através dos relacionamentos
    # Uma despesa pode estar relacionada a um caminhão, carreta, frete ou empresa
    # Todos esses modelos têm um campo 'usuario'
    despesas = Despesa.objects.filter(
        Q(caminhao__usuario=request.user) | 
        Q(carreta__usuario=request.user) | 
        Q(frete__caminhao__usuario=request.user) | 
        Q(empresa__usuario=request.user)
    ).distinct().order_by('-data_vencimento')
    
    # Preparar contadores e somatórios
    hoje = date.today()
    total_pendente = 0
    total_vence_hoje = 0
    total_vencido = 0
    total_pago = 0
    contador_pendente = 0
    contador_vence_hoje = 0
    contador_vencido = 0
    contador_pago = 0
    
    # Calcular totais para cada status
    todas_despesas = despesas
    for despesa in todas_despesas:
        if despesa.data_pagamento is None:
            if despesa.data_vencimento > hoje:
                # Pendente
                total_pendente += despesa.valor
                contador_pendente += 1
            elif despesa.data_vencimento == hoje:
                # Vence hoje
                total_vence_hoje += despesa.valor
                contador_vence_hoje += 1
            else:
                # Vencida
                total_vencido += despesa.valor
                contador_vencido += 1
        else:
            # Paga
            total_pago += despesa.valor
            contador_pago += 1
    
    # Aplicar filtros
    if status_filter:
        if status_filter == 'PENDENTE':
            despesas = despesas.filter(data_pagamento__isnull=True, data_vencimento__gt=hoje)
        elif status_filter == 'VENCE_HOJE':
            despesas = despesas.filter(data_pagamento__isnull=True, data_vencimento=hoje)
        elif status_filter == 'VENCIDA':
            despesas = despesas.filter(data_pagamento__isnull=True, data_vencimento__lt=hoje)
        elif status_filter == 'PAGA':
            despesas = despesas.filter(data_pagamento__isnull=False)
    
    # Adicionar status calculado para cada despesa
    for despesa in despesas:
        despesa.status_calculado = despesa.status
        despesa.status_display_calculado = despesa.status_display
    
    return render(request, 'core/despesa/lista.html', {
        'despesas': despesas,
        'status_filter': status_filter,
        'total_pendente': total_pendente,
        'total_vence_hoje': total_vence_hoje,
        'total_vencido': total_vencido,
        'total_pago': total_pago,
        'contador_pendente': contador_pendente,
        'contador_vence_hoje': contador_vence_hoje,
        'contador_vencido': contador_vencido,
        'contador_pago': contador_pago
    })

@login_required
def despesa_create(request):
    """Cria uma nova despesa"""
    # Carregar apenas categorias inicialmente - os outros dados serão carregados sob demanda
    categorias = Categoria.objects.filter(Q(usuario=request.user) | Q(usuario__isnull=True))
    # Incluir contatos do tipo FORNECEDOR e FUNCIONARIO
    contatos = Contato.objects.filter(usuario=request.user, tipo__in=['FORNECEDOR', 'FUNCIONARIO'])
    
    if request.method == 'POST':
        try:
            # Obter dados do formulário
            data = request.POST.get('data')
            data_vencimento = request.POST.get('data_vencimento')
            data_pagamento = request.POST.get('data_pagamento') or None
            valor = request.POST.get('valor')
            categoria_id = request.POST.get('categoria')
            subcategoria_id = request.POST.get('subcategoria')
            contato_id = request.POST.get('contato') or None
            observacoes = request.POST.get('observacoes', '')
            
            # Obter destino baseado na alocação da categoria
            categoria = Categoria.objects.get(id=categoria_id)
            alocacao = categoria.alocacao
            
            # Inicializar campos de destino
            caminhao_id = None
            carreta_id = None
            frete_id = None
            empresa_id = None
            
            if alocacao == 'VEICULO':
                # Verificar se o caminhão pertence ao usuário
                if request.POST.get('caminhao'):
                    caminhao = get_object_or_404(Caminhao, id=request.POST.get('caminhao'), usuario=request.user)
                    caminhao_id = caminhao.id
                # Verificar se a carreta pertence ao usuário
                if request.POST.get('carreta'):
                    carreta = get_object_or_404(Carreta, id=request.POST.get('carreta'), usuario=request.user)
                    carreta_id = carreta.id
            elif alocacao == 'FRETE':
                # Verificar se o frete pertence ao usuário
                if request.POST.get('frete'):
                    frete = get_object_or_404(Frete, id=request.POST.get('frete'), caminhao__usuario=request.user)
                    frete_id = frete.id
            elif alocacao == 'ADMINISTRATIVO':
                # Verificar se a empresa pertence ao usuário
                if request.POST.get('empresa'):
                    empresa = get_object_or_404(Empresa, id=request.POST.get('empresa'), usuario=request.user)
                    empresa_id = empresa.id
            
            # Criar despesa
            despesa = Despesa.objects.create(
                data=data,
                data_vencimento=data_vencimento,
                data_pagamento=data_pagamento,
                valor=valor,
                categoria_id=categoria_id,
                subcategoria_id=subcategoria_id,
                contato_id=contato_id,
                caminhao_id=caminhao_id,
                carreta_id=carreta_id,
                frete_id=frete_id,
                empresa_id=empresa_id,
                observacao=observacoes
            )
            
            messages.success(request, 'Despesa criada com sucesso!')
            return redirect('core:despesa_list')
        except Exception as e:
            messages.error(request, f'Erro ao criar despesa: {str(e)}')
    
    return render(request, 'core/despesa/form.html', {
        'categorias': categorias,
        'contatos': contatos,
        # Não enviar os dados inicialmente, apenas quando forem necessários
    })

@login_required
def despesa_edit(request, id):
    """Edita uma despesa existente"""
    # Garantir que a despesa pertence ao usuário
    despesa = get_object_or_404(
        Despesa,
        Q(pk=id) & (
            Q(caminhao__usuario=request.user) | 
            Q(carreta__usuario=request.user) | 
            Q(frete__caminhao__usuario=request.user) | 
            Q(empresa__usuario=request.user)
        )
    )
    
    # Carregar apenas dados essenciais
    categorias = Categoria.objects.filter(Q(usuario=request.user) | Q(usuario__isnull=True))
    # Incluir contatos do tipo FORNECEDOR e FUNCIONARIO
    contatos = Contato.objects.filter(usuario=request.user, tipo__in=['FORNECEDOR', 'FUNCIONARIO'])
    
    # Carregar dados relacionados apenas à alocação atual
    caminhoes = []
    carretas = []
    fretes = []
    empresas = []
    
    # Carregar dados específicos baseados na alocação
    if despesa.categoria.alocacao == 'VEICULO':
        caminhoes = Caminhao.objects.filter(usuario=request.user)
        carretas = Carreta.objects.filter(usuario=request.user)
    elif despesa.categoria.alocacao == 'FRETE':
        fretes = Frete.objects.filter(caminhao__usuario=request.user)
    elif despesa.categoria.alocacao == 'ADMINISTRATIVO':
        empresas = Empresa.objects.filter(usuario=request.user)
    
    if request.method == 'POST':
        try:
            # Obter dados do formulário
            despesa.data = request.POST.get('data')
            despesa.data_vencimento = request.POST.get('data_vencimento')
            despesa.data_pagamento = request.POST.get('data_pagamento') or None
            despesa.valor = request.POST.get('valor')
            despesa.categoria_id = request.POST.get('categoria')
            despesa.subcategoria_id = request.POST.get('subcategoria')
            despesa.contato_id = request.POST.get('contato') or None
            despesa.observacoes = request.POST.get('observacoes', '')
            
            # Obter destino baseado na alocação da categoria
            categoria = Categoria.objects.get(id=despesa.categoria_id)
            alocacao = categoria.alocacao
            
            # Limpar campos de destino anteriores
            despesa.caminhao = None
            despesa.carreta = None
            despesa.frete = None
            despesa.empresa = None
            
            if alocacao == 'VEICULO':
                if request.POST.get('caminhao'):
                    caminhao = get_object_or_404(Caminhao, id=request.POST.get('caminhao'), usuario=request.user)
                    despesa.caminhao = caminhao
                if request.POST.get('carreta'):
                    carreta = get_object_or_404(Carreta, id=request.POST.get('carreta'), usuario=request.user)
                    despesa.carreta = carreta
            elif alocacao == 'FRETE':
                if request.POST.get('frete'):
                    frete = get_object_or_404(Frete, id=request.POST.get('frete'), caminhao__usuario=request.user)
                    despesa.frete = frete
            elif alocacao == 'ADMINISTRATIVO':
                if request.POST.get('empresa'):
                    empresa = get_object_or_404(Empresa, id=request.POST.get('empresa'), usuario=request.user)
                    despesa.empresa = empresa
            
            despesa.save()
            messages.success(request, 'Despesa atualizada com sucesso!')
            return redirect('core:despesa_list')
        except Exception as e:
            messages.error(request, f'Erro ao atualizar despesa: {str(e)}')
    
    return render(request, 'core/despesa/form.html', {
        'despesa': despesa,
        'categorias': categorias,
        'contatos': contatos,
        'caminhoes': caminhoes,
        'carretas': carretas,
        'fretes': fretes,
        'empresas': empresas
    })

@login_required
def despesa_delete(request, id):
    """Exclui uma despesa"""
    # Garantir que a despesa pertence ao usuário
    despesa = get_object_or_404(
        Despesa, 
        Q(pk=id) & (
            Q(caminhao__usuario=request.user) | 
            Q(carreta__usuario=request.user) | 
            Q(frete__caminhao__usuario=request.user) | 
            Q(empresa__usuario=request.user)
        )
    )
    
    if request.method == 'POST':
        try:
            despesa.delete()
            messages.success(request, 'Despesa excluída com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao excluir despesa: {str(e)}')
        
        return redirect('core:despesa_list')
    
    return render(request, 'core/despesa/confirm_delete.html', {
        'despesa': despesa
    })

@login_required
def despesa_detail(request, id):
    """Exibe os detalhes de uma despesa"""
    # Garantir que a despesa pertence ao usuário
    despesa = get_object_or_404(
        Despesa,
        Q(pk=id) & (
            Q(caminhao__usuario=request.user) | 
            Q(carreta__usuario=request.user) | 
            Q(frete__caminhao__usuario=request.user) | 
            Q(empresa__usuario=request.user)
        )
    )
    
    return render(request, 'core/despesa/detail.html', {
        'despesa': despesa
    })

@login_required
def registrar_pagamento(request, id):
    """Registra o pagamento de uma despesa"""
    if request.method == 'POST':
        try:
            # Garantir que a despesa pertence ao usuário
            despesa = get_object_or_404(
                Despesa,
                Q(pk=id) & (
                    Q(caminhao__usuario=request.user) | 
                    Q(carreta__usuario=request.user) | 
                    Q(frete__caminhao__usuario=request.user) | 
                    Q(empresa__usuario=request.user)
                )
            )
            
            data_pagamento = request.POST.get('data_pagamento')
            novo_valor = request.POST.get('valor')
            
            if data_pagamento:
                despesa.data_pagamento = data_pagamento
                
                # Atualizar o valor se fornecido
                if novo_valor:
                    try:
                        despesa.valor = Decimal(novo_valor)
                    except (ValueError, InvalidOperation):
                        messages.warning(request, 'Valor inválido. O valor original foi mantido.')
                
                despesa.save()
                messages.success(request, 'Pagamento registrado com sucesso!')
            else:
                messages.error(request, 'Data de pagamento é obrigatória.')
            
            return redirect('core:despesa_detail', id=id)
            
        except Exception as e:
            messages.error(request, f'Erro ao registrar pagamento: {str(e)}')
            return redirect('core:despesa_detail', id=id)
    
    return redirect('core:despesa_list')

@login_required
def get_subcategorias(request):
    """Retorna as subcategorias de uma categoria em formato JSON"""
    categoria_id = request.GET.get('categoria_id')
    
    try:
        # Verificar se a categoria pertence ao usuário ou é padrão (usuário nulo)
        categoria = Categoria.objects.get(
            id=categoria_id,
            usuario__in=[request.user, None]  # Usuário atual ou valor nulo
        )
        
        subcategorias = Subcategoria.objects.filter(categoria_id=categoria_id).values('id', 'nome')
        return JsonResponse(list(subcategorias), safe=False)
    except Categoria.DoesNotExist:
        return JsonResponse([], safe=False)

@login_required
def get_destinos_por_alocacao(request):
    """Retorna os destinos específicos por tipo de alocação em formato JSON"""
    tipo = request.GET.get('tipo')
    response_data = []
    
    try:
        if tipo == 'caminhao':
            # Retornar caminhões do usuário
            caminhoes = Caminhao.objects.filter(usuario=request.user)
            response_data = [
                {
                    'id': caminhao.id,
                    'placa': caminhao.placa,
                    'marca': caminhao.marca,
                    'modelo': caminhao.modelo
                }
                for caminhao in caminhoes
            ]
        elif tipo == 'carreta':
            # Retornar carretas do usuário
            carretas = Carreta.objects.filter(usuario=request.user)
            response_data = [
                {
                    'id': carreta.id,
                    'placa': carreta.placa,
                    'marca': carreta.marca,
                    'modelo': carreta.modelo
                }
                for carreta in carretas
            ]
        elif tipo == 'frete':
            # Retornar fretes do usuário que estão em andamento
            fretes = Frete.objects.filter(caminhao__usuario=request.user, status_andamento='EM_ANDAMENTO')
            response_data = [
                {
                    'id': frete.id,
                    'cliente': frete.cliente.nome_completo if frete.cliente else 'Sem cliente',
                    'origem': frete.origem,
                    'destino': frete.destino,
                    'caminhao_placa': frete.caminhao.placa if frete.caminhao else None
                }
                for frete in fretes
            ]
        elif tipo == 'empresa':
            # Retornar empresas do usuário
            print(f"Buscando empresas para o usuário: {request.user.username} (ID: {request.user.id})")
            
            # Usar raw SQL para buscar diretamente na tabela core_empresa
            from django.db import connection
            
            empresas = []
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT id, razao_social, nome_fantasia, cnpj FROM core_empresa WHERE usuario_id = %s",
                    [request.user.id]
                )
                rows = cursor.fetchall()
                print(f"Consulta SQL retornou {len(rows)} empresas")
                
                for row in rows:
                    empresas.append({
                        'id': row[0],
                        'razao_social': row[1],
                        'nome': row[2] or row[1],  # Usa nome_fantasia ou razao_social se nome_fantasia for nulo
                        'cnpj': row[3]
                    })
                    print(f"Empresa encontrada via SQL: {row[1]} (ID: {row[0]})")
            
            # Se não encontrar empresas, buscar todas as empresas (temporariamente para debug)
            if not empresas:
                print("Nenhuma empresa encontrada para o usuário. Buscando todas as empresas...")
                cursor.execute("SELECT id, razao_social, nome_fantasia, cnpj, usuario_id FROM core_empresa")
                rows = cursor.fetchall()
                print(f"Total de empresas no sistema: {len(rows)}")
                for row in rows:
                    print(f"Empresa no sistema: {row[1]} (ID: {row[0]}, Usuário ID: {row[4]})")
            
            response_data = empresas
    except Exception as e:
        # Registrar o erro, mas retornar um array vazio para evitar erro no cliente
        print(f"Erro ao carregar destinos do tipo {tipo}: {str(e)}")
    
    return JsonResponse(response_data, safe=False)
