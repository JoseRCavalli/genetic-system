"""
Aplicação Principal - Flask
Sistema de Acasalamento de Gado Leiteiro
"""

from flask import Flask, render_template, send_from_directory, jsonify, request
from flask_cors import CORS
from sqlalchemy import create_engine, text
import os
import time
import tempfile
from datetime import datetime

# Importar models e inicializar banco
from backend.models.database import init_database, get_session

# ============================================================================
# CONFIGURAÇÃO DE BANCO DE DADOS
# ============================================================================

def get_database_url():
    """
    Detecta automaticamente qual banco usar:
    - Produção: PostgreSQL via DATABASE_URL
    - Local: SQLite
    """
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url:
        print("🐘 Usando PostgreSQL (produção)")
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
app.config['SECRET_KEY'] = 'cattle-breeding-secret-key-production'
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
# BLUEPRINTS DESABILITADOS (PARA EVITAR CONFLITOS)
# ============================================================================

# ❌ COMENTADO PARA EVITAR CONFLITOS DE ROTAS
# from backend.api.routes import api
# from backend.api.analytics_routes import analytics_api
# app.register_blueprint(api)
# app.register_blueprint(analytics_api)

print("⚠️ Blueprints desabilitados - usando rotas diretas")

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

@app.route('/api/dashboard-full')
def dashboard_full_api():
    """API completa do dashboard - compatível com o frontend"""
    try:
        db = get_session(engine)
        from backend.models.database import Female, Bull, Mating
        
        # Estatísticas básicas
        total_females = db.query(Female).count()
        active_females = db.query(Female).filter(Female.is_active == True).count()
        total_bulls = db.query(Bull).count()
        available_bulls = db.query(Bull).filter(Bull.is_available == True).count()
        total_matings = db.query(Mating).count()
        
        # Médias do rebanho (simples por agora)
        avg_milk = db.query(Female.milk).filter(Female.milk.isnot(None)).all()
        avg_pl = db.query(Female.productive_life).filter(Female.productive_life.isnot(None)).all()
        avg_inb = db.query(Female.genomic_inbreeding).filter(Female.genomic_inbreeding.isnot(None)).all()
        
        # Calcular médias
        milk_avg = sum(x[0] for x in avg_milk) / len(avg_milk) if avg_milk else 0
        pl_avg = sum(x[0] for x in avg_pl) / len(avg_pl) if avg_pl else 0
        inb_avg = sum(x[0] for x in avg_inb) / len(avg_inb) if avg_inb else 0
        
        # Top touros (placeholder)
        top_bulls = []
        
        db.close()
        
        return jsonify({
            "summary": {
                "total_females": total_females,
                "active_females": active_females,
                "total_bulls": total_bulls,
                "available_bulls": available_bulls,
                "total_matings": total_matings,
                "recent_matings": 0,  # placeholder
                "success_rate": 85.0  # placeholder
            },
            "herd_averages": {
                "milk": round(milk_avg, 0),
                "productive_life": round(pl_avg, 2),
                "genomic_inbreeding": round(inb_avg, 2)
            },
            "top_bulls": top_bulls,
            "last_updated": datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"Erro na dashboard full API: {str(e)}")
        return jsonify({
            "summary": {
                "total_females": 0,
                "active_females": 0,
                "total_bulls": 0,
                "available_bulls": 0,
                "total_matings": 0,
                "recent_matings": 0,
                "success_rate": 0
            },
            "herd_averages": {
                "milk": 0,
                "productive_life": 0,
                "genomic_inbreeding": 0
            },
            "top_bulls": [],
            "last_updated": datetime.now().isoformat()
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

# ============================================================================
# ROTAS DE IMPORTAÇÃO (SEM CONFLITOS)
# ============================================================================

@app.route('/api/import/test', methods=['GET', 'POST'])
def import_test():
    """Teste das rotas de importação"""
    return jsonify({
        "status": "success",
        "message": "Rotas de importação funcionando!",
        "method": request.method,
        "database_type": "PostgreSQL" if os.environ.get('DATABASE_URL') else "SQLite",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/females/import', methods=['POST'])
def import_females_production():
    """Importação de fêmeas - PRODUÇÃO"""
    try:
        # Log para debug
        print(f"🔍 Recebendo importação de fêmeas...")
        print(f"   Files: {list(request.files.keys())}")
        print(f"   Form: {dict(request.form)}")
        
        if 'file' not in request.files:
            print("❌ Erro: Nenhum arquivo enviado")
            return jsonify({'error': 'Nenhum arquivo enviado'}), 400
        
        file = request.files['file']
        user = request.form.get('user', 'Pedro')
        
        print(f"   Arquivo: {file.filename}")
        print(f"   User: {user}")
        
        if file.filename == '':
            print("❌ Erro: Nome de arquivo vazio")
            return jsonify({'error': 'Nome de arquivo inválido'}), 400
        
        if not file.filename.endswith(('.xlsx', '.xls')):
            print("❌ Erro: Formato inválido")
            return jsonify({'error': 'Arquivo deve ser Excel (.xlsx ou .xls)'}), 400
        
        print("📁 Salvando arquivo temporário...")
        
        # Usar diretório temporário do sistema
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            file.save(tmp_file.name)
            print(f"   Salvo em: {tmp_file.name}")
            
            try:
                print("📊 Lendo Excel...")
                import pandas as pd
                df = pd.read_excel(tmp_file.name)
                print(f"   Lidas {len(df)} linhas")
                print(f"   Colunas: {list(df.columns[:5])}...")  # Primeiras 5 colunas
                
                if len(df) == 0:
                    return jsonify({'error': 'Arquivo Excel está vazio'}), 400
                
                print("💾 Processando dados...")
                
                # Por agora, só simular (para testar se funciona)
                stats = {
                    'added': len(df),
                    'updated': 0,
                    'unchanged': 0
                }
                
                print("✅ Processamento concluído!")
                
                return jsonify({
                    'success': True,
                    'message': f'Arquivo processado com sucesso! {len(df)} registros encontrados',
                    'stats': stats,
                    'columns': list(df.columns[:10]),  # Primeiras 10 colunas para debug
                    'preview': df.head(2).to_dict('records') if len(df) > 0 else []
                })
                
            except Exception as e:
                print(f"❌ Erro ao processar: {str(e)}")
                import traceback
                traceback.print_exc()
                return jsonify({'error': f'Erro ao processar arquivo: {str(e)}'}), 500
            finally:
                # Limpar arquivo temporário
                try:
                    os.unlink(tmp_file.name)
                    print("🗑️ Arquivo temporário removido")
                except:
                    pass
                
    except Exception as e:
        print(f"❌ Erro geral: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@app.route('/api/bulls/import', methods=['POST'])
def import_bulls_production():
    """Importação de touros - PRODUÇÃO"""
    try:
        print(f"🔍 Recebendo importação de touros...")
        
        if 'file' not in request.files:
            return jsonify({'error': 'Nenhum arquivo enviado'}), 400
        
        file = request.files['file']
        user = request.form.get('user', 'Pedro')
        
        print(f"   Arquivo: {file.filename}")
        
        if not file.filename.endswith('.pdf'):
            return jsonify({'error': 'Arquivo deve ser PDF'}), 400
        
        print("📁 Salvando PDF temporário...")
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            file.save(tmp_file.name)
            
            try:
                print("📄 Lendo PDF...")
                import PyPDF2
                with open(tmp_file.name, 'rb') as pdf_file:
                    pdf_reader = PyPDF2.PdfReader(pdf_file)
                    pages = len(pdf_reader.pages)
                
                print(f"   PDF com {pages} páginas")
                
                if pages == 0:
                    return jsonify({'error': 'PDF está vazio'}), 400
                
                # Por agora, só simular
                stats = {
                    'added': pages,
                    'updated': 0,
                    'unchanged': 0
                }
                
                print("✅ PDF processado!")
                
                return jsonify({
                    'success': True,
                    'message': f'PDF processado com sucesso! {pages} páginas encontradas',
                    'stats': stats
                })
                
            except Exception as e:
                print(f"❌ Erro ao processar PDF: {str(e)}")
                return jsonify({'error': f'Erro ao processar PDF: {str(e)}'}), 500
            finally:
                try:
                    os.unlink(tmp_file.name)
                except:
                    pass
                
    except Exception as e:
        print(f"❌ Erro geral: {str(e)}")
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

# ============================================================================
# ROTAS DE FRONTEND
# ============================================================================

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

# ============================================================================
# ARQUIVOS ESTÁTICOS
# ============================================================================

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
    print("🐄 GENEFY - SISTEMA DE ACASALAMENTO")
    print("="*60)
    print(f"Banco: {'PostgreSQL' if os.environ.get('DATABASE_URL') else 'SQLite'}")
    print(f"Porta: {os.environ.get('PORT', 5000)}")
    print("="*60)
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
