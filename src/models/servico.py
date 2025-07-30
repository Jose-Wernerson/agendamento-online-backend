from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from src.models.user import db

class Servico(db.Model):
    __tablename__ = 'servicos'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    duracao_minutos = db.Column(db.Integer, nullable=False, default=60)
    preco = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    categoria = db.Column(db.String(50), nullable=True)
    
    # Configurações
    ativo = db.Column(db.Boolean, default=True)
    requer_preparo = db.Column(db.Boolean, default=False)  # Tempo adicional antes do serviço
    tempo_preparo = db.Column(db.Integer, default=0)  # Minutos de preparo
    
    # Relacionamento com empresa
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False)
    
    # Timestamps
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    agendamentos = db.relationship('Agendamento', backref='servico', lazy=True)
    servicos_profissional = db.relationship('ServicoProfissional', backref='servico', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Servico {self.nome}>'

    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'descricao': self.descricao,
            'duracao_minutos': self.duracao_minutos,
            'preco': float(self.preco) if self.preco else 0.0,
            'categoria': self.categoria,
            'ativo': self.ativo,
            'requer_preparo': self.requer_preparo,
            'tempo_preparo': self.tempo_preparo,
            'empresa_id': self.empresa_id,
            'criado_em': self.criado_em.isoformat() if self.criado_em else None,
            'atualizado_em': self.atualizado_em.isoformat() if self.atualizado_em else None
        }

class ServicoProfissional(db.Model):
    """Tabela de relacionamento entre Serviços e Profissionais"""
    __tablename__ = 'servicos_profissionais'
    
    id = db.Column(db.Integer, primary_key=True)
    servico_id = db.Column(db.Integer, db.ForeignKey('servicos.id'), nullable=False)
    profissional_id = db.Column(db.Integer, db.ForeignKey('profissionais.id'), nullable=False)
    
    # Configurações específicas do profissional para este serviço
    preco_personalizado = db.Column(db.Numeric(10, 2), nullable=True)  # Preço diferente do padrão
    duracao_personalizada = db.Column(db.Integer, nullable=True)  # Duração diferente do padrão
    
    # Timestamps
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ServicoProfissional {self.servico_id}-{self.profissional_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'servico_id': self.servico_id,
            'profissional_id': self.profissional_id,
            'preco_personalizado': float(self.preco_personalizado) if self.preco_personalizado else None,
            'duracao_personalizada': self.duracao_personalizada,
            'criado_em': self.criado_em.isoformat() if self.criado_em else None
        }

