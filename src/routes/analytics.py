"""
Rotas para analytics e métricas
"""

from flask import Blueprint, request, jsonify
from ..services.analytics_service import analytics_service

analytics_bp = Blueprint('analytics', __name__)


@analytics_bp.route('/empresas/<int:empresa_id>/analytics/dashboard', methods=['GET'])
def get_dashboard_metrics(empresa_id):
    """Obtém métricas principais para o dashboard"""
    try:
        periodo = request.args.get('periodo', '30d')
        
        metrics = analytics_service.get_dashboard_metrics(empresa_id, periodo)
        
        return jsonify(metrics)
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@analytics_bp.route('/empresas/<int:empresa_id>/analytics/agendamentos', methods=['GET'])
def get_agendamentos_analytics(empresa_id):
    """Obtém analytics de agendamentos por período"""
    try:
        periodo = request.args.get('periodo', '30d')
        
        data = analytics_service.get_agendamentos_por_periodo(empresa_id, periodo)
        
        return jsonify({
            'periodo': periodo,
            'dados': data
        })
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@analytics_bp.route('/empresas/<int:empresa_id>/analytics/servicos', methods=['GET'])
def get_servicos_analytics(empresa_id):
    """Obtém analytics de serviços mais populares"""
    try:
        limite = request.args.get('limite', 10, type=int)
        
        data = analytics_service.get_servicos_mais_populares(empresa_id, limite)
        
        return jsonify({
            'servicos': data
        })
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@analytics_bp.route('/empresas/<int:empresa_id>/analytics/profissionais', methods=['GET'])
def get_profissionais_analytics(empresa_id):
    """Obtém analytics de performance dos profissionais"""
    try:
        data = analytics_service.get_profissionais_performance(empresa_id)
        
        return jsonify({
            'profissionais': data
        })
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@analytics_bp.route('/empresas/<int:empresa_id>/analytics/horarios-pico', methods=['GET'])
def get_horarios_pico(empresa_id):
    """Obtém horários de pico de agendamentos"""
    try:
        data = analytics_service.get_horarios_pico(empresa_id)
        
        return jsonify({
            'horarios': data
        })
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@analytics_bp.route('/empresas/<int:empresa_id>/analytics/status-agendamentos', methods=['GET'])
def get_status_agendamentos(empresa_id):
    """Obtém distribuição de status dos agendamentos"""
    try:
        periodo = request.args.get('periodo', '30d')
        
        data = analytics_service.get_status_agendamentos(empresa_id, periodo)
        
        return jsonify({
            'periodo': periodo,
            'status': data
        })
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@analytics_bp.route('/empresas/<int:empresa_id>/analytics/clientes-frequentes', methods=['GET'])
def get_clientes_frequentes(empresa_id):
    """Obtém clientes mais frequentes"""
    try:
        limite = request.args.get('limite', 10, type=int)
        
        data = analytics_service.get_clientes_frequentes(empresa_id, limite)
        
        return jsonify({
            'clientes': data
        })
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@analytics_bp.route('/empresas/<int:empresa_id>/analytics/relatorio-completo', methods=['GET'])
def get_relatorio_completo(empresa_id):
    """Obtém relatório completo com todas as métricas"""
    try:
        periodo = request.args.get('periodo', '30d')
        
        # Coletar todas as métricas
        dashboard_metrics = analytics_service.get_dashboard_metrics(empresa_id, periodo)
        agendamentos_periodo = analytics_service.get_agendamentos_por_periodo(empresa_id, periodo)
        servicos_populares = analytics_service.get_servicos_mais_populares(empresa_id, 5)
        profissionais_performance = analytics_service.get_profissionais_performance(empresa_id)
        horarios_pico = analytics_service.get_horarios_pico(empresa_id)
        status_agendamentos = analytics_service.get_status_agendamentos(empresa_id, periodo)
        clientes_frequentes = analytics_service.get_clientes_frequentes(empresa_id, 5)
        
        return jsonify({
            'periodo': periodo,
            'dashboard': dashboard_metrics,
            'agendamentos_periodo': agendamentos_periodo,
            'servicos_populares': servicos_populares,
            'profissionais_performance': profissionais_performance,
            'horarios_pico': horarios_pico,
            'status_agendamentos': status_agendamentos,
            'clientes_frequentes': clientes_frequentes,
            'gerado_em': analytics_service._get_agendamentos_hoje.__func__(analytics_service, empresa_id)
        })
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

