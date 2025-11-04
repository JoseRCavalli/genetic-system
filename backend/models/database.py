"""
Modelos do Banco de Dados - Sistema de Acasalamento
SQLAlchemy ORM Models
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, JSON, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import json

Base = declarative_base()

# ============================================================================
# MODELOS PRINCIPAIS
# ============================================================================

class Female(Base):
    """Modelo para Fêmeas/Vacas"""
    __tablename__ = 'females'
    
    id = Column(Integer, primary_key=True)
    reg_id = Column(String(50), unique=True, index=True)
    internal_id = Column(String(50), index=True)
    name = Column(String(200))
    birth_date = Column(DateTime)
    breed = Column(String(50))
    
    # Dados genéticos (armazenados como JSON para flexibilidade)
    genetic_data = Column(JSON)  # Todos os 165 índices
    
    # Índices principais (para queries rápidas)
    milk = Column(Float)
    protein = Column(Float)
    fat = Column(Float)
    productive_life = Column(Float)
    scs = Column(Float)  # Somatic Cell Score
    dpr = Column(Float)  # Daughter Pregnancy Rate
    fertility_index = Column(Float)
    udc = Column(Float)
    flc = Column(Float)
    ptat = Column(Float)
    net_merit = Column(Float)
    tpi = Column(Float)
    
    # Genômico
    genomic_inbreeding = Column(Float)  # gINB
    
    # Metadata
    last_updated = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    is_active = Column(Boolean, default=True)
    notes = Column(Text)
    
    # Relacionamentos
    matings = relationship('Mating', back_populates='female', foreign_keys='Mating.female_id')
    
    def __repr__(self):
        return f"<Female {self.reg_id} - {self.internal_id}>"
    
    def to_dict(self):
        """Converter para dicionário"""
        return {
            'id': self.id,
            'reg_id': self.reg_id,
            'internal_id': self.internal_id,
            'name': self.name,
            'birth_date': self.birth_date.isoformat() if self.birth_date else None,
            'breed': self.breed,
            'genetic_data': self.genetic_data,
            'main_indices': {
                'milk': self.milk,
                'protein': self.protein,
                'fat': self.fat,
                'productive_life': self.productive_life,
                'scs': self.scs,
                'dpr': self.dpr,
                'fertility_index': self.fertility_index,
                'udc': self.udc,
                'flc': self.flc,
                'ptat': self.ptat,
                'net_merit': self.net_merit,
                'tpi': self.tpi,
                'genomic_inbreeding': self.genomic_inbreeding,
            },
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'is_active': self.is_active
        }


class Bull(Base):
    """Modelo para Touros"""
    __tablename__ = 'bulls'
    
    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True, index=True)
    name = Column(String(200), index=True)
    naab_code = Column(String(50))
    reg_id = Column(String(50))
    
    # Origem
    source = Column(String(50))  # SelectSires, Strategy, etc.
    
    # Dados genéticos (JSON para flexibilidade)
    genetic_data = Column(JSON)
    
    # Índices principais (para queries rápidas)
    milk = Column(Float)
    protein = Column(Float)
    fat = Column(Float)
    fat_percent = Column(Float)
    protein_percent = Column(Float)
    
    # Econômicos
    net_merit = Column(Float)
    cheese_merit = Column(Float)
    grazing_merit = Column(Float)
    fluid_merit = Column(Float)
    
    # Tipo
    tpi = Column(Float)
    gtpi = Column(Float)
    udc = Column(Float)
    flc = Column(Float)
    ptat = Column(Float)
    
    # Funcionalidade
    productive_life = Column(Float)
    scs = Column(Float)
    dpr = Column(Float)
    hcr = Column(Float)  # Heifer Conception Rate
    ccr = Column(Float)  # Cow Conception Rate
    fertility_index = Column(Float)
    
    # Eficiência
    rfi = Column(Float)  # Residual Feed Intake
    feed_saved = Column(Float)
    
    # Facilidade de parto
    daughter_calving_ease = Column(Float)
    sire_calving_ease = Column(Float)
    
    # Genótipos
    beta_casein = Column(String(10))  # A1A1, A1A2, A2A2
    kappa_casein = Column(String(10))  # AA, AB, BB
    
    # Genômico
    gfi = Column(Float)  # Genomic Future Inbreeding
    haplotypes = Column(JSON)  # Lista de haplótipos (HH1-HH6)
    
    # Disponibilidade
    is_available = Column(Boolean, default=True)
    price_per_dose = Column(Float)
    doses_available = Column(Integer)
    
    # Metadata
    last_updated = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    notes = Column(Text)
    
    # Relacionamentos
    matings = relationship('Mating', back_populates='bull', foreign_keys='Mating.bull_id')
    
    def __repr__(self):
        return f"<Bull {self.code} - {self.name}>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'naab_code': self.naab_code,
            'source': self.source,
            'genetic_data': self.genetic_data,
            'main_indices': {
                'milk': self.milk,
                'protein': self.protein,
                'fat': self.fat,
                'net_merit': self.net_merit,
                'tpi': self.tpi,
                'gtpi': self.gtpi,
                'productive_life': self.productive_life,
                'fertility_index': self.fertility_index,
                'udc': self.udc,
                'flc': self.flc,
                'ptat': self.ptat,
                'gfi': self.gfi,
                'beta_casein': self.beta_casein,
                'kappa_casein': self.kappa_casein,
            },
            'is_available': self.is_available,
            'price_per_dose': self.price_per_dose,
            'doses_available': self.doses_available,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }


class Mating(Base):
    """Histórico de Acasalamentos"""
    __tablename__ = 'matings'
    
    id = Column(Integer, primary_key=True)
    
    # Relacionamentos
    female_id = Column(Integer, ForeignKey('females.id'), index=True)
    bull_id = Column(Integer, ForeignKey('bulls.id'), index=True)
    
    female = relationship('Female', back_populates='matings', foreign_keys=[female_id])
    bull = relationship('Bull', back_populates='matings', foreign_keys=[bull_id])
    
    # Datas
    mating_date = Column(DateTime, default=datetime.now)
    expected_calving_date = Column(DateTime)
    actual_calving_date = Column(DateTime)
    
    # Predições (calculadas no momento do acasalamento)
    predicted_pppv = Column(JSON)  # Todos os índices preditos
    predicted_inbreeding = Column(Float)
    compatibility_score = Column(Float)
    
    # Tipo de acasalamento
    mating_type = Column(String(50))  # manual, batch, recommended
    
    # Resultados reais (preenchidos após nascimento)
    calf_id = Column(String(50))
    calf_sex = Column(String(10))  # M, F
    actual_genetic_data = Column(JSON)  # Dados reais do bezerro
    
    # Status
    status = Column(String(50))  # planned, confirmed, born, failed
    success = Column(Boolean)
    
    # Notas
    notes = Column(Text)
    created_by = Column(String(100))
    
    # Metadata
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f"<Mating {self.id}: Female {self.female_id} x Bull {self.bull_id}>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'female': self.female.to_dict() if self.female else None,
            'bull': self.bull.to_dict() if self.bull else None,
            'mating_date': self.mating_date.isoformat() if self.mating_date else None,
            'predicted_pppv': self.predicted_pppv,
            'predicted_inbreeding': self.predicted_inbreeding,
            'compatibility_score': self.compatibility_score,
            'mating_type': self.mating_type,
            'status': self.status,
            'success': self.success,
            'actual_genetic_data': self.actual_genetic_data,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class BatchMating(Base):
    """Acasalamentos em Lote"""
    __tablename__ = 'batch_matings'
    
    id = Column(Integer, primary_key=True)
    batch_name = Column(String(200))
    description = Column(Text)
    
    # Configurações usadas
    priorities = Column(JSON)  # Prioridades configuradas
    max_inbreeding = Column(Float, default=6.0)
    
    # Females incluídas
    female_ids = Column(JSON)  # Lista de IDs
    
    # Resultados
    recommendations = Column(JSON)  # Top N touros para cada vaca
    
    # Metadata
    created_at = Column(DateTime, default=datetime.now)
    created_by = Column(String(100))
    
    def __repr__(self):
        return f"<BatchMating {self.id}: {self.batch_name}>"


class UserPreference(Base):
    """Preferências do Usuário"""
    __tablename__ = 'user_preferences'
    
    id = Column(Integer, primary_key=True)
    user_name = Column(String(100), default='Pedro')
    
    # Prioridades padrão
    default_priorities = Column(JSON)
    
    # Configurações
    max_inbreeding = Column(Float, default=6.0)
    top_n_bulls = Column(Integer, default=5)
    
    # Preferências de visualização
    preferred_indices = Column(JSON)  # ~30 índices mais usados
    
    # Metadata
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class ImportHistory(Base):
    """Histórico de Importações de Dados"""
    __tablename__ = 'import_history'
    
    id = Column(Integer, primary_key=True)
    import_type = Column(String(50))  # females_excel, bulls_pdf
    filename = Column(String(500))
    
    # Estatísticas
    records_added = Column(Integer, default=0)
    records_updated = Column(Integer, default=0)
    records_unchanged = Column(Integer, default=0)
    
    # Status
    status = Column(String(50))  # success, partial, failed
    error_log = Column(Text)
    
    # Metadata
    imported_at = Column(DateTime, default=datetime.now)
    imported_by = Column(String(100))
    
    def __repr__(self):
        return f"<Import {self.id}: {self.import_type} - {self.status}>"


# ============================================================================
# INICIALIZAÇÃO DO BANCO
# ============================================================================

def init_database(db_path='sqlite:///cattle_breeding.db'):
    """
    Inicializa o banco de dados
    """
    engine = create_engine(db_path, echo=False)
    Base.metadata.create_all(engine)
    return engine


def get_session(engine):
    """
    Cria uma sessão do banco
    """
    Session = sessionmaker(bind=engine)
    return Session()


if __name__ == '__main__':
    # Testar criação do banco
    print("Criando banco de dados...")
    engine = init_database('sqlite:///cattle_breeding.db')
    print(f"✓ Banco criado com sucesso!")
    print(f"✓ Tabelas criadas: {Base.metadata.tables.keys()}")