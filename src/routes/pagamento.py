"""
Rotas para gerenciamento de pagamentos
"""

from flask import Blueprint, request, jsonify
from ..models.pagamento import Pagamento
from ..models.agendamento import Agendamento
from ..models.cliente import Cliente
from ..models.user import db
from ..services.payment_service import payment_service
from ..services.notification_service import notification_service

pagamento_bp = Blueprint('pagamento', __name__)


@pagamento_bp.route('/pagamentos', methods=['POST'])
def criar_pagamento():
    """Cria um novo pagamento"""
    try:
        data = request.get_json()
        
        # Validar dados obrigatórios
        required_fields = ['agendamento_id', 'gateway', 'amount']
        for field in required_fields:
            if field not in data:
                return jsonify({'erro': f'Campo {field} é obrigatório'}), 400
        
        # Buscar agendamento
        agendamento = Agendamento.query.get(data['agendamento_id'])
        if not agendamento:
            return jsonify({'erro': 'Agendamento não encontrado'}), 404
        
        # Preparar dados para o gateway
        payment_data = {
            'gateway': data['gateway'],
            'amount': float(data['amount']),
            'description': f"Pagamento - {agendamento.servico.nome}",
            'customer': {
                'nome': agendamento.cliente.nome,
                'email': agendamento.cliente.email,
                'telefone': agendamento.cliente.telefone
            },
            'agendamento_id': agendamento.id
        }
        
        # Criar pagamento no gateway
        payment_result = payment_service.create_payment(payment_data)
        
        # Salvar no banco de dados
        pagamento = Pagamento(
            agendamento_id=agendamento.id,
            gateway=data['gateway'],
            valor=float(data['amount']),
            status='pendente',
            payment_id=payment_result['payment_id'],
            dados_gateway=payment_result
        )
        
        db.session.add(pagamento)
        db.session.commit()
        
        return jsonify({
            'id': pagamento.id,
            'payment_id': payment_result['payment_id'],
            'gateway': pagamento.gateway,
            'valor': pagamento.valor,
            'status': pagamento.status,
            'payment_data': payment_result
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500


@pagamento_bp.route('/pagamentos/<int:pagamento_id>', methods=['GET'])
def obter_pagamento(pagamento_id):
    """Obtém detalhes de um pagamento"""
    try:
        pagamento = Pagamento.query.get_or_404(pagamento_id)
        
        return jsonify({
            'id': pagamento.id,
            'agendamento_id': pagamento.agendamento_id,
            'gateway': pagamento.gateway,
            'valor': pagamento.valor,
            'status': pagamento.status,
            'payment_id': pagamento.payment_id,
            'dados_gateway': pagamento.dados_gateway,
            'criado_em': pagamento.criado_em.isoformat(),
            'atualizado_em': pagamento.atualizado_em.isoformat() if pagamento.atualizado_em else None
        })
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@pagamento_bp.route('/pagamentos/<int:pagamento_id>/status', methods=['GET'])
def verificar_status_pagamento(pagamento_id):
    """Verifica status atual do pagamento no gateway"""
    try:
        pagamento = Pagamento.query.get_or_404(pagamento_id)
        
        # Consultar status no gateway
        status_result = payment_service.check_payment_status(
            pagamento.payment_id,
            pagamento.gateway
        )
        
        # Atualizar status se mudou
        if status_result['status'] != pagamento.status:
            pagamento.status = status_result['status']
            pagamento.dados_gateway.update(status_result)
            db.session.commit()
            
            # Enviar notificação se foi pago
            if status_result['status'] == 'paid':
                notification_service.send_payment_notification({
                    'id': pagamento.id,
                    'amount': pagamento.valor,
                    'gateway': pagamento.gateway,
                    'status': 'paid',
                    'agendamento': {
                        'id': pagamento.agendamento.id,
                        'data_hora': pagamento.agendamento.data_hora.isoformat(),
                        'cliente': {
                            'nome': pagamento.agendamento.cliente.nome,
                            'email': pagamento.agendamento.cliente.email,
                            'telefone': pagamento.agendamento.cliente.telefone
                        }
                    }
                })
        
        return jsonify({
            'id': pagamento.id,
            'status': pagamento.status,
            'gateway_status': status_result
        })
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@pagamento_bp.route('/pagamentos/webhook/<gateway>', methods=['POST'])
def webhook_pagamento(gateway):
    """Recebe webhooks dos gateways de pagamento"""
    try:
        data = request.get_json()
        
        # Processar webhook
        webhook_result = payment_service.process_webhook(gateway, data)
        
        # Buscar pagamento
        pagamento = Pagamento.query.filter_by(
            payment_id=webhook_result['payment_id']
        ).first()
        
        if not pagamento:
            return jsonify({'erro': 'Pagamento não encontrado'}), 404
        
        # Atualizar status
        pagamento.status = webhook_result['status']
        pagamento.dados_gateway.update(webhook_result)
        db.session.commit()
        
        # Enviar notificação se foi pago
        if webhook_result['status'] == 'paid':
            notification_service.send_payment_notification({
                'id': pagamento.id,
                'amount': pagamento.valor,
                'gateway': pagamento.gateway,
                'status': 'paid',
                'agendamento': {
                    'id': pagamento.agendamento.id,
                    'data_hora': pagamento.agendamento.data_hora.isoformat(),
                    'cliente': {
                        'nome': pagamento.agendamento.cliente.nome,
                        'email': pagamento.agendamento.cliente.email,
                        'telefone': pagamento.agendamento.cliente.telefone
                    }
                }
            })
        
        return jsonify({'status': 'ok'}), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@pagamento_bp.route('/pagamentos/gateways', methods=['GET'])
def listar_gateways():
    """Lista gateways de pagamento disponíveis"""
    try:
        gateways = payment_service.get_available_gateways()
        return jsonify({'gateways': gateways})
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@pagamento_bp.route('/pagamentos/calcular-taxas', methods=['POST'])
def calcular_taxas():
    """Calcula taxas para um pagamento"""
    try:
        data = request.get_json()
        
        if 'amount' not in data or 'gateway' not in data:
            return jsonify({'erro': 'Campos amount e gateway são obrigatórios'}), 400
        
        fees = payment_service.calculate_fees(
            float(data['amount']),
            data['gateway']
        )
        
        return jsonify(fees)
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@pagamento_bp.route('/empresas/<int:empresa_id>/pagamentos', methods=['GET'])
def listar_pagamentos_empresa(empresa_id):
    """Lista pagamentos de uma empresa"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status')
        gateway = request.args.get('gateway')
        
        # Query base
        query = db.session.query(Pagamento).join(Agendamento).filter(
            Agendamento.empresa_id == empresa_id
        )
        
        # Filtros
        if status:
            query = query.filter(Pagamento.status == status)
        if gateway:
            query = query.filter(Pagamento.gateway == gateway)
        
        # Ordenação
        query = query.order_by(Pagamento.criado_em.desc())
        
        # Paginação
        pagamentos = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return jsonify({
            'pagamentos': [{
                'id': p.id,
                'agendamento_id': p.agendamento_id,
                'cliente_nome': p.agendamento.cliente.nome,
                'servico_nome': p.agendamento.servico.nome,
                'gateway': p.gateway,
                'valor': p.valor,
                'status': p.status,
                'criado_em': p.criado_em.isoformat()
            } for p in pagamentos.items],
            'total': pagamentos.total,
            'pages': pagamentos.pages,
            'current_page': page
        })
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

