import os

PALAVRAS_RESERVADAS = {'variables', 'const', 'class', 'methods', 'main', 
                       'return', 'if', 'else', 'for', 'read', 'print', 
                       'void', 'int', 'float', 'boolean', 'string', 
                       'true', 'false'}

OPERADORES = {'!', '+', '-', '*', '/', '++', '--', '=', '!=', '==', '<', '<=', '>', '>=', '&&', '||'}

DELIMITADORES = {';', ',', '.', '(', ')', '[', ']', '{', '}', '->'}

LETRA = [  
    'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',  
    'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z'  
]  

DIGITO = [  
    '0', '1', '2', '3', '4', '5', '6', '7', '8', '9'  
]  

SIMBOLO = [  
    ' ', '!', '#', '$', '%', '&', "'", '(', ')', '*', '+', ',', '-', '.', '/', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', ':', ';',  
    '<', '=', '>', '?', '@', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',  
    '[', '\\', ']', '^', '_', '`', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',  
    '{', '|', '}', '~'  
]  

def reconhecer_token(palavra):
    if palavra in PALAVRAS_RESERVADAS:
        return "PRE"
    elif palavra in OPERADORES:
        if palavra == '+' or palavra == '-' or palavra == '*' or palavra == '/' or palavra == '++' or palavra == '--':
            return 'ART'
        elif palavra == '!' or palavra == '&&' or palavra == '||':
            return 'LOG'
        else:
            return "REL"
    elif palavra in DELIMITADORES:
        return "DEL"
    elif palavra.isidentifier():
        if palavra[0] != "_":
            return "IDE"
        else:
            return "TMF"
    else:
        return "TMF"

def identificar_tokens(texto):
    tokens = []
    tokens_mal_formados = []
    estado = "q0"
    palavra = ""
    string_aberta = None
    erro_string = False
    

    for linha_numero, linha in enumerate(texto.split("\n"), start=1):
        i = 0
        while i < len(linha):
            char = linha[i]

            if estado == "q0":
                if char in LETRA:
                    estado = "q1"
                    palavra += char
                elif char in "-":
                    palavra += char
                    if i + 1 < len(linha) and (char + linha[i + 1]) in OPERADORES:
                        palavra += linha[i + 1]
                        if reconhecer_token(palavra) == 'TMF':
                            tokens_mal_formados.append(f"{linha_numero} {reconhecer_token(palavra)} {palavra}")
                        else:
                            tokens.append(f"{linha_numero} {reconhecer_token(palavra)} {palavra}")
                        palavra = ""
                        i += 1
                    else:
                        if len(linha) == i + 1 or (linha[i-1] != " " and i != 0):
                            tokens.append(f"{linha_numero} ART {palavra}")
                            palavra = ""
                        else:
                            estado = "verifica_proximo"
                elif char.isdigit():
                    palavra += char
                
                    if palavra[0] == ".":
                        if reconhecer_token(palavra) == 'TMF':
                            tokens_mal_formados.append(f"{linha_numero} {reconhecer_token(palavra)} {palavra}")
                        else:
                            tokens.append(f"{linha_numero} {reconhecer_token(palavra)} {palavra}")
                        palavra = ""
                    else:
                        if i + 1 == len(linha):
                            tokens.append(f"{linha_numero} NRO {palavra}")
                            palavra = ""
                        else:
                            estado = "q2"
                elif char == "/" and (linha[i+1] == "/" or linha[i+1] == "*"):
                    if linha[i + 1] == "/":
                        break
                    if linha[i + 1] == "*":
                        palavra += char+linha[i+1]
                        estado = "q4"
                        linha_inicio_comentario = linha_numero
                        i += 1
                elif char in OPERADORES or i + 1 < len(linha) and (char + linha[i + 1]) in OPERADORES:  
                    palavra = char
                    if i + 1 < len(linha):
                        possivel_composto = char + linha[i + 1]
                        if possivel_composto in OPERADORES or possivel_composto in DELIMITADORES:
                            palavra = possivel_composto
                            i += 1
                    if palavra in OPERADORES or palavra in DELIMITADORES:
                        if reconhecer_token(palavra) == 'TMF':
                            tokens_mal_formados.append(f"{linha_numero} {reconhecer_token(palavra)} {palavra}")
                        else:
                            tokens.append(f"{linha_numero} {reconhecer_token(palavra)} {palavra}")
                    else:
                        tokens_mal_formados.append(f"{linha_numero} TMF {palavra}")
                    palavra = ""
                elif char in DELIMITADORES:  
                    palavra = char
                    tokens.append(f"{linha_numero} DEL {palavra}")
                    palavra = ""
                elif char in {'"', "'"}:
                    estado = "q3"
                    string_aberta = char
                    palavra += char
                elif char.isspace():
                    pass 
                else:
                    tokens_mal_formados.append(f"{linha_numero} TMF {char}")

            elif estado == "q1":
                if char in LETRA or char in DIGITO or char == "_":
                    palavra += char
                else:
                    if reconhecer_token(palavra) == 'TMF':    
                        tokens_mal_formados.append(f"{linha_numero} {reconhecer_token(palavra)} {palavra}")
                    else:
                        tokens.append(f"{linha_numero} {reconhecer_token(palavra)} {palavra}")
                    palavra = ""
                    estado = "q0"
                    continue
            
            elif estado == "verifica_proximo":
                if char.isspace():
                    if len(linha) == i + 1:
                        tokens.append(f"{linha_numero} ART {palavra}")
                        palavra = ""
                        estado = "q0"
                    else:
                        pass  # Ignora espaços após um sinal
                elif char.isdigit():
                    palavra += char
                    estado = "q2"
                    if len(linha) == i + 1:
                        tokens.append(f"{linha_numero} NRO {palavra}")
                        palavra = ""
                        estado = "q0"
                else:
                    tokens.append(f"{linha_numero} ART {palavra}")
                    palavra = ""
                    estado = "q0"
                    continue
            elif estado == "q2":
                if char.isdigit():
                    palavra += char
                    if i + 1 == len(linha):
                        tokens.append(f"{linha_numero} NRO {palavra}")
                        palavra = ""
                        estado = "q0"
                elif char == ".":
                    if "." in palavra:
                        if palavra.endswith("."):
                            tokens_mal_formados.append(f"{linha_numero} NMF {palavra}")
                            palavra = ""
                            estado = "q0"
                        else:
                            tokens.append(f"{linha_numero} NRO {palavra}")
                            palavra = ""
                            estado = "q0"
                        continue
                    else:
                        palavra += char  

                else:
                    if palavra.endswith(".") or palavra.startswith("."):
                        tokens_mal_formados.append(f"{linha_numero} NMF {palavra}")
                    else:
                        tokens.append(f"{linha_numero} NRO {palavra}")
                    palavra = ""
                    estado = "q0"
                    continue

            elif estado == "q3":
                palavra += char
                if (char not in LETRA and char not in DIGITO and char not in SIMBOLO and palavra != '""' and char != '"'):
                    erro_string = True
                elif char == string_aberta:
                    if erro_string == True:
                        tokens_mal_formados.append(f"{linha_numero} CadMF {palavra}")
                        erro_string = False
                    else:
                        tokens.append(f"{linha_numero} CAC {palavra}")
                    palavra = ""
                    estado = "q0"
                    string_aberta = None                 
            elif estado == "q4":
                palavra += char
                if char == "*" and i + 1 < len(linha) and linha[i + 1] == "/":
                    estado = "q0"
                    palavra = ""
                    i += 1
                
            i += 1

        if estado == "q1":
            if reconhecer_token(palavra) == 'TMF':
                tokens_mal_formados.append(f"{linha_numero} {reconhecer_token(palavra)} {palavra}")
            else:
                tokens.append(f"{linha_numero} {reconhecer_token(palavra)} {palavra}")
            palavra = ""
            estado = "q0"

        if estado == "q3":
            tokens_mal_formados.append(f"{linha_numero} CadMF {palavra}")
            palavra = ""
            estado = "q0"
            
    if estado == "q4":
        tokens_mal_formados.append(f"{linha_inicio_comentario} CoMF {palavra}")
            
    return tokens, tokens_mal_formados

def processar_arquivos():
    raiz_projeto = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pasta_entrada = os.path.join(raiz_projeto, "files")

    resultados = {}
    for arquivo in os.listdir(pasta_entrada):
        if arquivo.endswith(".txt") and not arquivo.endswith("-saida.txt"):
            caminho_entrada = os.path.join(pasta_entrada, arquivo)

            with open(caminho_entrada, "r", encoding="utf-8") as f:
                conteudo = f.read()

            tokens, tokens_mal_formados = identificar_tokens(conteudo)

            # Verificar se há tokens mal formados
            if tokens_mal_formados:
                return f"Erro: Tokens mal formados encontrados no arquivo {arquivo}"
            
            # Modificar a estrutura dos tokens para a lista [linha, tipo, valor]
            tokens_formatados = []
            for token in tokens:
                partes = token.split(" ")
                if len(partes) == 3:
                    linha_numero, tipo_token, valor_token = partes
                    tokens_formatados.append([int(linha_numero), tipo_token, valor_token])

            # Se não houver erros, salvar os tokens válidos no dicionário
            resultados[arquivo] = tokens_formatados

    return resultados  # Retorna o dicionário com os tokens válidos

if __name__ == "__main__":
    processar_arquivos()