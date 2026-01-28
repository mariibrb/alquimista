import streamlit as st
import pandas as pd
import io
import re

def processar_regras_mariana(df):
    processed_rows = []
    current_percent = None
    
    # Transformamos em lista para percorrer linha a linha com precisão
    data = df.values.tolist()
    
    for row in data:
        # Limpa e converte cada célula para string
        parts = [str(item).strip() if pd.notna(item) else "" for item in row]
        line_full = " ".join(parts)
        
        # 1. Identifica o Percentual (Ex: 1.3, 6.0, 14.0)
        if "Percentual de recolhimento efetivo:" in line_full:
            match = re.search(r"recolhimento efetivo:\s*(\d+\.?\d*)", line_full)
            if match:
                current_percent = match.group(1)
            processed_rows.append(parts)
            continue

        # 2. Processa linhas de Itens (Onde a data é o número do Excel > 40000)
        try:
            # Remove o '.0' que o Excel coloca em números
            val_0 = parts[0].split('.')[0]
            if val_0.isdigit() and int(val_0) > 40000 and len(parts) > 10:
                doc = parts[1].split('.')[0]
                prod_desc = parts[10]
                
                # Criando o ID conforme sua aba Python: Documento-Produto (Índice 6)
                parts[6] = f"{doc}-{prod_desc}"
                # Inserindo o Percentual na Coluna H (Índice 7)
                parts[7] = current_percent if current_percent else ""
                
                processed_rows.append(parts)
                continue
        except (ValueError, IndexError):
            pass

        # 3. Totais e Cabeçalhos
        if "Total:" in line_full or "DÉBITOS PELAS SAÍDAS" in line_full:
            if len(parts) > 7:
                parts[5] = "-"
                parts[7] = current_percent if current_percent else ""
            processed_rows.append(parts)
        else:
            processed_rows.append(parts)
            
    return pd.DataFrame(processed_rows)

# --- Interface Streamlit ---
st.set_page_config(page_title="Conversor RET Domínio", layout="wide")
st.title("📂 Conversor RET - Direto da Domínio (XLS)")

# Upload sem travas de tipo para evitar o erro "Not Allowed"
file = st.file_uploader("Suba o arquivo XLS EXATAMENTE como sai do sistema")

if file is not None:
    try:
        # O segredo: engine='xlrd' para ler o formato binário que você enviou
        df_raw = pd.read_excel(file, engine='xlrd', header=None)
        
        with st.spinner('Aplicando regras fiscais...'):
            df_final = processar_regras_mariana(df_raw)
        
        st.success("✅ Arquivo cru lido e processado!")
        
        # Download do CSV pronto para o seu Python
        csv_ready = df_final.to_csv(index=False, header=False)
        st.download_button(
            label="📥 Baixar Relatório para Python",
            data=csv_ready,
            file_name=f"PYTHON_{file.name.replace('.xls', '.csv')}",
            mime="text/csv"
        )
        
        st.write("### 🔍 Conferência Visual (Primeiras 30 linhas)")
        st.dataframe(df_final.head(30))

    except Exception as e:
        st.error(f"Erro ao ler o arquivo original: {e}")
        st.info("Dica: Certifique-se de que o xlrd está no requirements.txt.")
