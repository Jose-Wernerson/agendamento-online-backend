from flask import Blueprint, request, jsonify
from src.models.user import db
from src.models.cliente import Cliente
from datetime import datetime

cliente_bp = Blueprint('cliente', __name__)

@cliente_bp.route('/empresas/<int:empresa_id>/clientes', methods=['GET'])
def listar_clientes(empresa_id):
    """Lista todos os clientes de uma empresa"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        busca = request.args.get('busca', '')
        
        query = Cliente.query.filter_by(empresa_id=empresa_id)
        
        if busca:
            query = query.filter(
                (Cliente.nome.contains(busca)) |
                (Cliente.telefone.contains(busca)) |
                (Cliente.email.contains(busca))
            )
        
        clientes = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return jsonify({
            'clientes': [cliente.to_dict() for cliente in clientes.items],
            'total': clientes.total,
            'pages': clientes.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@cliente_bp.route('/empresas/<int:empresa_id>/clientes', methods=['POST'])
def criar_cliente(empresa_id):
    """Cria um novo cliente"""
    try:
        dados = request.get_json()
        
        # Validações básicas
        if not dados.get('nome'):
            return jsonify({'erro': 'Nome do cliente é obrigatório'}), 400
        
        if not dados.get('telefone'):
            return jsonify({'erro': 'Telefone do cliente é obrigatório'}), 400
        
        # Verificar se telefone já existe na empresa
        cliente_existente = Cliente.query.filter_by(
            empresa_id=empresa_id,
            telefone=dados['telefone']
        ).first()
        
        if cliente_existente:
            return jsonify({'erro': 'Cliente com este telefone já cadastrado'}), 400
        
        # Criar novo cliente
        novo_cliente = Cliente(
            nome=dados['nome'],
            email=dados.get('email'),
            telefone=dados['telefone'],
            cpf=dados.get('cpf'),
            data_nascimento=datetime.strptime(dados['data_nascimento'], '%Y-%m-%d').date() if dados.get('data_nascimento') else None,
            endereco=dados.get('endereco'),
            campos_personalizados=dados.get('campos_personalizados'),
            preferencias=dados.get('preferencias'),
            observacoes=dados.get('observacoes'),
            empresa_id=empresa_id
        )
        
        db.session.add(novo_cliente)
        db.session.commit()
        
        return jsonify(novo_cliente.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500

@cliente_bp.route('/clientes/<int:cliente_id>', methods=['GET'])
def obter_cliente(cliente_id):
    """Obtém um cliente específico"""
    try:
        cliente = Cliente.query.get_or_404(cliente_id)
        return jsonify(cliente.to_dict()), 200
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@cliente_bp.route('/clientes/<int:cliente_id>', methods=['PUT'])
def atualizar_cliente(cliente_id):
    """Atualiza um cliente"""
    try:
        cliente = Cliente.query.get_or_404(cliente_id)
        dados = request.get_json()
        
        # Atualizar campos permitidos
        campos_permitidos = [
            'nome', 'email', 'telefone', 'cpf', 'endereco',
            'campos_personalizados', 'preferencias', 'observacoes', 'ativo'
        ]
        
        for campo in campos_permitidos:
            if campo in dados:
                if campo == 'data_nascimento' and dados[campo]:
                    setattr(cliente, campo, datetime.strptime(dados[campo], '%Y-%m-%d').date())
                else:
                    setattr(cliente, campo, dados[campo])
        
        cliente.atualizado_em = datetime.utcnow()
        db.session.commit()
        
        return jsonify(cliente.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500

@cliente_bp.route('/clientes/<int:cliente_id>', methods=['DELETE'])
def deletar_cliente(cliente_id):
    """Deleta um cliente"""
    try:
        cliente = Cliente.query.get_or_404(cliente_id)
        db.session.delete(cliente)
        db.session.commit()
        
        return jsonify({'mensagem': 'Cliente deletado com sucesso'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500

@cliente_bp.route('/clientes/<int:cliente_id>/historico', methods=['GET'])
def obter_historico_cliente(cliente_id):
    """Obtém o histórico de agendamentos do cliente"""
    try:
        cliente = Cliente.query.get_or_404(cliente_id)
        historico = cliente.get_historico_agendamentos()
        
        return jsonify({
            'cliente': cliente.to_dict(),
            'historico': historico
        }), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@cliente_bp.route('/empresas/<int:empresa_id>/clientes/buscar', methods=['GET'])
def buscar_clientes(empresa_id):
    """Busca clientes por nome ou telefone"""
    try:
        termo = request.args.get('termo', '')
        
        if not termo:
            return jsonify({'clientes': []}), 200
        
        clientes = Cliente.query.filter(
            Cliente.empresa_id == empresa_id,
            (Cliente.nome.contains(termo)) |
            (Cliente.telefone.contains(termo))
        ).limit(10).all()
        
        return jsonify({
            'clientes': [cliente.to_dict() for cliente in clientes]
        }), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

