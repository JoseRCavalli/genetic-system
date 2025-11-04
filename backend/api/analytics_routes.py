"""
API REST - Parte 2: Analytics, Relatórios e Utilitários
"""

from flask import Blueprint, request, jsonify
from backend.services.analytics import AnalyticsService
from backend.models.database import get_session, ImportHistory

# Criar blueprint para analytics
analytics_api = Blueprint('analytics', __name__, url_prefix='/api/analytics')


def get_db():
    """Helper para pegar sessão do banco"""
    from app import engine
    return get_session(engine)


# ============================================================================
# DASHBOARD E ESTATÍSTICAS
# ============================================================================

@analytics_api.route('/dashboard', methods=['GET'])
def get_dashboard():
    """
    GET /api/analytics/dashboard
    Dados principais para o dashboard
    """
    try:
        db = get_db()
        analytics = AnalyticsService(db)
        
        stats = analytics.get_dashboard_stats()
        
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analytics_api.route('/distributions/<index>', methods=['GET'])
def get_distribution(index):
    """
    GET /api/analytics/distributions/:index
    Distribuição de um índice genético
    
    Query params:
        - entity: 'female' ou 'bull' (default: female)
        - bins: número de bins (default: 10)
    """
    try:
        db = get_db()
        analytics = AnalyticsService(db)
        
        entity = request.args.get('entity', 'female')
        bins = request.args.get('bins', 10, type=int)
        
        distribution = analytics.get_index_distribution(index, entity, bins)
        
        return jsonify(distribution)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analytics_api.route('/distributions', methods=['GET'])
def get_multiple_distributions():
    """
    GET /api/analytics/distributions
    Distribuições de múltiplos índices
    
    Query params:
        - indices: lista separada por vírgula (ex: milk,protein,fat)
    """
    try:
        db = get_db()
        analytics = AnalyticsService(db)
        
        indices_str = request.args.get('indices', 'milk,protein,fat,productive_life')
        indices = [i.strip() for i in indices_str.split(',')]
        
        distributions = analytics.get_multiple_distributions(indices)
        
        return jsonify(distributions)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analytics_api.route('/evolution/<index>', methods=['GET'])
def get_evolution(index):
    """
    GET /api/analytics/evolution/:index
    Evolução temporal de um índice
    
    Query params:
        - months: período em meses (default: 12)
    """
    try:
        db = get_db()
        analytics = AnalyticsService(db)
        
        months = request.args.get('months', 12, type=int)
        
        evolution = analytics.get_genetic_evolution(index, months)
        
        return jsonify(evolution)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# ANÁLISE DE ACASALAMENTOS
# ============================================================================

@analytics_api.route('/matings', methods=['GET'])
def get_mating_analysis():
    """
    GET /api/analytics/matings
    Análise completa dos acasalamentos
    """
    try:
        db = get_db()
        analytics = AnalyticsService(db)
        
        analysis = analytics.get_mating_analysis()
        
        return jsonify(analysis)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analytics_api.route('/bulls/performance', methods=['GET'])
def get_bull_performance():
    """
    GET /api/analytics/bulls/performance
    Performance dos touros
    
    Query params:
        - bull_id: ID específico (opcional)
    """
    try:
        db = get_db()
        analytics = AnalyticsService(db)
        
        bull_id = request.args.get('bull_id', type=int)
        
        performance = analytics.get_bull_performance(bull_id)
        
        return jsonify(performance)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analytics_api.route('/accuracy', methods=['GET'])
def get_prediction_accuracy():
    """
    GET /api/analytics/accuracy
    Análise de acurácia: Predito vs Real
    """
    try:
        db = get_db()
        analytics = AnalyticsService(db)
        
        accuracy = analytics.get_prediction_accuracy()
        
        return jsonify(accuracy)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# RELATÓRIOS
# ============================================================================

@analytics_api.route('/reports/herd', methods=['GET'])
def get_herd_report():
    """
    GET /api/analytics/reports/herd
    Relatório completo do rebanho
    """
    try:
        db = get_db()
        analytics = AnalyticsService(db)
        
        report = analytics.generate_herd_report()
        
        return jsonify(report)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# GRÁFICOS (dados formatados para Chart.js)
# ============================================================================

@analytics_api.route('/charts/distribution/<index>', methods=['GET'])
def get_chart_distribution(index):
    """
    GET /api/analytics/charts/distribution/:index
    Dados formatados para gráfico de distribuição (Chart.js)
    """
    try:
        db = get_db()
        analytics = AnalyticsService(db)
        
        entity = request.args.get('entity', 'female')
        bins = request.args.get('bins', 10, type=int)
        
        distribution = analytics.get_index_distribution(index, entity, bins)
        
        if 'error' in distribution:
            return jsonify(distribution), 404
        
        # Formatar para Chart.js
        chart_data = {
            'type': 'bar',
            'data': {
                'labels': [item['bin'] for item in distribution['histogram']],
                'datasets': [{
                    'label': f'{index.upper()} - Distribuição',
                    'data': [item['count'] for item in distribution['histogram']],
                    'backgroundColor': 'rgba(54, 162, 235, 0.5)',
                    'borderColor': 'rgba(54, 162, 235, 1)',
                    'borderWidth': 1
                }]
            },
            'options': {
                'responsive': True,
                'plugins': {
                    'title': {
                        'display': True,
                        'text': f'Distribuição de {index.upper()}'
                    }
                },
                'scales': {
                    'y': {
                        'beginAtZero': True,
                        'title': {
                            'display': True,
                            'text': 'Frequência'
                        }
                    }
                }
            },
            'statistics': distribution['statistics']
        }
        
        return jsonify(chart_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analytics_api.route('/charts/evolution/<index>', methods=['GET'])
def get_chart_evolution(index):
    """
    GET /api/analytics/charts/evolution/:index
    Dados formatados para gráfico de evolução temporal
    """
    try:
        db = get_db()
        analytics = AnalyticsService(db)
        
        months = request.args.get('months', 12, type=int)
        
        evolution = analytics.get_genetic_evolution(index, months)
        
        if 'error' in evolution:
            return jsonify(evolution), 404
        
        # Formatar para Chart.js
        chart_data = {
            'type': 'line',
            'data': {
                'labels': [item['date'] for item in evolution['evolution']],
                'datasets': [{
                    'label': f'{index.upper()} - Média do Rebanho',
                    'data': [item['average'] for item in evolution['evolution']],
                    'borderColor': 'rgba(75, 192, 192, 1)',
                    'backgroundColor': 'rgba(75, 192, 192, 0.2)',
                    'tension': 0.1,
                    'fill': True
                }]
            },
            'options': {
                'responsive': True,
                'plugins': {
                    'title': {
                        'display': True,
                        'text': f'Evolução de {index.upper()} ao Longo do Tempo'
                    }
                },
                'scales': {
                    'y': {
                        'title': {
                            'display': True,
                            'text': index.upper()
                        }
                    },
                    'x': {
                        'title': {
                            'display': True,
                            'text': 'Período'
                        }
                    }
                }
            },
            'trend': evolution.get('trend')
        }
        
        return jsonify(chart_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analytics_api.route('/charts/compatibility', methods=['GET'])
def get_chart_compatibility():
    """
    GET /api/analytics/charts/compatibility
    Distribuição de scores de compatibilidade
    """
    try:
        db = get_db()
        analytics = AnalyticsService(db)
        
        analysis = analytics.get_mating_analysis()
        
        distribution = analysis['compatibility']['distribution']
        
        # Formatar para Chart.js (Pizza)
        chart_data = {
            'type': 'doughnut',
            'data': {
                'labels': ['Excelente (≥80)', 'Bom (60-79)', 'Médio (40-59)', 'Fraco (<40)'],
                'datasets': [{
                    'label': 'Acasalamentos por Score',
                    'data': [
                        distribution.get('excellent', 0),
                        distribution.get('good', 0),
                        distribution.get('average', 0),
                        distribution.get('poor', 0)
                    ],
                    'backgroundColor': [
                        'rgba(34, 197, 94, 0.8)',   # Verde
                        'rgba(59, 130, 246, 0.8)',  # Azul
                        'rgba(250, 204, 21, 0.8)',  # Amarelo
                        'rgba(239, 68, 68, 0.8)'    # Vermelho
                    ],
                    'borderWidth': 2
                }]
            },
            'options': {
                'responsive': True,
                'plugins': {
                    'title': {
                        'display': True,
                        'text': 'Distribuição de Scores de Compatibilidade'
                    },
                    'legend': {
                        'position': 'bottom'
                    }
                }
            }
        }
        
        return jsonify(chart_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# HISTÓRICO DE IMPORTAÇÕES
# ============================================================================

@analytics_api.route('/imports', methods=['GET'])
def get_import_history():
    """
    GET /api/analytics/imports
    Histórico de importações
    """
    try:
        db = get_db()
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        query = db.query(ImportHistory).order_by(ImportHistory.imported_at.desc())
        
        total = query.count()
        imports = query.offset((page - 1) * per_page).limit(per_page).all()
        
        return jsonify({
            'total': total,
            'page': page,
            'per_page': per_page,
            'imports': [{
                'id': imp.id,
                'type': imp.import_type,
                'filename': imp.filename,
                'added': imp.records_added,
                'updated': imp.records_updated,
                'unchanged': imp.records_unchanged,
                'status': imp.status,
                'date': imp.imported_at.isoformat(),
                'user': imp.imported_by
            } for imp in imports]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# PREFERÊNCIAS DO USUÁRIO
# ============================================================================

from backend.models.database import UserPreference

@analytics_api.route('/preferences', methods=['GET'])
def get_preferences():
    """
    GET /api/analytics/preferences
    Preferências do usuário
    """
    try:
        db = get_db()
        
        prefs = db.query(UserPreference).first()
        
        if not prefs:
            # Criar preferências padrão
            prefs = UserPreference(
                user_name='Pedro',
                default_priorities={
                    'milk': 1.0,
                    'productive_life': 1.5,
                    'fertility_index': 1.3,
                    'scs': -1.2,
                    'udc': 1.1
                },
                max_inbreeding=6.0,
                top_n_bulls=5,
                preferred_indices=[
                    'milk', 'protein', 'fat', 'net_merit', 'productive_life',
                    'fertility_index', 'udc', 'flc', 'ptat', 'scs',
                    'dpr', 'hcr', 'ccr', 'rfi', 'beta_casein', 'gfi'
                ]
            )
            db.add(prefs)
            db.commit()
        
        return jsonify({
            'user_name': prefs.user_name,
            'default_priorities': prefs.default_priorities,
            'max_inbreeding': prefs.max_inbreeding,
            'top_n_bulls': prefs.top_n_bulls,
            'preferred_indices': prefs.preferred_indices,
            'updated_at': prefs.updated_at.isoformat() if prefs.updated_at else None
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analytics_api.route('/preferences', methods=['PUT'])
def update_preferences():
    """
    PUT /api/analytics/preferences
    Atualiza preferências do usuário
    """
    try:
        db = get_db()
        data = request.json
        
        prefs = db.query(UserPreference).first()
        
        if not prefs:
            prefs = UserPreference()
            db.add(prefs)
        
        # Atualizar campos
        if 'default_priorities' in data:
            prefs.default_priorities = data['default_priorities']
        if 'max_inbreeding' in data:
            prefs.max_inbreeding = data['max_inbreeding']
        if 'top_n_bulls' in data:
            prefs.top_n_bulls = data['top_n_bulls']
        if 'preferred_indices' in data:
            prefs.preferred_indices = data['preferred_indices']
        
        db.commit()
        
        return jsonify({
            'success': True,
            'message': 'Preferências atualizadas'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500