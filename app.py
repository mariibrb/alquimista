import streamlit as st
import pandas as pd
import io
import re

def processar_relatorio_dominio_ret(file_buffer):
    """
    Processa o RET mantendo a integridade absoluta das colunas originais.
    Removeu-se a replicação automática da alíquota para preenchimento manual posterior.
    """
    try:
        # Lendo o CSV com separador ';'
        df = pd.read_csv(file_buffer, sep=';', encoding='latin-1', dtype=str, header=None)
    except Exception:
        file_buffer.seek(0)
        df = pd.read_csv(file_buffer, sep=None, engine='python', dtype=str, header=None)

    total_colunas_originais = len(df.columns)
    linhas_finais = []

    for index, row in df.iterrows():
        linha = row.tolist()
        
        # A lógica de replicação automática na Coluna J (linha[9]) foi removida.
        # Agora o código apenas mantém o que já veio no arquivo original.
        
        linhas_finais.append(linha)

    # Criando DataFrame final com o layout original
    df_final = pd.DataFrame(linhas_finais)

    # Exportação para Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_final.to_excel(writer, index=False, header=False, sheet_name='RET_Auditado')
        
        workbook = writer.book
        worksheet = writer.sheets['RET_Auditado']
        format_texto = workbook.add_format({'align': 'left'})
        
        # Mantendo apenas o ajuste visual para facilitar seu trabalho manual
        if total_colunas_originais > 10:
            worksheet.set_column(8, 8, 12, format_texto)  # CFOP
            worksheet.set_column(9, 9, 12, format_texto)  # Espaço para sua Alíquota
            worksheet.set_column(10, 10, 45, format_texto) # Produto
            worksheet.set_column(0, total_colunas_originais - 1, None, format_texto)

    return output.getvalue()

# Interface Streamlit
st.set_page_config(page_title="Auditoria RET - Domínio", layout="wide")
st.title("Relatório de Crédito Presumido - RET")

upped_file = st.file_uploader("Arraste o CSV nº 4 aqui", type=["csv"])

if upped_file is not None:
    with st.spinner("Processando..."):
        try:
            excel_out = processar_relatorio_dominio_ret(upped_file)
            st.success("Arquivo pronto! Agora você pode informar os percentuais onde desejar.")
            st.download_button(
                label="📥 Baixar Excel para Preenchimento",
                data=excel_out,
                file_name="RET_Dominio_Limpo.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        except Exception as e:
            st.error(f"Erro no processamento: {e}")
