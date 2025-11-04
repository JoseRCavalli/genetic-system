"""
Serviço de Matching e Recomendação
Algoritmo para recomendar melhores touros para cada fêmea
"""

from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from backend.models.database import Female, Bull
from backend.services.genetics import genetic_calculator


class MatchingService:
    """Serviço de matching entre fêmeas e touros"""
    
    def __init__(self, db_session: Session):
        self.session = db_session
        self.calculator = genetic_calculator
    
    # ========================================================================
    # MATCHING INDIVIDUAL
    # ========================================================================
    
    def match_single(self, female_id: int, bull_id: int) -> Dict:
        """
        Analisa um acasalamento específico (manual)
        
        Returns:
            Dict com todas as análises e predições
        """
        # Buscar animais
        female = self.session.query(Female).get(female_id)
        bull = self.session.query(Bull).get(bull_id)
        
        if not female:
            raise ValueError(f"Fêmea {female_id} não encontrada")
        if not bull:
            raise ValueError(f"Touro {bull_id} não encontrado")
        
        # Preparar dados
        female_data = self._prepare_female_data(female)
        bull_data = self._prepare_bull_data(bull)
        
        # Cálculos
        pppv = self.calculator.calculate_pppv(female_data, bull_data)
        inbreeding = self.calculator.calculate_inbreeding(female_data, bull_data)
        compatibility = self.calculator.calculate_compatibility_score(
            female_data, bull_data
        )
        predictions = self.calculator.predict_offspring_performance(pppv)
        
        return {
            'female': {
                'id': female.id,
                'reg_id': female.reg_id,
                'internal_id': female.internal_id,
                'name': female.name,
                'main_indices': self._get_main_indices(female_data)
            },
            'bull': {
                'id': bull.id,
                'code': bull.code,
                'name': bull.name,
                'source': bull.source,
                'main_indices': self._get_main_indices(bull_data)
            },
            'analysis': {
                'pppv': pppv,
                'inbreeding': inbreeding,
                'compatibility': compatibility,
                'predictions': predictions
            },
            'recommendation': self._generate_recommendation(
                compatibility, inbreeding
            )
        }
    
    # ========================================================================
    # MATCHING EM LOTE
    # ========================================================================
    
    def match_batch(self, female_ids: List[int], 
                   priorities: Optional[Dict] = None,
                   max_inbreeding: float = 6.0,
                   top_n: int = 5,
                   filters: Optional[Dict] = None) -> Dict:
        """
        Encontra os melhores touros para um lote de fêmeas
        
        Args:
            female_ids: Lista de IDs das fêmeas
            priorities: Pesos customizados para cálculo
            max_inbreeding: Limite de consanguinidade (apenas informativo)
            top_n: Quantos touros retornar para cada fêmea
            filters: Filtros adicionais para touros
        
        Returns:
            Dict com recomendações para cada fêmea
        """
        results = []
        
        # Buscar fêmeas
        females = self.session.query(Female).filter(
            Female.id.in_(female_ids)
        ).all()
        
        # Buscar touros disponíveis
        bulls_query = self.session.query(Bull).filter(
            Bull.is_available == True
        )
        
        # Aplicar filtros
        if filters:
            bulls_query = self._apply_bull_filters(bulls_query, filters)
        
        bulls = bulls_query.all()
        
        if not bulls:
            raise ValueError("Nenhum touro disponível com os filtros especificados")
        
        print(f"Processando {len(females)} fêmeas contra {len(bulls)} touros...")
        
        # Para cada fêmea
        for idx, female in enumerate(females):
            print(f"  Fêmea {idx+1}/{len(females)}: {female.reg_id or female.internal_id}")
            
            female_data = self._prepare_female_data(female)
            
            # Calcular score com cada touro
            bull_scores = []
            for bull in bulls:
                bull_data = self._prepare_bull_data(bull)
                
                # Calcular compatibilidade
                compatibility = self.calculator.calculate_compatibility_score(
                    female_data, bull_data, priorities
                )
                
                # Calcular consanguinidade
                inbreeding = self.calculator.calculate_inbreeding(
                    female_data, bull_data
                )
                
                bull_scores.append({
                    'bull': bull,
                    'score': compatibility['score'],
                    'compatibility': compatibility,
                    'inbreeding': inbreeding
                })
            
            # Ordenar por score (maior = melhor)
            bull_scores.sort(key=lambda x: x['score'], reverse=True)
            
            # Pegar top N
            top_bulls = []
            for rank, item in enumerate(bull_scores[:top_n], 1):
                bull = item['bull']
                
                # Calcular PPPV para os top bulls
                bull_data = self._prepare_bull_data(bull)
                pppv = self.calculator.calculate_pppv(female_data, bull_data)
                
                top_bulls.append({
                    'rank': rank,
                    'bull': {
                        'id': bull.id,
                        'code': bull.code,
                        'name': bull.name,
                        'source': bull.source,
                        'main_indices': self._get_main_indices(bull_data)
                    },
                    'score': item['score'],
                    'compatibility': item['compatibility'],
                    'inbreeding': item['inbreeding'],
                    'pppv_summary': self._summarize_pppv(pppv),
                    'recommendation': self._generate_recommendation(
                        item['compatibility'],
                        item['inbreeding']
                    )
                })
            
            results.append({
                'female': {
                    'id': female.id,
                    'reg_id': female.reg_id,
                    'internal_id': female.internal_id,
                    'name': female.name,
                    'main_indices': self._get_main_indices(female_data)
                },
                'top_bulls': top_bulls
            })
        
        return {
            'summary': {
                'total_females': len(females),
                'total_bulls_analyzed': len(bulls),
                'top_n': top_n,
                'priorities_used': priorities or self.calculator.default_weights,
                'max_inbreeding': max_inbreeding
            },
            'results': results
        }
    
    # ========================================================================
    # BUSCA E RECOMENDAÇÃO
    # ========================================================================
    
    def find_best_bulls(self, criteria: Dict, limit: int = 10) -> List[Bull]:
        """
        Busca touros que atendem critérios específicos
        
        Args:
            criteria: Dict com critérios {index: min_value}
            limit: Quantos touros retornar
        
        Returns:
            Lista de touros ordenados por Net Merit
        """
        query = self.session.query(Bull).filter(Bull.is_available == True)
        
        # Aplicar critérios
        for index, min_value in criteria.items():
            if hasattr(Bull, index):
                query = query.filter(getattr(Bull, index) >= min_value)
        
        # Ordenar por Net Merit (padrão)
        query = query.order_by(Bull.net_merit.desc())
        
        return query.limit(limit).all()
    
    def recommend_for_improvement(self, female_id: int, 
                                 target_index: str,
                                 top_n: int = 5) -> List[Dict]:
        """
        Recomenda touros para melhorar um índice específico da fêmea
        
        Args:
            female_id: ID da fêmea
            target_index: Índice que quer melhorar (ex: 'milk', 'udc')
            top_n: Quantos touros retornar
        
        Returns:
            Lista de touros ordenados pelo valor do target_index
        """
        female = self.session.query(Female).get(female_id)
        if not female:
            raise ValueError(f"Fêmea {female_id} não encontrada")
        
        # Buscar touros com alto valor no target_index
        query = self.session.query(Bull).filter(
            Bull.is_available == True
        )
        
        if hasattr(Bull, target_index):
            query = query.filter(
                getattr(Bull, target_index).isnot(None)
            ).order_by(
                getattr(Bull, target_index).desc()
            )
        
        bulls = query.limit(top_n * 2).all()  # Pegar mais para filtrar
        
        # Calcular compatibilidade com cada um
        female_data = self._prepare_female_data(female)
        
        recommendations = []
        for bull in bulls:
            bull_data = self._prepare_bull_data(bull)
            
            compatibility = self.calculator.calculate_compatibility_score(
                female_data, bull_data
            )
            inbreeding = self.calculator.calculate_inbreeding(
                female_data, bull_data
            )
            
            # Pegar valor do target_index
            target_value = getattr(bull, target_index, None)
            
            recommendations.append({
                'bull': bull,
                'target_value': target_value,
                'compatibility_score': compatibility['score'],
                'inbreeding': inbreeding['expected_inbreeding']
            })
        
        # Ordenar por target_value
        recommendations.sort(key=lambda x: x['target_value'] or -999, reverse=True)
        
        # Retornar top N
        result = []
        for item in recommendations[:top_n]:
            bull = item['bull']
            result.append({
                'bull': {
                    'id': bull.id,
                    'code': bull.code,
                    'name': bull.name,
                    target_index: item['target_value']
                },
                'compatibility_score': item['compatibility_score'],
                'inbreeding': item['inbreeding'],
                'improvement_potential': self._calculate_improvement(
                    female, bull, target_index
                )
            })
        
        return result
    
    def _calculate_improvement(self, female: Female, bull: Bull, 
                              index: str) -> Dict:
        """Calcula potencial de melhoria"""
        female_value = getattr(female, index, None)
        bull_value = getattr(bull, index, None)
        
        if female_value is None or bull_value is None:
            return {'possible': False}
        
        # PPPV = média
        pppv = (female_value + bull_value) / 2
        improvement = pppv - female_value
        improvement_percent = (improvement / abs(female_value)) * 100 if female_value != 0 else 0
        
        return {
            'possible': True,
            'female_value': round(female_value, 2),
            'bull_value': round(bull_value, 2),
            'expected_offspring': round(pppv, 2),
            'absolute_improvement': round(improvement, 2),
            'percent_improvement': round(improvement_percent, 1)
        }
    
    # ========================================================================
    # UTILITÁRIOS
    # ========================================================================
    
    def _prepare_female_data(self, female: Female) -> Dict:
        """Prepara dados da fêmea para cálculos"""
        data = {
            'id': female.id,
            'reg_id': female.reg_id,
            'internal_id': female.internal_id,
            'genetic_data': female.genetic_data or {},
        }
        
        # Adicionar índices principais
        indices = [
            'milk', 'protein', 'fat', 'productive_life', 'scs',
            'dpr', 'fertility_index', 'udc', 'flc', 'ptat',
            'net_merit', 'tpi', 'genomic_inbreeding'
        ]
        
        for index in indices:
            value = getattr(female, index, None)
            if value is not None:
                data[index] = value
        
        return data
    
    def _prepare_bull_data(self, bull: Bull) -> Dict:
        """Prepara dados do touro para cálculos"""
        data = {
            'id': bull.id,
            'code': bull.code,
            'name': bull.name,
            'source': bull.source,
            'genetic_data': bull.genetic_data or {},
        }
        
        # Adicionar índices principais
        indices = [
            'milk', 'protein', 'fat', 'net_merit', 'cheese_merit',
            'grazing_merit', 'tpi', 'gtpi', 'udc', 'flc', 'ptat',
            'productive_life', 'scs', 'dpr', 'fertility_index',
            'rfi', 'beta_casein', 'kappa_casein', 'gfi'
        ]
        
        for index in indices:
            value = getattr(bull, index, None)
            if value is not None:
                data[index] = value
        
        return data
    
    def _get_main_indices(self, data: Dict) -> Dict:
        """Extrai índices principais de forma legível"""
        indices = {}
        
        keys = [
            'milk', 'protein', 'fat', 'net_merit', 'productive_life',
            'fertility_index', 'udc', 'scs', 'ptat'
        ]
        
        for key in keys:
            value = data.get(key)
            if value is not None:
                indices[key] = round(value, 2) if isinstance(value, float) else value
        
        return indices
    
    def _summarize_pppv(self, pppv: Dict) -> Dict:
        """Resume PPPV para visualização rápida"""
        summary = {}
        
        # Principais índices para mostrar
        main_indices = ['milk', 'protein', 'fat', 'productive_life', 
                       'fertility_index', 'udc']
        
        for index in main_indices:
            if index in pppv:
                summary[index] = pppv[index]['pppv']
        
        return summary
    
    def _apply_bull_filters(self, query, filters: Dict):
        """Aplica filtros à query de touros"""
        
        # Filtro: Milk mínimo
        if 'min_milk' in filters and filters['min_milk']:
            query = query.filter(Bull.milk >= filters['min_milk'])
        
        # Filtro: Net Merit mínimo
        if 'min_net_merit' in filters and filters['min_net_merit']:
            query = query.filter(Bull.net_merit >= filters['min_net_merit'])
        
        # Filtro: Productive Life mínimo
        if 'min_productive_life' in filters and filters['min_productive_life']:
            query = query.filter(Bull.productive_life >= filters['min_productive_life'])
        
        # Filtro: Beta-Casein
        if 'beta_casein' in filters and filters['beta_casein']:
            query = query.filter(Bull.beta_casein == filters['beta_casein'])
        
        # Filtro: GFI máximo
        if 'max_gfi' in filters and filters['max_gfi']:
            query = query.filter(Bull.gfi <= filters['max_gfi'])
        
        # Filtro: Fonte
        if 'source' in filters and filters['source']:
            query = query.filter(Bull.source == filters['source'])
        
        return query
    
    def _generate_recommendation(self, compatibility: Dict, 
                                inbreeding: Dict) -> Dict:
        """
        Gera recomendação final sobre o acasalamento
        """
        score = compatibility['score']
        inb = inbreeding['expected_inbreeding']
        
        # Determinar status
        if score >= 75 and inb <= 6.0:
            status = 'highly_recommended'
            message = 'Acasalamento altamente recomendado!'
            color = 'green'
        elif score >= 60 and inb <= 6.0:
            status = 'recommended'
            message = 'Acasalamento recomendado'
            color = 'blue'
        elif score >= 50 or inb <= 8.0:
            status = 'acceptable'
            message = 'Acasalamento aceitável - monitorar resultados'
            color = 'yellow'
        else:
            status = 'not_recommended'
            message = 'Acasalamento não recomendado - considerar outras opções'
            color = 'red'
        
        # Pontos positivos e negativos
        positives = []
        negatives = []
        
        if score >= 70:
            positives.append('Excelente compatibilidade genética')
        if inb <= 4.0:
            positives.append('Baixa consanguinidade')
        if compatibility.get('adjustments', {}).get('complementarity_bonus', 0) > 0:
            positives.append('Touro complementa fraquezas da fêmea')
        
        if score < 50:
            negatives.append('Compatibilidade abaixo da média')
        if inb > 6.0:
            negatives.append(f'Consanguinidade elevada ({inb:.1f}%)')
        if inb > 8.0:
            negatives.append('Alto risco genético')
        
        return {
            'status': status,
            'message': message,
            'color': color,
            'positives': positives,
            'negatives': negatives,
            'confidence': self._calculate_confidence(compatibility, inbreeding)
        }
    
    def _calculate_confidence(self, compatibility: Dict, inbreeding: Dict) -> float:
        """Calcula nível de confiança da recomendação"""
        # Baseado em reliability dos dados
        # Simplificado para agora
        base_confidence = 75.0
        
        # Ajustar baseado em dados disponíveis
        if inbreeding['method'] == 'genomic':
            base_confidence += 10  # +10% se tem dados genômicos
        
        return min(95, base_confidence)