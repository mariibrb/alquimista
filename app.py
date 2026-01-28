import pdfplumber
import pandas as pd

def converter_pdf_para_excel(pdf_path, excel_path):
    all_data = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            # Extrai a tabela da página atual
            table = page.extract_table()
            if table:
                # Transforma em DataFrame mantendo os dados brutos
                df_page = pd.DataFrame(table[1:], columns=table[0])
                all_data.append(df_page)
    
    # Consolida todas as páginas
    if all_data:
        df_final = pd.concat(all_data, ignore_index=True)
        
        # Garante que números não sejam convertidos para float americano (ponto) 
        # para manter a vírgula original do PDF na visualização do Excel
        df_final = df_final.astype(str)
        
        # Exporta para Excel
        df_final.to_excel(excel_path, index=False)
        print(f"Conversão concluída: {excel_path}")
    else:
        print("Nenhuma tabela encontrada no PDF.")

# Execução
pdf_input = "Crédito Presumido Regime Especial de Tributação - RET.pdf"
excel_output = "Relatorio_Convertido.xlsx"
converter_pdf_para_excel(pdf_input, excel_output)
