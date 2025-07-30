"""
Rotas para gerenciamento de notificações
"""

from flask import Blueprint, request, jsonify
from ..models.agendamento import Agendamento
from ..models.cliente import Cliente
from ..services.notification_service import notification_service
from datetime import datetime, timedelta

notificacao_bp = Blueprint('notificacao', __name__)


@notificacao_bp.route('/notificacoes/agendamento/<int:agendamento_id>/confirmacao', methods=['POST'])
def enviar_confirmacao_agendamento(agendamento_id):
    """Envia confirmação de agendamento"""
    try:
        agendamento = Agendamento.query.get_or_404(agendamento_id)
        
        # Preparar dados do agendamento
        agendamento_data = {
            'id': agendamento.id,
            'data_hora': agendamento.data_hora.isoformat(),
            'cliente': {
                'nome': agendamento.cliente.nome,
                'email': agendamento.cliente.email,
                'telefone': agendamento.cliente.telefone
            },
            'profissional': {
                'nome': agendamento.profissional.nome
            },
            'servico': {
                'nome': agendamento.servico.nome,
                'preco': float(agendamento.servico.preco)
            },
            'empresa': {
                'nome': agendamento.empresa.nome,
                'endereco': agendamento.empresa.endereco
            }
        }
        
        # Enviar notificações
        result = notification_service.send_appointment_confirmation(agendamento_data)
        
        return jsonify({
            'agendamento_id': agendamento_id,
            'notifications_sent': result['notifications_sent'],
            'total_sent': result['total_sent']
        })
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@notificacao_bp.route('/notificacoes/agendamento/<int:agendamento_id>/lembrete', methods=['POST'])
def enviar_lembrete_agendamento(agendamento_id):
    """Envia lembrete de agendamento"""
    try:
        data = request.get_json() or {}
        hours_before = data.get('hours_before', 24)
        
        agendamento = Agendamento.query.get_or_404(agendamento_id)
        
        # Preparar dados do agendamento
        agendamento_data = {
            'id': agendamento.id,
            'data_hora': agendamento.data_hora.isoformat(),
            'cliente': {
                'nome': agendamento.cliente.nome,
                'email': agendamento.cliente.email,
                'telefone': agendamento.cliente.telefone
            },
            'profissional': {
                'nome': agendamento.profissional.nome
            },
            'servico': {
                'nome': agendamento.servico.nome,
                'preco': float(agendamento.servico.preco)
            },
            'empresa': {
                'nome': agendamento.empresa.nome,
                'endereco': agendamento.empresa.endereco
            }
        }
        
        # Enviar lembretes
        result = notification_service.send_appointment_reminder(agendamento_data, hours_before)
        
        return jsonify({
            'agendamento_id': agendamento_id,
            'notifications_sent': result['notifications_sent'],
            'total_sent': result['total_sent']
        })
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@notificacao_bp.route('/notificacoes/email', methods=['POST'])
def enviar_email():
    """Envia email personalizado"""
    try:
        data = request.get_json()
        
        # Validar dados obrigatórios
        required_fields = ['to_email', 'subject', 'body']
        for field in required_fields:
            if field not in data:
                return jsonify({'erro': f'Campo {field} é obrigatório'}), 400
        
        result = notification_service.send_email(
            data['to_email'],
            data['subject'],
            data['body'],
            data.get('html_body')
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@notificacao_bp.route('/notificacoes/whatsapp', methods=['POST'])
def enviar_whatsapp():
    """Envia mensagem WhatsApp personalizada"""
    try:
        data = request.get_json()
        
        # Validar dados obrigatórios
        required_fields = ['phone', 'message']
        for field in required_fields:
            if field not in data:
                return jsonify({'erro': f'Campo {field} é obrigatório'}), 400
        
        result = notification_service.send_whatsapp(
            data['phone'],
            data['message']
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@notificacao_bp.route('/notificacoes/lembrete/agendar', methods=['POST'])
def agendar_lembrete():
    """Agenda um lembrete automático"""
    try:
        data = request.get_json()
        
        # Validar dados obrigatórios
        required_fields = ['agendamento_id', 'send_at']
        for field in required_fields:
            if field not in data:
                return jsonify({'erro': f'Campo {field} é obrigatório'}), 400
        
        agendamento_id = data['agendamento_id']
        send_at = datetime.fromisoformat(data['send_at'])
        
        # Verificar se o agendamento existe
        agendamento = Agendamento.query.get_or_404(agendamento_id)
        
        # Agendar lembrete
        result = notification_service.schedule_reminder(agendamento_id, send_at)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@notificacao_bp.route('/notificacoes/lembretes/automaticos', methods=['POST'])
def configurar_lembretes_automaticos():
    """Configura lembretes automáticos para agendamentos futuros"""
    try:
        data = request.get_json() or {}
        empresa_id = data.get('empresa_id')
        hours_before_list = data.get('hours_before', [24, 2])  # 24h e 2h antes por padrão
        
        if not empresa_id:
            return jsonify({'erro': 'Campo empresa_id é obrigatório'}), 400
        
        # Buscar agendamentos futuros da empresa
        now = datetime.now()
        agendamentos = Agendamento.query.filter(
            Agendamento.empresa_id == empresa_id,
            Agendamento.data_hora > now,
            Agendamento.status.in_(['agendado', 'confirmado'])
        ).all()
        
        lembretes_agendados = []
        
        for agendamento in agendamentos:
            for hours_before in hours_before_list:
                send_at = agendamento.data_hora - timedelta(hours=hours_before)
                
                # Só agendar se a data de envio for no futuro
                if send_at > now:
                    result = notification_service.schedule_reminder(agendamento.id, send_at)
                    lembretes_agendados.append({
                        'agendamento_id': agendamento.id,
                        'cliente_nome': agendamento.cliente.nome,
                        'data_agendamento': agendamento.data_hora.isoformat(),
                        'send_at': send_at.isoformat(),
                        'hours_before': hours_before,
                        'reminder_id': result['reminder_id']
                    })
        
        return jsonify({
            'empresa_id': empresa_id,
            'total_agendamentos': len(agendamentos),
            'total_lembretes': len(lembretes_agendados),
            'lembretes_agendados': lembretes_agendados
        })
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@notificacao_bp.route('/clientes/<int:cliente_id>/preferencias', methods=['GET'])
def obter_preferencias_notificacao(cliente_id):
    """Obtém preferências de notificação do cliente"""
    try:
        cliente = Cliente.query.get_or_404(cliente_id)
        
        preferencias = notification_service.get_notification_preferences(cliente_id)
        
        return jsonify({
            'cliente_id': cliente_id,
            'cliente_nome': cliente.nome,
            'preferencias': preferencias
        })
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@notificacao_bp.route('/clientes/<int:cliente_id>/preferencias', methods=['PUT'])
def atualizar_preferencias_notificacao(cliente_id):
    """Atualiza preferências de notificação do cliente"""
    try:
        cliente = Cliente.query.get_or_404(cliente_id)
        data = request.get_json()
        
        # Em um sistema real, salvaria no banco de dados
        # Por enquanto, apenas simular a atualização
        
        return jsonify({
            'cliente_id': cliente_id,
            'cliente_nome': cliente.nome,
            'preferencias_atualizadas': data,
            'message': 'Preferências atualizadas com sucesso'
        })
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@notificacao_bp.route('/notificacoes/teste', methods=['POST'])
def testar_notificacoes():
    """Testa envio de notificações"""
    try:
        data = request.get_json()
        tipo = data.get('tipo', 'email')  # 'email' ou 'whatsapp'
        
        if tipo == 'email':
            result = notification_service.send_email(
                data.get('email', 'teste@exemplo.com'),
                'Teste de Notificação - AgendaOnline',
                'Este é um teste de envio de email do sistema AgendaOnline.'
            )
        elif tipo == 'whatsapp':
            result = notification_service.send_whatsapp(
                data.get('telefone', '+5511999999999'),
                'Este é um teste de envio de WhatsApp do sistema AgendaOnline.'
            )
        else:
            return jsonify({'erro': 'Tipo de notificação inválido'}), 400
        
        return jsonify({
            'tipo': tipo,
            'resultado': result
        })
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

