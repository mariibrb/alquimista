import streamlit as st
import pandas as pd
import io
import re

def processar_relatorio_dominio_ret(file_buffer):
    """
    Processa o RET com concatenação sem espaços (celula-celula) na Coluna G
    e mantém a réplica da alíquota na Coluna I.
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

        # 1. IDENTIFICAÇÃO DO PERCENTUAL (Normalmente na Coluna I / Índice 8)
        if "Percentual de recolhimento efetivo" in linha_texto:
            for i, celula in enumerate(linha):
                if pd.notna(celula):
                    match = padrao_aliquota.search(str(celula))
                    if match:
                        percentual_atual = match.group(1)
                        col_index_aliquota = i 
                        break

        # 2. PROCESSAMENTO DAS LINHAS DE DADOS (Identificadas por data na Coluna A)
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
                
                # Ajuste Finiiiissimo: removido o espaço antes e depois do hífen
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

# Interface Streamlit
st.set_page_config(page_title="Auditoria RET - Domínio", layout="wide")
st.title("Relatório de Crédito Presumido - RET")

upped_file = st.file_uploader("Arraste o CSV nº 4 aqui", type=["csv"])

if upped_file is not None:
    with st.spinner("Finalizando ajuste de concatenação..."):
        try:
            excel_out = processar_relatorio_dominio_ret(upped_file)
            st.success("Tudo pronto! Concatenação ajustada sem espaços.")
            st.download_button(
                label="📥 Baixar Excel Ajustado",
                data=excel_out,
                file_name="RET_Dominio_Ajuste_Final.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        except Exception as e:
            st.error(f"Erro no processamento: {e}")
