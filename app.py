import streamlit as st
import pandas as pd
import pdfplumber
import io
import re

def processar_pdf_fiscal(pdf_file):
    dados_finais = []
    percentual_atual = ""
    
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            # Extraímos as tabelas com configurações específicas para não perder colunas de valores
            # A Domínio gera tabelas que o pdfplumber as vezes ignora sem esses ajustes
            tabelas = page.extract_tables({
                "vertical_strategy": "text", 
                "horizontal_strategy": "text",
                "snap_tolerance": 3,
            })
            
            if not tabelas:
                # Se não achar tabela, tentamos extrair o texto bruto para não te deixar na mão
                texto_bruto = page.extract_text()
                if texto_bruto:
                    linhas_texto = texto_bruto.split('\n')
                    tabelas = [[l.split()] for l in linhas_texto]

            for tabela in tabelas:
                for row in tabela:
                    # Limpeza de caracteres nulos e espaços
                    row_clean = [str(item).strip() if item else "" for item in row]
                    line_text = " ".join(row_clean)
                    
                    # Ignora linhas totalmente vazias
                    if not any(row_clean):
                        continue

                    # Criamos a linha base com as 22 colunas da sua Aba Python
                    linha_excel = [""] * 22

                    # 1. Captura o Percentual de Recolhimento (Ajuste Fino: 1,3)
                    if "Percentual de recolhimento efetivo:" in line_text:
                        match = re.search(r"(\d+[\.,]\d+)", line_text)
                        if match:
                            percentual_atual = match.group(1).replace('.', ',')
                        linha_excel[0] = line_text
                        dados_finais.append(linha_excel)
                        continue

                    # 2. Captura o Cabeçalho da Linha 7 (Documento, Acumulador, etc.)
                    if "Documento" in line_text and "Acumulador" in line_text:
                        # Mapeamos o cabeçalho para a primeira linha para você visualizar
                        for i, col_name in enumerate(row_clean):
                            if i < 22: linha_excel[i] = col_name
                        dados_finais.append(linha_excel)
                        continue

                    # 3. Identifica Linhas de Itens (Pela Data no início: DD/MM/AAAA)
                    if len(row_clean) >= 5 and re.match(r"\d{2}/\d{2}/\d{4}", row_clean[0]):
                        # Extração Direta por Posição (Padrão Domínio RET)
                        data_doc = row_clean[0]
                        num_doc  = row_clean[1]
                        acumulador = row_clean[2]
                        
                        # O CFOP e o Produto as vezes vêm grudados na mesma célula no PDF
                        cfop_prod = row_clean[3] if len(row_clean) > 3 else ""
                        parts_cfop = cfop_prod.split('\n')
                        cfop = parts_cfop[0].replace('-', '') if len(parts_cfop) > 0 else ""
                        produto = parts_cfop[-1] if len(parts_cfop) > 1 else cfop_prod
                        
                        # Preenchimento seguindo a hierarquia da sua Aba Python
                        linha_excel[0] = data_doc         # Coluna A
                        linha_excel[1] = num_doc          # Coluna B
                        linha_excel[5] = acumulador       # Coluna F
                        
                        # REGRA MARIANA: ID Único e Percentual
                        linha_excel[6] = f"{num_doc}-{produto}" # Coluna G
                        linha_excel[7] = percentual_atual       # Coluna H
                        linha_excel[8] = cfop                   # Coluna I
                        linha_excel[10] = produto               # Coluna K
                        
                        # Captura das Colunas de Valores (Base de Cálculo, Isentas, ICMS...)
                        # Mapeamento dinâmico baseado no final da linha (onde ficam os valores)
                        if len(row_clean) >= 10:
                            linha_excel[12] = row_clean[4]  # Tipo Produto
                            linha_excel[13] = row_clean[5]  # Valor Produto
                            linha_excel[14] = row_clean[6]  # Valor Contábil
                            linha_excel[15] = row_clean[7]  # Base Cálculo
                            linha_excel[16] = row_clean[8]  # Isentas
                            linha_excel[20] = row_clean[9]  # Valor ICMS
                        
                        dados_finais.append(linha_excel)
                        continue

                    # 4. Tratamento de Totais
                    if "Total:" in line_text or "Total saídas:" in line_text:
                        linha_excel[0] = line_text
                        linha_excel[5] = "-"
                        linha_excel[7] = percentual_atual
                        # Tenta pegar os valores do total que ficam no final da linha
                        if len(row_clean) > 5:
                            linha_excel[14] = row_clean[-4] # Total Contábil
                            linha_excel[15] = row_clean[-3] # Total Base
                            linha_excel[20] = row_clean[-1] # Total ICMS
                        dados_finais.append(linha_excel)
                    else:
                        # Mantém o restante (Cabeçalhos de página, etc.)
                        linha_excel[0] = line_text
                        dados_finais.append(linha_excel)

    return pd.DataFrame(dados_finais)

# --- Interface Streamlit ---
st.set_page_config(page_title="PDF para Aba Python - Nascel", layout="wide", page_icon="⚖️")

st.title("⚖️ Conversor Fiscal: PDF para Excel (Aba Python)")
st.info("Foco: Recuperação de todas as colunas de valores e cabeçalhos iniciados na linha 7.")

arquivo_pdf = st.file_uploader("Suba o PDF ORIGINAL da Domínio", type=["pdf"])

if arquivo_pdf:
    try:
        with st.spinner('Escaneando todas as colunas de valores...'):
            df_final = processar_pdf_fiscal(arquivo_pdf)
            
            if not df_final.empty:
                # Gerando Excel (.xlsx) real
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    df_final.to_excel(writer, index=False, header=False, sheet_name='Aba Python')
                
                st.success("✅ Excel gerado com todas as colunas de valores!")
                
                st.download_button(
                    label="📥 Baixar Planilha para Auditoria (.xlsx)",
                    data=buffer.getvalue(),
                    file_name=f"AUDITORIA_COMPLETA_{arquivo_pdf.name.split('.')[0]}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
                st.divider()
                st.write("### 🔍 Conferência Visual (Verifique os Valores e o Cabeçalho)")
                st.dataframe(df_final.head(100))
            else:
                st.error("Não foi possível extrair os dados. O PDF está no formato original?")
                
    except Exception as e:
        st.error(f"Erro ao processar: {e}")
