import streamlit as st
import pandas as pd
import io
import re

def process_dominio_ret(file):
    # Lendo o conteúdo do arquivo
    # Usamos o 'bytes.decode' com 'replace' para evitar erros de caracteres especiais (comuns em arquivos da Domínio)
    try:
        string_data = file.getvalue().decode("utf-8")
    except UnicodeDecodeError:
        string_data = file.getvalue().decode("latin-1")
    
    lines = string_data.split('\n')
    
    processed_lines = []
    current_percent = None
    
    for line in lines:
        # Remove quebras de linha residuais
        line = line.replace('\r', '')
        parts = line.split(',')
        
        # Limpeza básica de espaços em cada campo
        parts = [p.strip() for p in parts]
        
        # 1. Identifica e captura o Percentual de recolhimento atual
        if "Percentual de recolhimento efetivo:" in line:
            match = re.search(r"(\d+\.?\d*)", line)
            if match:
                current_percent = match.group(1)
            processed_lines.append(line)
            continue

        # 2. Processa linhas de dados (Produtos)
        # Verifica se a primeira coluna é uma data/número e se a linha tem colunas suficientes
        try:
            if parts[0] and float(parts[0]) > 40000 and len(parts) > 10:
                doc = parts[1]
                prod_desc = parts[10]
                
                # Criando o ID: Documento-Produto (Coluna G / Índice 6)
                parts[6] = f"{doc}-{prod_desc}"
                
                # Inserindo o Percentual na Coluna H / Índice 7
                parts[7] = current_percent if current_percent else ""
                
                processed_lines.append(",".join(parts))
                continue
        except (ValueError, IndexError):
            pass

        # 3. Tratamento para linhas de Total ou Cabeçalhos de seção
        if "Total:" in line or "DÉBITOS PELAS SAÍDAS" in line:
            if len(parts) > 7:
                parts[5] = "-"
                parts[7] = current_percent if current_percent else ""
            processed_lines.append(",".join(parts))
        else:
            # Mantém as outras linhas (Cabeçalhos do sistema, Resumos de Apuração)
            processed_lines.append(line)

    return "\n".join(processed_lines)

# --- Interface Streamlit ---
st.set_page_config(page_title="Conversor RET Domínio", layout="wide", page_icon="📊")

st.title("📂 Conversor Relatório RET - Domínio Sistemas")
st.markdown("""
### Instruções:
1. Extraia o relatório **Crédito Presumido (3 - Apuração 1)** do sistema Domínio em formato **CSV**.
2. Arraste o arquivo abaixo para formatar as chaves de busca e percentuais.
""")

# Ajuste aqui: Aceitando CSV mesmo que o Windows/Excel o identifique como Excel
uploaded_file = st.file_uploader(
    "Selecione o arquivo CSV extraído", 
    type=["csv"], 
    accept_multiple_files=False
)

if uploaded_file is not None:
    try:
        with st.spinner('Processando regras fiscais...'):
            result_csv = process_dominio_ret(uploaded_file)
        
        st.success("✅ Arquivo processado com sucesso!")
        
        # Colunas para os botões e informações
        col1, col2 = st.columns(2)
        
        with col1:
            st.download_button(
                label="📥 Baixar Arquivo para Python (CSV)",
                data=result_csv,
                file_name=f"PYTHON_{uploaded_file.name}",
                mime="text/csv",
            )
            
        with col2:
            if st.button("Limpar cache"):
                st.rerun()

        st.divider()
        
        # Visualização Prévia para conferência da Mariana
        st.subheader("🔍 Prévia dos dados (Visualização em Bloco)")
        st.text_area(
            label="As primeiras linhas processadas aparecerão aqui:",
            value=result_csv[:3000],
            height=400
        )

    except Exception as e:
        st.error(f"Ocorreu um erro no processamento: {e}")
        st.info("Verifique se o arquivo enviado é realmente o CSV separado por vírgulas.")

st.sidebar.markdown("---")
st.sidebar.write("📌 **Status do Projeto:**")
st.sidebar.info("Conversor configurado para respeitar a hierarquia fiscal da Domínio e gerar IDs únicos de Documento + Produto.")
