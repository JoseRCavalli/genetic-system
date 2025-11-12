"""
Aplicação Principal - Flask
Sistema de Acasalamento de Gado Leiteiro
VERSÃO HÍBRIDA: SQLite local + PostgreSQL produção
"""

from flask import Flask, render_template, send_from_directory, jsonify
from flask_cors import CORS
from sqlalchemy import create_engine, text
import os
from datetime import datetime

# Importar models e inicializar banco
from backend.models.database import init_database, get_session

# Importar rotas
from backend.api.routes import api
from backend.api.analytics_routes import analytics_api

# ============================================================================
# CONFIGURAÇÃO DE BANCO DE DADOS INTELIGENTE
# ============================================================================

def get_database_url():
    """
    Detecta automaticamente qual banco usar:
    - Produção (Railway): PostgreSQL via DATABASE_URL
    - Local: SQLite
    """
    # Se existe DATABASE_URL (Railway PostgreSQL)
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url:
        # PostgreSQL no Railway
        print("🐘 Usando PostgreSQL (produção)")
        return database_url
    else:
        # SQLite local
        base_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(base_dir, 'database', 'cattle_breeding.db')
        sqlite_url = f'sqlite:///{db_path}'
        print("🗃️  Usando SQLite (desenvolvimento)")
        return sqlite_url

# ============================================================================
# CONFIGURAÇÃO
# ============================================================================

# Detectar diretório base (onde está o app.py)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Criar app
app = Flask(__name__,
           template_folder=os.path.join(BASE_DIR, 'frontend', 'pages'),
           static_folder=os.path.join(BASE_DIR, 'frontend'))

# CORS
CORS(app)

# Configurações
app.config['SECRET_KEY'] = 'cattle-breeding-secret-key-change-in-production'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max upload
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'uploads')

# Garantir que pastas existem (só para SQLite local)
if not os.environ.get('DATABASE_URL'):
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(BASE_DIR, 'database'), exist_ok=True)

# ============================================================================
# INICIALIZAÇÃO DO BANCO DE DADOS
# ============================================================================

DB_URL = get_database_url()

print("Inicializando banco de dados...")
print(f"Localização: {DB_URL}")
engine = init_database(DB_URL)
print("✓ Banco de dados pronto!")

# ============================================================================
# REGISTRAR BLUEPRINTS (ROTAS)
# ============================================================================

app.register_blueprint(api)
app.register_blueprint(analytics_api)

# ============================================================================
# ROTAS DO FRONTEND
# ============================================================================

@app.route('/')
def index():
    """Página principal - Dashboard"""
    return render_template('index.html')

@app.route('/api/dashboard')
def dashboard_api():
    """API do dashboard - retorna estatísticas gerais"""
    try:
        # Usar a mesma conexão configurada
        dashboard_engine = create_engine(DB_URL, echo=False)
        
        with dashboard_engine.connect() as conn:
            # Contar fêmeas
            result_femeas = conn.execute(text("SELECT COUNT(*) as total FROM females"))
            total_femeas = result_femeas.fetchone()[0]
            
            # Contar touros  
            result_touros = conn.execute(text("SELECT COUNT(*) as total FROM bulls"))
            total_touros = result_touros.fetchone()[0]
            
            # Contar acasalamentos (se a tabela existir)
            try:
                result_matings = conn.execute(text("SELECT COUNT(*) as total FROM matings"))
                total_acasalamentos = result_matings.fetchone()[0]
            except:
                total_acasalamentos = 0
            
            # Calcular taxa de sucesso (placeholder)
            taxa_sucesso = 85 if total_acasalamentos > 0 else 0
            
            return jsonify({
                "total_femeas": total_femeas,
                "total_touros": total_touros, 
                "total_acasalamentos": total_acasalamentos,
                "taxa_sucesso": taxa_sucesso,
                "status": "success",
                "database_type": "PostgreSQL" if os.environ.get('DATABASE_URL') else "SQLite"
            })
            
    except Exception as e:
        print(f"Erro na dashboard API: {str(e)}")
        return jsonify({
            "error": str(e),
            "total_femeas": 0,
            "total_touros": 0,
            "total_acasalamentos": 0,
            "taxa_sucesso": 0
        }), 500


@app.route('/manual')
def manual():
    """Página de acasalamento manual"""
    return render_template('manual.html')


@app.route('/batch')
def batch():
    """Página de acasalamento em lote"""
    return render_template('batch.html')


@app.route('/history')
def history():
    """Página de histórico"""
    return render_template('history.html')


@app.route('/analytics')
def analytics():
    """Página de análises e gráficos"""
    return render_template('analytics.html')


@app.route('/import')
def import_data():
    """Página de importação de dados"""
    return send_from_directory('frontend/pages', 'import.html')


@app.route('/femeas')
def femeas():
    """Página de listagem de fêmeas"""
    return send_from_directory('frontend/pages', 'femeas.html')


@app.route('/touros')
def touros():
    """Página de listagem de touros"""
    return send_from_directory('frontend/pages', 'touros.html')


# ============================================================================
# ROTAS ESTÁTICAS
# ============================================================================

@app.route('/css/<path:filename>')
def serve_css(filename):
    """Servir arquivos CSS"""
    return send_from_directory(os.path.join(BASE_DIR, 'frontend', 'css'), filename)


@app.route('/js/<path:filename>')
def serve_js(filename):
    """Servir arquivos JavaScript"""
    return send_from_directory(os.path.join(BASE_DIR, 'frontend', 'js'), filename)


@app.route('/assets/<path:filename>')
def serve_assets(filename):
    """Servir assets (imagens, etc)"""
    return send_from_directory(os.path.join(BASE_DIR, 'frontend', 'assets'), filename)


# ============================================================================
# TRATAMENTO DE ERROS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Página não encontrada"""
    return {'error': 'Página não encontrada'}, 404


@app.errorhandler(500)
def internal_error(error):
    """Erro interno"""
    return {'error': 'Erro interno do servidor'}, 500


# ============================================================================
# COMANDOS CLI
# ============================================================================

@app.cli.command()
def init_db():
    """Comando CLI para inicializar banco de dados"""
    print("\n" + "="*80)
    print("Criando tabelas do banco de dados...")
    print("="*80)
    
    engine = init_database(DB_URL)
    
    print("\n✓ Banco de dados inicializado com sucesso!")
    print(f"  Localização: {DB_URL}")
    print("="*80 + "\n")


@app.cli.command()
def import_initial_data():
    """Comando CLI para importar dados iniciais"""
    from backend.services.importer import DataImporter
    
    print("\n" + "="*80)
    print("IMPORTANDO DADOS INICIAIS")
    print("="*80)
    
    db = get_session(engine)
    importer = DataImporter(db)
    
    # Procurar arquivos na pasta uploads
    uploads_dir = app.config['UPLOAD_FOLDER']
    
    # Só funciona em ambiente local (SQLite)
    if os.environ.get('DATABASE_URL'):
        print("⚠️  Comando não disponível em produção (PostgreSQL)")
        print("   Use a interface web para importar dados")
        return
    
    # Importar fêmeas
    print("\n1. Procurando arquivo de fêmeas...")
    females_files = [f for f in os.listdir(uploads_dir) if 'Female' in f and f.endswith('.xlsx')]
    
    if females_files:
        females_file = os.path.join(uploads_dir, females_files[0])
        print(f"   Encontrado: {females_files[0]}")
        print(f"   Importando...")
        
        try:
            stats_females = importer.import_females_from_excel(females_file, 'Sistema')
            print(f"   ✓ Fêmeas importadas:")
            print(f"      Adicionadas: {stats_females['added']}")
            print(f"      Atualizadas: {stats_females['updated']}")
            print(f"      Sem mudanças: {stats_females['unchanged']}")
        except Exception as e:
            print(f"   ✗ Erro: {e}")
    else:
        print(f"   ⚠ Nenhum arquivo de fêmeas encontrado em: {uploads_dir}")
        print(f"   Coloque um arquivo Excel com 'Female' no nome na pasta uploads/")
    
    # Importar touros
    print("\n2. Procurando arquivo de touros...")
    bulls_files = [f for f in os.listdir(uploads_dir) if f.endswith('.pdf')]
    
    if bulls_files:
        bulls_file = os.path.join(uploads_dir, bulls_files[0])
        print(f"   Encontrado: {bulls_files[0]}")
        print(f"   Importando...")
        
        try:
            stats_bulls = importer.import_bulls_from_pdf(bulls_file, 'Sistema')
            print(f"   ✓ Touros importados:")
            print(f"      Adicionadas: {stats_bulls['added']}")
            print(f"      Atualizadas: {stats_bulls['updated']}")
            print(f"      Sem mudanças: {stats_bulls['unchanged']}")
        except Exception as e:
            print(f"   ✗ Erro: {e}")
    else:
        print(f"   ⚠ Nenhum arquivo PDF encontrado em: {uploads_dir}")
        print(f"   Coloque um arquivo PDF na pasta uploads/")
    
    print("\n" + "="*80)
    print("✓ Importação concluída!")
    print("="*80 + "\n")


# ============================================================================
# STATUS E HEALTH CHECK
# ============================================================================

@app.route('/api/health')
def health_check():
    """Health check da API"""
    try:
        # Testar conexão com banco
        db = get_session(engine)
        from backend.models.database import Female
        count = db.query(Female).count()
        
        return {
            'status': 'ok',
            'database': 'connected',
            'database_type': 'PostgreSQL' if os.environ.get('DATABASE_URL') else 'SQLite',
            'database_url': DB_URL.split('@')[0] + '@***' if '@' in DB_URL else 'SQLite local',
            'females_count': count,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }, 500


@app.route('/api/status')
def api_status():
    """Status geral do sistema"""
    try:
        db = get_session(engine)
        
        from backend.models.database import Female, Bull, Mating
        
        females_count = db.query(Female).count()
        bulls_count = db.query(Bull).count()
        matings_count = db.query(Mating).count()
        
        return {
            'status': 'online',
            'version': '2.0',
            'database': {
                'type': 'PostgreSQL' if os.environ.get('DATABASE_URL') else 'SQLite',
                'females': females_count,
                'bulls': bulls_count,
                'matings': matings_count
            },
            'base_dir': BASE_DIR,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }, 500


# ============================================================================
# EXECUTAR APLICAÇÃO
# ============================================================================

if __name__ == '__main__':
    print("\n" + "="*80)
    print("  🐄 SISTEMA DE ACASALAMENTO - GADO LEITEIRO 🐄")
    print("="*80)
    print(f"\nDiretório base: {BASE_DIR}")
    print(f"Banco de dados: {DB_URL}")
    print(f"Tipo de banco: {'PostgreSQL' if os.environ.get('DATABASE_URL') else 'SQLite'}")
    print(f"Uploads: {app.config['UPLOAD_FOLDER']}")
    print(f"\nIniciando servidor...")
    print(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("="*80 + "\n")
    
    # Pegar porta do ambiente (Railway usa variável PORT)
    port = int(os.environ.get('PORT', 5000))
    
    print(f"Porta: {port}")
    print(f"Host: 0.0.0.0")
    print("\n" + "="*80 + "\n")
    
    # Rodar servidor
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False  # IMPORTANTE: False em produção!
    )
