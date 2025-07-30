"""
Serviço de notificações por email e WhatsApp
Gerencia lembretes automáticos e comunicações
"""

import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from flask import current_app
import json


class NotificationService:
    """Serviço centralizado para envio de notificações"""
    
    def __init__(self):
        self.email_enabled = True
        self.whatsapp_enabled = True
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.email_user = "sistema@agendaonline.com"
        self.email_password = "senha_app"  # Em produção, usar variáveis de ambiente
        self.whatsapp_api_url = "https://api.whatsapp.com/send"  # API simulada
    
    def send_email(self, to_email: str, subject: str, body: str, html_body: str = None) -> Dict[str, Any]:
        """
        Envia email
        
        Args:
            to_email: Email do destinatário
            subject: Assunto do email
            body: Corpo do email em texto
            html_body: Corpo do email em HTML (opcional)
        
        Returns:
            Dict com resultado do envio
        """
        try:
            # Criar mensagem
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email_user
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Adicionar corpo em texto
            text_part = MIMEText(body, 'plain', 'utf-8')
            msg.attach(text_part)
            
            # Adicionar corpo em HTML se fornecido
            if html_body:
                html_part = MIMEText(html_body, 'html', 'utf-8')
                msg.attach(html_part)
            
            # Simular envio (em produção, usar SMTP real)
            print(f"[EMAIL SIMULADO] Para: {to_email}")
            print(f"[EMAIL SIMULADO] Assunto: {subject}")
            print(f"[EMAIL SIMULADO] Corpo: {body}")
            
            return {
                'success': True,
                'message': 'Email enviado com sucesso',
                'sent_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Erro ao enviar email: {str(e)}',
                'error': str(e)
            }
    
    def send_whatsapp(self, phone: str, message: str) -> Dict[str, Any]:
        """
        Envia mensagem via WhatsApp
        
        Args:
            phone: Número do telefone (formato: +5511999999999)
            message: Mensagem a ser enviada
        
        Returns:
            Dict com resultado do envio
        """
        try:
            # Formatar número de telefone
            if not phone.startswith('+'):
                phone = f"+55{phone.replace('(', '').replace(')', '').replace('-', '').replace(' ', '')}"
            
            # Simular envio via API do WhatsApp
            print(f"[WHATSAPP SIMULADO] Para: {phone}")
            print(f"[WHATSAPP SIMULADO] Mensagem: {message}")
            
            return {
                'success': True,
                'message': 'WhatsApp enviado com sucesso',
                'sent_at': datetime.now().isoformat(),
                'phone': phone
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Erro ao enviar WhatsApp: {str(e)}',
                'error': str(e)
            }
    
    def send_appointment_confirmation(self, agendamento: Dict[str, Any]) -> Dict[str, Any]:
        """Envia confirmação de agendamento"""
        cliente = agendamento.get('cliente', {})
        profissional = agendamento.get('profissional', {})
        servico = agendamento.get('servico', {})
        
        # Formatar data e hora
        data_hora = datetime.fromisoformat(agendamento['data_hora'])
        data_formatada = data_hora.strftime('%d/%m/%Y às %H:%M')
        
        # Preparar mensagens
        subject = "Agendamento Confirmado - AgendaOnline"
        
        email_body = f"""
Olá {cliente.get('nome', 'Cliente')},

Seu agendamento foi confirmado com sucesso!

📅 Data e Hora: {data_formatada}
👤 Profissional: {profissional.get('nome', 'N/A')}
💼 Serviço: {servico.get('nome', 'N/A')}
💰 Valor: R$ {servico.get('preco', 0):.2f}

Endereço:
{agendamento.get('empresa', {}).get('endereco', 'Endereço não informado')}

Em caso de dúvidas, entre em contato conosco.

Atenciosamente,
Equipe AgendaOnline
        """
        
        whatsapp_message = f"""
🎉 *Agendamento Confirmado!*

Olá {cliente.get('nome', 'Cliente')}!

📅 *Data:* {data_formatada}
👤 *Profissional:* {profissional.get('nome', 'N/A')}
💼 *Serviço:* {servico.get('nome', 'N/A')}
💰 *Valor:* R$ {servico.get('preco', 0):.2f}

Nos vemos em breve! 😊
        """
        
        results = []
        
        # Enviar email se disponível
        if cliente.get('email') and self.email_enabled:
            email_result = self.send_email(
                cliente['email'],
                subject,
                email_body
            )
            results.append({'type': 'email', 'result': email_result})
        
        # Enviar WhatsApp se disponível
        if cliente.get('telefone') and self.whatsapp_enabled:
            whatsapp_result = self.send_whatsapp(
                cliente['telefone'],
                whatsapp_message
            )
            results.append({'type': 'whatsapp', 'result': whatsapp_result})
        
        return {
            'agendamento_id': agendamento.get('id'),
            'notifications_sent': results,
            'total_sent': len([r for r in results if r['result']['success']])
        }
    
    def send_appointment_reminder(self, agendamento: Dict[str, Any], hours_before: int = 24) -> Dict[str, Any]:
        """Envia lembrete de agendamento"""
        cliente = agendamento.get('cliente', {})
        profissional = agendamento.get('profissional', {})
        servico = agendamento.get('servico', {})
        
        # Formatar data e hora
        data_hora = datetime.fromisoformat(agendamento['data_hora'])
        data_formatada = data_hora.strftime('%d/%m/%Y às %H:%M')
        
        # Preparar mensagens
        subject = "Lembrete: Seu agendamento é amanhã - AgendaOnline"
        
        email_body = f"""
Olá {cliente.get('nome', 'Cliente')},

Este é um lembrete do seu agendamento:

📅 Data e Hora: {data_formatada}
👤 Profissional: {profissional.get('nome', 'N/A')}
💼 Serviço: {servico.get('nome', 'N/A')}
💰 Valor: R$ {servico.get('preco', 0):.2f}

Endereço:
{agendamento.get('empresa', {}).get('endereco', 'Endereço não informado')}

Caso precise cancelar ou reagendar, entre em contato conosco com antecedência.

Atenciosamente,
Equipe AgendaOnline
        """
        
        whatsapp_message = f"""
⏰ *Lembrete de Agendamento*

Olá {cliente.get('nome', 'Cliente')}!

Seu agendamento é amanhã:

📅 *{data_formatada}*
👤 *Profissional:* {profissional.get('nome', 'N/A')}
💼 *Serviço:* {servico.get('nome', 'N/A')}

Nos vemos em breve! 😊

Para cancelar ou reagendar, responda esta mensagem.
        """
        
        results = []
        
        # Enviar email se disponível
        if cliente.get('email') and self.email_enabled:
            email_result = self.send_email(
                cliente['email'],
                subject,
                email_body
            )
            results.append({'type': 'email', 'result': email_result})
        
        # Enviar WhatsApp se disponível
        if cliente.get('telefone') and self.whatsapp_enabled:
            whatsapp_result = self.send_whatsapp(
                cliente['telefone'],
                whatsapp_message
            )
            results.append({'type': 'whatsapp', 'result': whatsapp_result})
        
        return {
            'agendamento_id': agendamento.get('id'),
            'notifications_sent': results,
            'total_sent': len([r for r in results if r['result']['success']])
        }
    
    def send_payment_notification(self, pagamento: Dict[str, Any]) -> Dict[str, Any]:
        """Envia notificação de pagamento"""
        agendamento = pagamento.get('agendamento', {})
        cliente = agendamento.get('cliente', {})
        
        if pagamento['status'] == 'paid':
            subject = "Pagamento Confirmado - AgendaOnline"
            
            email_body = f"""
Olá {cliente.get('nome', 'Cliente')},

Seu pagamento foi confirmado com sucesso!

💰 Valor: R$ {pagamento['amount']:.2f}
💳 Método: {pagamento['gateway'].upper()}
📅 Agendamento: {agendamento.get('data_hora', 'N/A')}

Obrigado pela preferência!

Atenciosamente,
Equipe AgendaOnline
            """
            
            whatsapp_message = f"""
✅ *Pagamento Confirmado!*

Olá {cliente.get('nome', 'Cliente')}!

💰 *Valor:* R$ {pagamento['amount']:.2f}
💳 *Método:* {pagamento['gateway'].upper()}

Seu agendamento está confirmado! 🎉
            """
        else:
            subject = "Problema com Pagamento - AgendaOnline"
            
            email_body = f"""
Olá {cliente.get('nome', 'Cliente')},

Identificamos um problema com seu pagamento.

💰 Valor: R$ {pagamento['amount']:.2f}
💳 Método: {pagamento['gateway'].upper()}
📅 Agendamento: {agendamento.get('data_hora', 'N/A')}

Por favor, entre em contato conosco para resolver a situação.

Atenciosamente,
Equipe AgendaOnline
            """
            
            whatsapp_message = f"""
⚠️ *Problema com Pagamento*

Olá {cliente.get('nome', 'Cliente')}!

Identificamos um problema com seu pagamento de R$ {pagamento['amount']:.2f}.

Entre em contato conosco para resolver.
            """
        
        results = []
        
        # Enviar notificações
        if cliente.get('email') and self.email_enabled:
            email_result = self.send_email(
                cliente['email'],
                subject,
                email_body
            )
            results.append({'type': 'email', 'result': email_result})
        
        if cliente.get('telefone') and self.whatsapp_enabled:
            whatsapp_result = self.send_whatsapp(
                cliente['telefone'],
                whatsapp_message
            )
            results.append({'type': 'whatsapp', 'result': whatsapp_result})
        
        return {
            'payment_id': pagamento.get('id'),
            'notifications_sent': results,
            'total_sent': len([r for r in results if r['result']['success']])
        }
    
    def schedule_reminder(self, agendamento_id: int, send_at: datetime) -> Dict[str, Any]:
        """Agenda um lembrete para ser enviado"""
        # Em um sistema real, isso seria salvo no banco de dados
        # e processado por um job scheduler (Celery, etc.)
        
        return {
            'reminder_id': f"reminder_{agendamento_id}_{int(send_at.timestamp())}",
            'agendamento_id': agendamento_id,
            'scheduled_for': send_at.isoformat(),
            'status': 'scheduled'
        }
    
    def get_notification_preferences(self, cliente_id: int) -> Dict[str, Any]:
        """Obtém preferências de notificação do cliente"""
        # Em um sistema real, isso viria do banco de dados
        return {
            'email_enabled': True,
            'whatsapp_enabled': True,
            'reminder_hours': [24, 2],  # 24h e 2h antes
            'marketing_emails': False
        }


# Instância global do serviço
notification_service = NotificationService()

