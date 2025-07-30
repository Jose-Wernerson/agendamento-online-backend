from flask import Blueprint, request, jsonify
from src.models.user import db
from src.models.servico import Servico, ServicoProfissional
from datetime import datetime

servico_bp = Blueprint('servico', __name__)

@servico_bp.route('/empresas/<int:empresa_id>/servicos', methods=['GET'])
def listar_servicos(empresa_id):
    """Lista todos os serviços de uma empresa"""
    try:
        servicos = Servico.query.filter_by(empresa_id=empresa_id).all()
        return jsonify([servico.to_dict() for servico in servicos]), 200
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@servico_bp.route('/empresas/<int:empresa_id>/servicos', methods=['POST'])
def criar_servico(empresa_id):
    """Cria um novo serviço"""
    try:
        dados = request.get_json()
        
        # Validações básicas
        if not dados.get('nome'):
            return jsonify({'erro': 'Nome do serviço é obrigatório'}), 400
        
        if not dados.get('duracao_minutos'):
            return jsonify({'erro': 'Duração do serviço é obrigatória'}), 400
        
        if not dados.get('preco'):
            return jsonify({'erro': 'Preço do serviço é obrigatório'}), 400
        
        # Criar novo serviço
        novo_servico = Servico(
            nome=dados['nome'],
            descricao=dados.get('descricao'),
            duracao_minutos=dados['duracao_minutos'],
            preco=dados['preco'],
            categoria=dados.get('categoria'),
            requer_preparo=dados.get('requer_preparo', False),
            tempo_preparo=dados.get('tempo_preparo', 0),
            empresa_id=empresa_id
        )
        
        db.session.add(novo_servico)
        db.session.commit()
        
        return jsonify(novo_servico.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500

@servico_bp.route('/servicos/<int:servico_id>', methods=['GET'])
def obter_servico(servico_id):
    """Obtém um serviço específico"""
    try:
        servico = Servico.query.get_or_404(servico_id)
        return jsonify(servico.to_dict()), 200
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@servico_bp.route('/servicos/<int:servico_id>', methods=['PUT'])
def atualizar_servico(servico_id):
    """Atualiza um serviço"""
    try:
        servico = Servico.query.get_or_404(servico_id)
        dados = request.get_json()
        
        # Atualizar campos permitidos
        campos_permitidos = [
            'nome', 'descricao', 'duracao_minutos', 'preco', 'categoria',
            'ativo', 'requer_preparo', 'tempo_preparo'
        ]
        
        for campo in campos_permitidos:
            if campo in dados:
                setattr(servico, campo, dados[campo])
        
        servico.atualizado_em = datetime.utcnow()
        db.session.commit()
        
        return jsonify(servico.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500

@servico_bp.route('/servicos/<int:servico_id>', methods=['DELETE'])
def deletar_servico(servico_id):
    """Deleta um serviço"""
    try:
        servico = Servico.query.get_or_404(servico_id)
        db.session.delete(servico)
        db.session.commit()
        
        return jsonify({'mensagem': 'Serviço deletado com sucesso'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500

@servico_bp.route('/servicos/<int:servico_id>/profissionais', methods=['GET'])
def listar_profissionais_servico(servico_id):
    """Lista profissionais habilitados para um serviço"""
    try:
        from src.models.profissional import Profissional
        
        servico = Servico.query.get_or_404(servico_id)
        
        # Buscar relacionamentos serviço-profissional
        relacionamentos = ServicoProfissional.query.filter_by(servico_id=servico_id).all()
        
        profissionais = []
        for rel in relacionamentos:
            profissional = Profissional.query.get(rel.profissional_id)
            if profissional and profissional.ativo:
                prof_dict = profissional.to_dict()
                prof_dict['preco_personalizado'] = float(rel.preco_personalizado) if rel.preco_personalizado else None
                prof_dict['duracao_personalizada'] = rel.duracao_personalizada
                profissionais.append(prof_dict)
        
        return jsonify({
            'servico': servico.to_dict(),
            'profissionais': profissionais
        }), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@servico_bp.route('/servicos/<int:servico_id>/profissionais', methods=['POST'])
def associar_profissional_servico(servico_id):
    """Associa um profissional a um serviço"""
    try:
        dados = request.get_json()
        
        if not dados.get('profissional_id'):
            return jsonify({'erro': 'ID do profissional é obrigatório'}), 400
        
        # Verificar se associação já existe
        associacao_existente = ServicoProfissional.query.filter_by(
            servico_id=servico_id,
            profissional_id=dados['profissional_id']
        ).first()
        
        if associacao_existente:
            return jsonify({'erro': 'Profissional já associado a este serviço'}), 400
        
        # Criar nova associação
        nova_associacao = ServicoProfissional(
            servico_id=servico_id,
            profissional_id=dados['profissional_id'],
            preco_personalizado=dados.get('preco_personalizado'),
            duracao_personalizada=dados.get('duracao_personalizada')
        )
        
        db.session.add(nova_associacao)
        db.session.commit()
        
        return jsonify(nova_associacao.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500

@servico_bp.route('/servicos/<int:servico_id>/profissionais/<int:profissional_id>', methods=['DELETE'])
def desassociar_profissional_servico(servico_id, profissional_id):
    """Remove a associação entre um profissional e um serviço"""
    try:
        associacao = ServicoProfissional.query.filter_by(
            servico_id=servico_id,
            profissional_id=profissional_id
        ).first_or_404()
        
        db.session.delete(associacao)
        db.session.commit()
        
        return jsonify({'mensagem': 'Associação removida com sucesso'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500

@servico_bp.route('/empresas/<int:empresa_id>/servicos/categorias', methods=['GET'])
def listar_categorias_servicos(empresa_id):
    """Lista todas as categorias de serviços de uma empresa"""
    try:
        categorias = db.session.query(Servico.categoria).filter(
            Servico.empresa_id == empresa_id,
            Servico.categoria.isnot(None),
            Servico.ativo == True
        ).distinct().all()
        
        categorias_lista = [cat[0] for cat in categorias if cat[0]]
        
        return jsonify({'categorias': categorias_lista}), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

