from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from src.models.user import db

class Cliente(db.Model):
    __tablename__ = 'clientes'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    telefone = db.Column(db.String(20), nullable=False)
    cpf = db.Column(db.String(14), nullable=True)
    data_nascimento = db.Column(db.Date, nullable=True)
    endereco = db.Column(db.Text, nullable=True)
    
    # Campos personalizados (JSON)
    campos_personalizados = db.Column(db.Text, nullable=True)  # JSON string
    
    # Preferências
    preferencias = db.Column(db.Text, nullable=True)  # JSON string
    observacoes = db.Column(db.Text, nullable=True)
    
    # Status
    ativo = db.Column(db.Boolean, default=True)
    
    # Relacionamento com empresa
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False)
    
    # Timestamps
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    ultimo_atendimento = db.Column(db.DateTime, nullable=True)
    
    # Relacionamentos
    agendamentos = db.relationship('Agendamento', backref='cliente', lazy=True)

    def __repr__(self):
        return f'<Cliente {self.nome}>'

    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'email': self.email,
            'telefone': self.telefone,
            'cpf': self.cpf,
            'data_nascimento': self.data_nascimento.isoformat() if self.data_nascimento else None,
            'endereco': self.endereco,
            'campos_personalizados': self.campos_personalizados,
            'preferencias': self.preferencias,
            'observacoes': self.observacoes,
            'ativo': self.ativo,
            'empresa_id': self.empresa_id,
            'criado_em': self.criado_em.isoformat() if self.criado_em else None,
            'atualizado_em': self.atualizado_em.isoformat() if self.atualizado_em else None,
            'ultimo_atendimento': self.ultimo_atendimento.isoformat() if self.ultimo_atendimento else None
        }

    def get_historico_agendamentos(self):
        """Retorna o histórico de agendamentos do cliente"""
        return [agendamento.to_dict() for agendamento in self.agendamentos]

