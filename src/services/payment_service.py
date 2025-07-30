"""
Serviço de integração com gateways de pagamento
Suporte para Pix, PagSeguro e Mercado Pago
"""

import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import requests
from flask import current_app


class PaymentService:
    """Serviço centralizado para processamento de pagamentos"""
    
    def __init__(self):
        self.pix_enabled = True
        self.pagseguro_enabled = True
        self.mercadopago_enabled = True
    
    def create_payment(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cria um pagamento usando o gateway especificado
        
        Args:
            payment_data: {
                'gateway': 'pix|pagseguro|mercadopago',
                'amount': float,
                'description': str,
                'customer': dict,
                'agendamento_id': int
            }
        
        Returns:
            Dict com informações do pagamento criado
        """
        gateway = payment_data.get('gateway', 'pix')
        
        if gateway == 'pix':
            return self._create_pix_payment(payment_data)
        elif gateway == 'pagseguro':
            return self._create_pagseguro_payment(payment_data)
        elif gateway == 'mercadopago':
            return self._create_mercadopago_payment(payment_data)
        else:
            raise ValueError(f"Gateway não suportado: {gateway}")
    
    def _create_pix_payment(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Cria pagamento PIX"""
        payment_id = str(uuid.uuid4())
        
        # Simular geração de QR Code PIX
        pix_code = f"00020126580014BR.GOV.BCB.PIX0136{payment_id}520400005303986540{data['amount']:.2f}5802BR5925{data['customer']['nome'][:25]}6009SAO PAULO62070503***6304"
        
        return {
            'payment_id': payment_id,
            'gateway': 'pix',
            'status': 'pending',
            'amount': data['amount'],
            'currency': 'BRL',
            'pix_code': pix_code,
            'qr_code_url': f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={pix_code}",
            'expires_at': (datetime.now() + timedelta(minutes=30)).isoformat(),
            'created_at': datetime.now().isoformat(),
            'agendamento_id': data.get('agendamento_id')
        }
    
    def _create_pagseguro_payment(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Cria pagamento PagSeguro"""
        payment_id = str(uuid.uuid4())
        
        # Simular criação de pagamento no PagSeguro
        payment_url = f"https://pagseguro.uol.com.br/checkout/payment/eft/{payment_id}"
        
        return {
            'payment_id': payment_id,
            'gateway': 'pagseguro',
            'status': 'pending',
            'amount': data['amount'],
            'currency': 'BRL',
            'payment_url': payment_url,
            'expires_at': (datetime.now() + timedelta(hours=24)).isoformat(),
            'created_at': datetime.now().isoformat(),
            'agendamento_id': data.get('agendamento_id')
        }
    
    def _create_mercadopago_payment(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Cria pagamento Mercado Pago"""
        payment_id = str(uuid.uuid4())
        
        # Simular criação de preferência no Mercado Pago
        checkout_url = f"https://www.mercadopago.com.br/checkout/v1/redirect?pref_id={payment_id}"
        
        return {
            'payment_id': payment_id,
            'gateway': 'mercadopago',
            'status': 'pending',
            'amount': data['amount'],
            'currency': 'BRL',
            'checkout_url': checkout_url,
            'expires_at': (datetime.now() + timedelta(hours=24)).isoformat(),
            'created_at': datetime.now().isoformat(),
            'agendamento_id': data.get('agendamento_id')
        }
    
    def check_payment_status(self, payment_id: str, gateway: str) -> Dict[str, Any]:
        """Verifica status de um pagamento"""
        # Em um sistema real, consultaria a API do gateway
        # Por enquanto, simular diferentes status
        import random
        
        statuses = ['pending', 'paid', 'cancelled', 'expired']
        status = random.choice(statuses)
        
        return {
            'payment_id': payment_id,
            'gateway': gateway,
            'status': status,
            'updated_at': datetime.now().isoformat()
        }
    
    def process_webhook(self, gateway: str, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Processa webhook de notificação de pagamento"""
        if gateway == 'pix':
            return self._process_pix_webhook(webhook_data)
        elif gateway == 'pagseguro':
            return self._process_pagseguro_webhook(webhook_data)
        elif gateway == 'mercadopago':
            return self._process_mercadopago_webhook(webhook_data)
        else:
            raise ValueError(f"Gateway não suportado: {gateway}")
    
    def _process_pix_webhook(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Processa webhook PIX"""
        return {
            'payment_id': data.get('payment_id'),
            'status': data.get('status', 'paid'),
            'amount': data.get('amount'),
            'paid_at': datetime.now().isoformat()
        }
    
    def _process_pagseguro_webhook(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Processa webhook PagSeguro"""
        return {
            'payment_id': data.get('payment_id'),
            'status': data.get('status', 'paid'),
            'amount': data.get('amount'),
            'paid_at': datetime.now().isoformat()
        }
    
    def _process_mercadopago_webhook(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Processa webhook Mercado Pago"""
        return {
            'payment_id': data.get('payment_id'),
            'status': data.get('status', 'paid'),
            'amount': data.get('amount'),
            'paid_at': datetime.now().isoformat()
        }
    
    def get_available_gateways(self) -> list:
        """Retorna lista de gateways disponíveis"""
        gateways = []
        
        if self.pix_enabled:
            gateways.append({
                'id': 'pix',
                'name': 'PIX',
                'description': 'Pagamento instantâneo via PIX',
                'icon': 'pix',
                'processing_time': 'Instantâneo'
            })
        
        if self.pagseguro_enabled:
            gateways.append({
                'id': 'pagseguro',
                'name': 'PagSeguro',
                'description': 'Cartão de crédito, débito e boleto',
                'icon': 'pagseguro',
                'processing_time': 'Até 2 dias úteis'
            })
        
        if self.mercadopago_enabled:
            gateways.append({
                'id': 'mercadopago',
                'name': 'Mercado Pago',
                'description': 'Cartão, PIX e outras formas',
                'icon': 'mercadopago',
                'processing_time': 'Até 1 dia útil'
            })
        
        return gateways
    
    def calculate_fees(self, amount: float, gateway: str) -> Dict[str, float]:
        """Calcula taxas do gateway"""
        fees = {
            'pix': 0.0,  # PIX sem taxa
            'pagseguro': amount * 0.0399,  # 3.99%
            'mercadopago': amount * 0.0499  # 4.99%
        }
        
        fee = fees.get(gateway, 0.0)
        net_amount = amount - fee
        
        return {
            'gross_amount': amount,
            'fee': fee,
            'net_amount': net_amount,
            'fee_percentage': (fee / amount * 100) if amount > 0 else 0
        }


# Instância global do serviço
payment_service = PaymentService()

