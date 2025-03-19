import streamlit as st
import os
import shutil
import zipfile
import tempfile
from io import BytesIO

def salvar_arquivo(arquivo, pasta_destino):
    """Salva um arquivo na pasta de destino."""
    os.makedirs(pasta_destino, exist_ok=True)
    caminho_completo = os.path.join(pasta_destino, arquivo.name)
    with open(caminho_completo, "wb") as f:
        f.write(arquivo.getbuffer())

def extrair_zip(arquivo_zip, pasta_destino):
    """Extrai arquivos ZIP para uma pasta específica."""
    os.makedirs(pasta_destino, exist_ok=True)
    with zipfile.ZipFile(arquivo_zip, 'r') as zip_ref:
        zip_ref.extractall(pasta_destino)

def verificar_arquivo(arquivo):
    """Verifica se o arquivo não está corrompido."""
    try:
        if arquivo.name.endswith(".xml") or arquivo.name.endswith(".txt"):
            conteudo = arquivo.read()
            if not conteudo.strip():
                return False
        return True
    except Exception as e:
        return False

def classificar_arquivo(nome_arquivo):
    nome_arquivo_lower = nome_arquivo.lower()

    if "cte" in nome_arquivo_lower and "entrada" in nome_arquivo_lower:
        return "CTE_ENTRADA"
    elif "cte" in nome_arquivo_lower and "saida" in nome_arquivo_lower:
        return "CTE_SAIDA"
    elif "cte" in nome_arquivo_lower and "cancelada" in nome_arquivo_lower:
        return "CTE_CANCELADA"
    elif "nfe" in nome_arquivo_lower and "entrada" in nome_arquivo_lower and "saída" in nome_arquivo_lower:
        return "NFE"
    elif "nfce" in nome_arquivo_lower:
        return "NFCE_SAIDA"
    elif "sped" in nome_arquivo_lower:
        return "SPED"
    elif "tomado" in nome_arquivo_lower and "nfse" in nome_arquivo_lower:
        return "NFS_TOMADOS"
    elif "prestado" in nome_arquivo_lower:
        return "NFS_PRESTADO"
    elif ".xls" in nome_arquivo_lower or ".xlsx" in nome_arquivo_lower:
        return "PLANILHA"
    elif ".txt" in nome_arquivo_lower:
        return "TXT"
    else:
        return "OUTROS"

def processar_arquivos(uploaded_files, nome_empresa):
    """Processa os arquivos, organizando-os por categoria e permitindo download."""
    if not nome_empresa:
        st.error("Por favor, digite o nome da empresa antes de processar os arquivos.")
        return
    
    with tempfile.TemporaryDirectory() as pasta_temp:
        pasta_empresa = os.path.join(pasta_temp, nome_empresa)
        os.makedirs(pasta_empresa, exist_ok=True)
        
        arquivos_corrompidos = []
        
        for arquivo in uploaded_files:
            if not verificar_arquivo(arquivo):
                arquivos_corrompidos.append(arquivo.name)
                continue
            
            if arquivo.name.endswith(".zip"):
                pasta_extracao = os.path.join(pasta_empresa, "TEMP_ZIP")
                os.makedirs(pasta_extracao, exist_ok=True)
                
                with open(os.path.join(pasta_extracao, arquivo.name), "wb") as f:
                    f.write(arquivo.getbuffer())
                
                extrair_zip(os.path.join(pasta_extracao, arquivo.name), pasta_extracao)
                
                for raiz, _, arquivos in os.walk(pasta_extracao):
                    for nome_arquivo in arquivos:
                        caminho_arquivo = os.path.join(raiz, nome_arquivo)
                        categoria = classificar_arquivo(nome_arquivo)
                        pasta_destino = os.path.join(pasta_empresa, categoria)
                        os.makedirs(pasta_destino, exist_ok=True)
                        shutil.move(caminho_arquivo, os.path.join(pasta_destino, nome_arquivo))
                
                shutil.rmtree(pasta_extracao)  # Remove a pasta temporária
            else:
                categoria = classificar_arquivo(arquivo.name)
                pasta_destino = os.path.join(pasta_empresa, categoria)
                salvar_arquivo(arquivo, pasta_destino)
        
        if arquivos_corrompidos:
            st.warning(f"Os seguintes arquivos estão corrompidos e não foram processados: {', '.join(arquivos_corrompidos)}")
        
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
            for raiz, _, arquivos in os.walk(pasta_empresa):
                for arquivo in arquivos:
                    caminho_completo = os.path.join(raiz, arquivo)
                    zipf.write(caminho_completo, os.path.relpath(caminho_completo, pasta_empresa))
        zip_buffer.seek(0)
        
        st.success("Arquivos processados com sucesso! Faça o download abaixo.")
        st.download_button("Baixar Arquivos Processados", zip_buffer, f"{nome_empresa}_arquivos.zip", "application/zip")

# Interface Streamlit
st.title("Organizador de Arquivos Fiscais")
nome_empresa = st.text_input("Nome da Empresa")
uploaded_files = st.file_uploader("Envie seus arquivos XML, TXT, ZIP ou Excel", accept_multiple_files=True)

if st.button("Processar Arquivos"):
    processar_arquivos(uploaded_files, nome_empresa)
