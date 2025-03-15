import streamlit as st
import os
import shutil
import zipfile
import tempfile
from io import BytesIO
import xml.etree.ElementTree as ET

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
    """Classifica o arquivo baseado no nome e conteúdo XML."""
    
    # Categoria de arquivos
    categorias = {
        "NFE_ENTRADA": ["NFe", "entrada"],
        "NFE_SAIDA": ["NFe", "saida"],
        "CTE_ENTRADA": ["CTe", "entrada"],
        "CTE_SAIDA": ["CTe", "saida"],
        "CTE_CANCELADA": ["CTe", "cancelada"],
        "NFCE_SAIDA": ["NFCe"],
        "SPED": [".txt"],  # SPED é tratado como TXT
        "NFS_TOMADOS": ["tomado"],
        "NFS_PRESTADO": ["prestado"],
        "PLANILHA": [".xls", ".xlsx"],  # Planilha Excel
        "TXT": [".txt"]
    }

    nome_arquivo_lower = nome_arquivo.lower()
    
    for categoria, palavras_chave in categorias.items():
        if any(palavra.lower() in nome_arquivo_lower for palavra in palavras_chave):
            return categoria
    
    # Analisando o conteúdo XML para distinguir NFe entrada e NFe saída
    if nome_arquivo.lower().endswith(".xml"):
        try:
            tree = ET.parse(nome_arquivo)
            root = tree.getroot()
            
            if "NFe" in nome_arquivo:
                if "entrada" in nome_arquivo.lower():
                    return "NFE_ENTRADA"
                if "saida" in nome_arquivo.lower():
                    return "NFE_SAIDA"
                # Checando dentro do XML para determinar o tipo
                for elem in root.iter("infNFe"):
                    tipo = elem.attrib.get("versao")
                    if tipo:
                        if "entrada" in tipo.lower():
                            return "NFE_ENTRADA"
                        elif "saida" in tipo.lower():
                            return "NFE_SAIDA"
            
            # NFCe
            if "NFCE" in nome_arquivo:
                return "NFCE_SAIDA"
            
            # Classificação de CTe
            if "CTe" in nome_arquivo:
                if "entrada" in nome_arquivo.lower():
                    return "CTE_ENTRADA"
                elif "saida" in nome_arquivo.lower():
                    return "CTE_SAIDA"
                elif "cancelada" in nome_arquivo.lower():
                    return "CTE_CANCELADA"
            
        except ET.ParseError:
            pass
        
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
