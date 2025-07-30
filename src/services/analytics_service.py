"""
Serviço de analytics e métricas do negócio
Coleta e processa dados para dashboard e relatórios
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy import func, and_, or_
from ..models.agendamento import Agendamento
from ..models.cliente import Cliente
from ..models.pagamento import Pagamento
from ..models.profissional import Profissional
from ..models.servico import Servico
from ..models.user import db


class AnalyticsService:
    """Serviço para análise de dados e métricas"""
    
    def get_dashboard_metrics(self, empresa_id: int, periodo: str = '30d') -> Dict[str, Any]:
        """
        Obtém métricas principais para o dashboard
        
        Args:
            empresa_id: ID da empresa
            periodo: Período para análise ('7d', '30d', '90d', '1y')
        
        Returns:
            Dict com métricas principais
        """
        end_date = datetime.now()
        
        # Calcular data de início baseada no período
        if periodo == '7d':
            start_date = end_date - timedelta(days=7)
        elif periodo == '30d':
            start_date = end_date - timedelta(days=30)
        elif periodo == '90d':
            start_date = end_date - timedelta(days=90)
        elif periodo == '1y':
            start_date = end_date - timedelta(days=365)
        else:
            start_date = end_date - timedelta(days=30)
        
        # Métricas básicas
        total_agendamentos = self._get_total_agendamentos(empresa_id, start_date, end_date)
        agendamentos_hoje = self._get_agendamentos_hoje(empresa_id)
        total_clientes = self._get_total_clientes(empresa_id)
        clientes_ativos = self._get_clientes_ativos(empresa_id, start_date, end_date)
        receita_periodo = self._get_receita_periodo(empresa_id, start_date, end_date)
        receita_hoje = self._get_receita_hoje(empresa_id)
        taxa_ocupacao = self._get_taxa_ocupacao(empresa_id, start_date, end_date)
        
        # Crescimento comparado ao período anterior
        periodo_anterior_start = start_date - (end_date - start_date)
        periodo_anterior_end = start_date
        
        agendamentos_periodo_anterior = self._get_total_agendamentos(
            empresa_id, periodo_anterior_start, periodo_anterior_end
        )
        receita_periodo_anterior = self._get_receita_periodo(
            empresa_id, periodo_anterior_start, periodo_anterior_end
        )
        
        # Calcular percentuais de crescimento
        crescimento_agendamentos = self._calcular_crescimento(
            total_agendamentos, agendamentos_periodo_anterior
        )
        crescimento_receita = self._calcular_crescimento(
            receita_periodo, receita_periodo_anterior
        )
        
        return {
            'periodo': periodo,
            'data_inicio': start_date.isoformat(),
            'data_fim': end_date.isoformat(),
            'agendamentos': {
                'total': total_agendamentos,
                'hoje': agendamentos_hoje,
                'crescimento': crescimento_agendamentos
            },
            'clientes': {
                'total': total_clientes,
                'ativos': clientes_ativos,
                'novos': self._get_novos_clientes(empresa_id, start_date, end_date)
            },
            'receita': {
                'total': receita_periodo,
                'hoje': receita_hoje,
                'crescimento': crescimento_receita,
                'ticket_medio': receita_periodo / total_agendamentos if total_agendamentos > 0 else 0
            },
            'ocupacao': {
                'taxa': taxa_ocupacao,
                'horarios_disponiveis': self._get_horarios_disponiveis_hoje(empresa_id),
                'horarios_ocupados': agendamentos_hoje
            }
        }
    
    def get_agendamentos_por_periodo(self, empresa_id: int, periodo: str = '30d') -> List[Dict[str, Any]]:
        """Obtém agendamentos agrupados por período"""
        end_date = datetime.now()
        
        if periodo == '7d':
            start_date = end_date - timedelta(days=7)
            group_by = 'day'
        elif periodo == '30d':
            start_date = end_date - timedelta(days=30)
            group_by = 'day'
        elif periodo == '90d':
            start_date = end_date - timedelta(days=90)
            group_by = 'week'
        elif periodo == '1y':
            start_date = end_date - timedelta(days=365)
            group_by = 'month'
        else:
            start_date = end_date - timedelta(days=30)
            group_by = 'day'
        
        if group_by == 'day':
            # Agrupar por dia
            query = db.session.query(
                func.date(Agendamento.data_hora).label('periodo'),
                func.count(Agendamento.id).label('total'),
                func.sum(Servico.preco).label('receita')
            ).join(Servico).filter(
                Agendamento.empresa_id == empresa_id,
                Agendamento.data_hora >= start_date,
                Agendamento.data_hora <= end_date,
                Agendamento.status.in_(['confirmado', 'concluido'])
            ).group_by(func.date(Agendamento.data_hora)).all()
            
        elif group_by == 'week':
            # Agrupar por semana
            query = db.session.query(
                func.strftime('%Y-W%W', Agendamento.data_hora).label('periodo'),
                func.count(Agendamento.id).label('total'),
                func.sum(Servico.preco).label('receita')
            ).join(Servico).filter(
                Agendamento.empresa_id == empresa_id,
                Agendamento.data_hora >= start_date,
                Agendamento.data_hora <= end_date,
                Agendamento.status.in_(['confirmado', 'concluido'])
            ).group_by(func.strftime('%Y-W%W', Agendamento.data_hora)).all()
            
        else:  # month
            # Agrupar por mês
            query = db.session.query(
                func.strftime('%Y-%m', Agendamento.data_hora).label('periodo'),
                func.count(Agendamento.id).label('total'),
                func.sum(Servico.preco).label('receita')
            ).join(Servico).filter(
                Agendamento.empresa_id == empresa_id,
                Agendamento.data_hora >= start_date,
                Agendamento.data_hora <= end_date,
                Agendamento.status.in_(['confirmado', 'concluido'])
            ).group_by(func.strftime('%Y-%m', Agendamento.data_hora)).all()
        
        return [
            {
                'periodo': str(row.periodo),
                'agendamentos': row.total,
                'receita': float(row.receita or 0)
            }
            for row in query
        ]
    
    def get_servicos_mais_populares(self, empresa_id: int, limite: int = 10) -> List[Dict[str, Any]]:
        """Obtém serviços mais populares"""
        query = db.session.query(
            Servico.nome,
            func.count(Agendamento.id).label('total_agendamentos'),
            func.sum(Servico.preco).label('receita_total'),
            func.avg(Servico.preco).label('preco_medio')
        ).join(Agendamento).filter(
            Agendamento.empresa_id == empresa_id,
            Agendamento.status.in_(['confirmado', 'concluido'])
        ).group_by(Servico.id, Servico.nome).order_by(
            func.count(Agendamento.id).desc()
        ).limit(limite).all()
        
        return [
            {
                'nome': row.nome,
                'total_agendamentos': row.total_agendamentos,
                'receita_total': float(row.receita_total or 0),
                'preco_medio': float(row.preco_medio or 0)
            }
            for row in query
        ]
    
    def get_profissionais_performance(self, empresa_id: int) -> List[Dict[str, Any]]:
        """Obtém performance dos profissionais"""
        query = db.session.query(
            Profissional.nome,
            func.count(Agendamento.id).label('total_agendamentos'),
            func.sum(Servico.preco).label('receita_total'),
            func.avg(Servico.preco).label('ticket_medio')
        ).join(Agendamento).join(Servico).filter(
            Agendamento.empresa_id == empresa_id,
            Agendamento.status.in_(['confirmado', 'concluido'])
        ).group_by(Profissional.id, Profissional.nome).order_by(
            func.sum(Servico.preco).desc()
        ).all()
        
        return [
            {
                'nome': row.nome,
                'total_agendamentos': row.total_agendamentos,
                'receita_total': float(row.receita_total or 0),
                'ticket_medio': float(row.ticket_medio or 0)
            }
            for row in query
        ]
    
    def get_horarios_pico(self, empresa_id: int) -> List[Dict[str, Any]]:
        """Obtém horários de pico de agendamentos"""
        query = db.session.query(
            func.strftime('%H', Agendamento.data_hora).label('hora'),
            func.count(Agendamento.id).label('total_agendamentos')
        ).filter(
            Agendamento.empresa_id == empresa_id,
            Agendamento.status.in_(['confirmado', 'concluido'])
        ).group_by(func.strftime('%H', Agendamento.data_hora)).order_by(
            func.strftime('%H', Agendamento.data_hora)
        ).all()
        
        return [
            {
                'hora': f"{row.hora}:00",
                'agendamentos': row.total_agendamentos
            }
            for row in query
        ]
    
    def get_status_agendamentos(self, empresa_id: int, periodo: str = '30d') -> Dict[str, int]:
        """Obtém distribuição de status dos agendamentos"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=int(periodo.replace('d', '')))
        
        query = db.session.query(
            Agendamento.status,
            func.count(Agendamento.id).label('total')
        ).filter(
            Agendamento.empresa_id == empresa_id,
            Agendamento.data_hora >= start_date,
            Agendamento.data_hora <= end_date
        ).group_by(Agendamento.status).all()
        
        return {row.status: row.total for row in query}
    
    def get_clientes_frequentes(self, empresa_id: int, limite: int = 10) -> List[Dict[str, Any]]:
        """Obtém clientes mais frequentes"""
        query = db.session.query(
            Cliente.nome,
            Cliente.telefone,
            func.count(Agendamento.id).label('total_agendamentos'),
            func.sum(Servico.preco).label('valor_total'),
            func.max(Agendamento.data_hora).label('ultimo_agendamento')
        ).join(Agendamento).join(Servico).filter(
            Agendamento.empresa_id == empresa_id
        ).group_by(Cliente.id, Cliente.nome, Cliente.telefone).order_by(
            func.count(Agendamento.id).desc()
        ).limit(limite).all()
        
        return [
            {
                'nome': row.nome,
                'telefone': row.telefone,
                'total_agendamentos': row.total_agendamentos,
                'valor_total': float(row.valor_total or 0),
                'ultimo_agendamento': row.ultimo_agendamento.isoformat() if row.ultimo_agendamento else None
            }
            for row in query
        ]
    
    # Métodos auxiliares privados
    def _get_total_agendamentos(self, empresa_id: int, start_date: datetime, end_date: datetime) -> int:
        return db.session.query(Agendamento).filter(
            Agendamento.empresa_id == empresa_id,
            Agendamento.data_hora >= start_date,
            Agendamento.data_hora <= end_date,
            Agendamento.status.in_(['confirmado', 'concluido'])
        ).count()
    
    def _get_agendamentos_hoje(self, empresa_id: int) -> int:
        hoje = datetime.now().date()
        return db.session.query(Agendamento).filter(
            Agendamento.empresa_id == empresa_id,
            func.date(Agendamento.data_hora) == hoje
        ).count()
    
    def _get_total_clientes(self, empresa_id: int) -> int:
        return db.session.query(Cliente).filter(
            Cliente.empresa_id == empresa_id,
            Cliente.ativo == True
        ).count()
    
    def _get_clientes_ativos(self, empresa_id: int, start_date: datetime, end_date: datetime) -> int:
        return db.session.query(Cliente).join(Agendamento).filter(
            Agendamento.empresa_id == empresa_id,
            Agendamento.data_hora >= start_date,
            Agendamento.data_hora <= end_date
        ).distinct().count()
    
    def _get_novos_clientes(self, empresa_id: int, start_date: datetime, end_date: datetime) -> int:
        return db.session.query(Cliente).filter(
            Cliente.empresa_id == empresa_id,
            Cliente.criado_em >= start_date,
            Cliente.criado_em <= end_date
        ).count()
    
    def _get_receita_periodo(self, empresa_id: int, start_date: datetime, end_date: datetime) -> float:
        result = db.session.query(
            func.sum(Servico.preco)
        ).join(Agendamento).filter(
            Agendamento.empresa_id == empresa_id,
            Agendamento.data_hora >= start_date,
            Agendamento.data_hora <= end_date,
            Agendamento.status.in_(['confirmado', 'concluido'])
        ).scalar()
        
        return float(result or 0)
    
    def _get_receita_hoje(self, empresa_id: int) -> float:
        hoje = datetime.now().date()
        result = db.session.query(
            func.sum(Servico.preco)
        ).join(Agendamento).filter(
            Agendamento.empresa_id == empresa_id,
            func.date(Agendamento.data_hora) == hoje,
            Agendamento.status.in_(['confirmado', 'concluido'])
        ).scalar()
        
        return float(result or 0)
    
    def _get_taxa_ocupacao(self, empresa_id: int, start_date: datetime, end_date: datetime) -> float:
        # Simplificado: assumir 8 horas de trabalho por dia
        dias_periodo = (end_date - start_date).days
        horarios_disponiveis = dias_periodo * 8  # 8 slots por dia
        
        agendamentos = self._get_total_agendamentos(empresa_id, start_date, end_date)
        
        if horarios_disponiveis > 0:
            return (agendamentos / horarios_disponiveis) * 100
        return 0
    
    def _get_horarios_disponiveis_hoje(self, empresa_id: int) -> int:
        # Simplificado: 8 horários por dia
        return 8
    
    def _calcular_crescimento(self, valor_atual: float, valor_anterior: float) -> float:
        if valor_anterior > 0:
            return ((valor_atual - valor_anterior) / valor_anterior) * 100
        return 0 if valor_atual == 0 else 100


# Instância global do serviço
analytics_service = AnalyticsService()

