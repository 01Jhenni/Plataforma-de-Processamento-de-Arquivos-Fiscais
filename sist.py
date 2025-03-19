import streamlit as st
import sqlite3
import pandas as pd
import os
import shutil
import zipfile
import tempfile
import xml.etree.ElementTree as ET
import re
from io import BytesIO

conn = sqlite3.connect("importa_register.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS registros (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data TEXT,
                    empresa TEXT,
                    tipo_nota TEXT,
                    erro TEXT,
                    arquivo_erro TEXT,
                    status TEXT DEFAULT 'Pendente')''')
conn.commit()

def extrair_cnpj(texto):
    """ Extrai CNPJ de um texto usando regex. """
    match = re.search(r'\d{14}', texto)
    return match.group(0) if match else None

def identificar_tipo_nota(caminho_arquivo, cnpj_empresa):
    """
    Lê o conteúdo do arquivo e identifica se é Nota de Entrada ou Saída baseado no CNPJ.
    Retorna a categoria correta.
    """
    try:
        if caminho_arquivo.endswith(".xml"):
            tree = ET.parse(caminho_arquivo)
            root = tree.getroot()
            
            cnpj_emitente = None
            cnpj_destinatario = None
            
            for elem in root.iter():
                if "emit" in elem.tag:  # Pega o CNPJ do emitente
                    for subelem in elem.iter():
                        if "CNPJ" in subelem.tag:
                            cnpj_emitente = subelem.text
                if "dest" in elem.tag:  # Pega o CNPJ do destinatário
                    for subelem in elem.iter():
                        if "CNPJ" in subelem.tag:
                            cnpj_destinatario = subelem.text
            
            if cnpj_destinatario == cnpj_empresa:
                return "NFE_ENTRADA"
            elif cnpj_emitente == cnpj_empresa:
                return "NFE_SAIDA"

        elif caminho_arquivo.endswith(".txt"):
            with open(caminho_arquivo, "r", encoding="utf-8") as f:
                conteudo = f.read()
                
                cnpj_emitente = extrair_cnpj(conteudo)
                cnpj_destinatario = extrair_cnpj(conteudo)

                if cnpj_destinatario == cnpj_empresa:
                    return "NFE_ENTRADA"
                elif cnpj_emitente == cnpj_empresa:
                    return "NFE_SAIDA"

    except Exception as e:
        print(f"Erro ao identificar tipo de nota: {e}")
    
    return "OUTROS"

def processar_arquivos(uploaded_files, nome_empresa, cnpj_empresa):
    if not nome_empresa or not cnpj_empresa:
        st.error("Por favor, digite o nome e o CNPJ da empresa antes de processar os arquivos.")
        return None
    
    with tempfile.TemporaryDirectory() as pasta_temp:
        pasta_empresa = os.path.join(pasta_temp, nome_empresa)
        os.makedirs(pasta_empresa, exist_ok=True)
        arquivos_corrompidos = []
        
        for arquivo in uploaded_files:
            if arquivo.name.endswith(".zip"):
                pasta_extracao = os.path.join(pasta_empresa, "TEMP_ZIP")
                os.makedirs(pasta_extracao, exist_ok=True)
                with open(os.path.join(pasta_extracao, arquivo.name), "wb") as f:
                    f.write(arquivo.getbuffer())
                extrair_zip(os.path.join(pasta_extracao, arquivo.name), pasta_extracao)
                for raiz, _, arquivos in os.walk(pasta_extracao):
                    for nome_arquivo in arquivos:
                        caminho_arquivo = os.path.join(raiz, nome_arquivo)
                        categoria = identificar_tipo_nota(caminho_arquivo, cnpj_empresa)
                        pasta_destino = os.path.join(pasta_empresa, categoria)
                        os.makedirs(pasta_destino, exist_ok=True)
                        shutil.move(caminho_arquivo, os.path.join(pasta_destino, nome_arquivo))
                shutil.rmtree(pasta_extracao)
            else:
                categoria = identificar_tipo_nota(arquivo.name, cnpj_empresa)
                pasta_destino = os.path.join(pasta_empresa, categoria)
                salvar_arquivo(arquivo, pasta_destino)
        
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
            for raiz, _, arquivos in os.walk(pasta_empresa):
                for arquivo in arquivos:
                    caminho_completo = os.path.join(raiz, arquivo)
                    zipf.write(caminho_completo, os.path.relpath(caminho_completo, pasta_empresa))
        zip_buffer.seek(0)
        return zip_buffer

st.title("Organizador de Arquivos Fiscais")
nome_empresa = st.text_input("Nome da Empresa")
cnpj_empresa = st.text_input("CNPJ da Empresa")
uploaded_files = st.file_uploader("Envie seus arquivos XML, TXT, ZIP ou Excel", accept_multiple_files=True)

if st.button("Processar Arquivos"):
    zip_buffer = processar_arquivos(uploaded_files, nome_empresa, cnpj_empresa)
    if zip_buffer:
        st.success("Arquivos processados com sucesso! Faça o download abaixo.")
        st.download_button("Baixar Arquivos Processados", zip_buffer, f"{nome_empresa}.zip", "application/zip")
