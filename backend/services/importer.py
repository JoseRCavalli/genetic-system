"""
Serviço de Importação de Dados
Importa Excel (fêmeas) e PDF (touros) de forma inteligente:
- Adiciona novos registros
- Atualiza registros existentes apenas se mudaram
- Mantém histórico
"""

import pandas as pd
import PyPDF2
import re
import json
from datetime import datetime
from sqlalchemy.orm import Session
from typing import Dict, List, Tuple
import hashlib

from backend.models.database import Female, Bull, ImportHistory


class DataImporter:
    """Importador inteligente de dados"""
    
    def __init__(self, db_session: Session):
        self.session = db_session
    
    # ========================================================================
    # IMPORTAÇÃO DE FÊMEAS (EXCEL)
    # ========================================================================
    
    def import_females_from_excel(self, excel_path: str, user: str = 'Pedro') -> Dict:
        """
        Importa fêmeas do Excel do Herd Dynamics
        Atualiza apenas o que mudou
        """
        print(f"Importando fêmeas de: {excel_path}")
        
        stats = {
            'added': 0,
            'updated': 0,
            'unchanged': 0,
            'errors': []
        }
        
        try:
            # Ler Excel
            df = pd.read_excel(excel_path)
            print(f"  Lidas {len(df)} fêmeas do Excel")
            
            for idx, row in df.iterrows():
                try:
                    # Identificadores
                    reg_id = str(row.get('REG ID', ''))
                    internal_id = str(row.get('ID', ''))
                    
                    if not reg_id and not internal_id:
                        continue
                    
                    # Buscar fêmea existente
                    existing = None
                    if reg_id:
                        existing = self.session.query(Female).filter_by(reg_id=reg_id).first()
                    if not existing and internal_id:
                        existing = self.session.query(Female).filter_by(internal_id=internal_id).first()
                    
                    # Preparar dados genéticos (todos os índices)
                    genetic_data = {}
                    for col in df.columns:
                        val = row[col]
                        if pd.notna(val):
                            genetic_data[col] = float(val) if isinstance(val, (int, float)) else str(val)
                    
                    # Hash dos dados genéticos (para detectar mudanças)
                    data_hash = self._hash_dict(genetic_data)
                    
                    # Extrair índices principais
                    main_indices = self._extract_female_main_indices(row)
                    
                    if existing:
                        # Verificar se mudou
                        existing_hash = self._hash_dict(existing.genetic_data or {})
                        
                        if data_hash != existing_hash:
                            # ATUALIZAR
                            existing.genetic_data = genetic_data
                            existing.name = str(row.get('ID', ''))
                            
                            # Atualizar índices principais
                            for key, value in main_indices.items():
                                setattr(existing, key, value)
                            
                            existing.last_updated = datetime.now()
                            stats['updated'] += 1
                            
                            if (idx + 1) % 50 == 0:
                                print(f"    Processadas {idx + 1}/{len(df)} fêmeas...")
                        else:
                            stats['unchanged'] += 1
                    else:
                        # ADICIONAR NOVA
                        new_female = Female(
                            reg_id=reg_id if reg_id else None,
                            internal_id=internal_id if internal_id else None,
                            name=str(row.get('ID', '')),
                            breed=str(row.get('BREED', 'HO')),
                            genetic_data=genetic_data,
                            **main_indices
                        )
                        self.session.add(new_female)
                        stats['added'] += 1
                    
                except Exception as e:
                    stats['errors'].append(f"Linha {idx}: {str(e)}")
                    continue
            
            # Commit
            self.session.commit()
            
            # Registrar importação
            self._log_import(
                import_type='females_excel',
                filename=excel_path,
                stats=stats,
                user=user
            )
            
            print(f"\n✓ Importação concluída:")
            print(f"  Adicionadas: {stats['added']}")
            print(f"  Atualizadas: {stats['updated']}")
            print(f"  Sem mudanças: {stats['unchanged']}")
            if stats['errors']:
                print(f"  Erros: {len(stats['errors'])}")
            
            return stats
            
        except Exception as e:
            self.session.rollback()
            print(f"✗ Erro na importação: {e}")
            raise
    
    def _extract_female_main_indices(self, row: pd.Series) -> Dict:
        """Extrai índices principais da fêmea"""
        return {
            'milk': self._safe_float(row.get('MILK')),
            'protein': self._safe_float(row.get('PROTEIN')),
            'fat': self._safe_float(row.get('FAT')),
            'productive_life': self._safe_float(row.get('PRODUCTIVE LIFE')),
            'scs': self._safe_float(row.get('SOMATIC CELL SCORE')),
            'dpr': self._safe_float(row.get('DAUGHTER PREGNANCY RATE')),
            'fertility_index': self._safe_float(row.get('FERTILITY INDEX')),
            'udc': self._safe_float(row.get('UDC')),
            'flc': self._safe_float(row.get('FLC')),
            'ptat': self._safe_float(row.get('PTAT')),
            'net_merit': self._safe_float(row.get('NET MERIT')),
            'tpi': self._safe_float(row.get('TPI')),
            'genomic_inbreeding': self._safe_float(row.get('gINB')),
        }
    
    # ========================================================================
    # IMPORTAÇÃO DE TOUROS (PDF)
    # ========================================================================
    
    def import_bulls_from_pdf(self, pdf_path: str, user: str = 'Pedro') -> Dict:
        """
        Importa touros do PDF (SelectSires/Strategy)
        Atualiza apenas o que mudou
        """
        print(f"Importando touros de: {pdf_path}")
        
        stats = {
            'added': 0,
            'updated': 0,
            'unchanged': 0,
            'errors': []
        }
        
        try:
            # Extrair dados do PDF
            bulls_data = self._parse_bulls_pdf(pdf_path)
            print(f"  Extraídos {len(bulls_data)} touros do PDF")
            
            for idx, bull_data in enumerate(bulls_data):
                try:
                    code = bull_data.get('code')
                    if not code:
                        continue
                    
                    # Buscar touro existente
                    existing = self.session.query(Bull).filter_by(code=code).first()
                    
                    # Hash dos dados
                    data_hash = self._hash_dict(bull_data)
                    
                    # Extrair índices principais
                    main_indices = self._extract_bull_main_indices(bull_data)
                    
                    if existing:
                        # Verificar se mudou
                        existing_hash = self._hash_dict(existing.genetic_data or {})
                        
                        if data_hash != existing_hash:
                            # ATUALIZAR
                            existing.genetic_data = bull_data
                            existing.name = bull_data.get('name', existing.name)
                            
                            # Atualizar índices principais
                            for key, value in main_indices.items():
                                setattr(existing, key, value)
                            
                            existing.last_updated = datetime.now()
                            stats['updated'] += 1
                            
                            if (idx + 1) % 50 == 0:
                                print(f"    Processados {idx + 1}/{len(bulls_data)} touros...")
                        else:
                            stats['unchanged'] += 1
                    else:
                        # ADICIONAR NOVO
                        new_bull = Bull(
                            code=code,
                            name=bull_data.get('name', ''),
                            source='SelectSires',
                            genetic_data=bull_data,
                            **main_indices
                        )
                        self.session.add(new_bull)
                        stats['added'] += 1
                    
                except Exception as e:
                    stats['errors'].append(f"Touro {idx}: {str(e)}")
                    continue
            
            # Commit
            self.session.commit()
            
            # Registrar importação
            self._log_import(
                import_type='bulls_pdf',
                filename=pdf_path,
                stats=stats,
                user=user
            )
            
            print(f"\n✓ Importação concluída:")
            print(f"  Adicionados: {stats['added']}")
            print(f"  Atualizados: {stats['updated']}")
            print(f"  Sem mudanças: {stats['unchanged']}")
            if stats['errors']:
                print(f"  Erros: {len(stats['errors'])}")
            
            return stats
            
        except Exception as e:
            self.session.rollback()
            print(f"✗ Erro na importação: {e}")
            raise
    
    def _parse_bulls_pdf(self, pdf_path: str) -> List[Dict]:
        """Parser de PDF de touros"""
        bulls_data = []
        
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                
                bull_data = self._parse_bull_page(text)
                if bull_data and 'code' in bull_data:
                    bull_data['page'] = page_num + 1
                    bulls_data.append(bull_data)
        
        return bulls_data
    
    def _parse_bull_page(self, text: str) -> Dict:
        """Parser de uma página de touro"""
        bull_data = {}
        
        # Código e nome
        code_match = re.search(r'(\d+HO\d+)\s+(\w+)', text)
        if code_match:
            bull_data['code'] = code_match.group(1)
            bull_data['name'] = code_match.group(2)
        
        # Produção
        prod_section = re.search(r'Production\s+Milk\s+Protein\s+Fat.*?([+\-]\d+)\s+([+\-]\d+)\s+([+\-]\d+)', text, re.DOTALL)
        if prod_section:
            bull_data['milk'] = int(prod_section.group(1))
            bull_data['protein'] = int(prod_section.group(2))
            bull_data['fat'] = int(prod_section.group(3))
        
        # Net Merit, etc
        money_section = re.search(r'NM\$\s+CM\$\s+GM\$[+\-\$,\d\s]+\+\$([,\d]+)\s+\+\$([,\d]+)\s+\+\$([,\d]+)', text)
        if money_section:
            bull_data['net_merit'] = int(money_section.group(1).replace(',', ''))
            bull_data['cheese_merit'] = int(money_section.group(2).replace(',', ''))
            bull_data['grazing_merit'] = int(money_section.group(3).replace(',', ''))
        
        # Tipo
        type_section = re.search(r'Type\s+UDC\s+FLC[+\-\d.\s]+([+\-]\d+\.?\d*)\s+([+\-]\d+\.?\d*)', text)
        if type_section:
            bull_data['udc'] = float(type_section.group(1))
            bull_data['flc'] = float(type_section.group(2))
        
        # PTAT
        ptat_match = re.search(r'BWC.*?([+\-]\d+\.\d+)', text, re.DOTALL)
        if ptat_match:
            bull_data['ptat'] = float(ptat_match.group(1))
        
        # Productive Life
        pl_match = re.search(r'Productive Life\s+([+\-]?\d+\.?\d*)\s+\d+%R', text)
        if pl_match:
            bull_data['productive_life'] = float(pl_match.group(1))
        
        # SCS
        scs_match = re.search(r'Somatic Cell Score\s+([+\-]?\d+\.?\d*)\s+\d+%R', text)
        if scs_match:
            bull_data['scs'] = float(scs_match.group(1))
        
        # Fertilidade
        dpr_match = re.search(r'Daughter Pregnancy Rate\s+([+\-]?\d+\.?\d*)\s+\d+%R', text)
        if dpr_match:
            bull_data['dpr'] = float(dpr_match.group(1))
        
        fi_match = re.search(r'Fertility Index\s+([+\-]?\d+\.?\d*)\s+\d+%R', text)
        if fi_match:
            bull_data['fertility_index'] = float(fi_match.group(1))
        
        # RFI
        rfi_match = re.search(r'RFI\s+([+\-]\d+)\s+\d+%R', text)
        if rfi_match:
            bull_data['rfi'] = int(rfi_match.group(1))
        
        # Genótipos
        beta_match = re.search(r'Beta-Casein:\s*(A1A2|A2A2|A1A1)', text)
        if beta_match:
            bull_data['beta_casein'] = beta_match.group(1)
        
        kappa_match = re.search(r'Kappa-Casein:\s*(AA|AB|BB)', text)
        if kappa_match:
            bull_data['kappa_casein'] = kappa_match.group(1)
        
        # GFI
        gfi_match = re.search(r'GFI.*?(\d+\.?\d*)%', text, re.DOTALL)
        if gfi_match:
            bull_data['gfi'] = float(gfi_match.group(1))
        
        return bull_data
    
    def _extract_bull_main_indices(self, data: Dict) -> Dict:
        """Extrai índices principais do touro"""
        return {
            'milk': data.get('milk'),
            'protein': data.get('protein'),
            'fat': data.get('fat'),
            'net_merit': data.get('net_merit'),
            'cheese_merit': data.get('cheese_merit'),
            'grazing_merit': data.get('grazing_merit'),
            'tpi': data.get('tpi'),
            'gtpi': data.get('gtpi'),
            'udc': data.get('udc'),
            'flc': data.get('flc'),
            'ptat': data.get('ptat'),
            'productive_life': data.get('productive_life'),
            'scs': data.get('scs'),
            'dpr': data.get('dpr'),
            'fertility_index': data.get('fertility_index'),
            'rfi': data.get('rfi'),
            'feed_saved': data.get('feed_saved'),
            'beta_casein': data.get('beta_casein'),
            'kappa_casein': data.get('kappa_casein'),
            'gfi': data.get('gfi'),
        }
    
    # ========================================================================
    # UTILITÁRIOS
    # ========================================================================
    
    def _hash_dict(self, data: Dict) -> str:
        """Cria hash de um dicionário para detectar mudanças"""
        json_str = json.dumps(data, sort_keys=True)
        return hashlib.md5(json_str.encode()).hexdigest()
    
    def _safe_float(self, value) -> float:
        """Converte valor para float com segurança"""
        try:
            if value is None or pd.isna(value):
                return None
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def _log_import(self, import_type: str, filename: str, stats: Dict, user: str):
        """Registra importação no histórico"""
        log = ImportHistory(
            import_type=import_type,
            filename=filename,
            records_added=stats['added'],
            records_updated=stats['updated'],
            records_unchanged=stats['unchanged'],
            status='success' if not stats['errors'] else 'partial',
            error_log='\n'.join(stats['errors'][:100]) if stats['errors'] else None,
            imported_by=user
        )
        self.session.add(log)
        self.session.commit()