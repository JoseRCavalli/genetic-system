#!/usr/bin/env python3
"""
Script para processar PDFs de touros do SelectSires/Strategy
e gerar arquivo JSON com dados extraídos
"""

import PyPDF2
import re
import json
import sys
from pathlib import Path

def parse_bull_page(text):
    """Parser robusto para extrair dados dos touros"""
    bull_data = {}
    
    # Código e nome do touro
    code_match = re.search(r'(\d+HO\d+)\s+(\w+)', text)
    if code_match:
        bull_data['code'] = code_match.group(1)
        bull_data['name'] = code_match.group(2)
    
    # Production section
    prod_section = re.search(r'Production\s+Milk\s+Protein\s+Fat.*?([+\-]\d+)\s+([+\-]\d+)\s+([+\-]\d+)', text, re.DOTALL)
    if prod_section:
        bull_data['milk'] = int(prod_section.group(1))
        bull_data['protein'] = int(prod_section.group(2))
        bull_data['fat'] = int(prod_section.group(3))
    
    # NM$, CM$, GM$
    money_section = re.search(r'NM\$\s+CM\$\s+GM\$[+\-\$,\d\s]+\+\$([,\d]+)\s+\+\$([,\d]+)\s+\+\$([,\d]+)', text)
    if money_section:
        bull_data['net_merit'] = int(money_section.group(1).replace(',', ''))
        bull_data['cheese_merit'] = int(money_section.group(2).replace(',', ''))
        bull_data['grazing_merit'] = int(money_section.group(3).replace(',', ''))
    
    # GTPI
    gtpi_section = re.search(r'Type\s+GTPI.*?\+(\d+)', text, re.DOTALL)
    if not gtpi_section:
        gtpi_section = re.search(r'GTPI.*?\+(\d{4})', text)
    if gtpi_section:
        bull_data['gtpi'] = int(gtpi_section.group(1))
    
    # TPI
    tpi_match = re.search(r'TPI.*?(\d{4})', text)
    if tpi_match:
        bull_data['tpi'] = int(tpi_match.group(1))
    
    # Type traits
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
    
    # DPR
    dpr_match = re.search(r'Daughter Pregnancy Rate\s+([+\-]?\d+\.?\d*)\s+\d+%R', text)
    if dpr_match:
        bull_data['dpr'] = float(dpr_match.group(1))
    
    # HCR
    hcr_match = re.search(r'Heifer Conception Rate\s+([+\-]?\d+\.?\d*)\s+\d+%R', text)
    if hcr_match:
        bull_data['hcr'] = float(hcr_match.group(1))
    
    # CCR
    ccr_match = re.search(r'Cow Conception Rate\s+([+\-]?\d+\.?\d*)\s+\d+%R', text)
    if ccr_match:
        bull_data['ccr'] = float(ccr_match.group(1))
    
    # Fertility Index
    fi_match = re.search(r'Fertility Index\s+([+\-]?\d+\.?\d*)\s+\d+%R', text)
    if fi_match:
        bull_data['fertility_index'] = float(fi_match.group(1))
    
    # RFI
    rfi_match = re.search(r'RFI\s+([+\-]\d+)\s+\d+%R', text)
    if rfi_match:
        bull_data['rfi'] = int(rfi_match.group(1))
    
    # Feed Saved
    feed_match = re.search(r'Feed Saved\s+([+\-]\d+)\s+\d+%R', text)
    if feed_match:
        bull_data['feed_saved'] = int(feed_match.group(1))
    
    # Calving Ease
    dce_match = re.search(r'Daughter Calving Ease.*?([+\-]?\d+\.?\d*)\s+\d+%R', text)
    sce_match = re.search(r'Sire Calving Ease.*?([+\-]?\d+\.?\d*)\s+\d+%R', text)
    if dce_match:
        bull_data['daughter_calving_ease'] = float(dce_match.group(1))
    if sce_match:
        bull_data['sire_calving_ease'] = float(sce_match.group(1))
    
    # Genotypes
    beta_match = re.search(r'Beta-Casein:\s*(A1A2|A2A2|A1A1)', text)
    kappa_match = re.search(r'Kappa-Casein:\s*(AA|AB|BB)', text)
    
    if beta_match:
        bull_data['beta_casein'] = beta_match.group(1)
    if kappa_match:
        bull_data['kappa_casein'] = kappa_match.group(1)
    
    # Haplotypes
    haplotypes = []
    if 'HH1T' in text or 'HH1C' in text:
        haplotypes.append('HH1')
    if 'HH2T' in text or 'HH2C' in text:
        haplotypes.append('HH2')
    if 'HH3T' in text or 'HH3C' in text:
        haplotypes.append('HH3')
    if 'HH4T' in text or 'HH4C' in text:
        haplotypes.append('HH4')
    if 'HH5T' in text or 'HH5C' in text:
        haplotypes.append('HH5')
    if 'HH6T' in text or 'HH6C' in text:
        haplotypes.append('HH6')
    
    if haplotypes:
        bull_data['haplotypes'] = haplotypes
    
    # GFI
    gfi_match = re.search(r'GFI.*?(\d+\.?\d*)%', text, re.DOTALL)
    if gfi_match:
        bull_data['gfi'] = float(gfi_match.group(1))
    
    return bull_data

def process_pdf(pdf_path, output_path=None):
    """
    Processa PDF de touros e gera arquivo JSON
    
    Args:
        pdf_path: Caminho para o PDF
        output_path: Caminho para salvar JSON (opcional)
    
    Returns:
        Lista de touros extraídos
    """
    print(f"Processando: {pdf_path}")
    
    bulls_data = []
    
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        total_pages = len(pdf_reader.pages)
        
        print(f"Total de páginas: {total_pages}")
        
        for page_num in range(total_pages):
            if (page_num + 1) % 50 == 0:
                print(f"  Processando página {page_num + 1}/{total_pages}...")
            
            page = pdf_reader.pages[page_num]
            text = page.extract_text()
            
            bull_data = parse_bull_page(text)
            if bull_data and 'code' in bull_data:
                bull_data['page'] = page_num + 1
                bulls_data.append(bull_data)
    
    print(f"\n✓ Extraídos {len(bulls_data)} touros")
    
    # Estatísticas
    with_milk = sum(1 for b in bulls_data if 'milk' in b)
    with_nm = sum(1 for b in bulls_data if 'net_merit' in b)
    with_pl = sum(1 for b in bulls_data if 'productive_life' in b)
    with_beta = sum(1 for b in bulls_data if 'beta_casein' in b)
    
    print(f"\nEstatísticas:")
    print(f"  Com Milk: {with_milk} ({with_milk/len(bulls_data)*100:.1f}%)")
    print(f"  Com Net Merit: {with_nm} ({with_nm/len(bulls_data)*100:.1f}%)")
    print(f"  Com Productive Life: {with_pl} ({with_pl/len(bulls_data)*100:.1f}%)")
    print(f"  Com Beta-Casein: {with_beta} ({with_beta/len(bulls_data)*100:.1f}%)")
    
    # Salvar JSON
    if not output_path:
        pdf_name = Path(pdf_path).stem
        output_path = f'bulls_data_{pdf_name}.json'
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(bulls_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Dados salvos em: {output_path}")
    
    return bulls_data

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python3 process_bulls_pdf.py <caminho_para_pdf> [caminho_saida_json]")
        print("\nExemplo:")
        print("  python3 process_bulls_pdf.py touros.pdf")
        print("  python3 process_bulls_pdf.py touros.pdf bulls_data.json")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not Path(pdf_path).exists():
        print(f"Erro: Arquivo não encontrado: {pdf_path}")
        sys.exit(1)
    
    try:
        process_pdf(pdf_path, output_path)
        print("\n✓ Processamento concluído com sucesso!")
    except Exception as e:
        print(f"\n✗ Erro ao processar PDF: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
