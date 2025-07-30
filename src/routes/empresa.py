from flask import Blueprint, request, jsonify
from src.models.user import db
from src.models.empresa import Empresa
from datetime import datetime

empresa_bp = Blueprint('empresa', __name__)

@empresa_bp.route('/empresas', methods=['GET'])
def listar_empresas():
    """Lista todas as empresas"""
    try:
        empresas = Empresa.query.all()
        return jsonify([empresa.to_dict() for empresa in empresas]), 200
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@empresa_bp.route('/empresas', methods=['POST'])
def criar_empresa():
    """Cria uma nova empresa"""
    try:
        dados = request.get_json()
        
        # Validações básicas
        if not dados.get('nome'):
            return jsonify({'erro': 'Nome da empresa é obrigatório'}), 400
        
        if not dados.get('email'):
            return jsonify({'erro': 'Email da empresa é obrigatório'}), 400
        
        # Verificar se email já existe
        empresa_existente = Empresa.query.filter_by(email=dados['email']).first()
        if empresa_existente:
            return jsonify({'erro': 'Email já cadastrado'}), 400
        
        # Criar nova empresa
        nova_empresa = Empresa(
            nome=dados['nome'],
            email=dados['email'],
            telefone=dados.get('telefone'),
            endereco=dados.get('endereco'),
            logo_url=dados.get('logo_url'),
            cor_primaria=dados.get('cor_primaria', '#007BFF'),
            cor_secundaria=dados.get('cor_secundaria', '#6C757D'),
            cor_acento=dados.get('cor_acento', '#28A745'),
            plano=dados.get('plano', 'basico'),
            whatsapp_ativo=dados.get('whatsapp_ativo', False),
            email_ativo=dados.get('email_ativo', True)
        )
        
        db.session.add(nova_empresa)
        db.session.commit()
        
        return jsonify(nova_empresa.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500

@empresa_bp.route('/empresas/<int:empresa_id>', methods=['GET'])
def obter_empresa(empresa_id):
    """Obtém uma empresa específica"""
    try:
        empresa = Empresa.query.get_or_404(empresa_id)
        return jsonify(empresa.to_dict()), 200
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@empresa_bp.route('/empresas/<int:empresa_id>', methods=['PUT'])
def atualizar_empresa(empresa_id):
    """Atualiza uma empresa"""
    try:
        empresa = Empresa.query.get_or_404(empresa_id)
        dados = request.get_json()
        
        # Atualizar campos permitidos
        campos_permitidos = [
            'nome', 'telefone', 'endereco', 'logo_url',
            'cor_primaria', 'cor_secundaria', 'cor_acento',
            'horario_abertura', 'horario_fechamento', 'dias_funcionamento',
            'plano', 'whatsapp_ativo', 'email_ativo', 'whatsapp_token'
        ]
        
        for campo in campos_permitidos:
            if campo in dados:
                setattr(empresa, campo, dados[campo])
        
        empresa.atualizado_em = datetime.utcnow()
        db.session.commit()
        
        return jsonify(empresa.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500

@empresa_bp.route('/empresas/<int:empresa_id>', methods=['DELETE'])
def deletar_empresa(empresa_id):
    """Deleta uma empresa"""
    try:
        empresa = Empresa.query.get_or_404(empresa_id)
        db.session.delete(empresa)
        db.session.commit()
        
        return jsonify({'mensagem': 'Empresa deletada com sucesso'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500

@empresa_bp.route('/empresas/<int:empresa_id>/configuracoes', methods=['GET'])
def obter_configuracoes_empresa(empresa_id):
    """Obtém as configurações de estilo e funcionamento da empresa"""
    try:
        empresa = Empresa.query.get_or_404(empresa_id)
        
        configuracoes = {
            'estilo': {
                'cor_primaria': empresa.cor_primaria,
                'cor_secundaria': empresa.cor_secundaria,
                'cor_acento': empresa.cor_acento,
                'logo_url': empresa.logo_url
            },
            'funcionamento': {
                'horario_abertura': empresa.horario_abertura.strftime('%H:%M') if empresa.horario_abertura else None,
                'horario_fechamento': empresa.horario_fechamento.strftime('%H:%M') if empresa.horario_fechamento else None,
                'dias_funcionamento': empresa.dias_funcionamento
            },
            'notificacoes': {
                'whatsapp_ativo': empresa.whatsapp_ativo,
                'email_ativo': empresa.email_ativo
            },
            'plano': empresa.plano
        }
        
        return jsonify(configuracoes), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

