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
            # Extrai o texto da página mantendo a estrutura visual para não perder colunas
            text = page.extract_text()
            if not text:
                continue
                
            linhas = text.split('\n')
            for linha in linhas:
                colunas = linha.split()
                # Criamos a linha com 22 colunas conforme o seu padrão de auditoria
                linha_excel = [""] * 22
                
                # 1. Captura o Percentual de Recolhimento e ajusta para o formato com vírgula (Ex: 1,3)
                if "Percentual de recolhimento efetivo:" in linha:
                    match = re.search(r"(\d+[\.,]\d+)", linha)
                    if match:
                        # AJUSTE FINO: Força o uso da vírgula como separador decimal
                        percentual_atual = match.group(1).replace('.', ',')
                    
                    # Mantém o cabeçalho da seção na primeira célula
                    linha_excel[0] = linha
                    dados_finais.append(linha_excel)
                    continue

                # 2. Identifica Linhas de Itens (Pela Data no início: DD/MM/AAAA)
                if len(colunas) >= 5 and re.match(r"\d{2}/\d{2}/\d{4}", colunas[0]):
                    data_doc = colunas[0]
                    num_doc = colunas[1]
                    
                    # Localiza a descrição do produto no meio da linha (padrão PDF Domínio)
                    # Pegamos o conteúdo entre o Acumulador/CFOP e os valores finais
                    desc_completa = " ".join(colunas[4:-5]) 
                    
                    # Preenchimento seguindo a hierarquia da Aba Python:
                    linha_excel[0] = data_doc        # Coluna A
                    linha_excel[1] = num_doc         # Coluna B
                    linha_excel[5] = colunas[2]      # Coluna F (Ex: Acumulador)
                    
                    # REGRA MARIANA: Coluna G (índice 6) -> ID Único (Documento-Produto)
                    linha_excel[6] = f"{num_doc}-{desc_completa}"
                    
                    # REGRA MARIANA: Coluna H (índice 7) -> Percentual com vírgula replicado
                    linha_excel[7] = percentual_atual
                    
                    # Coluna K (índice 10): Descrição do Produto isolada
                    linha_excel[10] = desc_completa
                    
                    # Captura de valores (Base de Cálculo e ICMS)
                    if len(colunas) >= 8:
                        linha_excel[15] = colunas[-3] # Base Cálculo
                        linha_excel[20] = colunas[-1] # Valor ICMS

                    dados_finais.append(linha_excel)
                    continue

                # 3. Tratamento de Linhas de Totais e Sub-totais
                if "Total:" in linha or "Total saídas:" in linha:
                    linha_excel[0] = linha
                    linha_excel[5] = "-"  # Marcador solicitado para totais
                    linha_excel[7] = percentual_atual
                    dados_finais.append(linha_excel)
                else:
                    # Mantém as demais linhas (cabeçalhos do sistema, etc) para não quebrar o layout
                    linha_excel[0] = linha
                    dados_finais.append(linha_excel)

    return pd.DataFrame(dados_finais)

# --- Configuração da Interface Streamlit ---
st.set_page_config(page_title="PDF para Aba Python - Nascel", layout="wide", page_icon="⚖️")

st.title("⚖️ Conversor Fiscal: PDF para Excel (.xlsx)")
st.markdown("### Foco: Auditoria RET | Analista: Mariana")

arquivo_pdf = st.file_uploader("Suba o PDF ORIGINAL da Domínio (Crédito Presumido)", type=["pdf"])

if arquivo_pdf:
    try:
        with st.spinner('Lendo tabelas, gerando IDs e ajustando decimais...'):
            # Processamento dos dados
            df_processado = processar_pdf_fiscal(arquivo_pdf)
            
            if not df_processado.empty:
                # Gerando o arquivo Excel real (.xlsx) para evitar erros de visualização
                output_buffer = io.BytesIO()
                with pd.ExcelWriter(output_buffer, engine='xlsxwriter') as writer:
                    # header=False para manter o layout idêntico à Aba Python enviada
                    df_processado.to_excel(writer, index=False, header=False, sheet_name='Aba Python')
                
                st.success("✅ Processamento concluído!")
                
                # Botão para Download
                st.download_button(
                    label="📥 Baixar Planilha para Auditoria (.xlsx)",
                    data=output_buffer.getvalue(),
                    file_name=f"RET_CONVERTIDO_{arquivo_pdf.name.split('.')[0]}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
                # Conferência visual imediata no App
                st.divider()
                st.write("### 🔍 Prévia da Auditoria (Verifique Colunas G e H)")
                st.dataframe(df_processado.head(100))
            else:
                st.error("Não foram encontrados dados no PDF. Verifique se o arquivo é o relatório original.")
                
    except Exception as e:
        st.error(f"Erro crítico no processamento: {e}")
        st.info("Verifique se o PDF não está protegido por senha ou corrompido.")

st.sidebar.markdown("---")
st.sidebar.write("📌 **Regras de Auditoria Ativas:**")
st.sidebar.write("- ID Único: `Documento-Produto`")
st.sidebar.write("- Decimal: `,` (Padrão Contábil)")
st.sidebar.write("- Estrutura: 22 Colunas (Aba Python)")
