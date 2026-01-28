import streamlit as st
import pandas as pd
import io
import re

def aplicar_regras_mariana(df):
    """Aplica a lógica de IDs e Percentuais no DataFrame extraído"""
    processed_rows = []
    current_percent = None
    
    # Converte para lista de listas para manter a fidelidade do processamento
    data = df.values.tolist()
    
    for row in data:
        # Limpa cada célula e converte para string
        parts = [str(item).strip() if pd.notna(item) else "" for item in row]
        line_content = " ".join(parts)
        
        # 1. Identifica Percentual
        if "Percentual de recolhimento efetivo:" in line_content:
            match = re.search(r"(\d+\.?\d*)", line_content)
            if match:
                current_percent = match.group(1)
            processed_rows.append(parts)
            continue

        # 2. Processa Itens (Hierarquia Fiscal)
        try:
            # Verifica se a primeira coluna é uma data/número da Domínio
            val_0 = parts[0].split('.')[0] # Pega só o inteiro antes do ponto
            if val_0.isdigit() and int(val_0) > 40000 and len(parts) > 10:
                doc = parts[1].split('.')[0]
                prod_desc = parts[10]
                
                # Criando ID: Doc-Produto (Índice 6)
                parts[6] = f"{doc}-{prod_desc}"
                # Inserindo Percentual (Índice 7)
                parts[7] = current_percent if current_percent else ""
                
                processed_rows.append(parts)
                continue
        except (ValueError, IndexError):
            pass

        # 3. Totais e Cabeçalhos
        if "Total:" in line_content or "DÉBITOS PELAS SAÍDAS" in line_content:
            if len(parts) > 7:
                parts[5] = "-"
                parts[7] = current_percent if current_percent else ""
            processed_rows.append(parts)
        else:
            processed_rows.append(parts)
            
    return pd.DataFrame(processed_rows)

# --- Interface Streamlit ---
st.set_page_config(page_title="Conversor RET Domínio", layout="wide")
st.title("🚀 Conversor RET Domínio (Versão Suprema)")

file = st.file_uploader("Suba o arquivo original da Domínio", type=None)

if file:
    df_raw = None
    bytes_data = file.getvalue()
    
    # TESTE 1: Tenta como HTML/XML (O "falso" XLS da Domínio)
    try:
        df_raw = pd.read_html(io.BytesIO(bytes_data))[0]
    except:
        # TESTE 2: Tenta como Excel Moderno
        try:
            df_raw = pd.read_excel(io.BytesIO(bytes_data), engine='openpyxl')
        except:
            # TESTE 3: Tenta como Excel Antigo (com engine manual)
            try:
                df_raw = pd.read_excel(io.BytesIO(bytes_data), engine='xlrd')
            except:
                # TESTE 4: Tenta como CSV Puro
                try:
                    df_raw = pd.read_csv(io.BytesIO(bytes_data), sep=None, engine='python')
                except Exception as e:
                    st.error(f"Não consegui decifrar esse arquivo. Erro: {e}")

    if df_raw is not None:
        try:
            # Aplica as regras de negócio
            df_final = aplicar_regras_mariana(df_raw)
            
            st.success("✅ Arquivo decifrado e processado com as regras fiscais!")
            
            # Botão de Download
            csv_final = df_final.to_csv(index=False, header=False)
            st.download_button(
                label="📥 Baixar CSV para Python",
                data=csv_final,
                file_name=f"PYTHON_{file.name}.csv",
                mime="text/csv"
            )
            
            st.write("### 🔍 Prévia dos Dados:")
            st.dataframe(df_final.head(30))
            
        except Exception as e:
            st.error(f"Erro na aplicação das regras: {e}")
