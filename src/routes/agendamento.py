from flask import Blueprint, request, jsonify
from src.models.user import db
from src.models.agendamento import Agendamento
from src.models.cliente import Cliente
from src.models.profissional import Profissional
from src.models.servico import Servico
from datetime import datetime, timedelta

agendamento_bp = Blueprint('agendamento', __name__)

@agendamento_bp.route('/empresas/<int:empresa_id>/agendamentos', methods=['GET'])
def listar_agendamentos(empresa_id):
    """Lista agendamentos de uma empresa"""
    try:
        # Parâmetros de filtro
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        profissional_id = request.args.get('profissional_id', type=int)
        status = request.args.get('status')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        query = Agendamento.query.filter_by(empresa_id=empresa_id)
        
        # Filtros de data
        if data_inicio:
            data_inicio_dt = datetime.strptime(data_inicio, '%Y-%m-%d')
            query = query.filter(Agendamento.data_hora >= data_inicio_dt)
        
        if data_fim:
            data_fim_dt = datetime.strptime(data_fim, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(Agendamento.data_hora < data_fim_dt)
        
        # Filtro por profissional
        if profissional_id:
            query = query.filter(Agendamento.profissional_id == profissional_id)
        
        # Filtro por status
        if status:
            query = query.filter(Agendamento.status == status)
        
        # Ordenar por data
        query = query.order_by(Agendamento.data_hora.desc())
        
        # Paginação
        agendamentos = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return jsonify({
            'agendamentos': [agendamento.to_dict() for agendamento in agendamentos.items],
            'total': agendamentos.total,
            'pages': agendamentos.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@agendamento_bp.route('/empresas/<int:empresa_id>/agendamentos', methods=['POST'])
def criar_agendamento(empresa_id):
    """Cria um novo agendamento"""
    try:
        dados = request.get_json()
        
        # Validações básicas
        campos_obrigatorios = ['cliente_id', 'profissional_id', 'servico_id', 'data_hora']
        for campo in campos_obrigatorios:
            if not dados.get(campo):
                return jsonify({'erro': f'{campo} é obrigatório'}), 400
        
        # Verificar se entidades existem
        cliente = Cliente.query.get(dados['cliente_id'])
        if not cliente or cliente.empresa_id != empresa_id:
            return jsonify({'erro': 'Cliente não encontrado'}), 404
        
        profissional = Profissional.query.get(dados['profissional_id'])
        if not profissional or profissional.empresa_id != empresa_id:
            return jsonify({'erro': 'Profissional não encontrado'}), 404
        
        servico = Servico.query.get(dados['servico_id'])
        if not servico or servico.empresa_id != empresa_id:
            return jsonify({'erro': 'Serviço não encontrado'}), 404
        
        # Converter data_hora
        data_hora = datetime.fromisoformat(dados['data_hora'].replace('Z', '+00:00'))
        data_fim = data_hora + timedelta(minutes=servico.duracao_minutos)
        
        # Verificar disponibilidade do profissional
        conflito = Agendamento.query.filter(
            Agendamento.profissional_id == dados['profissional_id'],
            Agendamento.data_hora < data_fim,
            Agendamento.data_fim > data_hora,
            Agendamento.status.in_(['agendado', 'confirmado', 'em_andamento'])
        ).first()
        
        if conflito:
            return jsonify({'erro': 'Horário não disponível para este profissional'}), 400
        
        # Calcular valores
        valor_servico = float(servico.preco)
        valor_desconto = float(dados.get('valor_desconto', 0))
        valor_total = valor_servico - valor_desconto
        
        # Criar agendamento
        novo_agendamento = Agendamento(
            data_hora=data_hora,
            data_fim=data_fim,
            observacoes_cliente=dados.get('observacoes_cliente'),
            observacoes_profissional=dados.get('observacoes_profissional'),
            observacoes_internas=dados.get('observacoes_internas'),
            valor_servico=valor_servico,
            valor_desconto=valor_desconto,
            valor_total=valor_total,
            empresa_id=empresa_id,
            cliente_id=dados['cliente_id'],
            profissional_id=dados['profissional_id'],
            servico_id=dados['servico_id']
        )
        
        db.session.add(novo_agendamento)
        db.session.commit()
        
        # Atualizar último atendimento do cliente
        cliente.ultimo_atendimento = data_hora
        db.session.commit()
        
        return jsonify(novo_agendamento.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500

@agendamento_bp.route('/agendamentos/<int:agendamento_id>', methods=['GET'])
def obter_agendamento(agendamento_id):
    """Obtém um agendamento específico"""
    try:
        agendamento = Agendamento.query.get_or_404(agendamento_id)
        return jsonify(agendamento.to_dict()), 200
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@agendamento_bp.route('/agendamentos/<int:agendamento_id>', methods=['PUT'])
def atualizar_agendamento(agendamento_id):
    """Atualiza um agendamento"""
    try:
        agendamento = Agendamento.query.get_or_404(agendamento_id)
        dados = request.get_json()
        
        # Campos que podem ser atualizados
        campos_permitidos = [
            'status', 'observacoes_cliente', 'observacoes_profissional',
            'observacoes_internas', 'valor_desconto'
        ]
        
        for campo in campos_permitidos:
            if campo in dados:
                setattr(agendamento, campo, dados[campo])
        
        # Recalcular valor total se desconto foi alterado
        if 'valor_desconto' in dados:
            agendamento.valor_total = agendamento.valor_servico - float(dados['valor_desconto'])
        
        # Atualizar timestamps específicos
        if 'status' in dados:
            if dados['status'] == 'confirmado' and not agendamento.confirmado_em:
                agendamento.confirmado_em = datetime.utcnow()
            elif dados['status'] == 'cancelado' and not agendamento.cancelado_em:
                agendamento.cancelado_em = datetime.utcnow()
        
        agendamento.atualizado_em = datetime.utcnow()
        db.session.commit()
        
        return jsonify(agendamento.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500

@agendamento_bp.route('/agendamentos/<int:agendamento_id>/cancelar', methods=['POST'])
def cancelar_agendamento(agendamento_id):
    """Cancela um agendamento"""
    try:
        agendamento = Agendamento.query.get_or_404(agendamento_id)
        
        if not agendamento.pode_ser_cancelado():
            return jsonify({'erro': 'Agendamento não pode ser cancelado'}), 400
        
        dados = request.get_json() or {}
        
        agendamento.status = 'cancelado'
        agendamento.cancelado_em = datetime.utcnow()
        agendamento.observacoes_internas = dados.get('motivo_cancelamento', '')
        agendamento.atualizado_em = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify(agendamento.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500

@agendamento_bp.route('/agendamentos/<int:agendamento_id>/reagendar', methods=['POST'])
def reagendar_agendamento(agendamento_id):
    """Reagenda um agendamento"""
    try:
        agendamento = Agendamento.query.get_or_404(agendamento_id)
        dados = request.get_json()
        
        if not agendamento.pode_ser_reagendado():
            return jsonify({'erro': 'Agendamento não pode ser reagendado'}), 400
        
        if not dados.get('nova_data_hora'):
            return jsonify({'erro': 'Nova data e hora são obrigatórias'}), 400
        
        # Converter nova data_hora
        nova_data_hora = datetime.fromisoformat(dados['nova_data_hora'].replace('Z', '+00:00'))
        nova_data_fim = nova_data_hora + timedelta(minutes=agendamento.servico.duracao_minutos)
        
        # Verificar disponibilidade
        conflito = Agendamento.query.filter(
            Agendamento.profissional_id == agendamento.profissional_id,
            Agendamento.id != agendamento_id,
            Agendamento.data_hora < nova_data_fim,
            Agendamento.data_fim > nova_data_hora,
            Agendamento.status.in_(['agendado', 'confirmado', 'em_andamento'])
        ).first()
        
        if conflito:
            return jsonify({'erro': 'Novo horário não disponível'}), 400
        
        # Atualizar agendamento
        agendamento.data_hora = nova_data_hora
        agendamento.data_fim = nova_data_fim
        agendamento.status = 'agendado'  # Resetar status
        agendamento.confirmado_em = None
        agendamento.atualizado_em = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify(agendamento.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500

@agendamento_bp.route('/empresas/<int:empresa_id>/agenda/hoje', methods=['GET'])
def agenda_hoje(empresa_id):
    """Obtém a agenda do dia atual"""
    try:
        hoje = datetime.now().date()
        inicio_dia = datetime.combine(hoje, datetime.min.time())
        fim_dia = datetime.combine(hoje, datetime.max.time())
        
        agendamentos = Agendamento.query.filter(
            Agendamento.empresa_id == empresa_id,
            Agendamento.data_hora >= inicio_dia,
            Agendamento.data_hora <= fim_dia
        ).order_by(Agendamento.data_hora).all()
        
        return jsonify({
            'data': hoje.isoformat(),
            'agendamentos': [agendamento.to_dict() for agendamento in agendamentos]
        }), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

