from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from src.models.user import db

class Empresa(db.Model):
    __tablename__ = 'empresas'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    telefone = db.Column(db.String(20), nullable=True)
    endereco = db.Column(db.Text, nullable=True)
    logo_url = db.Column(db.String(255), nullable=True)
    
    # Configurações de estilo
    cor_primaria = db.Column(db.String(7), default='#007BFF')  # Hex color
    cor_secundaria = db.Column(db.String(7), default='#6C757D')
    cor_acento = db.Column(db.String(7), default='#28A745')
    
    # Configurações de funcionamento
    horario_abertura = db.Column(db.Time, nullable=True)
    horario_fechamento = db.Column(db.Time, nullable=True)
    dias_funcionamento = db.Column(db.String(7), default='1111100')  # Segunda a Domingo (1=funciona, 0=não)
    
    # Plano de assinatura
    plano = db.Column(db.String(20), default='basico')  # basico, profissional, avancado
    
    # Configurações de notificação
    whatsapp_ativo = db.Column(db.Boolean, default=False)
    email_ativo = db.Column(db.Boolean, default=True)
    whatsapp_token = db.Column(db.String(255), nullable=True)
    
    # Timestamps
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    profissionais = db.relationship('Profissional', backref='empresa', lazy=True, cascade='all, delete-orphan')
    servicos = db.relationship('Servico', backref='empresa', lazy=True, cascade='all, delete-orphan')
    clientes = db.relationship('Cliente', backref='empresa', lazy=True, cascade='all, delete-orphan')
    agendamentos = db.relationship('Agendamento', backref='empresa', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Empresa {self.nome}>'

    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'email': self.email,
            'telefone': self.telefone,
            'endereco': self.endereco,
            'logo_url': self.logo_url,
            'cor_primaria': self.cor_primaria,
            'cor_secundaria': self.cor_secundaria,
            'cor_acento': self.cor_acento,
            'horario_abertura': self.horario_abertura.strftime('%H:%M') if self.horario_abertura else None,
            'horario_fechamento': self.horario_fechamento.strftime('%H:%M') if self.horario_fechamento else None,
            'dias_funcionamento': self.dias_funcionamento,
            'plano': self.plano,
            'whatsapp_ativo': self.whatsapp_ativo,
            'email_ativo': self.email_ativo,
            'criado_em': self.criado_em.isoformat() if self.criado_em else None,
            'atualizado_em': self.atualizado_em.isoformat() if self.atualizado_em else None
        }

