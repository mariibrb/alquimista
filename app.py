import streamlit as st
import pandas as pd
import io
import re
from style import aplicar_estilo_rihanna  # Importa o visual

# Configuração da Página
st.set_page_config(page_title="Auditoria RET - Domínio", layout="wide")
aplicar_estilo_rihanna()  # Aplica a "maquiagem" Rihanna

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

        # Identificação da Alíquota
        if "Percentual de recolhimento efetivo" in linha_texto:
            for i, celula in enumerate(linha):
                if pd.notna(celula):
                    match = padrao_aliquota.search(str(celula))
                    if match:
                        percentual_atual = match.group(1)
                        col_index_aliquota = i 
                        break

        # Processamento das Linhas de Dados
        primeira_celula = str(linha[0]).strip()
        if len(primeira_celula) >= 8 and primeira_celula[0:2].isdigit() and "/" in primeira_celula:
            
            # Réplica na Coluna I (Índice 8)
            if percentual_atual and col_index_aliquota is not None:
                if len(linha) > col_index_aliquota:
                    linha[col_index_aliquota] = percentual_atual

            # Concatenação na Coluna G (Índice 6) sem espaços
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
            worksheet.set_column(6, 6, 35, format_texto)
            worksheet.set_column(8, 8, 12, format_texto)
            worksheet.set_column(10, 10, 45, format_texto)

    return output.getvalue()

# Interface do Usuário
st.title("💎 Relatório de Crédito Presumido - RET")
st.markdown("---")

upped_file = st.file_uploader("Arraste o CSV nº 4 aqui para brilhar", type=["csv"])

if upped_file is not None:
    with st.spinner("Shine bright like a diamond..."):
        try:
            excel_out = processar_relatorio_dominio_ret(upped_file)
            st.success("Tudo pronto! Layout ajustado e dados protegidos.")
            st.download_button(
                label="📥 BAIXAR EXCEL FENTY EDIT",
                data=excel_out,
                file_name="RET_Ajuste_Rihanna.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        except Exception as e:
            st.error(f"Erro no processamento: {e}")
