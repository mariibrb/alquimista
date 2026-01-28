import streamlit as st
import pandas as pd
import io
import re

def processar_relatorio_dominio_ret(file_buffer):
    """
    Localiza o percentual de recolhimento efetivo e o replica nas linhas abaixo
    exatamente na mesma coluna onde o valor foi encontrado, respeitando o layout.
    """
    try:
        # Lendo o CSV original com separador ';'
        df = pd.read_csv(file_buffer, sep=';', encoding='latin-1', dtype=str, header=None)
    except Exception:
        file_buffer.seek(0)
        df = pd.read_csv(file_buffer, sep=None, engine='python', dtype=str, header=None)

    percentual_atual = ""
    col_index_aliquota = None
    linhas_finais = []
    
    # Regex para capturar o valor numérico (ex: 1,30)
    padrao_aliquota = re.compile(r'(\d+,\d+)')

    for index, row in df.iterrows():
        linha = row.tolist()
        
        # Transformamos a linha em texto para busca do gatilho
        linha_texto = " ".join([str(x) for x in linha if pd.notna(x)])

        # 1. IDENTIFICAÇÃO DINÂMICA DO PERCENTUAL E DA COLUNA
        # Procuramos a frase gatilho que você mostrou na imagem
        if "Percentual de recolhimento efetivo" in linha_texto:
            # Vasculhamos a linha para ver em qual coluna o número (ex: 1,30) está
            for i, celula in enumerate(linha):
                if pd.notna(celula):
                    match = padrao_aliquota.search(str(celula))
                    if match:
                        percentual_atual = match.group(1)
                        col_index_aliquota = i # Salva que é o índice 8 (Coluna I), por exemplo
                        break

        # 2. REPLICAÇÃO NA MESMA COLUNA
        # Identificamos se é uma linha de dados (Data na Coluna A no formato DD/MM/AAAA)
        primeira_celula = str(linha[0]).strip()
        if len(primeira_celula) >= 8 and primeira_celula[0:2].isdigit() and "/" in primeira_celula:
            if percentual_atual and col_index_aliquota is not None:
                # Replicamos o percentual exatamente na mesma coluna identificada
                # Isso preencherá a coluna abaixo do "1,30" original
                if len(linha) > col_index_aliquota:
                    linha[col_index_aliquota] = percentual_atual

        linhas_finais.append(linha)

    # DataFrame Final mantendo a estrutura original
    df_final = pd.DataFrame(linhas_finais)

    # Exportação para Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_final.to_excel(writer, index=False, header=False, sheet_name='RET_Auditado')
        
        workbook = writer.book
        worksheet = writer.sheets['RET_Auditado']
        format_texto = workbook.add_format({'align': 'left'})
        
        # Ajuste visual das colunas existentes
        total_cols = len(df_final.columns)
        if total_cols > 0:
            worksheet.set_column(0, total_cols - 1, 12, format_texto)
        if total_cols > 10:
            worksheet.set_column(10, 10, 45, format_texto) # Coluna do Produto

    return output.getvalue()

# Interface Streamlit
st.set_page_config(page_title="Auditoria RET - Domínio", layout="wide")
st.title("Relatório de Crédito Presumido - RET")

upped_file = st.file_uploader("Arraste o CSV nº 4 aqui", type=["csv"])

if upped_file is not None:
    with st.spinner("Processando ajuste fino..."):
        try:
            excel_out = processar_relatorio_dominio_ret(upped_file)
            st.success("Boooooa! O percentual foi replicado exatamente na coluna correta.")
            st.download_button(
                label="📥 Baixar Excel Corrigido",
                data=excel_out,
                file_name="RET_Dominio_Alinhado.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        except Exception as e:
            st.error(f"Erro no processamento: {e}")
