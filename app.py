import streamlit as st
import pandas as pd
import pdfplumber
import io
import re

def processar_pdf_aba_python(pdf_file):
    dados_finais = []
    percentual_atual = ""
    
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            # Extraímos as tabelas com foco em capturar todas as colunas de valores
            tabelas = page.extract_tables({
                "vertical_strategy": "text", 
                "horizontal_strategy": "text",
                "snap_tolerance": 4,
            })
            
            for tabela in tabelas:
                for row in tabela:
                    # Limpeza de dados nulos
                    row_clean = [str(item).strip() if item else "" for item in row]
                    line_text = " ".join(row_clean)
                    
                    if not any(row_clean) or "Página:" in line_text:
                        continue

                    # Criamos a linha base com 22 colunas (índices 0 a 21)
                    linha_excel = [""] * 22

                    # 1. Captura o Percentual de Recolhimento (Ajuste: 1,3)
                    if "Percentual de recolhimento efetivo:" in line_text:
                        match = re.search(r"(\d+[\.,]\d+)", line_text)
                        if match:
                            percentual_atual = match.group(1).replace('.', ',')
                        linha_excel[0] = line_text
                        dados_finais.append(linha_excel)
                        continue

                    # 2. Captura o Cabeçalho (Linha 7)
                    if "Documento" in line_text and "Acumulador" in line_text:
                        # Mapeamos o cabeçalho conforme a estrutura da aba python
                        linha_excel[0] = "Data"
                        linha_excel[1] = "Documento"
                        linha_excel[5] = "Acumulador"
                        linha_excel[6] = "ID Único"
                        linha_excel[7] = "Percentual"
                        linha_excel[8] = "CFOP"
                        linha_excel[10] = "Produto"
                        linha_excel[12] = "Tipo do produto"
                        linha_excel[13] = "Valor produto"
                        linha_excel[14] = "Valor contábil"
                        linha_excel[15] = "Base cálculo"
                        linha_excel[16] = "Isentas"
                        linha_excel[20] = "Valor ICMS"
                        dados_finais.append(linha_excel)
                        continue

                    # 3. Identifica Linhas de Itens (Data: DD/MM/AAAA)
                    # Exemplo no PDF: "02/01/2026", "1177", "5000", "6-106... Produto", "2", "142,00", etc.
                    if len(row_clean) >= 5 and re.match(r"\d{2}/\d{2}/\d{4}", row_clean[0]):
                        data_original = row_clean[0]
                        documento = row_clean[1]
                        acumulador = row_clean[2]
                        
                        # Tratamento do CFOP e Produto que podem vir na mesma célula
                        cfop_produto = row_clean[3] if len(row_clean) > 3 else ""
                        cfop_match = re.match(r"^(\d-?\d{3})", cfop_produto)
                        cfop = cfop_match.group(1).replace('-', '') if cfop_match else ""
                        produto = cfop_produto.replace(cfop_match.group(0), "").strip() if cfop_match else cfop_produto
                        
                        # REGRAS DA MARIANA (Mapeamento exato de colunas):
                        linha_excel[0] = data_original       # Col A
                        linha_excel[1] = documento           # Col B
                        linha_excel[5] = acumulador          # Col F
                        linha_excel[6] = f"{documento}-{produto}" # Col G: ID Único
                        linha_excel[7] = percentual_atual    # Col H: % com vírgula
                        linha_excel[8] = cfop                # Col I: CFOP
                        linha_excel[10] = produto            # Col K: Produto
                        
                        # Mapeamento das colunas de valores (conforme PDF original)
                        # No PDF, após o produto temos: Tipo(4), V.Prod(5), V.Cont(6), Base(7), Isentas(8), ICMS(9)
                        if len(row_clean) >= 10:
                            linha_excel[12] = row_clean[4]   # Col M: Tipo do produto
                            linha_excel[13] = row_clean[5]   # Col N: Valor produto
                            linha_excel[14] = row_clean[6]   # Col O: Valor contábil
                            linha_excel[15] = row_clean[7]   # Col P: Base cálculo
                            linha_excel[16] = row_clean[8]   # Col Q: Isentas
                            linha_excel[20] = row_clean[9]   # Col U: Valor ICMS
                        
                        dados_finais.append(linha_excel)
                        continue

                    # 4. Tratamento de Totais
                    if "Total:" in line_text or "Total saídas:" in line_text:
                        linha_excel[0] = line_text
                        linha_excel[5] = "-" # Sinal de total solicitado
                        linha_excel[7] = percentual_atual
                        # Captura valores do total
                        valores_total = [c for c in row_clean if "," in c]
                        if len(valores_total) >= 3:
                            linha_excel[14] = valores_total[-4] if len(valores_total) > 3 else ""
                            linha_excel[15] = valores_total[-3]
                            linha_excel[20] = valores_total[-1]
                        dados_finais.append(linha_excel)
                    else:
                        # Mantém outras linhas (MIRAO, CNPJ, Competência)
                        linha_excel[0] = line_text
                        dados_finais.append(linha_excel)

    return pd.DataFrame(dados_finais)

# --- Interface Streamlit ---
st.set_page_config(page_title="PDF para Aba Python", layout="wide", page_icon="⚖️")

st.title("⚖️ Conversor Fiscal: PDF -> Excel (Padrão Aba Python)")
st.markdown("### Analista: Mariana | Nascel Contabilidade")

arquivo_pdf = st.file_uploader("Suba o PDF ORIGINAL da Domínio", type=["pdf"])

if arquivo_pdf:
    try:
        with st.spinner('Construindo a Aba Python com ID Único e Valores...'):
            df_final = processar_pdf_aba_python(arquivo_pdf)
            
            if not df_final.empty:
                # Criando Excel Real (.xlsx)
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    df_final.to_excel(writer, index=False, header=False, sheet_name='Aba Python')
                
                st.success("✅ Excel gerado exatamente no seu padrão!")
                st.download_button(
                    label="📥 Baixar Planilha (.xlsx)",
                    data=buffer.getvalue(),
                    file_name=f"ABA_PYTHON_{arquivo_pdf.name.split('.')[0]}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
                st.divider()
                st.write("### 🔍 Conferência do Mapeamento de Colunas")
                st.dataframe(df_final.head(100))
            else:
                st.error("Erro: Não foi possível extrair dados deste PDF.")
    except Exception as e:
        st.error(f"Erro técnico: {e}")
