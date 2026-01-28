import streamlit as st
import pandas as pd
import io
import re

def processar_ret_dominio(file):
    # Lendo o CSV da Domínio (usando latin-1 pois arquivos fiscais costumam ter acentos)
    try:
        content = file.getvalue().decode('utf-8')
    except:
        content = file.getvalue().decode('latin-1')
        
    lines = content.split('\n')
    processed_rows = []
    current_percent = ""

    for line in lines:
        # Divide por vírgula (padrão do CSV que você enviou)
        parts = line.split(',')
        parts = [p.strip() for p in parts]
        line_str = " ".join(parts)

        # 1. Captura o Percentual de Recolhimento (Lógica Visual)
        if "Percentual de recolhimento efetivo:" in line_str:
            match = re.search(r"(\d+[\.,]\d+)", line_str)
            if match:
                current_percent = match.group(1).replace(',', '.')
            processed_rows.append(parts)
            continue

        # 2. Identifica Linhas de Itens (Data no formato Excel ex: 46024.0)
        try:
            # Verifica se a primeira coluna é um número de data
            if parts[0].replace('.0', '').isdigit() and float(parts[0]) > 40000:
                doc = parts[1].replace('.0', '')
                produto = parts[10]
                
                # Garante que a linha tenha colunas suficientes para o seu padrão
                while len(parts) < 22: parts.append("")
                
                # REGRAS DA MARIANA:
                # Coluna G (índice 6): ID Único (Documento-Produto)
                parts[6] = f"{doc}-{produto}"
                # Coluna H (índice 7): Percentual replicado
                parts[7] = current_percent
                
                processed_rows.append(parts)
                continue
        except:
            pass

        # 3. Tratamento de Totais (Adiciona o '-' e o % conforme seu modelo)
        if "Total:" in line_str or "Total saídas:" in line_str:
            while len(parts) < 22: parts.append("")
            parts[5] = "-"
            parts[7] = current_percent
            processed_rows.append(parts)
        else:
            processed_rows.append(parts)

    return pd.DataFrame(processed_rows)

# --- Interface Streamlit ---
st.set_page_config(page_title="Conversor RET Domínio", layout="wide", page_icon="📝")

st.title("📝 Conversor RET - Domínio Sistemas")
st.markdown(f"**Analista:** Mariana | **Empresa:** Nascel Contabilidade")

uploaded_file = st.file_uploader("Suba o arquivo CSV extraído da Domínio", type=['csv'])

if uploaded_file:
    with st.spinner('Transformando dados para o padrão Python...'):
        df_final = processar_ret_dominio(uploaded_file)
        
        if not df_final.empty:
            st.success("✅ Arquivo processado com sucesso!")
            
            # Preparação do Download
            csv_ready = df_final.to_csv(index=False, header=False)
            st.download_button(
                label="📥 Baixar CSV Convertido",
                data=csv_ready,
                file_name=f"PYTHON_{uploaded_file.name}",
                mime="text/csv"
            )
            
            st.divider()
            st.write("### 🔍 Conferência da Estrutura (Aba Python)")
            # Mostra as colunas principais para você conferir visualmente
            st.dataframe(df_final.head(50))
        else:
            st.error("Não foi possível processar os dados. Verifique o formato do arquivo.")

st.sidebar.info("Este conversor aplica automaticamente as chaves de ID e os percentuais por linha.")
