"""
Serviço de Analytics e Estatísticas
Gera dados para gráficos, relatórios e análises do rebanho
"""

from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta
from collections import Counter

from backend.models.database import Female, Bull, Mating, BatchMating, ImportHistory


class AnalyticsService:
    """Serviço de analytics e estatísticas"""
    
    def __init__(self, db_session: Session):
        self.session = db_session
    
    # ========================================================================
    # DASHBOARD PRINCIPAL
    # ========================================================================
    
    def get_dashboard_stats(self) -> Dict:
        """
        Estatísticas principais para o dashboard
        """
        # Contagens básicas
        total_females = self.session.query(func.count(Female.id)).scalar()
        active_females = self.session.query(func.count(Female.id)).filter(
            Female.is_active == True
        ).scalar()
        
        total_bulls = self.session.query(func.count(Bull.id)).scalar()
        available_bulls = self.session.query(func.count(Bull.id)).filter(
            Bull.is_available == True
        ).scalar()
        
        total_matings = self.session.query(func.count(Mating.id)).scalar()
        
        # Acasalamentos recentes (últimos 30 dias)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_matings = self.session.query(func.count(Mating.id)).filter(
            Mating.created_at >= thirty_days_ago
        ).scalar()
        
        # Acasalamentos bem-sucedidos
        successful_matings = self.session.query(func.count(Mating.id)).filter(
            Mating.success == True
        ).scalar()
        
        success_rate = (successful_matings / total_matings * 100) if total_matings > 0 else 0
        
        # Médias genéticas do rebanho
        avg_milk = self.session.query(func.avg(Female.milk)).filter(
            Female.is_active == True,
            Female.milk.isnot(None)
        ).scalar() or 0
        
        avg_productive_life = self.session.query(func.avg(Female.productive_life)).filter(
            Female.is_active == True,
            Female.productive_life.isnot(None)
        ).scalar() or 0
        
        avg_inbreeding = self.session.query(func.avg(Female.genomic_inbreeding)).filter(
            Female.is_active == True,
            Female.genomic_inbreeding.isnot(None)
        ).scalar() or 0
        
        # Top touros mais usados
        top_bulls_query = self.session.query(
            Bull.code,
            Bull.name,
            func.count(Mating.id).label('usage_count')
        ).join(
            Mating, Mating.bull_id == Bull.id
        ).group_by(
            Bull.id
        ).order_by(
            func.count(Mating.id).desc()
        ).limit(5).all()
        
        top_bulls = [
            {'code': code, 'name': name, 'count': count}
            for code, name, count in top_bulls_query
        ]
        
        return {
            'summary': {
                'total_females': total_females,
                'active_females': active_females,
                'total_bulls': total_bulls,
                'available_bulls': available_bulls,
                'total_matings': total_matings,
                'recent_matings': recent_matings,
                'success_rate': round(success_rate, 1)
            },
            'herd_averages': {
                'milk': round(avg_milk, 0),
                'productive_life': round(avg_productive_life, 2),
                'genomic_inbreeding': round(avg_inbreeding, 2)
            },
            'top_bulls': top_bulls,
            'last_updated': datetime.now().isoformat()
        }
    
    # ========================================================================
    # GRÁFICOS - DISTRIBUIÇÃO DE ÍNDICES
    # ========================================================================
    
    def get_index_distribution(self, index: str, 
                               entity: str = 'female',
                               bins: int = 10) -> Dict:
        """
        Distribuição de um índice genético
        
        Args:
            index: Nome do índice (milk, productive_life, etc)
            entity: 'female' ou 'bull'
            bins: Número de bins para histograma
        
        Returns:
            Dados para gráfico de distribuição
        """
        Model = Female if entity == 'female' else Bull
        
        # Buscar valores
        values = self.session.query(
            getattr(Model, index)
        ).filter(
            getattr(Model, index).isnot(None)
        ).all()
        
        values = [v[0] for v in values if v[0] is not None]
        
        if not values:
            return {'error': 'Sem dados disponíveis'}
        
        # Calcular estatísticas
        values.sort()
        n = len(values)
        
        stats = {
            'count': n,
            'min': round(min(values), 2),
            'max': round(max(values), 2),
            'mean': round(sum(values) / n, 2),
            'median': round(values[n // 2], 2),
            'q1': round(values[n // 4], 2),
            'q3': round(values[3 * n // 4], 2)
        }
        
        # Criar histograma
        bin_width = (stats['max'] - stats['min']) / bins
        histogram = []
        
        for i in range(bins):
            bin_start = stats['min'] + i * bin_width
            bin_end = bin_start + bin_width
            
            count = sum(1 for v in values if bin_start <= v < bin_end)
            
            histogram.append({
                'bin': f"{bin_start:.1f} - {bin_end:.1f}",
                'count': count,
                'percentage': round(count / n * 100, 1)
            })
        
        return {
            'index': index,
            'entity': entity,
            'statistics': stats,
            'histogram': histogram
        }
    
    def get_multiple_distributions(self, indices: List[str]) -> Dict:
        """Distribuições de múltiplos índices para comparação"""
        distributions = {}
        
        for index in indices:
            dist = self.get_index_distribution(index, 'female')
            if 'error' not in dist:
                distributions[index] = dist['statistics']
        
        return distributions
    
    # ========================================================================
    # GRÁFICOS - EVOLUÇÃO TEMPORAL
    # ========================================================================
    
    def get_genetic_evolution(self, index: str, 
                             months: int = 12) -> Dict:
        """
        Evolução temporal de um índice genético do rebanho
        Baseado em dados de importações e acasalamentos
        """
        # Buscar histórico de importações
        start_date = datetime.now() - timedelta(days=months * 30)
        
        imports = self.session.query(ImportHistory).filter(
            ImportHistory.imported_at >= start_date,
            ImportHistory.import_type == 'females_excel'
        ).order_by(ImportHistory.imported_at).all()
        
        if not imports:
            return {'error': 'Sem dados históricos suficientes'}
        
        # Para cada importação, calcular média do índice
        evolution = []
        
        for imp in imports:
            # Buscar fêmeas ativas naquela data
            avg_value = self.session.query(func.avg(getattr(Female, index))).filter(
                Female.last_updated <= imp.imported_at,
                getattr(Female, index).isnot(None)
            ).scalar()
            
            if avg_value:
                evolution.append({
                    'date': imp.imported_at.strftime('%Y-%m'),
                    'average': round(avg_value, 2),
                    'import_id': imp.id
                })
        
        # Calcular tendência (simples)
        if len(evolution) >= 2:
            first_value = evolution[0]['average']
            last_value = evolution[-1]['average']
            change = last_value - first_value
            change_percent = (change / first_value * 100) if first_value != 0 else 0
            
            trend = {
                'direction': 'up' if change > 0 else 'down',
                'change': round(change, 2),
                'change_percent': round(change_percent, 1)
            }
        else:
            trend = None
        
        return {
            'index': index,
            'period_months': months,
            'evolution': evolution,
            'trend': trend
        }
    
    # ========================================================================
    # ANÁLISE DE ACASALAMENTOS
    # ========================================================================
    
    def get_mating_analysis(self) -> Dict:
        """
        Análise completa dos acasalamentos realizados
        """
        # Total de acasalamentos por status
        status_counts = {}
        statuses = self.session.query(
            Mating.status,
            func.count(Mating.id)
        ).group_by(Mating.status).all()
        
        for status, count in statuses:
            status_counts[status or 'unknown'] = count
        
        # Taxa de sucesso
        total = self.session.query(func.count(Mating.id)).scalar()
        successful = self.session.query(func.count(Mating.id)).filter(
            Mating.success == True
        ).scalar()
        
        success_rate = (successful / total * 100) if total > 0 else 0
        
        # Distribuição de scores de compatibilidade
        scores = self.session.query(Mating.compatibility_score).filter(
            Mating.compatibility_score.isnot(None)
        ).all()
        
        scores = [s[0] for s in scores if s[0] is not None]
        
        if scores:
            avg_score = sum(scores) / len(scores)
            score_distribution = {
                'excellent': sum(1 for s in scores if s >= 80),
                'good': sum(1 for s in scores if 60 <= s < 80),
                'average': sum(1 for s in scores if 40 <= s < 60),
                'poor': sum(1 for s in scores if s < 40)
            }
        else:
            avg_score = 0
            score_distribution = {}
        
        # Distribuição de consanguinidade
        inbreeding_values = self.session.query(Mating.predicted_inbreeding).filter(
            Mating.predicted_inbreeding.isnot(None)
        ).all()
        
        inbreeding_values = [i[0] for i in inbreeding_values if i[0] is not None]
        
        if inbreeding_values:
            avg_inbreeding = sum(inbreeding_values) / len(inbreeding_values)
            inbreeding_distribution = {
                'low': sum(1 for i in inbreeding_values if i < 4.5),
                'moderate': sum(1 for i in inbreeding_values if 4.5 <= i < 6.0),
                'high': sum(1 for i in inbreeding_values if 6.0 <= i < 8.0),
                'very_high': sum(1 for i in inbreeding_values if i >= 8.0)
            }
        else:
            avg_inbreeding = 0
            inbreeding_distribution = {}
        
        return {
            'total_matings': total,
            'by_status': status_counts,
            'success_rate': round(success_rate, 1),
            'compatibility': {
                'average_score': round(avg_score, 1),
                'distribution': score_distribution
            },
            'inbreeding': {
                'average': round(avg_inbreeding, 2),
                'distribution': inbreeding_distribution
            }
        }
    
    def get_bull_performance(self, bull_id: Optional[int] = None) -> Dict:
        """
        Performance de touros nos acasalamentos
        
        Args:
            bull_id: ID específico ou None para todos
        """
        if bull_id:
            # Performance de um touro específico
            bull = self.session.query(Bull).get(bull_id)
            if not bull:
                return {'error': 'Touro não encontrado'}
            
            matings = self.session.query(Mating).filter(
                Mating.bull_id == bull_id
            ).all()
            
            if not matings:
                return {
                    'bull': {'code': bull.code, 'name': bull.name},
                    'matings_count': 0,
                    'message': 'Sem acasalamentos registrados'
                }
            
            total = len(matings)
            successful = sum(1 for m in matings if m.success)
            avg_score = sum(m.compatibility_score for m in matings if m.compatibility_score) / total
            
            return {
                'bull': {'code': bull.code, 'name': bull.name},
                'matings_count': total,
                'successful_matings': successful,
                'success_rate': round(successful / total * 100, 1),
                'avg_compatibility_score': round(avg_score, 1)
            }
        else:
            # Ranking de todos os touros
            bull_stats = {}
            
            matings = self.session.query(Mating).all()
            
            for mating in matings:
                if not mating.bull_id:
                    continue
                
                if mating.bull_id not in bull_stats:
                    bull_stats[mating.bull_id] = {
                        'total': 0,
                        'successful': 0,
                        'scores': []
                    }
                
                bull_stats[mating.bull_id]['total'] += 1
                if mating.success:
                    bull_stats[mating.bull_id]['successful'] += 1
                if mating.compatibility_score:
                    bull_stats[mating.bull_id]['scores'].append(mating.compatibility_score)
            
            # Construir ranking
            ranking = []
            for bull_id, stats in bull_stats.items():
                bull = self.session.query(Bull).get(bull_id)
                if not bull:
                    continue
                
                success_rate = (stats['successful'] / stats['total'] * 100) if stats['total'] > 0 else 0
                avg_score = sum(stats['scores']) / len(stats['scores']) if stats['scores'] else 0
                
                ranking.append({
                    'bull': {'code': bull.code, 'name': bull.name},
                    'matings_count': stats['total'],
                    'success_rate': round(success_rate, 1),
                    'avg_compatibility_score': round(avg_score, 1)
                })
            
            # Ordenar por número de acasalamentos
            ranking.sort(key=lambda x: x['matings_count'], reverse=True)
            
            return {
                'total_bulls_used': len(ranking),
                'ranking': ranking[:20]  # Top 20
            }
    
    # ========================================================================
    # PREDITO VS REAL
    # ========================================================================
    
    def get_prediction_accuracy(self) -> Dict:
        """
        Análise de acurácia: Predito vs Real
        Para acasalamentos onde já há dados do bezerro
        """
        # Buscar acasalamentos com dados reais
        matings_with_results = self.session.query(Mating).filter(
            Mating.actual_genetic_data.isnot(None),
            Mating.predicted_pppv.isnot(None)
        ).all()
        
        if not matings_with_results:
            return {
                'message': 'Sem dados suficientes para análise',
                'matings_with_results': 0
            }
        
        # Comparar predito vs real para cada índice
        comparisons = {}
        
        for mating in matings_with_results:
            predicted = mating.predicted_pppv or {}
            actual = mating.actual_genetic_data or {}
            
            for index, pred_data in predicted.items():
                if index not in comparisons:
                    comparisons[index] = {
                        'predictions': [],
                        'actuals': [],
                        'errors': []
                    }
                
                pred_value = pred_data.get('pppv')
                act_value = actual.get(index)
                
                if pred_value is not None and act_value is not None:
                    try:
                        pred_value = float(pred_value)
                        act_value = float(act_value)
                        
                        error = act_value - pred_value
                        
                        comparisons[index]['predictions'].append(pred_value)
                        comparisons[index]['actuals'].append(act_value)
                        comparisons[index]['errors'].append(error)
                    except (ValueError, TypeError):
                        continue
        
        # Calcular estatísticas
        accuracy_stats = {}
        
        for index, data in comparisons.items():
            if not data['predictions']:
                continue
            
            n = len(data['predictions'])
            errors = data['errors']
            
            mae = sum(abs(e) for e in errors) / n  # Mean Absolute Error
            rmse = (sum(e**2 for e in errors) / n) ** 0.5  # Root Mean Square Error
            
            accuracy_stats[index] = {
                'sample_size': n,
                'mae': round(mae, 2),
                'rmse': round(rmse, 2),
                'avg_predicted': round(sum(data['predictions']) / n, 2),
                'avg_actual': round(sum(data['actuals']) / n, 2)
            }
        
        return {
            'matings_with_results': len(matings_with_results),
            'indices_analyzed': list(accuracy_stats.keys()),
            'accuracy': accuracy_stats
        }
    
    # ========================================================================
    # RELATÓRIOS
    # ========================================================================
    
    def generate_herd_report(self) -> Dict:
        """
        Relatório completo do rebanho
        """
        # Dashboard stats
        dashboard = self.get_dashboard_stats()
        
        # Distribuições principais
        distributions = self.get_multiple_distributions([
            'milk', 'productive_life', 'fertility_index', 'udc'
        ])
        
        # Análise de acasalamentos
        mating_analysis = self.get_mating_analysis()
        
        # Performance de touros
        bull_performance = self.get_bull_performance()
        
        return {
            'report_date': datetime.now().isoformat(),
            'dashboard': dashboard,
            'genetic_distributions': distributions,
            'mating_analysis': mating_analysis,
            'bull_performance': bull_performance
        }