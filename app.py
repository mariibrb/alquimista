import streamlit as st
import pandas as pd
import io

def processar_relatorio_dominio_ret(file_buffer):
    # Lendo o arquivo CSV nº 4 com separador ';' conforme identificado
    # dtype=str é essencial para manter a integridade de CNPJs e vírgulas decimais
    try:
        df = pd.read_csv(file_buffer, sep=';', encoding='latin-1', dtype=str, header=None)
    except Exception:
        # Fallback para arquivos com encoding diferente ou problemas de delimitador
        file_buffer.seek(0)
        df = pd.read_csv(file_buffer, sep=None, engine='python', dtype=str, header=None)

    percentual_atual = ""
    linhas_finais = []

    for index, row in df.iterrows():
        # Convertendo a linha para lista para manipulação precisa de colunas
        linha = row.tolist()
        
        # Transformamos a linha em texto para busca de padrões de bloco
        linha_texto = " ".join([str(x) for x in linha if pd.notna(x)])

        # Lógica de Identificação de Bloco (Replicação de 1.3, 6 e 14)
        # Captura o percentual e o mantém "vivo" para as linhas seguintes do bloco
        if "recolhimento efetivo" in linha_texto.lower() or "Percentual" in linha_texto:
            if "1,30" in linha_texto:
                percentual_atual = "1,30"
            elif "6,00" in linha_texto:
                percentual_atual = "6,00"
            elif "14,00" in linha_texto:
                percentual_atual = "14,00"

        # --- REGRAS DE COLUNA SOLICITADAS ---
        
        # 1. Garantir que a linha tenha tamanho suficiente para alcançar a Coluna J (índice 9)
        while len(linha) < 12:
            linha.append("")

        # 2. REPLICAÇÃO: Colocando o percentual "abaixo da coluna I" (na Coluna J / índice 9)
        # Isso evita que o dado fique "lá no final" e mantém o alinhamento com a Base de Cálculo (I)
        linha[9] = percentual_atual

        # 3. CONCATENAÇÃO: Unindo dados de duas colunas (ex: CFOP + Produto)
        # Mantemos a lógica da sua aba Python: Coluna 3 (D) + Coluna 4 (E)
        cfop = str(linha[3]) if pd.notna(linha[3]) else ""
        produto = str(linha[4]) if pd.notna(linha[4]) else ""
        
        if cfop or produto:
            # Colocamos o concatenado na Coluna K (índice 10) para não sobrescrever o original
            linha[10] = f"{cfop} - {produto}".strip(" -")

        linhas_finais.append(linha)

    # Reconstruindo o DataFrame preservando a hierarquia original
    df_final = pd.DataFrame(linhas_finais)

    # Exportação para Excel via Buffer para o Streamlit
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_final.to_excel(writer, index=False, header=False)
        
        # Ajuste automático de colunas para facilitar a leitura imediata
        worksheet = writer.sheets['Sheet1']
        for i, col in enumerate(df_final.columns):
            worksheet.set_column(i, i, 15)

    return output.getvalue()

# Interface Streamlit
st.set_page_config(page_title="Auditoria RET - Domínio", layout="wide")
st.title("Processador de Crédito Presumido (RET)")
st.markdown("### Lógica de Blocos: 1.3, 6 e 14")

uploaded_file = st.file_uploader("Arraste o arquivo CSV (nº 4) aqui", type=["csv"])

if uploaded_file is not None:
    with st.spinner("Processando replicação de blocos e concatenação..."):
        try:
            excel_processado = processar_relatorio_dominio_ret(uploaded_file)
            
            st.success("Processamento concluído com sucesso!")
            st.download_button(
                label="📥 Baixar Planilha (Percentuais na Coluna J)",
                data=excel_processado,
                file_name="Auditoria_RET_Final.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        except Exception as e:
            st.error(f"Erro crítico no processamento: {e}")
