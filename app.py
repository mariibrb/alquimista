import streamlit as st
import pandas as pd
import io
import re

# --- BLOCO DE ESTILO SENTINELA (RIHANNA STYLE) ---
def aplicar_estilo_sentinela():
    st.markdown("""
        <style>
        /* Fundo Luxo e Fontes */
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&display=swap');
        
        .stApp {
            background-color: #0b0b0b;
            color: #e0e0e0;
        }

        /* Título Diamond */
        h1 {
            color: #d4af37 !important;
            font-family: 'Playfair Display', serif;
            text-align: center;
            text-transform: uppercase;
            letter-spacing: 4px;
            border-bottom: 2px solid #d4af37;
            padding-bottom: 15px;
        }

        /* Botão Stunna Lip Paint (Dourado) */
        div.stButton > button {
            background-color: #d4af37;
            color: black;
            font-weight: bold;
            border-radius: 5px;
            width: 100%;
            border: none;
            transition: 0.3s;
        }

        div.stButton > button:hover {
            background-color: #ffffff;
            box-shadow: 0px 0px 15px #d4af37;
        }

        /* Dropzone (O Primer) */
        section[data-testid="stFileUploadDropzone"] {
            background-color: #1a1a1a;
            border: 2px dashed #d4af37 !important;
        }

        /* Sucesso e Alertas */
        div[data-testid="stNotification"] {
            background-color: #0b0b0b;
            color: #d4af37;
            border: 1px solid #d4af37;
        }
        </style>
    """, unsafe_allow_html=True)

# --- CONFIGURAÇÃO DA INTERFACE ---
st.set_page_config(page_title="Sentinela RET - Rihanna Edit", layout="wide")
aplicar_estilo_sentinela()

def processar_relatorio_dominio_ret(file_buffer):
    """
    Processa o RET com concatenação sem espaços (celula-celula) na Coluna G
    e mantém a réplica da alíquota na Coluna I.
    Lógica original mantida 100% intacta.
    """
    try:
        df = pd.read_csv(file_buffer, sep=';', encoding='latin-1', dtype=str, header=None)
    except Exception:
        file_buffer.seek(0)
        df = pd.read_csv(file_buffer, sep=None, engine='python', dtype=str, header=None)

    percentual_atual = ""
    col_index_aliquota = None
    linhas_finais = []
    padrao_aliquota = re.compile(r'(\d+,\d+)')

    for index, row in df.iterrows():
        linha = row.tolist()
        linha_texto = " ".join([str(x) for x in linha if pd.notna(x)])

        # 1. IDENTIFICAÇÃO DO PERCENTUAL
        if "Percentual de recolhimento efetivo" in linha_texto:
            for i, celula in enumerate(linha):
                if pd.notna(celula):
                    match = padrao_aliquota.search(str(celula))
                    if match:
                        percentual_atual = match.group(1)
                        col_index_aliquota = i 
                        break

        # 2. PROCESSAMENTO DAS LINHAS DE DADOS
        primeira_celula = str(linha[0]).strip()
        if len(primeira_celula) >= 8 and primeira_celula[0:2].isdigit() and "/" in primeira_celula:
            
            # A) REPLICAÇÃO DA ALÍQUOTA (Coluna I / Índice 8)
            if percentual_atual and col_index_aliquota is not None:
                if len(linha) > col_index_aliquota:
                    linha[col_index_aliquota] = percentual_atual

            # B) CONCATENAÇÃO NO ÍNDICE 6 (Coluna G) - SEM ESPAÇOS
            if len(linha) > 10:
                valor_b = str(linha[1]) if pd.notna(linha[1]) and str(linha[1]) != "nan" else ""
                valor_produto = str(linha[10]) if pd.notna(linha[10]) and str(linha[10]) != "nan" else ""
                linha[6] = f"{valor_b}-{valor_produto}".strip("-")

        linhas_finais.append(linha)

    df_final = pd.DataFrame(linhas_finais)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_final.to_excel(writer, index=False, header=False, sheet_name='RET_Auditado')
        workbook = writer.book
        worksheet = writer.sheets['RET_Auditado']
        format_texto = workbook.add_format({'align': 'left'})
        
        total_cols = len(df_final.columns)
        if total_cols > 10:
            worksheet.set_column(6, 6, 35, format_texto)  # Concatenação (G)
            worksheet.set_column(8, 8, 12, format_texto)  # Alíquota (I)
            worksheet.set_column(10, 10, 45, format_texto) # Produto (K)

    return output.getvalue()

# --- ÁREA VISUAL DO APP ---
st.title("💎 SENTINELA RET - RIHANNA EDITION")

upped_file = st.file_uploader("📥 Arraste o CSV nº 4 aqui para a auditoria de luxo", type=["csv"])

if upped_file is not None:
    with st.spinner("Work, work, work... Shine bright like a diamond!"):
        try:
            excel_out = processar_relatorio_dominio_ret(upped_file)
            st.success("✨ Auditoria concluída! O layout está impecável.")
            st.download_button(
                label="📥 BAIXAR EXCEL AJUSTADO",
                data=excel_out,
                file_name="RET_Dominio_Sentinela.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        except Exception as e:
            st.error(f"Erro no processamento: {e}")
