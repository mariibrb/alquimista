import streamlit as st
import pandas as pd
import io
import re

def process_dominio_logic(df):
    """Aplica as regras da Mariana em um DataFrame já extraído do Excel"""
    processed_rows = []
    current_percent = None
    
    # Transformamos o DataFrame em lista de listas para processar linha a linha
    data = df.values.tolist()
    
    for row in data:
        # Converte tudo para string e limpa espaços
        parts = [str(item).strip() if pd.notna(item) else "" for item in row]
        line_full = " ".join(parts)
        
        # 1. Identifica o Percentual
        if "Percentual de recolhimento efetivo:" in line_full:
            match = re.search(r"(\d+\.?\d*)", line_full)
            if match:
                current_percent = match.group(1)
            processed_rows.append(parts)
            continue

        # 2. Processa linhas de Produtos (Hierarquia Fiscal)
        try:
            # Verifica se a primeira coluna parece uma data/número da Domínio
            # O Excel converte datas em números (ex: 46024.0)
            val_0 = parts[0].replace('.0', '')
            if val_0.isdigit() and float(val_0) > 40000 and len(parts) > 10:
                doc = parts[1].replace('.0', '') # Remove o .0 do número da nota
                prod_desc = parts[10]
                
                # Criando o ID: Documento-Produto (Coluna G / Índice 6)
                parts[6] = f"{doc}-{prod_desc}"
                # Inserindo o Percentual (Coluna H / Índice 7)
                parts[7] = current_percent if current_percent else ""
                
                processed_rows.append(parts)
                continue
        except (ValueError, IndexError):
            pass

        # 3. Totais e Outras Linhas
        if "Total:" in line_full or "DÉBITOS PELAS SAÍDAS" in line_full:
            if len(parts) > 7:
                parts[5] = "-"
                parts[7] = current_percent if current_percent else ""
            processed_rows.append(parts)
        else:
            processed_rows.append(parts)
            
    # Converte de volta para CSV
    output_df = pd.DataFrame(processed_rows)
    return output_df.to_csv(index=False, header=False)

# --- Interface ---
st.set_page_config(page_title="Conversor RET Domínio", layout="wide")
st.title("📊 Conversor RET - Formato Binário (XLS)")

uploaded_file = st.file_uploader("Suba o arquivo .xls gerado pela Domínio", type=["xls"])

if uploaded_file is not None:
    try:
        # Lê o arquivo binário direto usando xlrd (específico para esse erro que deu)
        # engine='xlrd' é o segredo para arquivos que começam com ÐÏà¡±
        df_raw = pd.read_excel(uploaded_file, engine='xlrd', header=None)
        
        # Processa com a lógica da Mariana
        result_csv = process_dominio_logic(df_raw)
        
        st.success("✅ Arquivo binário convertido com sucesso!")
        
        st.download_button(
            label="📥 Baixar CSV para Python",
            data=result_csv,
            file_name=f"CONVERTIDO_{uploaded_file.name.replace('.xls', '.csv')}",
            mime="text/csv"
        )
        
        st.write("### 🔍 Prévia dos dados convertidos")
        st.dataframe(df_raw.head(20)) # Mostra como o Python está "enxergando" o Excel

    except Exception as e:
        st.error(f"Erro ao ler o Excel binário: {e}")
        st.info("O arquivo parece ser um XLS antigo. Certifique-se de que o 'xlrd' está no requirements.txt.")
