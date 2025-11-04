"""
Serviço de Cálculos Genéticos
Funções para calcular PPPV, consanguinidade, compatibilidade
"""

from typing import Dict, List, Optional
import math


class GeneticCalculator:
    """Calculadora de índices genéticos"""
    
    def __init__(self):
        # Pesos padrão para cálculo de compatibilidade
        self.default_weights = {
            'milk': 1.0,
            'protein': 1.2,
            'fat': 1.0,
            'productive_life': 1.5,
            'fertility_index': 1.3,
            'scs': -1.2,  # Negativo = menor é melhor
            'udc': 1.1,
            'flc': 0.8,
            'ptat': 0.9,
        }
    
    # ========================================================================
    # PPPV - PREDICTED PRODUCING VALUE
    # ========================================================================
    
    def calculate_pppv(self, female_data: Dict, bull_data: Dict, 
                       indices: Optional[List[str]] = None) -> Dict:
        """
        Calcula PPPV (Predicted Producing Value) para o possível bezerro
        
        PPPV = (PTA_Touro + PTA_Vaca) / 2
        
        Args:
            female_data: Dados genéticos da fêmea
            bull_data: Dados genéticos do touro
            indices: Lista de índices para calcular (None = todos)
        
        Returns:
            Dict com PPPV calculado para cada índice
        """
        if not indices:
            # Índices principais para calcular
            indices = [
                'milk', 'protein', 'fat', 'fat_percent', 'protein_percent',
                'productive_life', 'scs', 'dpr', 'fertility_index',
                'udc', 'flc', 'ptat', 'net_merit', 'tpi'
            ]
        
        results = {}
        
        # Mapear nomes de colunas (fêmea pode ter nomes diferentes)
        female_mapping = {
            'milk': 'MILK',
            'protein': 'PROTEIN',
            'fat': 'FAT',
            'fat_percent': 'FAT PERCENT',
            'protein_percent': 'PROTEIN PERCENT',
            'productive_life': 'PRODUCTIVE LIFE',
            'scs': 'SOMATIC CELL SCORE',
            'dpr': 'DAUGHTER PREGNANCY RATE',
            'fertility_index': 'FERTILITY INDEX',
            'udc': 'UDC',
            'flc': 'FLC',
            'ptat': 'PTAT',
            'net_merit': 'NET MERIT',
            'tpi': 'TPI',
        }
        
        for index in indices:
            # Pegar valores
            female_key = female_mapping.get(index, index.upper())
            
            # Tentar pegar do genetic_data ou diretamente
            female_value = None
            if 'genetic_data' in female_data and female_data['genetic_data']:
                female_value = female_data['genetic_data'].get(female_key)
            if female_value is None:
                female_value = female_data.get(index)
            
            bull_value = None
            if 'genetic_data' in bull_data and bull_data['genetic_data']:
                bull_value = bull_data['genetic_data'].get(index)
            if bull_value is None:
                bull_value = bull_data.get(index)
            
            # Converter para float
            try:
                if female_value is not None:
                    female_value = float(female_value)
                if bull_value is not None:
                    bull_value = float(bull_value)
            except (ValueError, TypeError):
                continue
            
            # Calcular PPPV se ambos existem
            if female_value is not None and bull_value is not None:
                pppv = (female_value + bull_value) / 2
                
                # Calcular confiabilidade (média das confiabilidades dos pais)
                female_reliability = self._get_reliability(female_data, index)
                bull_reliability = self._get_reliability(bull_data, index)
                combined_reliability = (female_reliability + bull_reliability) / 2
                
                results[index] = {
                    'female': round(female_value, 2),
                    'bull': round(bull_value, 2),
                    'pppv': round(pppv, 2),
                    'reliability': round(combined_reliability, 1),
                    'interpretation': self._interpret_pppv(index, pppv)
                }
        
        return results
    
    def _get_reliability(self, data: Dict, index: str) -> float:
        """
        Busca confiabilidade do índice
        Em geral, touros têm ~70-85%, vacas ~50-70%
        """
        # Padrões conservadores
        if 'source' in data and data['source']:
            return 75.0  # Touro
        return 60.0  # Fêmea
    
    def _interpret_pppv(self, index: str, value: float) -> str:
        """Interpreta o valor do PPPV"""
        # Interpretações baseadas em ranges típicos
        interpretations = {
            'milk': [
                (-1000, 'Muito Baixo'),
                (0, 'Baixo'),
                (500, 'Médio'),
                (1000, 'Alto'),
                (1500, 'Muito Alto'),
                (float('inf'), 'Excepcional')
            ],
            'productive_life': [
                (-2, 'Muito Baixo'),
                (0, 'Baixo'),
                (2, 'Médio'),
                (4, 'Alto'),
                (6, 'Muito Alto'),
                (float('inf'), 'Excepcional')
            ],
            'scs': [  # Menor é melhor
                (-float('inf'), 'Excepcional'),
                (2.5, 'Muito Bom'),
                (2.8, 'Bom'),
                (3.0, 'Médio'),
                (3.2, 'Ruim'),
                (float('inf'), 'Muito Ruim')
            ],
            'fertility_index': [
                (-2, 'Muito Baixo'),
                (0, 'Baixo'),
                (1, 'Médio'),
                (2, 'Alto'),
                (3, 'Muito Alto'),
                (float('inf'), 'Excepcional')
            ],
        }
        
        ranges = interpretations.get(index)
        if not ranges:
            return 'N/A'
        
        for threshold, interpretation in ranges:
            if value < threshold:
                return interpretation
        
        return 'N/A'
    
    # ========================================================================
    # CONSANGUINIDADE
    # ========================================================================
    
    def calculate_inbreeding(self, female_data: Dict, bull_data: Dict) -> Dict:
        """
        Calcula consanguinidade esperada do acasalamento
        
        Usa GFI (Genomic Future Inbreeding) quando disponível
        A consanguinidade esperada do bezerro depende da relação entre os pais
        
        Returns:
            Dict com consanguinidade esperada e interpretação
        """
        # Pegar GFI/gINB dos pais
        female_gfi = self._get_gfi(female_data)
        bull_gfi = self._get_gfi(bull_data)
        
        # Calcular consanguinidade esperada DO BEZERRO
        if female_gfi is not None and bull_gfi is not None:
            # Com dados genômicos
            # O bezerro herda ~metade da consanguinidade de cada pai
            # MAIS o incremento do acasalamento (assumindo não aparentados = 0)
            # Fórmula correta: (GFI_vaca + GFI_touro) / 4 + incremento
            # Como não temos pedigree completo, usamos estimativa conservadora
            
            base_inbreeding = (female_gfi + bull_gfi) / 4  # Herança dos pais
            
            # Assumir incremento mínimo (pais não relacionados)
            # Em rebanhos comerciais, incremento típico é 0-2%
            increment = 1.0  # 1% default (conservador)
            
            expected_inbreeding = base_inbreeding + increment
            method = 'genomic'
        else:
            # Sem dados genômicos, usar estimativa baseada em população
            # Rebanhos comerciais: 2-4% típico
            expected_inbreeding = 3.0  # 3% default
            method = 'estimated'
        
        # Classificar risco
        risk_level = self._classify_inbreeding_risk(expected_inbreeding)
        
        return {
            'female_gfi': round(female_gfi, 2) if female_gfi else None,
            'bull_gfi': round(bull_gfi, 2) if bull_gfi else None,
            'expected_inbreeding': round(expected_inbreeding, 2),
            'method': method,
            'risk_level': risk_level,
            'acceptable': expected_inbreeding <= 6.0,
            'recommendation': self._inbreeding_recommendation(expected_inbreeding)
        }
    
    def _get_gfi(self, data: Dict) -> Optional[float]:
        """Extrai GFI/gINB dos dados"""
        # Tentar várias chaves possíveis
        keys = ['gfi', 'GFI', 'genomic_inbreeding', 'gINB']
        
        for key in keys:
            value = data.get(key)
            if value is not None:
                try:
                    return float(value)
                except (ValueError, TypeError):
                    pass
        
        # Tentar no genetic_data
        if 'genetic_data' in data and data['genetic_data']:
            for key in keys:
                value = data['genetic_data'].get(key)
                if value is not None:
                    try:
                        return float(value)
                    except (ValueError, TypeError):
                        pass
        
        return None
    
    def _classify_inbreeding_risk(self, inbreeding: float) -> str:
        """Classifica nível de risco da consanguinidade"""
        if inbreeding < 6.0:
            return 'Baixo'          # Verde: Ideal
        elif inbreeding < 8.0:
            return 'Moderado'       # Amarelo: Atenção
        elif inbreeding < 10.0:
            return 'Alto'           # Laranja: Cuidado
        else:
            return 'Muito Alto'     # Vermelho: Crítico
    
    def _inbreeding_recommendation(self, inbreeding: float) -> str:
        """Recomendação baseada na consanguinidade"""
        if inbreeding < 6.0:
            return '✅ Acasalamento recomendado - consanguinidade ideal'
        elif inbreeding < 8.0:
            return '⚠️ Acasalamento aceitável - monitorar progênie'
        elif inbreeding < 10.0:
            return '⚠️ Atenção - considerar outras opções se disponível'
        else:
            return '❌ Não recomendado - alto risco genético'
    
    # ========================================================================
    # COMPATIBILIDADE
    # ========================================================================
    
    def calculate_compatibility_score(self, female_data: Dict, bull_data: Dict,
                                     priorities: Optional[Dict] = None) -> Dict:
        """
        Calcula score de compatibilidade (0-100)
        
        Score baseado em:
        - Complementaridade genética
        - Prioridades do usuário
        - Consanguinidade
        
        Args:
            female_data: Dados da fêmea
            bull_data: Dados do touro
            priorities: Pesos customizados {index: weight}
        
        Returns:
            Dict com score e detalhes
        """
        if priorities is None:
            priorities = self.default_weights
        
        # Calcular contribuições de cada índice
        contributions = {}
        total_contribution = 0
        max_possible = 0
        
        for index, weight in priorities.items():
            # Pegar valor do touro
            bull_value = self._get_value(bull_data, index)
            if bull_value is None:
                continue
            
            # Normalizar valor (0-1)
            normalized = self._normalize_value(index, bull_value)
            
            # Calcular contribuição
            contribution = normalized * abs(weight) * 100
            total_contribution += contribution
            max_possible += abs(weight) * 100
            
            contributions[index] = {
                'value': bull_value,
                'normalized': round(normalized, 3),
                'weight': weight,
                'contribution': round(contribution, 2)
            }
        
        # Score base
        if max_possible > 0:
            base_score = (total_contribution / max_possible) * 100
        else:
            base_score = 50
        
        # Ajustes
        adjustments = {}
        final_score = base_score
        
        # Penalidade por consanguinidade alta
        inbreeding_data = self.calculate_inbreeding(female_data, bull_data)
        inbreeding = inbreeding_data['expected_inbreeding']
        
        if inbreeding > 6.0:
            penalty = (inbreeding - 6.0) * 5  # 5 pontos por % acima de 6
            adjustments['inbreeding_penalty'] = -round(penalty, 1)
            final_score -= penalty
        
        # Bônus por complementaridade
        complementarity_bonus = self._calculate_complementarity_bonus(
            female_data, bull_data
        )
        if complementarity_bonus > 0:
            adjustments['complementarity_bonus'] = round(complementarity_bonus, 1)
            final_score += complementarity_bonus
        
        # Limitar entre 0-100
        final_score = max(0, min(100, final_score))
        
        return {
            'score': round(final_score, 1),
            'base_score': round(base_score, 1),
            'adjustments': adjustments,
            'contributions': contributions,
            'inbreeding': inbreeding_data,
            'grade': self._grade_score(final_score)
        }
    
    def _get_value(self, data: Dict, index: str) -> Optional[float]:
        """Pega valor de um índice"""
        # Tentar diretamente
        value = data.get(index)
        if value is not None:
            try:
                return float(value)
            except (ValueError, TypeError):
                pass
        
        # Tentar no genetic_data
        if 'genetic_data' in data and data['genetic_data']:
            value = data['genetic_data'].get(index)
            if value is not None:
                try:
                    return float(value)
                except (ValueError, TypeError):
                    pass
        
        return None
    
    def _normalize_value(self, index: str, value: float) -> float:
        """
        Normaliza valor para 0-1
        Baseado em ranges típicos de cada índice
        """
        # Ranges aproximados (min, max)
        ranges = {
            'milk': (-1000, 2000),
            'protein': (-30, 80),
            'fat': (-30, 150),
            'productive_life': (-3, 8),
            'scs': (3.5, 2.5),  # Invertido - menor é melhor
            'dpr': (-2, 3),
            'fertility_index': (-2, 4),
            'udc': (-2, 3),
            'flc': (-2, 2),
            'ptat': (-2, 3),
            'net_merit': (-500, 1500),
        }
        
        range_min, range_max = ranges.get(index, (0, 100))
        
        # Normalizar
        if range_min > range_max:  # Invertido (ex: SCS)
            normalized = 1 - ((value - range_max) / (range_min - range_max))
        else:
            normalized = (value - range_min) / (range_max - range_min)
        
        # Limitar 0-1
        return max(0, min(1, normalized))
    
    def _calculate_complementarity_bonus(self, female_data: Dict, 
                                        bull_data: Dict) -> float:
        """
        Bônus se touro compensa fraquezas da fêmea
        """
        bonus = 0
        
        # Índices para analisar
        indices = ['milk', 'productive_life', 'udc', 'fertility_index']
        
        for index in indices:
            female_val = self._get_value(female_data, index)
            bull_val = self._get_value(bull_data, index)
            
            if female_val is None or bull_val is None:
                continue
            
            # Se fêmea é fraca (<média) e touro é forte (>média)
            female_norm = self._normalize_value(index, female_val)
            bull_norm = self._normalize_value(index, bull_val)
            
            if female_norm < 0.4 and bull_norm > 0.6:
                bonus += 2  # +2 pontos por índice complementado
        
        return bonus
    
    def _grade_score(self, score: float) -> str:
        """Classifica o score"""
        if score >= 85:
            return 'A+ Excelente'
        elif score >= 75:
            return 'A Muito Bom'
        elif score >= 65:
            return 'B Bom'
        elif score >= 50:
            return 'C Regular'
        elif score >= 35:
            return 'D Fraco'
        else:
            return 'F Inadequado'
    
    # ========================================================================
    # PREDIÇÕES DE PERFORMANCE
    # ========================================================================
    
    def predict_offspring_performance(self, pppv_data: Dict) -> Dict:
        """
        Prediz performance esperada do bezerro na vida produtiva
        """
        predictions = {}
        
        # Produção de leite estimada (305 dias, primeira lactação)
        if 'milk' in pppv_data:
            base_milk = 25000  # Base média
            pppv_milk = pppv_data['milk']['pppv']
            estimated_milk = base_milk + pppv_milk
            predictions['first_lactation_milk'] = {
                'value': round(estimated_milk, 0),
                'unit': 'lbs',
                'description': 'Produção estimada 1ª lactação (305d)'
            }
        
        # Vida produtiva estimada
        if 'productive_life' in pppv_data:
            base_pl = 3.0  # Base média
            pppv_pl = pppv_data['productive_life']['pppv']
            estimated_pl = base_pl + pppv_pl
            predictions['productive_life_estimate'] = {
                'value': round(estimated_pl, 1),
                'unit': 'lactações',
                'description': 'Número esperado de lactações'
            }
        
        # Valor econômico lifetime
        if 'net_merit' in pppv_data:
            pppv_nm = pppv_data['net_merit']['pppv']
            # NM$ é lifetime, já considera toda vida produtiva
            predictions['lifetime_value'] = {
                'value': round(pppv_nm, 0),
                'unit': 'USD',
                'description': 'Valor econômico estimado (lifetime)'
            }
        
        return predictions


# Instância global
genetic_calculator = GeneticCalculator()