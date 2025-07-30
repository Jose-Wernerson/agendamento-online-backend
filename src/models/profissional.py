from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from src.models.user import db

class Profissional(db.Model):
    __tablename__ = 'profissionais'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    telefone = db.Column(db.String(20), nullable=True)
    especialidades = db.Column(db.Text, nullable=True)  # JSON string com especialidades
    biografia = db.Column(db.Text, nullable=True)
    foto_url = db.Column(db.String(255), nullable=True)
    
    # Configurações de horário
    horario_inicio = db.Column(db.Time, nullable=True)
    horario_fim = db.Column(db.Time, nullable=True)
    dias_trabalho = db.Column(db.String(7), default='1111100')  # Segunda a Domingo
    intervalo_atendimento = db.Column(db.Integer, default=30)  # Minutos entre atendimentos
    
    # Status
    ativo = db.Column(db.Boolean, default=True)
    
    # Relacionamento com empresa
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False)
    
    # Timestamps
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    agendamentos = db.relationship('Agendamento', backref='profissional', lazy=True)
    servicos_profissional = db.relationship('ServicoProfissional', backref='profissional', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Profissional {self.nome}>'

    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'email': self.email,
            'telefone': self.telefone,
            'especialidades': self.especialidades,
            'biografia': self.biografia,
            'foto_url': self.foto_url,
            'horario_inicio': self.horario_inicio.strftime('%H:%M') if self.horario_inicio else None,
            'horario_fim': self.horario_fim.strftime('%H:%M') if self.horario_fim else None,
            'dias_trabalho': self.dias_trabalho,
            'intervalo_atendimento': self.intervalo_atendimento,
            'ativo': self.ativo,
            'empresa_id': self.empresa_id,
            'criado_em': self.criado_em.isoformat() if self.criado_em else None,
            'atualizado_em': self.atualizado_em.isoformat() if self.atualizado_em else None
        }

