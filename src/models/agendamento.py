from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from src.models.user import db

class Agendamento(db.Model):
    __tablename__ = 'agendamentos'
    
    id = db.Column(db.Integer, primary_key=True)
    data_hora = db.Column(db.DateTime, nullable=False)
    data_fim = db.Column(db.DateTime, nullable=False)  # Calculado automaticamente
    
    # Status do agendamento
    status = db.Column(db.String(20), default='agendado')  # agendado, confirmado, em_andamento, concluido, cancelado, nao_compareceu
    
    # Observações
    observacoes_cliente = db.Column(db.Text, nullable=True)
    observacoes_profissional = db.Column(db.Text, nullable=True)
    observacoes_internas = db.Column(db.Text, nullable=True)
    
    # Valores
    valor_servico = db.Column(db.Numeric(10, 2), nullable=False)
    valor_desconto = db.Column(db.Numeric(10, 2), default=0.00)
    valor_total = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Relacionamentos
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    profissional_id = db.Column(db.Integer, db.ForeignKey('profissionais.id'), nullable=False)
    servico_id = db.Column(db.Integer, db.ForeignKey('servicos.id'), nullable=False)
    
    # Timestamps
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    confirmado_em = db.Column(db.DateTime, nullable=True)
    cancelado_em = db.Column(db.DateTime, nullable=True)
    
    # Relacionamentos
    pagamentos = db.relationship('Pagamento', backref='agendamento', lazy=True, cascade='all, delete-orphan')
    notificacoes = db.relationship('Notificacao', backref='agendamento', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Agendamento {self.id} - {self.data_hora}>'

    def to_dict(self):
        return {
            'id': self.id,
            'data_hora': self.data_hora.isoformat() if self.data_hora else None,
            'data_fim': self.data_fim.isoformat() if self.data_fim else None,
            'status': self.status,
            'observacoes_cliente': self.observacoes_cliente,
            'observacoes_profissional': self.observacoes_profissional,
            'observacoes_internas': self.observacoes_internas,
            'valor_servico': float(self.valor_servico) if self.valor_servico else 0.0,
            'valor_desconto': float(self.valor_desconto) if self.valor_desconto else 0.0,
            'valor_total': float(self.valor_total) if self.valor_total else 0.0,
            'empresa_id': self.empresa_id,
            'cliente_id': self.cliente_id,
            'profissional_id': self.profissional_id,
            'servico_id': self.servico_id,
            'criado_em': self.criado_em.isoformat() if self.criado_em else None,
            'atualizado_em': self.atualizado_em.isoformat() if self.atualizado_em else None,
            'confirmado_em': self.confirmado_em.isoformat() if self.confirmado_em else None,
            'cancelado_em': self.cancelado_em.isoformat() if self.cancelado_em else None,
            # Dados relacionados
            'cliente': self.cliente.to_dict() if self.cliente else None,
            'profissional': self.profissional.to_dict() if self.profissional else None,
            'servico': self.servico.to_dict() if self.servico else None
        }

    def pode_ser_cancelado(self):
        """Verifica se o agendamento pode ser cancelado"""
        if self.status in ['cancelado', 'concluido']:
            return False
        
        # Pode adicionar regras de tempo mínimo para cancelamento
        return True

    def pode_ser_reagendado(self):
        """Verifica se o agendamento pode ser reagendado"""
        if self.status in ['cancelado', 'concluido']:
            return False
        
        return True

