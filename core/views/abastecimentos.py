from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from decimal import Decimal
from django.http import JsonResponse
from core.models.abastecimento import Abastecimento
from core.models.caminhao import Caminhao
from core.models.contato import Contato
from core.models.frete import Frete
from django.contrib.auth.models import User

@login_required
def abastecimentos(request):
    # Filtrar abastecimentos pelo usuário logado através do caminhão
    abastecimentos_list = Abastecimento.objects.filter(caminhao__usuario=request.user).order_by('-data')
    total_valor = abastecimentos_list.aggregate(total=Sum('total_valor'))['total'] or 0
    return render(request, 'core/abastecimentos/lista.html', {
        'abastecimentos': abastecimentos_list,
        'total_valor': total_valor
    })

@login_required
def abastecimento_detalhe(request, id):
    # Obter o abastecimento pelo ID
    abastecimento = get_object_or_404(Abastecimento, id=id, caminhao__usuario=request.user)
    return render(request, 'core/abastecimentos/detalhe.html', {
        'abastecimento': abastecimento
    })

@login_required
def abastecimento_novo(request):
    if request.method == 'POST':
        try:
            caminhao = Caminhao.objects.get(id=request.POST['caminhao'], usuario=request.user)
            
            # Se o motorista_user foi selecionado, usá-lo; caso contrário, usar o motorista (contato)
            motorista_user_id = request.POST.get('motorista_user')
            motorista_id = request.POST.get('motorista')
            
            motorista_user = None
            motorista = None
            
            if motorista_user_id and motorista_user_id != '':
                motorista_user = User.objects.get(id=motorista_user_id)
            
            if motorista_id and motorista_id != '':
                motorista = Contato.objects.get(id=motorista_id, usuario=request.user)
                
            abastecimento = Abastecimento(
                data=request.POST['data'],
                data_vencimento=request.POST['data_vencimento'],
                data_pagamento=request.POST.get('data_pagamento'),
                caminhao=caminhao,
                situacao=request.POST['situacao'],
                tipo_combustivel=request.POST['tipo_combustivel'],
                litros=Decimal(request.POST['litros']),
                valor_litro=Decimal(request.POST['valor_litro']),
                motorista=motorista,
                motorista_user=motorista_user,
                posto=Contato.objects.get(id=request.POST['posto'], usuario=request.user),
                km_abastecimento=request.POST['km_abastecimento']
            )
            if 'frete' in request.POST and request.POST['frete']:
                abastecimento.frete = Frete.objects.get(id=request.POST['frete'], caminhao__usuario=request.user)
            
            # Calcular o valor total
            litros = Decimal(request.POST['litros'])
            valor_litro = Decimal(request.POST['valor_litro'])
            abastecimento.total_valor = litros * valor_litro
            
            abastecimento.save()
            
            # Atualiza a quilometragem do caminhão
            caminhao.quilometragem = request.POST['km_abastecimento']
            caminhao.save()
            messages.success(request, 'Abastecimento cadastrado com sucesso!')
            return redirect('core:abastecimentos')
        except Exception as e:
            messages.error(request, f'Erro ao cadastrar abastecimento: {str(e)}')
    
    context = {
        'caminhoes': Caminhao.objects.filter(usuario=request.user),
        'motoristas': Contato.objects.filter(tipo='MOTORISTA', usuario=request.user),
        'motoristas_users': User.objects.filter(
            perfil__tipo_usuario='MOTORISTA',
            perfil__criado_por=request.user
        ),
        'postos': Contato.objects.filter(tipo='POSTO', usuario=request.user),
        'fretes': Frete.objects.filter(caminhao__usuario=request.user).order_by('-data_saida')[:10]
    }
    return render(request, 'core/abastecimentos/form.html', context)

@login_required
def abastecimento_editar(request, id):
    # Garantir que o usuário só possa editar seus próprios abastecimentos
    abastecimento = get_object_or_404(Abastecimento, pk=id, caminhao__usuario=request.user)
    
    # Log para depuração
    print(f"Editando abastecimento ID: {id}")
    print(f"Origem pendente: {abastecimento.origem_pendente}")
    print(f"Tem abastecimento_pendente: {hasattr(abastecimento, 'abastecimento_pendente')}")
    if hasattr(abastecimento, 'abastecimento_pendente'):
        print(f"abastecimento_pendente é nulo: {abastecimento.abastecimento_pendente is None}")
    
    # Criar um dicionário para armazenar os dados do formulário em caso de erro
    form_data = {}
    
    if request.method == 'POST':
        # Armazenar os dados do formulário para uso em caso de erro
        form_data = request.POST.dict()
        print(f"Dados do POST: {form_data}")
        
        try:
            # Obter o caminhão
            caminhao = Caminhao.objects.get(id=request.POST['caminhao'], usuario=request.user)
            
            # Atualizar os campos básicos
            abastecimento.data = request.POST['data']
            abastecimento.data_vencimento = request.POST['data_vencimento']
            abastecimento.data_pagamento = request.POST.get('data_pagamento', None)
            abastecimento.caminhao = caminhao
            abastecimento.situacao = request.POST['situacao']
            abastecimento.tipo_combustivel = request.POST['tipo_combustivel']
            
            # Atualizar campos numéricos
            if 'litros' in request.POST and request.POST['litros']:
                # Substituir vírgula por ponto para conversão decimal
                litros_str = request.POST['litros'].replace(',', '.')
                abastecimento.litros = Decimal(litros_str)
            
            if 'valor_litro' in request.POST and request.POST['valor_litro']:
                # Substituir vírgula por ponto para conversão decimal
                valor_litro_str = request.POST['valor_litro'].replace(',', '.')
                abastecimento.valor_litro = Decimal(valor_litro_str)
            
            # Calcular o valor total
            abastecimento.total_valor = abastecimento.litros * abastecimento.valor_litro
            
            # Verificar se foi selecionado um motorista (usuário ou contato)
            if 'motorista_user' in request.POST and request.POST['motorista_user']:
                motorista_user = User.objects.get(id=request.POST['motorista_user'])
                abastecimento.motorista_user = motorista_user
                abastecimento.motorista = None  # Limpar o outro campo
            elif 'motorista' in request.POST and request.POST['motorista']:
                motorista = Contato.objects.get(id=request.POST['motorista'], usuario=request.user)
                abastecimento.motorista = motorista
                abastecimento.motorista_user = None  # Limpar o outro campo
            
            # Atualizar posto
            if 'posto' in request.POST and request.POST['posto']:
                abastecimento.posto = Contato.objects.get(id=request.POST['posto'], usuario=request.user)
            
            # Atualizar km_abastecimento
            if 'km_abastecimento' in request.POST and request.POST['km_abastecimento']:
                # Remover possíveis pontos ou vírgulas no valor da quilometragem
                km_str = request.POST['km_abastecimento'].replace('.', '').replace(',', '')
                abastecimento.km_abastecimento = int(km_str)
            
            # Atualizar frete (pode ser nulo)
            print(f"Valor do frete no POST: {request.POST.get('frete')}")
            try:
                if 'frete' in request.POST and request.POST['frete'] and request.POST['frete'].strip():
                    frete_id = request.POST['frete'].strip()
                    print(f"Tentando obter frete com ID: {frete_id}")
                    try:
                        abastecimento.frete = Frete.objects.get(id=frete_id, caminhao__usuario=request.user)
                        print(f"Frete encontrado: {abastecimento.frete}")
                    except Frete.DoesNotExist:
                        print("Frete não encontrado")
                        abastecimento.frete = None
                    except ValueError:
                        print(f"Valor inválido para ID de frete: {frete_id}")
                        abastecimento.frete = None
                else:
                    print("Definindo frete como None porque o campo está vazio")
                    abastecimento.frete = None
            except Exception as e:
                print(f"Erro ao processar o campo de frete: {str(e)}")
                abastecimento.frete = None
                
            # Salvar as alterações
            abastecimento.save()
            
            # Se o abastecimento tem origem em um abastecimento pendente, atualizar o pendente também
            # Verificar se o abastecimento tem a propriedade origem_pendente e se ela é True
            print(f"Verificando abastecimento pendente: origem_pendente={abastecimento.origem_pendente}")
            
            # Tentar obter o abastecimento pendente de forma segura
            abastecimento_pendente = None
            try:
                # Verificar se o atributo existe e não é nulo
                if hasattr(abastecimento, 'abastecimento_pendente'):
                    try:
                        # Usar getattr com valor padrão None para evitar erros
                        abastecimento_pendente = getattr(abastecimento, 'abastecimento_pendente', None)
                        print(f"Abastecimento pendente encontrado: {abastecimento_pendente}")
                    except Exception as e:
                        print(f"Erro ao acessar abastecimento_pendente diretamente: {str(e)}")
                        abastecimento_pendente = None
            except Exception as e:
                print(f"Erro ao verificar atributo abastecimento_pendente: {str(e)}")
                abastecimento_pendente = None
            
            if abastecimento.origem_pendente and abastecimento_pendente:
                try:
                    print("Atualizando abastecimento pendente")
                    # Atualizar o abastecimento pendente com os novos dados
                    try:
                        abastecimento_pendente.frete = abastecimento.frete
                    except Exception as e:
                        print(f"Erro ao atualizar frete do abastecimento pendente: {str(e)}")
                    
                    try:
                        abastecimento_pendente.combustivel = abastecimento.tipo_combustivel
                    except Exception as e:
                        print(f"Erro ao atualizar combustivel do abastecimento pendente: {str(e)}")
                    
                    try:
                        abastecimento_pendente.litros = abastecimento.litros
                        abastecimento_pendente.valor_litro = abastecimento.valor_litro
                        abastecimento_pendente.valor_total = abastecimento.total_valor
                        abastecimento_pendente.km_atual = abastecimento.km_abastecimento
                        abastecimento_pendente.situacao = abastecimento.situacao
                        abastecimento_pendente.data_vencimento = abastecimento.data_vencimento
                        abastecimento_pendente.data_pagamento = abastecimento.data_pagamento
                        abastecimento_pendente.data = abastecimento.data
                        abastecimento_pendente.save()
                        print("Abastecimento pendente atualizado com sucesso")
                    except Exception as e:
                        print(f"Erro ao atualizar outros campos do abastecimento pendente: {str(e)}")
                except Exception as e:
                    print(f"Erro ao atualizar abastecimento pendente: {str(e)}")
                    messages.warning(request, f'Abastecimento atualizado, mas houve um erro ao atualizar o abastecimento pendente: {str(e)}')
            
            messages.success(request, 'Abastecimento atualizado com sucesso!')
            return redirect('core:abastecimentos')
        except Exception as e:
            print(f"ERRO PRINCIPAL: {str(e)}")
            import traceback
            print(traceback.format_exc())
            messages.error(request, f'Erro ao atualizar abastecimento: {str(e)}')
            # Não redirecionamos aqui para manter os dados do formulário
    
    # Se houve erro no formulário, usamos os dados do POST para preencher o contexto
    if form_data:
        # Criar um objeto abastecimento com os dados do formulário para exibição
        form_abastecimento = abastecimento
        form_abastecimento.data = form_data.get('data', abastecimento.data)
        form_abastecimento.data_vencimento = form_data.get('data_vencimento', abastecimento.data_vencimento)
        form_abastecimento.data_pagamento = form_data.get('data_pagamento', abastecimento.data_pagamento)
        form_abastecimento.situacao = form_data.get('situacao', abastecimento.situacao)
        form_abastecimento.tipo_combustivel = form_data.get('tipo_combustivel', abastecimento.tipo_combustivel)
        form_abastecimento.litros = form_data.get('litros', abastecimento.litros)
        form_abastecimento.valor_litro = form_data.get('valor_litro', abastecimento.valor_litro)
        form_abastecimento.km_abastecimento = form_data.get('km_abastecimento', abastecimento.km_abastecimento)
        
        context = {
            'abastecimento': form_abastecimento,
            'form_data': form_data,  # Passar os dados do formulário para o template
            'caminhoes': Caminhao.objects.filter(usuario=request.user),
            'motoristas': Contato.objects.filter(tipo='MOTORISTA', usuario=request.user),
            'motoristas_users': User.objects.filter(
                perfil__tipo_usuario='MOTORISTA',
                perfil__criado_por=request.user
            ),
            'postos': Contato.objects.filter(tipo='POSTO', usuario=request.user),
            'fretes': Frete.objects.filter(caminhao__usuario=request.user).order_by('-data_saida')[:10]
        }
    else:
        context = {
            'abastecimento': abastecimento,
            'caminhoes': Caminhao.objects.filter(usuario=request.user),
            'motoristas': Contato.objects.filter(tipo='MOTORISTA', usuario=request.user),
            'motoristas_users': User.objects.filter(
                perfil__tipo_usuario='MOTORISTA',
                perfil__criado_por=request.user
            ),
            'postos': Contato.objects.filter(tipo='POSTO', usuario=request.user),
            'fretes': Frete.objects.filter(caminhao__usuario=request.user).order_by('-data_saida')[:10]
        }
    return render(request, 'core/abastecimentos/form.html', context)

@login_required
def abastecimento_excluir(request, id):
    # Garantir que o usuário só possa excluir seus próprios abastecimentos
    abastecimento = get_object_or_404(Abastecimento, pk=id, caminhao__usuario=request.user)
    try:
        abastecimento.delete()
        messages.success(request, 'Abastecimento excluído com sucesso!')
    except Exception as e:
        messages.error(request, f'Erro ao excluir abastecimento: {str(e)}')
    return redirect('core:abastecimentos')

@login_required
def buscar_frete_por_id(request, id):
    try:
        # Garantir que o usuário só possa ver seus próprios fretes
        frete = get_object_or_404(Frete, pk=id, caminhao__usuario=request.user)
        
        # Retornar os dados do frete em formato JSON
        return JsonResponse({
            'id': frete.id,
            'origem': frete.origem,
            'destino': frete.destino,
            'data_saida': frete.data_saida.strftime('%Y-%m-%d'),
            'status': frete.status,
            'caminhao_id': frete.caminhao.id,
            'caminhao_placa': frete.caminhao.placa,
            'caminhao_modelo': frete.caminhao.modelo,
            'cliente': str(frete.cliente) if frete.cliente else ''
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=404)

@login_required
def buscar_fretes_por_caminhao(request, caminhao_id):
    print(f"Buscando fretes para o caminhão {caminhao_id}")
    try:
        # Buscar o caminhão sem verificar o usuário (temporariamente para debug)
        caminhao = get_object_or_404(Caminhao, pk=caminhao_id)
        
        # Buscar os 50 fretes mais recentes deste caminhão
        fretes = Frete.objects.filter(caminhao=caminhao).order_by('-data_saida')[:50]
        
        # Preparar os dados para retornar em formato JSON
        fretes_data = []
        for frete in fretes:
            fretes_data.append({
                'id': frete.id,
                'origem': frete.origem,
                'destino': frete.destino,
                'data_saida': frete.data_saida.strftime('%Y-%m-%d'),
                'status': frete.status,
                'caminhao_id': frete.caminhao.id,
                'caminhao_placa': frete.caminhao.placa,
                'caminhao_modelo': frete.caminhao.modelo
            })
        
        return JsonResponse({'fretes': fretes_data})
    except Exception as e:
        print(f"Erro ao buscar fretes: {str(e)}")
        return JsonResponse({'error': str(e)}, status=404)