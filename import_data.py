"""
Script de Importação Direta
Importa fêmeas e touros diretamente para o banco
"""

import sys
import os

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.models.database import init_database, get_session
from backend.services.importer import DataImporter

# Configurar caminhos
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = f'sqlite:///{os.path.join(BASE_DIR, "database", "cattle_breeding.db")}'

# Seus arquivos (WINDOWS)
FEMALES_FILE = os.path.join(BASE_DIR, 'uploads', 'Females_All_List_-_2025-11-03.xlsx')
BULLS_FILE = os.path.join(BASE_DIR, 'uploads', 'ExportedSires-134065114375553634.pdf')

def main():
    print("\n" + "="*80)
    print("IMPORTAÇÃO DIRETA DE DADOS")
    print("="*80)
    
    # Inicializar banco
    print("\n1. Inicializando banco de dados...")
    engine = init_database(DB_PATH)
    db = get_session(engine)
    print("   ✓ Banco inicializado")
    
    # Criar importer
    importer = DataImporter(db)
    
    # Importar Fêmeas
    print("\n2. Importando fêmeas...")
    print(f"   Arquivo: {FEMALES_FILE}")
    
    if os.path.exists(FEMALES_FILE):
        try:
            stats = importer.import_females_from_excel(FEMALES_FILE, 'Sistema')
            print(f"   ✓ Fêmeas importadas:")
            print(f"      - Adicionadas: {stats['added']}")
            print(f"      - Atualizadas: {stats['updated']}")
            print(f"      - Sem mudanças: {stats['unchanged']}")
            print(f"      - Total: {stats['added'] + stats['updated'] + stats['unchanged']}")
        except Exception as e:
            print(f"   ✗ ERRO: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"   ✗ Arquivo não encontrado!")
    
    # Importar Touros
    print("\n3. Importando touros...")
    print(f"   Arquivo: {BULLS_FILE}")
    
    if os.path.exists(BULLS_FILE):
        try:
            stats = importer.import_bulls_from_pdf(BULLS_FILE, 'Sistema')
            print(f"   ✓ Touros importados:")
            print(f"      - Adicionados: {stats['added']}")
            print(f"      - Atualizados: {stats['updated']}")
            print(f"      - Sem mudanças: {stats['unchanged']}")
            print(f"      - Total: {stats['added'] + stats['updated'] + stats['unchanged']}")
        except Exception as e:
            print(f"   ✗ ERRO: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"   ✗ Arquivo não encontrado!")
    
    # Verificar resultados
    print("\n4. Verificando resultados...")
    from backend.models.database import Female, Bull
    
    females_count = db.query(Female).count()
    bulls_count = db.query(Bull).count()
    
    print(f"   ✓ Total de fêmeas no banco: {females_count}")
    print(f"   ✓ Total de touros no banco: {bulls_count}")
    
    print("\n" + "="*80)
    print("✓ IMPORTAÇÃO CONCLUÍDA!")
    print("="*80 + "\n")
    
    if females_count == 0 and bulls_count == 0:
        print("⚠️  ATENÇÃO: Nenhum dado foi importado!")
        print("   Verifique os erros acima.")
    else:
        print("🎉 Dados importados com sucesso!")
        print(f"\nRodando: python app.py")
        print(f"Acesse: http://localhost:5000/api/status")

if __name__ == '__main__':
    main()