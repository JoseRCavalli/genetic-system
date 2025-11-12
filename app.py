"""
Aplicação Principal - Flask
Sistema de Acasalamento de Gado Leiteiro
VERSÃO HÍBRIDA: SQLite local + PostgreSQL produção
"""

from flask import Flask, render_template, send_from_directory, jsonify
from flask_cors import CORS
from sqlalchemy import create_engine, text
import os
import time
from datetime import datetime

# Importar models e inicializar banco
from backend.models.database import init_database, get_session

# Importar rotas
from backend.api.routes import api
from backend.api.analytics_routes import analytics_api

# ============================================================================
# CONFIGURAÇÃO DE BANCO DE DADOS PARA RENDER
# ============================================================================

def get_database_url():
    """
    Detecta automaticamente qual banco usar:
    - Render: PostgreSQL via DATABASE_URL
    - Local: SQLite
    """
    # Render usa DATABASE_URL também
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url:
        print("🐘 Usando PostgreSQL (Render)")
        return database_url
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(base_dir, 'database', 'cattle_breeding.db')
        sqlite_url = f'sqlite:///{db_path}'
        print("🗃️  Usando SQLite (local)")
        return sqlite_url

# ============================================================================
# CONFIGURAÇÃO
# ============================================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Criar app
app = Flask(__name__,
           template_folder=os.path.join(BASE_DIR, 'frontend', 'pages'),
           static_folder=os.path.join(BASE_DIR, 'frontend'))

# CORS
CORS(app)

# Configurações
app.config['SECRET_KEY'] = 'cattle-breeding-secret-key-render'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'uploads')

# Criar pastas (só local)
if not os.environ.get('DATABASE_URL'):
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(BASE_DIR, 'database'), exist_ok=True)

# ============================================================================
# INICIALIZAÇÃO DO BANCO
# ============================================================================

DB_URL = get_database_url()
print(f"Banco: {DB_URL}")

try:
    engine = init_database(DB_URL)
    print("✓ Banco inicializado!")
except Exception as e:
    print(f"❌ Erro ao inicializar banco: {e}")
    # Continuar mesmo assim para poder debugar

# ============================================================================
# REGISTRAR ROTAS
# ============================================================================

try:
    app.register_blueprint(api)
    app.register_blueprint(analytics_api)
    print("✓ Blueprints registrados!")
except Exception as e:
    print(f"⚠️  Erro ao registrar blueprints: {e}")

# ============================================================================
# ROTAS PRINCIPAIS
# ============================================================================

@app.route('/')
def index():
    """Página principal"""
    try:
        return render_template('index.html')
    except Exception as e:
        return f"""
        <html>
            <body>
                <h1>🐄 Genefy - Sistema de Acasalamento</h1>
                <p><strong>Status:</strong> Online</p>
                <p><strong>Banco:</strong> {'PostgreSQL' if os.environ.get('DATABASE_URL') else 'SQLite'}</p>
                <p><strong>Erro template:</strong> {str(e)}</p>
                <p><a href="/api/health">Health Check</a></p>
                <p><a href="/api/dashboard">Dashboard API</a></p>
                <p><a href="/api/init-database">Inicializar Banco</a></p>
            </body>
        </html>
        """

@app.route('/api/health')
def health_check():
    """Health check"""
    try:
        db = get_session(engine)
        from backend.models.database import Female
        count = db.query(Female).count()
        db.close()
        
        return jsonify({
            'status': 'ok',
            'database': 'connected',
            'database_type': 'PostgreSQL' if os.environ.get('DATABASE_URL') else 'SQLite',
            'females_count': count,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/dashboard')
def dashboard_api():
    """Dashboard API com retry"""
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            db = get_session(engine)
            from backend.models.database import Female, Bull, Mating
            
            total_femeas = db.query(Female).count()
            total_touros = db.query(Bull).count() 
            total_acasalamentos = db.query(Mating).count()
            
            taxa_sucesso = 85 if total_acasalamentos > 0 else 0
            
            db.close()
            
            return jsonify({
                "total_femeas": total_femeas,
                "total_touros": total_touros, 
                "total_acasalamentos": total_acasalamentos,
                "taxa_sucesso": taxa_sucesso,
                "status": "success",
                "database_type": "PostgreSQL" if os.environ.get('DATABASE_URL') else "SQLite"
            })
            
        except Exception as e:
            if attempt < max_retries - 1 and ("starting up" in str(e) or "Connection refused" in str(e)):
                print(f"Tentativa {attempt + 1}, aguardando...")
                time.sleep(2)
                continue
            
            return jsonify({
                "error": str(e),
                "total_femeas": 0,
                "total_touros": 0,
                "total_acasalamentos": 0,
                "taxa_sucesso": 0,
                "status": "error"
            }), 500

@app.route('/api/init-database')
def init_database_api():
    """Inicializar banco"""
    try:
        from backend.models.database import Base
        Base.metadata.create_all(engine)
        
        # Verificar tabelas
        if os.environ.get('DATABASE_URL'):
            # PostgreSQL
            with engine.connect() as conn:
                result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'"))
                tables = [row[0] for row in result.fetchall()]
        else:
            # SQLite
            with engine.connect() as conn:
                result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
                tables = [row[0] for row in result.fetchall()]
        
        return jsonify({
            "status": "success",
            "tables_created": tables,
            "database_type": "PostgreSQL" if os.environ.get('DATABASE_URL') else "SQLite"
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

# Outras rotas de frontend
@app.route('/manual')
def manual():
    return render_template('manual.html')

@app.route('/batch') 
def batch():
    return render_template('batch.html')

@app.route('/history')
def history():
    return render_template('history.html')

@app.route('/analytics')
def analytics():
    return render_template('analytics.html')

@app.route('/import')
def import_data():
    return send_from_directory('frontend/pages', 'import.html')

# Arquivos estáticos
@app.route('/css/<path:filename>')
def serve_css(filename):
    return send_from_directory(os.path.join(BASE_DIR, 'frontend', 'css'), filename)

@app.route('/js/<path:filename>')
def serve_js(filename):
    return send_from_directory(os.path.join(BASE_DIR, 'frontend', 'js'), filename)

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory(os.path.join(BASE_DIR, 'frontend', 'assets'), filename)

# ============================================================================
# EXECUTAR
# ============================================================================

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🐄 GENEFY - RENDER.COM")
    print("="*60)
    print(f"Banco: {'PostgreSQL' if os.environ.get('DATABASE_URL') else 'SQLite'}")
    print(f"Porto: {os.environ.get('PORT', 5000)}")
    print("="*60)
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
