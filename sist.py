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
            # Caminho completo para o arquivo
            caminho_completo_arquivo = os.path.join(os.getcwd(), nome_arquivo)  # Adiciona o caminho completo

            tree = ET.parse(caminho_completo_arquivo)
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
