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
            # Extrai o texto da página mantendo a estrutura visual
            text = page.extract_text()
            if not text:
                continue
                
            linhas = text.split('\n')
            for linha in linhas:
                colunas = linha.split()
                # 22 colunas vazias para o seu padrão de Analista Fiscal
                linha_excel = [""] * 22
                
                # 1. Captura o Percentual de Recolhimento
                if "Percentual de recolhimento efetivo:" in linha:
                    match = re.search(r"(\d+[\.,]\d+)", linha)
                    if match:
                        percentual_atual = match.group(1).replace(',', '.')
                    # Coloca a linha inteira na primeira célula para manter o cabeçalho
                    linha_excel[0] = linha
                    dados_finais.append(linha_excel)
                    continue

                # 2. Identifica Linhas de Produtos (Pela Data no início: DD/MM/AAAA)
                if len(colunas) >= 5 and re.match(r"\d{2}/\d{2}/\d{4}", colunas[0]):
                    data_doc = colunas[0]
                    num_doc = colunas[1]
                    
                    # Reconstroi a descrição do produto (que costuma ficar no meio da linha)
                    # No PDF, pegamos o que está entre o CFOP e os valores
                    desc_completa = " ".join(colunas[4:-5]) 
                    
                    # Preenche as colunas conforme sua Aba Python:
                    linha_excel[0] = data_doc        # Coluna A
                    linha_excel[1] = num_doc         # Coluna B
                    linha_excel[5] = colunas[2]      # Coluna F (Ex: Acumulador)
                    
                    # REGRAS DA MARIANA:
                    # Coluna G (índice 6): ID Único (Documento-Produto)
                    linha_excel[6] = f"{num_doc}-{desc_completa}"
                    
                    # Coluna H (índice 7): Percentual replicado
                    linha_excel[7] = percentual_atual
                    
                    # Coluna K (índice 10): Descrição do Produto
                    linha_excel[10] = desc_completa
                    
                    # Preenche valores finais (Base, ICMS, etc)
                    if len(colunas) >= 8:
                        linha_excel[15] = colunas[-3] # Base Cálculo
                        linha_excel[20] = colunas[-1] # Valor ICMS

                    dados_finais.append(linha_excel)
                    continue

                # 3. Linhas de Totais
                if "Total:" in linha or "Total saídas:" in linha:
                    linha_excel[0] = linha
                    linha_excel[5] = "-"
                    linha_excel[7] = percentual_atual
                    dados_finais.append(linha_excel)
                else:
                    # Mantém outras linhas para não perder a hierarquia fiscal
                    linha_excel[0] = linha
                    dados_finais.append(linha_excel)

    return pd.DataFrame(dados_finais)

# --- Interface ---
st.set_page_config(page_title="PDF para Aba Python", layout="wide")

st.title("⚖️ Conversor de PDF para Excel (Aba Python)")
st.markdown(f"**Analista:** Mariana | Nascel Contabilidade")

arquivo_pdf = st.file_uploader("Suba o PDF da Domínio aqui", type=["pdf"])

if arquivo_pdf:
    with st.spinner('Escaneando PDF e gerando sua Auditoria...'):
        df = processar_pdf_fiscal(arquivo_pdf)
        
        if not df.empty:
            # Gerando Excel Real
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, header=False, sheet_name='Aba Python')
            
            st.success("✅ Excel gerado!")
            st.download_button(
                label="📥 Baixar Planilha para Auditoria (.xlsx)",
                data=buffer.getvalue(),
                file_name=f"AUDITORIA_RET_{arquivo_pdf.name.replace('.pdf', '')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
            st.divider()
            st.write("### 🔍 Conferência Visual (Coluna G e H)")
            st.dataframe(df.head(100))
