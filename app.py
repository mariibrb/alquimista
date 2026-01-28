import streamlit as st
import pandas as pd
import io
import re
import chardet

def extrair_texto_com_seguranca(file_bytes):
    """Detecta a codificação e limpa o texto do arquivo da Domínio."""
    resultado = chardet.detect(file_bytes)
    encoding = resultado['encoding'] if resultado['encoding'] else 'latin-1'
    
    try:
        texto = file_bytes.decode(encoding, errors='ignore')
    except:
        texto = file_bytes.decode('latin-1', errors='ignore')
    
    # Remove caracteres nulos e lixo eletrônico que causam erro de leitura
    texto_limpo = texto.replace('\x00', '').replace('\x01', '')
    return texto_limpo

def processar_relatorio_ret(file):
    conteudo_bruto = file.getvalue()
    texto_limpo = extrair_texto_com_seguranca(conteudo_bruto)
    
    # Divide em linhas e tenta identificar o separador
    lines = texto_limpo.split('\n')
    if len(lines) < 2: return None
    
    processed_rows = []
    current_percent = ""

    for line in lines:
        if not line.strip(): continue
        
        # Divide por vírgula ou ponto-e-vírgula
        parts = re.split(r'[,;]', line)
        parts = [p.strip().replace('"', '') for p in parts]
        line_str = " ".join(parts)

        # 1. Captura o Percentual
        if "Percentual de recolhimento efetivo:" in line_str:
            match = re.search(r"(\d+[\.,]\d+)", line_str)
            if match:
                current_percent = match.group(1).replace(',', '.')
            processed_rows.append(parts)
            continue

        # 2. Identifica Linhas de Itens (Produtos)
        try:
            # Verifica se a primeira coluna parece uma data/número do Excel
            val_0 = parts[0].replace('.0', '')
            if val_0.isdigit() and int(val_0) > 40000 and len(parts) > 10:
                doc = parts[1].replace('.0', '')
                produto = parts[10]

                # Garante que a linha tenha colunas suficientes (22 colunas)
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

        # 3. Tratamento de Totais
        if "Total:" in line_str or "Total saídas:" in line_str:
            while len(parts) < 22: parts.append("")
            parts[5] = "-"
            parts[7] = current_percent
            processed_rows.append(parts)
        else:
            processed_rows.append(parts)

    return pd.DataFrame(processed_rows)

# --- Interface Streamlit ---
st.set_page_config(page_title="Conversor RET Nascel", layout="wide")

st.title("⚖️ Conversor de Relatório RET (Versão Blindada)")
st.info("Esta versão detecta automaticamente a codificação do arquivo da Domínio para evitar erros de leitura.")

uploaded_file = st.file_uploader("Arraste o arquivo XLS ou CSV da Domínio aqui", type=None)

if uploaded_file:
    try:
        with st.spinner('Limpando e processando dados...'):
            df_result = processar_relatorio_ret(uploaded_file)
            
            if df_result is not None and not df_result.empty:
                # Gerando o EXCEL REAL (.xlsx)
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_result.to_excel(writer, index=False, header=False, sheet_name='Aba Python')
                
                st.success("✅ Conversão concluída!")
                
                st.download_button(
                    label="📥 Baixar Planilha Excel (.xlsx)",
                    data=output.getvalue(),
                    file_name=f"AUDITORIA_{uploaded_file.name.split('.')[0]}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
                st.divider()
                st.write("### 🔍 Prévia Visual (Colunas G e H)")
                st.dataframe(df_result.head(100))
            else:
                st.error("Não consegui extrair dados do arquivo. Ele pode estar vazio ou em um formato binário incompatível.")
    except Exception as e:
        st.error(f"Erro técnico: {e}")

st.sidebar.markdown("---")
st.sidebar.write("📌 **Foco:** Analista Fiscal Mariana")
st.sidebar.write("✅ Geração de ID Único")
st.sidebar.write("✅ Replicação de Percentual")
