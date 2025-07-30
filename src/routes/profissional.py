from flask import Blueprint, request, jsonify
from src.models.user import db
from src.models.profissional import Profissional
from datetime import datetime

profissional_bp = Blueprint('profissional', __name__)

@profissional_bp.route('/empresas/<int:empresa_id>/profissionais', methods=['GET'])
def listar_profissionais(empresa_id):
    """Lista todos os profissionais de uma empresa"""
    try:
        profissionais = Profissional.query.filter_by(empresa_id=empresa_id).all()
        return jsonify([profissional.to_dict() for profissional in profissionais]), 200
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@profissional_bp.route('/empresas/<int:empresa_id>/profissionais', methods=['POST'])
def criar_profissional(empresa_id):
    """Cria um novo profissional"""
    try:
        dados = request.get_json()
        
        # Validações básicas
        if not dados.get('nome'):
            return jsonify({'erro': 'Nome do profissional é obrigatório'}), 400
        
        # Criar novo profissional
        novo_profissional = Profissional(
            nome=dados['nome'],
            email=dados.get('email'),
            telefone=dados.get('telefone'),
            especialidades=dados.get('especialidades'),
            biografia=dados.get('biografia'),
            foto_url=dados.get('foto_url'),
            horario_inicio=datetime.strptime(dados['horario_inicio'], '%H:%M').time() if dados.get('horario_inicio') else None,
            horario_fim=datetime.strptime(dados['horario_fim'], '%H:%M').time() if dados.get('horario_fim') else None,
            dias_trabalho=dados.get('dias_trabalho', '1111100'),
            intervalo_atendimento=dados.get('intervalo_atendimento', 30),
            empresa_id=empresa_id
        )
        
        db.session.add(novo_profissional)
        db.session.commit()
        
        return jsonify(novo_profissional.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500

@profissional_bp.route('/profissionais/<int:profissional_id>', methods=['GET'])
def obter_profissional(profissional_id):
    """Obtém um profissional específico"""
    try:
        profissional = Profissional.query.get_or_404(profissional_id)
        return jsonify(profissional.to_dict()), 200
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@profissional_bp.route('/profissionais/<int:profissional_id>', methods=['PUT'])
def atualizar_profissional(profissional_id):
    """Atualiza um profissional"""
    try:
        profissional = Profissional.query.get_or_404(profissional_id)
        dados = request.get_json()
        
        # Atualizar campos permitidos
        campos_permitidos = [
            'nome', 'email', 'telefone', 'especialidades', 'biografia',
            'foto_url', 'dias_trabalho', 'intervalo_atendimento', 'ativo'
        ]
        
        for campo in campos_permitidos:
            if campo in dados:
                setattr(profissional, campo, dados[campo])
        
        # Campos de horário precisam de tratamento especial
        if 'horario_inicio' in dados and dados['horario_inicio']:
            profissional.horario_inicio = datetime.strptime(dados['horario_inicio'], '%H:%M').time()
        
        if 'horario_fim' in dados and dados['horario_fim']:
            profissional.horario_fim = datetime.strptime(dados['horario_fim'], '%H:%M').time()
        
        profissional.atualizado_em = datetime.utcnow()
        db.session.commit()
        
        return jsonify(profissional.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500

@profissional_bp.route('/profissionais/<int:profissional_id>', methods=['DELETE'])
def deletar_profissional(profissional_id):
    """Deleta um profissional"""
    try:
        profissional = Profissional.query.get_or_404(profissional_id)
        db.session.delete(profissional)
        db.session.commit()
        
        return jsonify({'mensagem': 'Profissional deletado com sucesso'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500

@profissional_bp.route('/profissionais/<int:profissional_id>/agenda', methods=['GET'])
def obter_agenda_profissional(profissional_id):
    """Obtém a agenda de um profissional"""
    try:
        from src.models.agendamento import Agendamento
        from datetime import datetime, timedelta
        
        profissional = Profissional.query.get_or_404(profissional_id)
        
        # Parâmetros de data
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        
        if not data_inicio:
            data_inicio = datetime.now().date()
        else:
            data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
        
        if not data_fim:
            data_fim = data_inicio + timedelta(days=7)
        else:
            data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
        
        # Buscar agendamentos do período
        agendamentos = Agendamento.query.filter(
            Agendamento.profissional_id == profissional_id,
            Agendamento.data_hora >= datetime.combine(data_inicio, datetime.min.time()),
            Agendamento.data_hora <= datetime.combine(data_fim, datetime.max.time()),
            Agendamento.status.in_(['agendado', 'confirmado', 'em_andamento'])
        ).all()
        
        return jsonify({
            'profissional': profissional.to_dict(),
            'agendamentos': [agendamento.to_dict() for agendamento in agendamentos],
            'periodo': {
                'inicio': data_inicio.isoformat(),
                'fim': data_fim.isoformat()
            }
        }), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@profissional_bp.route('/profissionais/<int:profissional_id>/horarios-disponiveis', methods=['GET'])
def obter_horarios_disponiveis(profissional_id):
    """Obtém os horários disponíveis de um profissional para uma data específica"""
    try:
        from src.models.agendamento import Agendamento
        from src.models.servico import Servico
        from datetime import datetime, timedelta
        
        profissional = Profissional.query.get_or_404(profissional_id)
        
        data = request.args.get('data')
        servico_id = request.args.get('servico_id', type=int)
        
        if not data:
            return jsonify({'erro': 'Data é obrigatória'}), 400
        
        data_consulta = datetime.strptime(data, '%Y-%m-%d').date()
        
        # Verificar se o profissional trabalha neste dia
        dia_semana = data_consulta.weekday()  # 0 = segunda, 6 = domingo
        if profissional.dias_trabalho[dia_semana] == '0':
            return jsonify({'horarios': []}), 200
        
        # Obter duração do serviço
        duracao_servico = 60  # padrão
        if servico_id:
            servico = Servico.query.get(servico_id)
            if servico:
                duracao_servico = servico.duracao_minutos
        
        # Gerar horários possíveis
        horarios_disponiveis = []
        if profissional.horario_inicio and profissional.horario_fim:
            inicio = datetime.combine(data_consulta, profissional.horario_inicio)
            fim = datetime.combine(data_consulta, profissional.horario_fim)
            
            atual = inicio
            while atual + timedelta(minutes=duracao_servico) <= fim:
                # Verificar se não há conflito com agendamentos existentes
                conflito = Agendamento.query.filter(
                    Agendamento.profissional_id == profissional_id,
                    Agendamento.data_hora <= atual,
                    Agendamento.data_fim > atual,
                    Agendamento.status.in_(['agendado', 'confirmado', 'em_andamento'])
                ).first()
                
                if not conflito:
                    horarios_disponiveis.append(atual.strftime('%H:%M'))
                
                atual += timedelta(minutes=profissional.intervalo_atendimento)
        
        return jsonify({
            'data': data,
            'profissional_id': profissional_id,
            'horarios': horarios_disponiveis
        }), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

