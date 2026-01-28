import streamlit as st
import pandas as pd
import io
import re

# --- ESTILO SENTINELA DINÂMICO ---
def aplicar_estilo_sentinela_zonas():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;800&family=Plus+Jakarta+Sans:wght@400;700&display=swap');

        /* 1. FUNDAÇÃO E CABEÇALHO */
        header, [data-testid="stHeader"] { display: none !important; }
        .stApp { transition: background 0.8s ease-in-out !important; }

        /* 2. MENU SUPERIOR E BOTÕES */
        div.stButton > button {
            color: #6C757D !important; 
            background-color: #FFFFFF !important; 
            border: 1px solid #DEE2E6 !important;
            border-radius: 15px !important;
            font-family: 'Montserrat', sans-serif !important;
            font-weight: 800 !important;
            height: 75px !important;
            text-transform: uppercase;
            opacity: 0.8;
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
        }

        div.stButton > button:hover {
            transform: translateY(-5px) !important;
            opacity: 1 !important;
            box-shadow: 0 10px 20px rgba(0,0,0,0.1) !important;
        }

        /* 3. ZONA ROSA (AUDITORIA) */
        .stApp { 
            background: radial-gradient(circle at top right, #FFDEEF 0%, #F8F9FA 100%) !important; 
        }

        [data-testid="stFileUploader"] { 
            border: 2px dashed #FF69B4 !important; 
            border-radius: 20px !important;
            background: #FFFFFF !important;
            padding: 30px !important;
        }

        [data-testid="stFileUploader"] section button, 
        div.stDownloadButton > button {
            background-color: #FF69B4 !important; 
            color: white !important; 
            border: 3px solid #FFFFFF !important;
            font-weight: 700 !important;
            border-radius: 15px !important;
            box-shadow: 0 0 15px rgba(255, 105, 180, 0.4) !important;
        }

        h1 {
            font-family: 'Montserrat', sans-serif;
            font-weight: 800;
            color: #FF69B4 !important;
            text-align: center;
        }
        </style>
    """, unsafe_allow_html=True)

# --- CONFIGURAÇÃO E INTERFACE ---
st.set_page_config(page_title="Sentinela RET - Auditoria", layout="wide")
aplicar_estilo_sentinela_zonas()

def processar_relatorio_dominio_ret(file_buffer):
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

        if "Percentual de recolhimento efetivo" in linha_texto:
            for i, celula in enumerate(linha):
                if pd.notna(celula):
                    match = padrao_aliquota.search(str(celula))
                    if match:
                        percentual_atual = match.group(1)
                        col_index_aliquota = i 
                        break

        primeira_celula = str(linha[0]).strip()
        if len(primeira_celula) >= 8 and primeira_celula[0:2].isdigit() and "/" in primeira_celula:
            if percentual_atual and col_index_aliquota is not None:
                linha[col_index_aliquota] = percentual_atual

            if len(linha) > 10:
                v_b = str(linha[1]) if pd.notna(linha[1]) and str(linha[1]) != "nan" else ""
                v_k = str(linha[10]) if pd.notna(linha[10]) and str(linha[10]) != "nan" else ""
                linha[6] = f"{v_b}-{v_k}".strip("-")

        linhas_finais.append(linha)

    df_final = pd.DataFrame(linhas_finais)
    output = io.BytesIO()
    
    # SALVAMENTO COM AJUSTE DE COLUNAS
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_final.to_excel(writer, index=False, header=False, sheet_name='RET_Auditado')
        workbook = writer.book
        worksheet = writer.sheets['RET_Auditado']
        format_texto = workbook.add_format({'align': 'left'})
        
        # Aplicando as larguras para facilitar sua leitura manual depois
        total_cols = len(df_final.columns)
        if total_cols > 10:
            worksheet.set_column(6, 6, 35, format_texto)   # Coluna G (Concatenação)
            worksheet.set_column(8, 8, 12, format_texto)   # Coluna I (Alíquota)
            worksheet.set_column(10, 10, 45, format_texto) # Coluna K (Produto)
            
    return output.getvalue()

# --- ÁREA VISUAL ---
st.title("CONVERSOR - DEMONSTRATIVO DE CRÉDITO PRESUMIDO")

upped_file = st.file_uploader("Arraste o CSV aqui para auditar", type=["csv"])

if upped_file is not None:
    # Usei o botão de processamento para você ter controle de quando iniciar
    if st.button("🚀 INICIAR CONVERSÃO"):
        with st.spinner("Processando..."):
            excel_out = processar_relatorio_dominio_ret(upped_file)
            st.success("✅ Conversão concluída com sucesso!")
            st.download_button(
                label="📥 BAIXAR EXCEL AJUSTADO",
                data=excel_out,
                file_name="RET_Crédito Presumido.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
