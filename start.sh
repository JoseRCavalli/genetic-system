#!/bin/bash
# Script de Inicialização do Sistema de Acasalamento

echo "========================================="
echo "  Sistema de Acasalamento - Gado Leiteiro"
echo "========================================="
echo ""

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "✗ Python 3 não encontrado. Por favor, instale Python 3.8+"
    exit 1
fi

echo "✓ Python encontrado: $(python3 --version)"

# Instalar dependências
echo ""
echo "Instalando dependências..."
pip install -r requirements.txt --break-system-packages -q

if [ $? -ne 0 ]; then
    echo "✗ Erro ao instalar dependências"
    exit 1
fi

echo "✓ Dependências instaladas"

# Verificar arquivos de dados
echo ""
echo "Verificando arquivos de dados..."

if [ ! -f "/mnt/user-data/uploads/Females_All_List_-_2025-11-03.xlsx" ]; then
    echo "⚠ Aviso: Arquivo de fêmeas não encontrado"
    echo "  Esperado: /mnt/user-data/uploads/Females_All_List_-_2025-11-03.xlsx"
fi

if [ ! -f "bulls_data.json" ]; then
    echo "⚠ Aviso: Arquivo de touros não encontrado (bulls_data.json)"
    echo "  Execute: python3 process_bulls_pdf.py <arquivo.pdf>"
fi

# Iniciar aplicação
echo ""
echo "========================================="
echo "  Iniciando aplicação..."
echo "========================================="
echo ""
echo "Acesse no navegador:"
echo "  → http://localhost:5000"
echo ""
echo "Pressione Ctrl+C para parar o servidor"
echo ""

python3 app.py
