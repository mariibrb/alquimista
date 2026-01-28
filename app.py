import streamlit as st
import pandas as pd
import io
import re

def processar_relatorio_dominio_ret(file_buffer):
    """
    Processa o RET mantendo o Produto original e replicando a alíquota na Coluna J.
    Realiza a concatenação em uma nova coluna ao final.
    """
    try:
        # Lendo o CSV nº 4 com separador ';' e mantendo tipos como string
        df = pd.read_csv(file_buffer, sep=';', encoding='latin-1', dtype=str, header=None)
    except Exception:
        file_buffer.seek(0)
        df = pd.read_csv(file_buffer, sep=None, engine='python', dtype=str, header=None)

    percentual_atual = ""
    linhas_finais = []
    
    # Regex para capturar qualquer alíquota informada no bloco
    padrao_aliquota = re.compile(r'(\d+,\d+)')

    for index, row in df.iterrows():
        linha = row.tolist()
        linha_texto = " ".join([str(x) for x in linha if pd.notna(x)])

        # 1. IDENTIFICAÇÃO DINÂMICA DO PERCENTUAL
        if "recolhimento efetivo" in linha_texto.lower() or "Percentual de" in linha_texto:
            busca = padrao_aliquota.search(linha_texto)
            if busca:
                percentual_atual = busca.group(1)

        # 2. AJUSTE DE TAMANHO DA LINHA
        # Garantimos que a linha tenha pelo menos 22 colunas (padrão do CSV 4 da Domínio)
        while len(linha) < 23:
            linha.append("")

        # 3. REPLICAÇÃO NA COLUNA J (Índice 9)
        # Colocamos a alíquota aqui para ficar "abaixo da coluna I"
        linha[9] = percentual_atual

        # 4. CONCATENAÇÃO (CFOP + PRODUTO)
        # CFOP está no índice 8 | Produto está no índice 10
        cfop = str(linha[8]) if pd.notna(linha[8]) and str(linha[8]) != "nan" else ""
        produto = str(linha[10]) if pd.notna(linha[10]) and str(linha[10]) != "nan" else ""
        
        # Criamos a concatenação em uma nova coluna no final (índice 22)
        # Assim NÃO sobrescrevemos o Produto original no índice 10
        if cfop or produto:
            linha[22] = f"{cfop} - {produto}".strip(" -")
        else:
            linha[22] = ""

        linhas_finais.append(linha)

    # Criando DataFrame final mantendo a integridade
    df_final = pd.DataFrame(linhas_finais)

    # Exportação para Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_final.to_excel(writer, index=False, header=False, sheet_name='RET_Auditado')
        
        workbook = writer.book
        worksheet = writer.sheets['RET_Auditado']
        format_texto = workbook.add_format({'align': 'left'})
        
        # Ajuste de largura das colunas principais
        worksheet.set_column(8, 8, 12, format_texto)  # CFOP
        worksheet.set_column(9, 9, 10, format_texto)  # Alíquota (Coluna J)
        worksheet.set_column(10, 10, 40, format_texto) # Produto (Preservado)
        worksheet.set_column(22, 22, 50, format_texto) # Concatenação Final

    return output.getvalue()

# Interface Streamlit
st.set_page_config(page_title="Auditoria RET - Domínio", layout="wide")
st.title("Relatório de Crédito Presumido - RET")

upped_file = st.file_uploader("Arraste o CSV nº 4 aqui", type=["csv"])

if upped_file is not None:
    with st.spinner("Processando..."):
        try:
            excel_out = processar_relatorio_dominio_ret(upped_file)
            st.success("Arquivo ajustado! O Produto foi mantido e a alíquota está na Coluna J.")
            st.download_button(
                label="📥 Baixar Excel Corrigido",
                data=excel_out,
                file_name="RET_Dominio_Final_Ajustado.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        except Exception as e:
            st.error(f"Erro no processamento: {e}")
