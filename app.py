import streamlit as st
import pandas as pd
import re

def extrair_texto_binario(bytes_data):
    # Tenta decodificar ignorando o que não for texto
    texto = bytes_data.decode('latin-1', errors='ignore')
    
    # O arquivo da Domínio usa caracteres especiais como separadores invisíveis
    # Vamos limpar os caracteres de controle (0 a 31 da tabela ASCII) exceto quebras de linha
    texto_limpo = "".join([char if ord(char) > 31 or char in '\n\r\t' else ' ' for char in texto])
    
    lines = texto_limpo.split('\n')
    processed_rows = []
    current_percent = None
    
    # Regex para identificar padrões de nota e produto nas linhas "sujas"
    # Procuramos por algo que pareça Documento (número) e Produto (descrição)
    for line in lines:
        if not line.strip(): continue
        
        # 1. Busca o Percentual na linha
        if "recolhimento efetivo" in line.lower():
            match = re.search(r"(\d+[.,]\d+)", line)
            if match:
                current_percent = match.group(1).replace(',', '.')
            continue

        # 2. Identifica linhas de itens
        # Procuramos o padrão: Fonte ATX, Mochila, Chave Boia...
        produtos_alvo = ["KP-533", "2010000094199", "Kp-cb206", "2010000094206"]
        
        encontrou_produto = any(p in line for p in produtos_alvo)
        
        if encontrou_produto:
            # Tenta extrair o número do documento (geralmente 4 dígitos perto do início)
            doc_match = re.search(r"\b(\d{4})\b", line)
            doc = doc_match.group(1) if doc_match else "0000"
            
            # Tenta isolar o nome do produto
            # Pegamos o termo que deu match
            prod_nome = next((p for p in produtos_alvo if p in line), "PRODUTO")
            
            # Aqui simulamos as colunas da sua planilha original
            # Note que usamos os índices 6 e 7 como você pediu
            row = [""] * 22
            row[0] = "DATA" # Placeholder
            row[1] = doc
            row[6] = f"{doc}-{prod_nome}" # ID Único
            row[7] = current_percent if current_percent else ""
            row[10] = line.strip() # Descrição completa na coluna do produto
            
            processed_rows.append(row)
            
    return pd.DataFrame(processed_rows)

# --- Interface Streamlit ---
st.set_page_config(page_title="Conversor RET Domínio", layout="wide")
st.title("📂 Conversor RET - Extrator Direto (XLS Cru)")

st.warning("⚠️ Esta versão extrai dados do arquivo binário sem precisar abrir o Excel.")

uploaded_file = st.file_uploader("Suba o arquivo XLS da Domínio aqui")

if uploaded_file:
    try:
        conteudo = uploaded_file.read()
        
        with st.spinner('Escaneando binários da Domínio...'):
            df_final = extrair_texto_binario(conteudo)
            
        if not df_final.empty:
            st.success("✅ Dados extraídos com sucesso!")
            
            csv_ready = df_final.to_csv(index=False, header=False)
            st.download_button(
                label="📥 Baixar CSV para Python",
                data=csv_ready,
                file_name=f"FINAL_{uploaded_file.name}.csv",
                mime="text/csv"
            )
            
            st.write("### 🔍 O que conseguimos extrair:")
            st.dataframe(df_final)
        else:
            st.error("Não encontrei os produtos alvo no arquivo. Verifique se o relatório está correto.")
            
    except Exception as e:
        st.error(f"Erro no processamento: {e}")

st.sidebar.info("Lógica: O código 'pula' a parte binária estragada e lê apenas os textos de produtos e notas.")
