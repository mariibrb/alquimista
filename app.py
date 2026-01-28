import streamlit as st
import pandas as pd
import io
import re

def process_text_content(string_data):
    lines = string_data.split('\n')
    processed_lines = []
    current_percent = None
    
    for line in lines:
        line = line.replace('\r', '')
        parts = line.split(',')
        parts = [p.strip() for p in parts]
        
        if "Percentual de recolhimento efetivo:" in line:
            match = re.search(r"(\d+\.?\d*)", line)
            if match:
                current_percent = match.group(1)
            processed_lines.append(line)
            continue

        try:
            # Verifica se é linha de dados (Data do Excel > 40000)
            if parts[0] and float(parts[0]) > 40000 and len(parts) > 10:
                doc = parts[1]
                prod_desc = parts[10]
                parts[6] = f"{doc}-{prod_desc}"
                parts[7] = current_percent if current_percent else ""
                processed_lines.append(",".join(parts))
                continue
        except (ValueError, IndexError):
            pass

        if "Total:" in line or "DÉBITOS PELAS SAÍDAS" in line:
            if len(parts) > 7:
                parts[5] = "-"
                parts[7] = current_percent if current_percent else ""
            processed_lines.append(",".join(parts))
        else:
            processed_lines.append(line)
            
    return "\n".join(processed_lines)

# --- Interface ---
st.set_page_config(page_title="Conversor Universal RET", layout="wide")

st.title("📂 Conversor de Relatório RET (Sem Travas)")
st.info("Pode subir CSV ou Excel. O sistema vai tentar processar de qualquer forma.")

# Removida a trava de 'type' para não dar erro de 'not allowed'
uploaded_file = st.file_uploader("Arraste seu arquivo aqui")

if uploaded_file is not None:
    try:
        # Verifica se o arquivo parece ser Excel binário
        if uploaded_file.name.endswith(('.xlsx', '.xls')):
            # Converte Excel para CSV temporário para usar a mesma lógica
            df_temp = pd.read_excel(uploaded_file)
            csv_data = df_temp.to_csv(index=False)
            result = process_text_content(csv_data)
        else:
            # Tenta ler como texto (CSV)
            try:
                string_data = uploaded_file.getvalue().decode("utf-8")
            except:
                string_data = uploaded_file.getvalue().decode("latin-1")
            result = process_text_content(string_data)
        
        st.success("✅ Arquivo capturado e processado!")
        
        st.download_button(
            label="📥 Baixar Resultado (CSV)",
            data=result,
            file_name=f"PROCESSADO_{uploaded_file.name}.csv",
            mime="text/csv",
        )
        
        st.text_area("Prévia:", value=result[:2000], height=300)

    except Exception as e:
        st.error(f"Erro crítico: {e}")
        st.warning("Se o erro persistir, tente salvar o arquivo como 'CSV Separado por vírgulas' no Excel antes de subir.")
