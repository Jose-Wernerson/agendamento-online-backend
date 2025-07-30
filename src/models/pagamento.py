from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from src.models.user import db

class Pagamento(db.Model):
    __tablename__ = 'pagamentos'
    
    id = db.Column(db.Integer, primary_key=True)
    valor = db.Column(db.Numeric(10, 2), nullable=False)
    metodo = db.Column(db.String(20), nullable=False)  # pix, cartao_credito, cartao_debito, dinheiro, mercado_pago, pagseguro
    status = db.Column(db.String(20), default='pendente')  # pendente, aprovado, rejeitado, cancelado, estornado
    
    # IDs externos das integrações
    transacao_id_externo = db.Column(db.String(100), nullable=True)
    gateway = db.Column(db.String(20), nullable=True)  # mercado_pago, pagseguro, pix
    
    # Dados do pagamento
    dados_pagamento = db.Column(db.Text, nullable=True)  # JSON com dados específicos do gateway
    
    # Relacionamento
    agendamento_id = db.Column(db.Integer, db.ForeignKey('agendamentos.id'), nullable=False)
    
    # Timestamps
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    processado_em = db.Column(db.DateTime, nullable=True)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Pagamento {self.id} - {self.valor} - {self.status}>'

    def to_dict(self):
        return {
            'id': self.id,
            'valor': float(self.valor) if self.valor else 0.0,
            'metodo': self.metodo,
            'status': self.status,
            'transacao_id_externo': self.transacao_id_externo,
            'gateway': self.gateway,
            'dados_pagamento': self.dados_pagamento,
            'agendamento_id': self.agendamento_id,
            'criado_em': self.criado_em.isoformat() if self.criado_em else None,
            'processado_em': self.processado_em.isoformat() if self.processado_em else None,
            'atualizado_em': self.atualizado_em.isoformat() if self.atualizado_em else None
        }

class Notificacao(db.Model):
    __tablename__ = 'notificacoes'
    
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(30), nullable=False)  # confirmacao, lembrete_24h, lembrete_2h, cancelamento, reagendamento
    canal = db.Column(db.String(20), nullable=False)  # whatsapp, email, sms
    destinatario = db.Column(db.String(120), nullable=False)  # telefone ou email
    
    # Conteúdo da notificação
    assunto = db.Column(db.String(200), nullable=True)
    mensagem = db.Column(db.Text, nullable=False)
    
    # Status
    status = db.Column(db.String(20), default='pendente')  # pendente, enviado, erro, entregue
    tentativas = db.Column(db.Integer, default=0)
    erro_detalhes = db.Column(db.Text, nullable=True)
    
    # Agendamento para envio
    enviar_em = db.Column(db.DateTime, nullable=False)
    
    # Relacionamento
    agendamento_id = db.Column(db.Integer, db.ForeignKey('agendamentos.id'), nullable=False)
    
    # Timestamps
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    enviado_em = db.Column(db.DateTime, nullable=True)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Notificacao {self.id} - {self.tipo} - {self.status}>'

    def to_dict(self):
        return {
            'id': self.id,
            'tipo': self.tipo,
            'canal': self.canal,
            'destinatario': self.destinatario,
            'assunto': self.assunto,
            'mensagem': self.mensagem,
            'status': self.status,
            'tentativas': self.tentativas,
            'erro_detalhes': self.erro_detalhes,
            'enviar_em': self.enviar_em.isoformat() if self.enviar_em else None,
            'agendamento_id': self.agendamento_id,
            'criado_em': self.criado_em.isoformat() if self.criado_em else None,
            'enviado_em': self.enviado_em.isoformat() if self.enviado_em else None,
            'atualizado_em': self.atualizado_em.isoformat() if self.atualizado_em else None
        }

