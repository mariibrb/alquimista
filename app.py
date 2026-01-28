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
            text = page.extract_text()
            if not text:
                continue
                
            linhas = text.split('\n')
            for linha in linhas:
                colunas = linha.split()
                linha_excel = [""] * 22
                
                # 1. Captura o Percentual de Recolhimento (Ajuste Fino: 1,3)
                if "Percentual de recolhimento efetivo:" in linha:
                    match = re.search(r"(\d+[\.,]\d+)", linha)
                    if match:
                        percentual_atual = match.group(1).replace('.', ',')
                    linha_excel[0] = linha
                    dados_finais.append(linha_excel)
                    continue

                # 2. Identifica Linhas de Itens (Data no início: DD/MM/AAAA)
                if len(colunas) >= 5 and re.match(r"\d{2}/\d{2}/\d{4}", colunas[0]):
                    data_doc = colunas[0]
                    num_doc = colunas[1]
                    
                    # --- Lógica de Captura de Valores ---
                    # Identificamos onde começam os valores (geralmente campos com vírgula no final da linha)
                    # Vamos pegar todos os campos que contém números e vírgulas do final para o início
                    valores_encontrados = [c for c in colunas if re.search(r"\d+,\d+", c)]
                    
                    # A descrição do produto é o que sobra entre as infos iniciais e os valores
                    # Vamos reconstruir a descrição pegando o que está entre o CFOP (coluna 4) e o primeiro valor
                    desc_completa = " ".join(colunas[4:colunas.index(valores_encontrados[0])]) if valores_encontrados else " ".join(colunas[4:-2])
                    
                    # Preenchimento seguindo sua Aba Python:
                    linha_excel[0] = data_doc        # Coluna A
                    linha_excel[1] = num_doc         # Coluna B
                    linha_excel[5] = colunas[2]      # Coluna F (Acumulador)
                    
                    # REGRA MARIANA: ID Único e Percentual
                    linha_excel[6] = f"{num_doc}-{desc_completa}" # Coluna G
                    linha_excel[7] = percentual_atual             # Coluna H
                    linha_excel[10] = desc_completa               # Coluna K
                    
                    # Mapeamento dos Valores (Baseado no layout da Domínio)
                    if len(valores_encontrados) >= 4:
                        linha_excel[13] = valores_encontrados[0] # Valor Produto
                        linha_excel[14] = valores_encontrados[1] # Valor Contábil
                        linha_excel[15] = valores_encontrados[2] # Base Cálculo
                        linha_excel[20] = valores_encontrados[3] # Valor ICMS
                    elif len(valores_encontrados) == 3:
                        linha_excel[14] = valores_encontrados[0]
                        linha_excel[15] = valores_encontrados[1]
                        linha_excel[20] = valores_encontrados[2]

                    dados_finais.append(linha_excel)
                    continue

                # 3. Tratamento de Totais
                if "Total:" in linha or "Total saídas:" in linha:
                    linha_excel[0] = linha
                    linha_excel[5] = "-"
                    linha_excel[7] = percentual_atual
                    
                    # Também tenta capturar os valores do total
                    valores_total = [c for c in colunas if re.search(r"\d+,\d+", c)]
                    if len(valores_total) >= 3:
                        linha_excel[14] = valores_total[-3]
                        linha_excel[15] = valores_total[-2]
                        linha_excel[20] = valores_total[-1]
                        
                    dados_finais.append(linha_excel)
                else:
                    linha_excel[0] = linha
                    dados_finais.append(linha_excel)

    return pd.DataFrame(dados_finais)

# --- Streamlit ---
st.set_page_config(page_title="PDF para Aba Python - Nascel", layout="wide")
st.title("⚖️ Conversor Fiscal: PDF para Excel (Com Valores)")

arquivo_pdf = st.file_uploader("Suba o PDF ORIGINAL da Domínio", type=["pdf"])

if arquivo_pdf:
    try:
        with st.spinner('Extraindo dados e colunas de valores...'):
            df_processado = processar_pdf_fiscal(arquivo_pdf)
            
            if not df_processado.empty:
                output_buffer = io.BytesIO()
                with pd.ExcelWriter(output_buffer, engine='xlsxwriter') as writer:
                    df_processado.to_excel(writer, index=False, header=False, sheet_name='Aba Python')
                
                st.success("✅ Processamento concluído com todos os valores!")
                st.download_button(
                    label="📥 Baixar Planilha (.xlsx)",
                    data=output_buffer.getvalue(),
                    file_name=f"AUDITORIA_COMPLETA_{arquivo_pdf.name.split('.')[0]}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                st.dataframe(df_processado.head(100))
    except Exception as e:
        st.error(f"Erro: {e}")
