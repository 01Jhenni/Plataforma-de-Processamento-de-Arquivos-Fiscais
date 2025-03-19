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

# Lista de empresas e CNPJs
empresas_cnpjs = {
  "2B COMBUSTIVEL LTDA": "40.994.024/0001-28",
  "A REDE GESTAO PATRIMONIAL LTDA": "10.309.735/0001-55",
  "A.M CHEQUER IMOVEIS LTDA": "49.247.110/0001-41",
  "A.R. PARTICIPACOES LTDA": "27.291.315/0001-91",
  "ABEL CONSTRUTORA LTDA": "08.488.463/0001-56",
  "ABEL SEMINOVOS LTDA": "45.320.266/0001-50",
  "ACOLOG LOGISTICA LTDA": "31.781.148/0001-34",
  "ACOS SERVICOS DE PROMOCAO LTDA": "31.859.834/0001-80",
  "ACR GESTAO PATRIMONIAL LTDA": "44.403.647/0001-30",
  "ADCAR SERVICO DE ESCRITORIO E APOIO ADMINISTRATIVO LTDA": "43.149.261/0001-80",
  "ADR MOBILIDADE E SERVICOS LTDA": "57.108.289/0001-84",
  "ADS COMERCIO E IMPORTACAO E EXPORTACAO EIRELI": "19.318.337/0001-70",
  "AESA PARTICIPAÇÕES LTDA": "12.397.940/0001-45",
  "AGM ESQUADRIAS LTDA": "56.052.524/0001-80",
  "AGP03 EMPREENDIMENTOS IMOBILIARIOS SPE LTDA": "50.446.827/0001-00",
  "AGP03 EMPREENDIMENTOS IMOBILIARIOS SPE LTDA FILIAL 02-82": "50.446.827/0002-82",
  "AGP03 EMPREENDIMENTOS IMOBILIARIOS SPE LTDA SCP RESIDENCIAL CAPARAO": "54.269.862/0001-43",
  "AGP05 ARGON EMPREENDIMENTOS IMOBILIARIOS SPE LTDA": "54.879.613/0001-70",
  "AGROPECUARIA BONANZA LTDA": "29.295.126/0001-12",
  "AGT01 MORADA NOVA DE MINAS SPE LTDA": "51.006.691/0001-71",
  "AGT01 MORADA NOVA DE MINAS SPE LTDA FILIAL 02-52": "51.006.691/0002-52",
  "AGUIA 8 COMERCIO DE COMBUSTIVEIS LTDA": "40.059.663/0001-04",
  "AGUIA IV COMERCIO DE COMBUSTIVEIS LTDA": "07.946.419/0001-80",
  "AGUIA IX COMERCIO DE COMBUSTIVEIS LTDA": "40.373.016/0001-64",
  "AGUIA V COMERCIO DE COMBUSTIVEIS LTDA": "39.609.220/0001-52",
  "ALLOTECH CONSULTORIA EM PRODUCAO INDUSTRIAL LTDA": "07.777.530/0001-90",
  "ALVES E SANTOS PARTICIPACOES LTDA.": "21.284.331/0001-70",
  "AMH COMERCIO E SERVICOS LTDA": "55.502.351/0001-92",
  "AML HOLDING S/A": "17.243.217/0001-25",
  "AMMC PARTICIPACOES LTDA": "48.530.421/0001-50",
  "AMPLUS PARTICIPACOES SA": "21.340.017/0001-68",
  "AMX GESTÃO PATRIMONIAL LTDA": "10.566.236/0001-43",
  "ANF EMPREENDIMENTOS E PARTICIPACOES LTDA": "07.015.759/0001-97",
  "ANITA CHEQUER PARTICIPACOES LTDA": "42.868.214/0001-24",
  "ANITA CHEQUER PATRIMONIAL LTDA": "47.131.991/0001-05",
  "APL ADMINISTRACAO E PARTICIPACOES LTDA": "24.346.183/0001-60",
  "APMG PARTICIPACOES S/A": "05.498.286/0001-09",
  "ARCI PARTICIPACOES LTDA": "39.329.294/0001-35",
  "ARCI PATRIMONIAL LTDA": "39.781.850/0001-00",
  "ARGON ENGENHARIA LTDA": "30.131.491/0001-70",
  "ARNDT PATRIMONIAL LTDA": "40.138.140/0001-45",
  "ARNDT REFORMAS E MANUTENCOES LTDA": "40.138.139/0001-10",
  "ARNDT, TRAVASSOS E MORRISON SPE LTDA": "50.745.643/0001-32",
  "ARTMIX HOLDING LTDA": "03.328.383/0001-10",
  "AUMAR PRESTACAO DE SERVICOS ADMINISTRATIVOS LTDA": "08.916.536/0001-63",
  "AUTO POSTO ALELUIA LTDA": "03.733.648/0001-65",
  "AUTO POSTO ALELUIA LTDA FILIAL 02-46": "03.733.648/0002-46",
  "AUTO POSTO CENTENARIO LTDA": "35.523.371/0001-32",
  "AUTO POSTO DAS LAJES LTDA": "03.543.109/0001-63",
  "AUTO POSTO DOM BOSCO LTDA": "00.982.905/0001-04",
  "AUTO POSTO MAQUINE LTDA": "42.866.251/0001-01",
  "AUTO POSTO MARIO CAMPOS COMERCIO DE COMBUSTIVEIS LTDA": "42.509.693/0001-92",
  "AUTO POSTO PORTAL DO NORTE LTDA": "12.383.729/0001-73",
  "AUTO POSTO VERONA LTDA": "00.911.111/0001-50",
  "AUTOREDE LOCADORA DE VEICULOS LTDA": "17.626.638/0001-35",
  "AUTOREDE PARTICIPACOES LTDA": "16.928.898/0001-00",
  "AXJ PARTICIPACOES EIRELI": "11.438.894/0001-12",

}

def extrair_cnpj(texto):
    """ Extrai CNPJ de um texto usando regex. """
    match = re.search(r'\d{14}', texto)
    return match.group(0) if match else None

def identificar_tipo_nota(caminho_arquivo, cnpj_empresa):
    """
    Identifica o tipo do documento com base na estrutura do XML/TXT e no CNPJ.
    """
    try:
        if caminho_arquivo.endswith(".xml"):
            tree = ET.parse(caminho_arquivo)
            root = tree.getroot()
            cnpj_emitente = None
            cnpj_destinatario = None
            tipo_doc = "OUTROS"
            
            for elem in root.iter():
                if "emit" in elem.tag:
                    for subelem in elem.iter():
                        if "CNPJ" in subelem.tag:
                            cnpj_emitente = subelem.text
                if "dest" in elem.tag:
                    for subelem in elem.iter():
                        if "CNPJ" in subelem.tag:
                            cnpj_destinatario = subelem.text
                if "mod" in elem.tag:  # Modelo da nota
                    if elem.text == "55":
                        tipo_doc = "NFE"
                    elif elem.text == "65":
                        tipo_doc = "NFCE"
                    elif elem.text == "57":
                        tipo_doc = "CTE"

            if tipo_doc == "NFE":
                return "NFE/ENTRADA" if cnpj_destinatario == cnpj_empresa else "NFE/SAIDA"
            elif tipo_doc == "NFCE":
                return "NFCE/SAIDA"
            elif tipo_doc == "CTE":
                if "canc" in root.tag:
                    return "CTE/CANCELADA"
                return "CTE/ENTRADA" if cnpj_destinatario == cnpj_empresa else "CTE/SAIDA"

        elif caminho_arquivo.endswith(".txt"):
            with open(caminho_arquivo, "r", encoding="utf-8") as f:
                conteudo = f.read()
                
                cnpj_emitente = extrair_cnpj(conteudo)
                cnpj_destinatario = extrair_cnpj(conteudo)
                
                if "SPED" in conteudo:
                    return "SPED"
                elif "NFS TOMADO" in conteudo:
                    return "NFS/TOMADO"
                elif "NFS PRESTADO" in conteudo:
                    return "NFS/PRESTADO"
        
        elif caminho_arquivo.endswith(".xls") or caminho_arquivo.endswith(".xlsx"):
            return "PLANILHA"

    except Exception as e:
        print(f"Erro ao identificar tipo de nota: {e}")
    
    return "OUTROS"

def salvar_arquivo(arquivo, pasta_destino):
    os.makedirs(pasta_destino, exist_ok=True)
    caminho_completo = os.path.join(pasta_destino, arquivo.name)
    with open(caminho_completo, "wb") as f:
        f.write(arquivo.getbuffer())

def processar_arquivos(uploaded_files, nome_empresa, cnpj_empresa):
    if not nome_empresa or not cnpj_empresa:
        st.error("Por favor, selecione a empresa antes de processar os arquivos.")
        return None
    
    with tempfile.TemporaryDirectory() as pasta_temp:
        pasta_empresa = os.path.join(pasta_temp, nome_empresa)
        os.makedirs(pasta_empresa, exist_ok=True)
        arquivos_corrompidos = []
        
        for arquivo in uploaded_files:
            caminho_arquivo = os.path.join(pasta_empresa, arquivo.name)
            salvar_arquivo(arquivo, pasta_empresa)
            categoria = identificar_tipo_nota(caminho_arquivo, cnpj_empresa)
            pasta_tipo, pasta_subtipo = categoria.split("/") if "/" in categoria else (categoria, "OUTROS")
            pasta_destino = os.path.join(pasta_empresa, pasta_tipo, pasta_subtipo)
            os.makedirs(pasta_destino, exist_ok=True)
            shutil.move(caminho_arquivo, os.path.join(pasta_destino, arquivo.name))
        
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
            for raiz, _, arquivos in os.walk(pasta_empresa):
                for arquivo in arquivos:
                    caminho_completo = os.path.join(raiz, arquivo)
                    zipf.write(caminho_completo, os.path.relpath(caminho_completo, pasta_empresa))
        zip_buffer.seek(0)
        return zip_buffer

st.title("Organizador de Arquivos Fiscais")
nome_empresa = st.selectbox("Nome da Empresa", list(empresas_cnpjs.keys()))
cnpj_empresa = empresas_cnpjs[nome_empresa]
uploaded_files = st.file_uploader("Envie seus arquivos XML, TXT, ZIP ou Excel", accept_multiple_files=True)

if st.button("Processar Arquivos"):
    zip_buffer = processar_arquivos(uploaded_files, nome_empresa, cnpj_empresa)
    if zip_buffer:
        st.success("Arquivos processados com sucesso! Faça o download abaixo.")
        st.download_button("Baixar Arquivos Processados", zip_buffer, f"{nome_empresa}.zip", "application/zip")
