from lexico import processar_arquivos
from sintatico import main_sintatico
import os
import json

tabela_de_simbolos = {}
pilha_escopos = []
pilha = []
tabela_de_simbolos_2 = {}
lista_obj = []

def verificar_duplicidade(escopo, categoria, nome_ident, linha, nome_metodo=None):
    """
    Verifica se o nome_ident já existe na categoria (variables, const, parametros ou methods) do escopo.
    Para 'parametros', exige também o nome do método.

    Parâmetros:
    - escopo: escopo atual (ex: 'global', 'Toin')
    - categoria: 'variables', 'const', 'parametros' ou 'methods'
    - nome_ident: nome do identificador (str)
    - linha: número da linha
    - nome_metodo: nome do método (obrigatório se categoria == 'parametros')

    Retorna:
    - True se houver duplicidade
    - False caso contrário
    """
    global tabela_de_simbolos, lista_erros

    if escopo not in tabela_de_simbolos:
        return False

    if categoria == "parametros":
        if not nome_metodo:
            raise ValueError("nome_metodo é obrigatório para verificação de parâmetros.")

        funcoes = tabela_de_simbolos.get(escopo, {}).get('methods', {}).get('funcoes', [])
        for metodo_dict in funcoes:
            if nome_metodo in metodo_dict:
                parametros = metodo_dict[nome_metodo].get('parametros', [])
                for tipo_param, nome_param in parametros:
                    if nome_param == nome_ident:
                        lista_erros.append(
                            f"Erro: parâmetro '{nome_ident}' duplicado no método '{nome_metodo}' do escopo '{escopo}' (linha {linha})"
                        )
                        return True
        return False

    elif categoria == "methods":
        funcoes = tabela_de_simbolos.get(escopo, {}).get('methods', {}).get('funcoes', [])
        for metodo_dict in funcoes:
            if nome_ident in metodo_dict:
                lista_erros.append(
                    f"Erro: método '{nome_ident}' já declarado no escopo '{escopo}' (linha {linha})"
                )
                return True
        return False
    # Verificação de variables dentro de métodos (quando pilha está ativa)
    elif pilha:
        # Estamos dentro de um método: verificar dentro das 'variables' internas do método
        if not nome_metodo:
            raise ValueError("nome_metodo é obrigatório para verificação de variables internas ao método.")

        funcoes = tabela_de_simbolos[escopo].get('methods', {}).get('funcoes', [])
        for metodo_dict in funcoes:
            if nome_metodo in metodo_dict:
                variaveis = metodo_dict[nome_metodo].get('variables', [])
                for tipo_var, nome_var in variaveis:
                    if nome_var == nome_ident:
                        lista_erros.append(
                            f"Erro: variável '{nome_ident}' duplicada dentro do método '{nome_metodo}' no escopo '{escopo}' (linha {linha})"
                        )
                        return True
        return False

    # Verificação no nível da classe (const ou variables no escopo atual)
    else:
        # Verificação entre 'variables' e 'const' no mesmo escopo (ambos não podem repetir nomes)
        identificadores_vars = tabela_de_simbolos[escopo].get("variables", {}).get("identificadores", [])
        identificadores_const = tabela_de_simbolos[escopo].get("const", {}).get("identificadores", [])

        # Junta os dois dicionários de identificadores
        identificadores = identificadores_vars + identificadores_const

        for ident in identificadores:
            if nome_ident in ident:
                lista_erros.append(
                    f"Erro: identificador '{nome_ident}' duplicado na categoria '{categoria}' do escopo '{escopo}' (linha {linha})"
                )
                return True

        return False
    
def existe_identificador(nome_ident, linha, escopo):
    """
    Verifica se um identificador existe no contexto atual, dado o escopo e a pilha de execução.

    - Procura em variáveis locais do método (se dentro de método)
    - Parâmetros do método
    - Variáveis e constantes no escopo atual
    - Variáveis e constantes no escopo global (se necessário)

    Parâmetros:
    - nome_ident: nome do identificador a buscar
    - linha: linha de uso (para mensagem de erro)
    - escopo: escopo atual (ex: 'global', 'orangotango', etc.)

    Retorna:
    - True se encontrado
    - False se não encontrado (e registra erro)
    """  
    # 1. Se estiver dentro de um método, verificar variáveis e parâmetros do método atual
    if pilha:
        nome_metodo = pilha[-1]
        funcoes = tabela_de_simbolos.get(escopo, {}).get("methods", {}).get("funcoes", [])
        for metodo_dict in funcoes:
            if nome_metodo in metodo_dict:
                metodo_info = metodo_dict[nome_metodo]

                # Variáveis locais do método
                for tipo, nome in metodo_info.get("variables", []):
                    if nome == nome_ident:
                        return True

                # Parâmetros do método
                for tipo, nome in metodo_info.get("parametros", []):
                    if nome == nome_ident:
                        return True

    # 2. Procurar em variables e const do escopo atual
    for cat in ["variables", "const"]:
        for ident in tabela_de_simbolos.get(escopo, {}).get(cat, {}).get("identificadores", []):
            if nome_ident in ident:
                return True

    # 3. Procurar no escopo global (caso não seja ele mesmo)
    if escopo != "global":
        for cat in ["variables", "const"]:
            for ident in tabela_de_simbolos.get("global", {}).get(cat, {}).get("identificadores", []):
                if nome_ident in ident:
                    return True
    if escopo == '':            
        # 4. verifica se é nome de classe
        nomes_classes = set(tabela_de_simbolos_2.keys())
        if nome_ident in nomes_classes:
            return True
        else:
            # 5. Não encontrado
            lista_erros.append(
                f"Erro: Não existe uma classe '{nome_ident}' para que esse objeto seja criado, (linha {linha})"
            )
            return False

    # 5. Não encontrado
    lista_erros.append(
        f"Erro: identificador '{nome_ident}' não declarado no escopo '{escopo}' (linha {linha})"
    )
    return False

def verifica_existencia_metodo_atributo(nome_ident, linha, escopo): 
    if escopo[1] == "atributo":
        identificadores = []
        if escopo[0]:
            escopo_obj = tabela_de_simbolos_2[escopo[0]]
            for categoria in ["variables", "const"]:
                try:
                    for ident in escopo_obj[categoria]["identificadores"]:
                        for nome in ident.keys():
                            identificadores.append(nome)
                except:
                    pass
        if nome_ident in identificadores:
            return True
        else:
            # 5. Não encontrado
            lista_erros.append(
                f"Erro: Não existe um atributo '{nome_ident}' no escopo '{escopo[0]}' (linha {linha})"
            )

    elif escopo[1] == "metodo":
        nomes_funcoes = []
        if escopo[0]:
            for categoria, conteudo in tabela_de_simbolos_2[escopo[0]].items():
                if "funcoes" in conteudo:
                    for funcao in conteudo["funcoes"]:
                        for nome_funcao in funcao:
                            nomes_funcoes.append(nome_funcao)
                            
        if nome_ident in nomes_funcoes:
            return True
        else:
            # 5. Não encontrado
            lista_erros.append(
                f"Erro: Não existe uma função '{nome_ident}' no escopo '{escopo[0]}' (linha {linha})"
            )
    
    return False    

def entrar_escopo(nome_escopo):
    pilha_escopos.append(nome_escopo)
    if nome_escopo not in tabela_de_simbolos:
        tabela_de_simbolos[nome_escopo] = {}

def sair_escopo():
    try:
        pilha_escopos.pop()
    except:
        pass

def declarar_simbolo(nome, categoria, tipo, linha, parametros=[], tipo_retorno=None, funcoes=[], identificadores=[]):
    escopo_atual = pilha_escopos[-1]
    tabela = tabela_de_simbolos[escopo_atual]

    if nome in tabela:
        raise f"Símbolo '{nome}' já declarado no escopo '{escopo_atual}' na linha {linha}"

    tabela[nome] = {
        "categoria": categoria,
        "tipo": tipo,
        "linha": linha,
        "parametros": parametros,
        "tipo_retorno": tipo_retorno,
        "funcoes": funcoes,
        "identificadores": identificadores
    }

def inicializar_analise():
    global tabela_de_simbolos, pilha_escopos, pilha
    tabela_de_simbolos.clear()
    pilha_escopos.clear()
    pilha_escopos.append("global")
    tabela_de_simbolos["global"] = {}

def consume_token(tokens, current_index):
    if current_index < len(tokens):
        current_index += 1
    
    return current_index

def current_token(tokens, current_index):
    if current_index < len(tokens):
        return tokens[current_index]
    return None

def match_token(tokens, current_index, token_type, token_value=None):
    token = current_token(tokens, current_index)
    if token and token[1] == token_type and (token_value is None or token[2] == token_value):
        return True
    return False

def parse_main(tokens, current_index): 
    if match_token(tokens, current_index, "PRE", "class"):
        current_index = consume_token(tokens, current_index)
    
    if match_token(tokens, current_index, "PRE", "main"):
        current_index = consume_token(tokens, current_index)

        # 4. Entrar no escopo 'main'
        entrar_escopo("global")

        # 5. Registrar 'main' na tabela de símbolos como uma classe
        declarar_simbolo(
            nome = "main",
            categoria = "classe",
            tipo = None,
            linha = current_token(tokens, current_index)[0],
            parametros = [],
            tipo_retorno = None,
            funcoes = [],
            identificadores = []
        )
    
    if match_token(tokens, current_index, "DEL", "{"):
        current_index = consume_token(tokens, current_index)
        current_index = parse_escopoMain(tokens, current_index)

    if match_token(tokens, current_index, "DEL", "}"):
        current_index = consume_token(tokens, current_index)

    # 8. Sai do escopo 'main'
    sair_escopo()

    return current_index

def parse_escopoMain(tokens, current_index):
    if match_token(tokens, current_index, "PRE", "class"):
        current_index = consume_token(tokens, current_index)

        if match_token(tokens, current_index, "IDE"):
            current_index = consume_token(tokens, current_index)

            entrar_escopo(current_token(tokens, current_index - 1)[2])

            declarar_simbolo(
                nome = current_token(tokens, current_index - 1)[2],
                categoria = "classe",
                tipo = None,
                linha = current_token(tokens, current_index)[0],
                parametros = [],
                tipo_retorno = None,
                funcoes = [],
                identificadores = []
            )

        if match_token(tokens, current_index, "DEL", "{"):
            current_index = consume_token(tokens, current_index)
            current_index = parse_defComeco2(tokens, current_index) #voltar aqui

        if match_token(tokens, current_index, "DEL", "}"):
            current_index = consume_token(tokens, current_index)
            sair_escopo()
            current_index = parse_escopoMain(tokens, current_index)

    else:
        current_index = parse_defComeco(tokens, current_index)

    return current_index

# <codigo>
def parse_escopoMain2(tokens, current_index):
    if match_token(tokens, current_index, 'PRE', 'print'):
        current_index = parse_comandoPrint(tokens, current_index)
        return parse_escopoMain2(tokens, current_index)
    elif match_token(tokens, current_index, 'PRE', 'read'):
        current_index = parse_comandoRead(tokens, current_index)
        return parse_escopoMain2(tokens, current_index)
    elif match_token(tokens, current_index, 'PRE', 'if'):
        current_index = parse_comandoIf(tokens, current_index)
        return parse_escopoMain2(tokens, current_index)
    elif match_token(tokens, current_index, 'IDE'):
        lookahead = tokens[current_index+1][2] if current_index+1 < len(tokens) else ''
        if lookahead == '=':
            existe_identificador(current_token(tokens, current_index)[2], current_token(tokens, current_index)[0], pilha_escopos[-1])
            current_index = consume_token(tokens, current_index)  # id
            current_index = consume_token(tokens, current_index)  # =
            current_index = parse_expressao(tokens, current_index)
            if match_token(tokens, current_index, 'DEL', ';'):
                current_index = consume_token(tokens, current_index)
                return parse_escopoMain2(tokens, current_index)
            
        elif lookahead == '[':
            existe_identificador(current_token(tokens, current_index)[2], current_token(tokens, current_index)[0], pilha_escopos[-1])
            if not match_token(tokens, current_index + 4, 'DEL', '['):
                current_index = parse_atribvetor(tokens, current_index)
            else:
                current_index = parse_atribMatriz(tokens, current_index)
            return parse_escopoMain2(tokens, current_index)
        elif lookahead == '.':
            if match_token(tokens, current_index+2, 'REL', '='):
                current_index = parse_chamadaAtributo(tokens, current_index)
                if match_token(tokens, current_index, 'REL', '='):
                    current_index = consume_token(tokens, current_index)
                    current_index = parse_expressao(tokens, current_index)
                    if match_token(tokens, current_index, 'DEL', ';'):
                        current_index = consume_token(tokens, current_index)
                        return parse_escopoMain2(tokens, current_index)
                    
            else:
                current_index = parse_chamadaAtributo(tokens, current_index)  
                if match_token(tokens, current_index, 'REL', '='):
                    current_index = consume_token(tokens, current_index)
                    current_index = parse_expressao(tokens, current_index)
                    if match_token(tokens, current_index, 'DEL', ';'):
                        current_index = consume_token(tokens, current_index)
                        return parse_escopoMain2(tokens, current_index)
                    
        elif lookahead == '-' and match_token(tokens, current_index +2, "REL", ">"):
            current_index = parse_chamadaMetodo(tokens, current_index)
            if match_token(tokens, current_index, 'DEL', ';'):
                current_index = consume_token(tokens, current_index)
                return parse_escopoMain2(tokens, current_index)
            
    elif match_token(tokens, current_index, 'PRE', 'for'):
        current_index = parse_comandoFor(tokens, current_index)
        return parse_escopoMain2(tokens, current_index)
    elif match_token(tokens, current_index, 'DEL', '}'):
        return current_index  # fim

# <codigo>
def parse_codigo(tokens, current_index):
    if match_token(tokens, current_index, 'PRE', 'variables'):
        categoria = 'variables'
        current_index = parse_defVar(tokens, current_index, categoria)
        return parse_codigo(tokens, current_index)
    elif match_token(tokens, current_index, 'PRE', 'print'):
        current_index = parse_comandoPrint(tokens, current_index)
        return parse_codigo(tokens, current_index)
    elif match_token(tokens, current_index, 'PRE', 'read'):
        current_index = parse_comandoRead(tokens, current_index)
        return parse_codigo(tokens, current_index)
    elif match_token(tokens, current_index, 'PRE', 'if'):
        current_index = parse_comandoIf(tokens, current_index)
        return parse_codigo(tokens, current_index)
    elif match_token(tokens, current_index, 'PRE', 'return'):
        current_index = consume_token(tokens, current_index)
        if not match_token(tokens, current_index, 'DEL', ';'):
            current_index = parse_expressao(tokens, current_index)
        if match_token(tokens, current_index, 'DEL', ';'):
            current_index = consume_token(tokens, current_index)
        
        return parse_codigo(tokens, current_index)
    elif match_token(tokens, current_index, 'IDE'):
        lookahead = tokens[current_index+1][2] if current_index+1 < len(tokens) else ''
        if lookahead == '=':
            existe_identificador(current_token(tokens, current_index)[2], current_token(tokens, current_index)[0], pilha_escopos[-1])
            current_index = consume_token(tokens, current_index)  # id
            current_index = consume_token(tokens, current_index)  # =
            current_index = parse_expressao(tokens, current_index)
            if match_token(tokens, current_index, 'DEL', ';'):
                current_index = consume_token(tokens, current_index)
                return parse_codigo(tokens, current_index)
            
        elif lookahead == '[':
            existe_identificador(current_token(tokens, current_index)[2], current_token(tokens, current_index)[0], pilha_escopos[-1])
            if not match_token(tokens, current_index + 4, 'DEL', '['):
                current_index = parse_atribvetor(tokens, current_index)
                pass
            else:
                current_index = parse_atribMatriz(tokens, current_index)
            return parse_codigo(tokens, current_index)
        elif lookahead == '.':
            if match_token(tokens, current_index+2, 'REL', '='):
                current_index = parse_chamadaAtributo(tokens, current_index)
                if match_token(tokens, current_index, 'REL', '='):
                    current_index = consume_token(tokens, current_index)
                    current_index = parse_expressao(tokens, current_index)
                    if match_token(tokens, current_index, 'DEL', ';'):
                        current_index = consume_token(tokens, current_index)
                        return parse_codigo(tokens, current_index)
                    
            else:
                current_index = parse_chamadaAtributo(tokens, current_index)  
                if match_token(tokens, current_index, 'REL', '='):
                    current_index = consume_token(tokens, current_index)
                    current_index = parse_expressao(tokens, current_index)
                    if match_token(tokens, current_index, 'DEL', ';'):
                        current_index = consume_token(tokens, current_index)
                        return parse_codigo(tokens, current_index)
                    
        elif lookahead == '-' and match_token(tokens, current_index +2, "REL", ">"):
            current_index = parse_chamadaMetodo(tokens, current_index)
            if match_token(tokens, current_index, 'DEL', ';'):
                current_index = consume_token(tokens, current_index)
                return parse_codigo(tokens, current_index)
            
    elif match_token(tokens, current_index, 'PRE', 'for'):
        current_index = parse_comandoFor(tokens, current_index)
        return parse_codigo(tokens, current_index)
    elif match_token(tokens, current_index, 'DEL', '}'):
        return current_index  # fim

# <chamadaMetodo> ::= <classeMetodo> '->' identificador '(' <args> ')'
def parse_chamadaMetodo(tokens, current_index):
    current_index = parse_classeMetodo(tokens, current_index)
    if match_token(tokens, current_index, 'ART', '-'):
        current_index = consume_token(tokens, current_index)
        if match_token(tokens, current_index, 'REL', '>'):
            current_index = consume_token(tokens, current_index)
            
            # verifica chamadaMetodo
            alvo = current_token(tokens, current_index - 3)[2]
            resultado = None
            resultado2 = None
            for item in lista_obj:
                if item[0][2] == alvo:
                    resultado = item[1]
                    resultado2 = item[0][2]
            resultado = [resultado, "metodo"]
            if alvo == "main":
                resultado2 = "main"
                resultado = ["global", "metodo"]
            if current_token(tokens, current_index - 3)[2] == resultado2:
                if verifica_existencia_metodo_atributo(current_token(tokens, current_index)[2], current_token(tokens, current_index)[0], resultado):
                    pass
            else:
                lista_erros.append(
                    f"Erro: Não existe um objeto com o nome '{current_token(tokens, current_index - 3)[2]}' (linha {current_token(tokens, current_index - 3)[0]})"
                )
            
            if match_token(tokens, current_index, 'IDE'):
                current_index = consume_token(tokens, current_index)
                if match_token(tokens, current_index, 'DEL', '('):
                    current_index = consume_token(tokens, current_index)
                    current_index = parse_args(tokens, current_index)
                    if match_token(tokens, current_index, 'DEL', ')'):
                        current_index = consume_token(tokens, current_index)
   
    return current_index

# <classeMetodo> ::= identificador | 'main'
def parse_classeMetodo(tokens, current_index):
    if match_token(tokens, current_index, 'IDE') or match_token(tokens, current_index, 'PRE', 'main'):
        current_index = consume_token(tokens, current_index)

    return current_index

# <args> ::= <listaArgumentos> |
def parse_args(tokens, current_index):
    if match_token(tokens, current_index, 'DEL', ')'):
        return current_index  # vazio
    return parse_listaArgumentos(tokens, current_index)

# <atribvetor> ::= <acessovetor> '=' <Expressao> ';'
def parse_atribvetor(tokens, current_index):
    current_index = parse_acessoVetor(tokens, current_index)
    if match_token(tokens, current_index, 'REL', '='):
        current_index = consume_token(tokens, current_index)
        current_index = parse_expressao(tokens, current_index)
        if match_token(tokens, current_index, 'DEL', ';'):
            current_index = consume_token(tokens, current_index)

    return current_index

# <acessovetor> ::= identificador '[' numero ']' | identificador '[' digito ']'
def parse_acessoVetor(tokens, current_index):
    if match_token(tokens, current_index, 'IDE'):
        current_index = consume_token(tokens, current_index)
        if match_token(tokens, current_index, 'DEL', '['):
            current_index = consume_token(tokens, current_index)
            if match_token(tokens, current_index, 'NRO'):
                current_index = consume_token(tokens, current_index)
                if match_token(tokens, current_index, 'DEL', ']'):
                    current_index = consume_token(tokens, current_index)

    return current_index

# <atribMatriz> ::= <indicesMatriz> '=' <Expressao> ';'
def parse_atribMatriz(tokens, current_index):
    current_index = parse_indicesMatriz(tokens, current_index)
    if match_token(tokens, current_index, 'REL', '='):
        current_index = consume_token(tokens, current_index)
        current_index = parse_expressao(tokens, current_index)
        if match_token(tokens, current_index, 'DEL', ';'):
            current_index = consume_token(tokens, current_index)

    return current_index

# <indicesMatriz> ::= identificador '[' digito ']' '[' digito ']'
def parse_indicesMatriz(tokens, current_index):
    if match_token(tokens, current_index, 'IDE'):
        current_index = consume_token(tokens, current_index)
        if match_token(tokens, current_index, 'DEL', '['):
            current_index = consume_token(tokens, current_index)
            if match_token(tokens, current_index, 'NRO'):
                current_index = consume_token(tokens, current_index)
                if match_token(tokens, current_index, 'DEL', ']'):
                    current_index = consume_token(tokens, current_index)
                    if match_token(tokens, current_index, 'DEL', '['):
                        current_index = consume_token(tokens, current_index)
                        if match_token(tokens, current_index, 'NRO'):
                            current_index = consume_token(tokens, current_index)
                            if match_token(tokens, current_index, 'DEL', ']'):
                                current_index = consume_token(tokens, current_index)

    return current_index

# <chamadaAtributo>
def parse_chamadaAtributo(tokens, current_index):
    if match_token(tokens, current_index, 'IDE'):
        current_index = consume_token(tokens, current_index)
        if match_token(tokens, current_index, 'DEL', '.'):
            current_index = consume_token(tokens, current_index)

            # verifica chamadaAtributo
            alvo = current_token(tokens, current_index - 2)[2]
            resultado = None
            resultado2 = None
            for item in lista_obj:
                if item[0][2] == alvo:
                    resultado = item[1]
                    resultado2 = item[0][2]
            resultado = [resultado, "atributo"]
            if alvo == "main":
                resultado2 = "main"
                resultado = ["global", "atributo"]
            if current_token(tokens, current_index - 2)[2] == resultado2:
                if verifica_existencia_metodo_atributo(current_token(tokens, current_index)[2], current_token(tokens, current_index)[0], resultado):
                    pass
            else:
                lista_erros.append(
                    f"Erro: Não existe um objeto com o nome '{current_token(tokens, current_index - 2)[2]}' (linha {current_token(tokens, current_index - 2)[0]})"
                )
            
            if match_token(tokens, current_index, 'IDE'):
                current_index = consume_token(tokens, current_index)

    return current_index

def parse_expressao(tokens, current_index):
    current_index = parse_expressaoLogica(tokens, current_index)
    return current_index

def parse_expressaoLogica(tokens, current_index):
    current_index = parse_expressaoRelacional(tokens, current_index)
    current_index = parse_expressaoLogicaCont(tokens, current_index)
    return current_index

def parse_expressaoRelacional(tokens, current_index):
    current_index = parse_expressaoAritmetica(tokens, current_index)
    current_index = parse_expressaoRelacionalCont(tokens, current_index)
    return current_index

def parse_expressaoRelacionalCont(tokens, current_index):
    if match_token(tokens, current_index, "REL", "!=") or match_token(tokens, current_index, "REL", "==") or match_token(tokens, current_index, "REL", ">") or match_token(tokens, current_index, "REL", ">=") or match_token(tokens, current_index, "REL", "<") or match_token(tokens, current_index, "REL", "<="):
        current_index = parse_opRelacional(tokens, current_index)
        current_index = parse_expressaoAritmetica(tokens, current_index)
        current_index = parse_expressaoRelacionalCont(tokens, current_index)
    return current_index

def parse_opRelacional(tokens, current_index):
    if match_token(tokens, current_index, "REL", "!=") or match_token(tokens, current_index, "REL", "==") or match_token(tokens, current_index, "REL", ">") or match_token(tokens, current_index, "REL", ">=") or match_token(tokens, current_index, "REL", "<") or match_token(tokens, current_index, "REL", "<="):
        current_index = consume_token(tokens, current_index)
    return current_index

def parse_expressaoAritmetica(tokens, current_index):
    current_index = parse_termo(tokens, current_index)
    current_index = parse_expressaoAritmeticaCont(tokens, current_index)
    return current_index

def parse_termo(tokens, current_index):
    current_index = parse_fator(tokens, current_index)
    current_index = parse_termoCont(tokens, current_index)
    return current_index

def parse_termoCont(tokens, current_index):
    if match_token(tokens, current_index, "ART", "*") or match_token(tokens, current_index, "ART", "/"):
        current_index = parse_opMult(tokens, current_index)
        current_index = parse_fator(tokens, current_index)
        current_index = parse_termoCont(tokens, current_index)
    return current_index

def parse_opMult(tokens, current_index):
    if match_token(tokens, current_index, "ART", "*") or match_token(tokens, current_index, "ART", "/"):
        current_index = consume_token(tokens, current_index)
    return current_index

def parse_expressaoAritmeticaCont(tokens, current_index):
    if match_token(tokens, current_index, "ART", "+") or match_token(tokens, current_index, "ART", "-"):
        current_index = parse_opSoma(tokens, current_index)
        current_index = parse_termo(tokens, current_index)
        current_index = parse_expressaoAritmeticaCont(tokens, current_index)
    return current_index

def parse_opSoma(tokens, current_index):
    if match_token(tokens, current_index, "ART", "+") or match_token(tokens, current_index, "ART", "-"):
        current_index = consume_token(tokens, current_index) 
    return current_index

def parse_fator(tokens, current_index):
    current_index = parse_negacao(tokens, current_index)
    if match_token(tokens, current_index, "DEL", "("):
        current_index = consume_token(tokens, current_index)
        current_index = parse_expressao(tokens, current_index)
        if match_token(tokens, current_index, "DEL", ")"):
            current_index = consume_token(tokens, current_index)
    else:
        current_index = parse_valor(tokens, current_index)
        current_index = parse_incr(tokens, current_index)
    return current_index

def parse_negacao(tokens, current_index):
    if match_token(tokens, current_index, "LOG", "!"):
        current_index = consume_token(tokens, current_index)
    
    return current_index

def parse_incr(tokens, current_index):
    if match_token(tokens, current_index, "ART", "++") or match_token(tokens, current_index, "ART", "--"):
        current_index = consume_token(tokens, current_index)
    
    return current_index

def parse_expressaoLogicaCont(tokens, current_index):
    if match_token(tokens, current_index, "LOG", "&&") or match_token(tokens, current_index, "LOG", "||"):
        current_index = parse_opLogico(tokens, current_index)
        current_index = parse_expressaoRelacional(tokens, current_index)
        current_index = parse_expressaoLogicaCont(tokens, current_index)
    return current_index

def parse_opLogico(tokens, current_index):
    if match_token(tokens, current_index, "LOG", "&&") or match_token(tokens, current_index, "LOG", "||"):
        current_index = consume_token(tokens, current_index)
    
    return current_index

def parse_comandoFor(tokens, current_index):
    if match_token(tokens, current_index, 'PRE', 'for'):
        current_index = consume_token(tokens, current_index)
        if match_token(tokens, current_index, 'DEL', '('):
            current_index = consume_token(tokens, current_index)
            current_index = parse_valor(tokens, current_index)
            if match_token(tokens, current_index, 'DEL', ';'):
                current_index = consume_token(tokens, current_index)
                current_index = parse_expressao(tokens, current_index)
                if match_token(tokens, current_index, 'DEL', ';'):
                    current_index = consume_token(tokens, current_index)
                    current_index = parse_expressao(tokens, current_index)
                    if match_token(tokens, current_index, 'DEL', ')'):
                        current_index = consume_token(tokens, current_index)
                        if match_token(tokens, current_index, 'DEL', '{'):
                            current_index = consume_token(tokens, current_index)
                            current_index = parse_codigo(tokens, current_index)
                            if match_token(tokens, current_index, 'DEL', '}'):
                                current_index = consume_token(tokens, current_index)
              
    return current_index

# <comandoIf>
def parse_comandoIf(tokens, current_index):
    if match_token(tokens, current_index, 'PRE', 'if'):
        current_index = consume_token(tokens, current_index)
        if match_token(tokens, current_index, 'DEL', '('):
            current_index = consume_token(tokens, current_index)
            current_index = parse_expressao(tokens, current_index)
            if match_token(tokens, current_index, 'DEL', ')'):
                current_index = consume_token(tokens, current_index)
                if match_token(tokens, current_index, 'DEL', '{'):
                    current_index = consume_token(tokens, current_index)
                    current_index = parse_codigo(tokens, current_index)
                    if match_token(tokens, current_index, 'DEL', '}'):
                        current_index = consume_token(tokens, current_index)
                        current_index = parse_opcionalElse(tokens, current_index)

    return current_index

# <opcionalElse>
def parse_opcionalElse(tokens, current_index):
    if match_token(tokens, current_index, 'PRE', 'else'):
        current_index = consume_token(tokens, current_index)
        if match_token(tokens, current_index, 'DEL', '{'):
            current_index = consume_token(tokens, current_index)
            current_index = parse_codigo(tokens, current_index)
            if match_token(tokens, current_index, 'DEL', '}'):
                current_index = consume_token(tokens, current_index)

    return current_index

def parse_comandoRead(tokens, current_index):
    if match_token(tokens, current_index, 'PRE', 'read'):
        current_index = consume_token(tokens, current_index)
        if match_token(tokens, current_index, 'DEL', '('):
            current_index = consume_token(tokens, current_index)
            current_index = parse_listaArgumentosRead(tokens, current_index)
            if match_token(tokens, current_index, 'DEL', ')'):
                current_index = consume_token(tokens, current_index)
                if match_token(tokens, current_index, 'DEL', ';'):
                    current_index = consume_token(tokens, current_index)

    return current_index

# <listaArgumentosRead>
def parse_listaArgumentosRead(tokens, current_index):
    current_index = parse_conteudoRead(tokens, current_index)
    current_index = parse_listaArgumentosRead2(tokens, current_index)
    return current_index

# <listaArgumentosRead2>
def parse_listaArgumentosRead2(tokens, current_index):
    while match_token(tokens, current_index, 'DEL', ','):
        current_index = consume_token(tokens, current_index)
        current_index = parse_conteudoRead(tokens, current_index)
    return current_index

# <conteudoRead> ::= identificador | <acessoVetor> | <chamadaAtributo>
def parse_conteudoRead(tokens, current_index):
    if match_token(tokens, current_index, 'IDE'):
        # Pode ser identificador simples, acesso vetor ou chamada atributo
        if match_token(tokens, current_index+1, 'DEL', '['):
            current_index = parse_acessoVetor(tokens, current_index)
        elif match_token(tokens, current_index+1, 'DEL', '.'):
            current_index = parse_chamadaAtributo(tokens, current_index)
        else:
            current_index = consume_token(tokens, current_index)
    
    return current_index

# <comandoPrint>
def parse_comandoPrint(tokens, current_index):
    if match_token(tokens, current_index, 'PRE', 'print'):
        current_index = consume_token(tokens, current_index)
        if match_token(tokens, current_index, 'DEL', '('):
            current_index = consume_token(tokens, current_index)
            current_index = parse_listaArgumentos(tokens, current_index)
            if match_token(tokens, current_index, 'DEL', ')'):
                current_index = consume_token(tokens, current_index)
                if match_token(tokens, current_index, 'DEL', ';'):
                    current_index = consume_token(tokens, current_index)

    return current_index

# <listaArgumentos>
def parse_listaArgumentos(tokens, current_index):
    current_index = parse_conteudoPrint(tokens, current_index)
    current_index = parse_listaArgumentos2(tokens, current_index)
    return current_index

# <listaArgumentos2>
def parse_listaArgumentos2(tokens, current_index):
    while match_token(tokens, current_index, 'DEL', ','):
        current_index = consume_token(tokens, current_index)
        current_index = parse_conteudoPrint(tokens, current_index)
    return current_index

# <conteudoPrint> ::= <valor>
def parse_conteudoPrint(tokens, current_index):
    return parse_valor(tokens, current_index)       
    
def parse_defComeco(tokens, current_index):
    if match_token(tokens, current_index, 'PRE', 'const'):
        nome = current_token(tokens, current_index)[2]
        linha = current_token(tokens, current_index)[0]
        categoria = 'const'
        if nome not in tabela_de_simbolos[pilha_escopos[-1]]:
            declarar_simbolo(
                nome = nome,
                categoria = "const",
                tipo = None,
                linha = linha,
                parametros = [],
                tipo_retorno = None,
                funcoes = [],
                identificadores = []
            )
        current_index = parse_defConst(tokens, current_index, categoria)
        
        current_index = parse_defComeco(tokens, current_index)
    elif match_token(tokens, current_index, 'PRE', 'variables'):
        nome = current_token(tokens, current_index)[2]
        linha = current_token(tokens, current_index)[0]
        categoria = 'variables'
        if nome not in tabela_de_simbolos[pilha_escopos[-1]]:
            declarar_simbolo(
                nome = nome,
                categoria = "variables",
                tipo = None,
                linha = linha,
                parametros = [],
                tipo_retorno = None,
                funcoes = [],
                identificadores = []
            )
        current_index = parse_defVar(tokens, current_index, categoria)
            
        current_index = parse_defComeco(tokens, current_index)
    elif match_token(tokens, current_index, 'PRE', 'methods'):
        nome = current_token(tokens, current_index)[2]
        linha = current_token(tokens, current_index)[0]
        if nome not in tabela_de_simbolos[pilha_escopos[-1]]:
            declarar_simbolo(
                nome = nome,
                categoria = "methods",
                tipo = None,
                linha = linha,
                parametros = [],
                tipo_retorno = None,
                funcoes = [],
                identificadores = []
            )
        current_index = parse_methods(tokens, current_index)

        current_index = parse_defComeco(tokens, current_index)
    elif current_token(tokens, current_index)[2] in ["print", "if", "for", "read"] or match_token(tokens, current_index, 'IDE'):
        current_index = parse_escopoMain2(tokens, current_index)
    elif match_token(tokens, current_index, 'PRE', 'class'):
        current_index = parse_escopoMain(tokens, current_index)
    elif match_token(tokens, current_index, 'DEL', '}'):
        return current_index
    
    return current_index

def parse_defComeco2(tokens, current_index):
    if match_token(tokens, current_index, 'PRE', 'variables'):
        nome = current_token(tokens, current_index)[2]
        linha = current_token(tokens, current_index)[0]
        categoria = 'variables'
        if nome not in tabela_de_simbolos[pilha_escopos[-1]]:
            declarar_simbolo(
                nome = nome,
                categoria = "variables",
                tipo = None,
                linha = linha,
                parametros = [],
                tipo_retorno = None,
                funcoes = [],
                identificadores = []
            )
        current_index = parse_defVar(tokens, current_index, categoria)
            
        current_index = parse_defComeco2(tokens, current_index)
    elif match_token(tokens, current_index, 'PRE', 'methods'):
        nome = current_token(tokens, current_index)[2]
        linha = current_token(tokens, current_index)[0]
        if nome not in tabela_de_simbolos[pilha_escopos[-1]]:
            declarar_simbolo(
                nome = nome,
                categoria = "methods",
                tipo = None,
                linha = linha,
                parametros = [],
                tipo_retorno = None,
                funcoes = [],
                identificadores = []
            )
        current_index = parse_methods(tokens, current_index)
        
        current_index = parse_defComeco2(tokens, current_index)
    elif current_token(tokens, current_index)[2] in ["print", "if", "for", "read"] or match_token(tokens, current_index, 'IDE'):
        current_index = parse_escopoMain2(tokens, current_index)
    elif match_token(tokens, current_index, 'DEL', '}'):
        return current_index
    
    return current_index

# <methods>
def parse_methods(tokens, current_index):
    if match_token(tokens, current_index, 'PRE', 'methods'):
        current_index = consume_token(tokens, current_index)
        if match_token(tokens, current_index, 'DEL', '{'):
            current_index = consume_token(tokens, current_index)
            current_index = parse_listaMetodos(tokens, current_index)
            if match_token(tokens, current_index, 'DEL', '}'):
                current_index = consume_token(tokens, current_index)
    return current_index

# <listaMetodos>
def parse_listaMetodos(tokens, current_index):
    while current_token(tokens, current_index)[2] in ["int", "string", "float", "boolean", "void"]:  # tipo
        tipo = current_token(tokens, current_index)[2]
        linha = current_token(tokens, current_index)[0]
        current_index = consume_token(tokens, current_index)
        if match_token(tokens, current_index, 'IDE'):
            nome = current_token(tokens, current_index)[2]
            pilha.append(nome)
            if not verificar_duplicidade(pilha_escopos[-1], 'methods', nome, linha):
                metodo = {
                    nome: {
                    'categoria': "método",
                    'tipo': tipo,
                    'linha' : linha,
                    'parametros' : [],
                    'tipo_retorno' : tipo,
                    'funcoes': [],
                    'variables': []
                    }
                }
            tabela_de_simbolos[pilha_escopos[-1]]['methods']['funcoes'].append(metodo)
            current_index = consume_token(tokens, current_index)
            if match_token(tokens, current_index, 'DEL', '('):
                current_index = consume_token(tokens, current_index)
                current_index = parse_listaParametros(tokens, current_index, nome)
                if match_token(tokens, current_index, 'DEL', ')'):
                    current_index = consume_token(tokens, current_index)
                    if match_token(tokens, current_index, 'DEL', '{'):
                        current_index = consume_token(tokens, current_index)
                        current_index = parse_codigo(tokens, current_index)
                        if match_token(tokens, current_index, 'DEL', '}'):
                            current_index = consume_token(tokens, current_index)
                            pilha.pop()
                            
        else:
            break
    return current_index

# <listaParametros>
def parse_listaParametros(tokens, current_index, nome):

    while current_token(tokens, current_index)[2] in ["int", "string", "float", "boolean"] or match_token(tokens, current_index, "IDE"):
        tipo = current_token(tokens, current_index)[2]
        current_index = consume_token(tokens, current_index)

        if match_token(tokens, current_index, 'IDE'):
            nome_param = current_token(tokens, current_index)[2]
            linha = current_token(tokens, current_index)[0]
            if not verificar_duplicidade(pilha_escopos[-1], 'parametros', nome_param, linha, nome):
                for metodo_dict in tabela_de_simbolos[pilha_escopos[-1]]['methods']['funcoes']:
                    if nome in metodo_dict:
                        metodo_dict[nome]['parametros'].append((tipo, nome_param))
                        break
  
            current_index = consume_token(tokens, current_index)

            if match_token(tokens, current_index, 'DEL', ','):
                current_index = consume_token(tokens, current_index)
            else:
                break  # Sai do loop se não houver vírgula
        else:
            raise SyntaxError("Esperado nome do parâmetro após tipo")

    return current_index

def parse_defConst(tokens, current_index, categoria):
    if match_token(tokens, current_index, 'PRE', 'const'):
        current_index = consume_token(tokens, current_index)

    if match_token(tokens, current_index, 'DEL', '{'):
        current_index = consume_token(tokens, current_index)
        current_index = parse_listaConst(tokens, current_index, categoria)
        if match_token(tokens, current_index, 'DEL', '}'):
            current_index = consume_token(tokens, current_index)
    return current_index

def parse_defVar(tokens, current_index, categoria):
    if match_token(tokens, current_index, 'PRE', 'variables'):
        current_index = consume_token(tokens, current_index)
    
    if match_token(tokens, current_index, 'DEL', '{'):
        current_index = consume_token(tokens, current_index)
        current_index = parse_listaConst(tokens, current_index, categoria)
        if match_token(tokens, current_index, 'DEL', '}'):
            current_index = consume_token(tokens, current_index)
        
    return current_index

# <listaConst>
def parse_listaConst(tokens, current_index, categoria):

    while True:

        if match_token(tokens, current_index, "DEL", "}"):
            break

        if (
            current_token(tokens, current_index)[2] in ["int", "float", "string", "boolean"]
            and match_token(tokens, current_index + 1, "IDE")
            and match_token(tokens, current_index + 2, "DEL", "[")
        ):
            current_index = parse_declVetor(tokens, current_index, categoria)
            continue

        elif current_token(tokens, current_index)[2] in ["int", "float", "string", "boolean"]:
            tipo = current_token(tokens, current_index)[2]
            current_index = consume_token(tokens, current_index)
            current_index = parse_listaItens(tokens, current_index, tipo, categoria)

            if match_token(tokens, current_index, 'DEL', ';'):
                current_index = consume_token(tokens, current_index)
            
            continue

        elif match_token(tokens, current_index, 'IDE'):
            if existe_identificador(current_token(tokens, current_index)[2], current_token(tokens, current_index)[0], ""):
                lista_obj.append([current_token(tokens, current_index + 1), current_token(tokens, current_index)[2]])
            current_index = consume_token(tokens, current_index)
            current_index = parse_listaItens(tokens, current_index, tipo, categoria)

            if match_token(tokens, current_index, 'DEL', ';'):
                current_index = consume_token(tokens, current_index)
            
            continue

        else:
            break
    
    return current_index

def parse_listaItens(tokens, current_index, tipo, categoria):

    while match_token(tokens, current_index, 'IDE'):
        nome = current_token(tokens, current_index)[2]
        linha = current_token(tokens, current_index)[0]
        if not pilha:
            if not verificar_duplicidade(pilha_escopos[-1], categoria, nome, linha):
                tabela_de_simbolos[pilha_escopos[-1]][categoria]['identificadores'].append({nome: tipo})
        else:
            if not verificar_duplicidade(pilha_escopos[-1], categoria, nome, linha, pilha[-1]):
                for metodo_dict in tabela_de_simbolos[pilha_escopos[-1]]['methods']['funcoes']:
                    if pilha[-1] in metodo_dict:
                        metodo_dict[pilha[-1]]['variables'].append((tipo, nome))
                        break
        current_index = consume_token(tokens, current_index)
        current_index = parse_possFinal(tokens, current_index)

        # Verifica se há outro identificador com vírgula
        if match_token(tokens, current_index, 'DEL', ','):
            current_index = consume_token(tokens, current_index)
            continue
        else:
            break

    return current_index

# <listaItens2>
def parse_listaItens2(tokens, current_index):
    while match_token(tokens, current_index, 'DEL', ','):
        current_index = consume_token(tokens, current_index)
        if match_token(tokens, current_index, 'IDE'):
            current_index = consume_token(tokens, current_index)
            current_index = parse_possFinal(tokens, current_index)
        
    return current_index

# <possFinal>
def parse_possFinal(tokens, current_index):
    if match_token(tokens, current_index, 'REL', '='):
        current_index = consume_token(tokens, current_index)
        current_index = parse_valor(tokens, current_index)
    return current_index

# <valor>
def parse_valor(tokens, current_index):        
    lookahead = tokens[current_index+1][2] if current_index+1 < len(tokens) else ''
    if match_token(tokens, current_index, 'PRE', 'main'):
        current_index = parse_chamadaMetodo(tokens, current_index)
    elif match_token(tokens, current_index, 'IDE') and lookahead in ["-", "[", "."]:
        if lookahead == '-' and match_token(tokens, current_index +2, "REL", ">"):
            current_index = parse_chamadaMetodo(tokens, current_index)
        elif lookahead == '[':
            existe_identificador(current_token(tokens, current_index)[2], current_token(tokens, current_index)[0], pilha_escopos[-1])
            if not match_token(tokens, current_index + 4, 'DEL', '['):
                current_index = parse_acessoVetor(tokens, current_index)
            
        elif lookahead == '.':
            current_index = parse_chamadaAtributo(tokens, current_index)
        
    elif match_token(tokens, current_index, 'NRO') or match_token(tokens, current_index, 'CAC') or match_token(tokens, current_index, 'PRE', 'true') or match_token(tokens, current_index, 'PRE', 'false') or match_token(tokens, current_index, 'IDE'):
        if match_token(tokens, current_index, 'IDE'):
            existe_identificador(current_token(tokens, current_index)[2], current_token(tokens, current_index)[0], pilha_escopos[-1])
        current_index = consume_token(tokens, current_index)
        
    return current_index

def parse_declVetor(tokens, current_index, categoria):
    if match_token(tokens, current_index, 'PRE'):  # tipo
        current_index = consume_token(tokens, current_index)
        if match_token(tokens, current_index, 'IDE'):
            if not pilha:
                if not verificar_duplicidade(pilha_escopos[-1], categoria, current_token(tokens, current_index)[2], current_token(tokens, current_index)[0]):
                    tabela_de_simbolos[pilha_escopos[-1]][categoria]['identificadores'].append({current_token(tokens, current_index)[2]: 'vetor/matriz'})
            else:
                if not verificar_duplicidade(pilha_escopos[-1], categoria, current_token(tokens, current_index)[2], current_token(tokens, current_index)[0], pilha[-1]):
                    for metodo_dict in tabela_de_simbolos[pilha_escopos[-1]]['methods']['funcoes']:
                        if pilha[-1] in metodo_dict:
                            metodo_dict[pilha[-1]]['variables'].append(('vetor/matriz', current_token(tokens, current_index)[2]))
                            break
            current_index = consume_token(tokens, current_index)
            if match_token(tokens, current_index, 'DEL', '['):
                current_index = consume_token(tokens, current_index)
                current_index = parse_declVetor2(tokens, current_index)
                if match_token(tokens, current_index, 'DEL', ']'):
                    current_index = consume_token(tokens, current_index)
                    if match_token(tokens, current_index, 'DEL', '['):  # matriz
                        current_index = consume_token(tokens, current_index)
                        current_index = parse_declVetor2(tokens, current_index)
                        if match_token(tokens, current_index, 'DEL', ']'):
                            current_index = consume_token(tokens, current_index)
                            current_index = parse_inicializacaoOptMatriz(tokens, current_index)
                        
                    else:
                        current_index = parse_inicializacaoOpt(tokens, current_index)
                    if match_token(tokens, current_index, 'DEL', ';'):
                        current_index = consume_token(tokens, current_index)
                    
    return current_index

# <declVetor2>
def parse_declVetor2(tokens, current_index):
    if match_token(tokens, current_index, 'NRO'):
        current_index = consume_token(tokens, current_index)
    
    return current_index

# <inicializacaoOpt>
def parse_inicializacaoOpt(tokens, current_index):
    if match_token(tokens, current_index, 'REL', '='):
        current_index = consume_token(tokens, current_index)
        if match_token(tokens, current_index, 'DEL', '['):
            current_index = consume_token(tokens, current_index)
            current_index = parse_valores(tokens, current_index)
            if match_token(tokens, current_index, 'DEL', ']'):
                current_index = consume_token(tokens, current_index)
          
    return current_index

# <inicializacaoOptMatriz>
def parse_inicializacaoOptMatriz(tokens, current_index):
    if match_token(tokens, current_index, 'REL', '='):
        current_index = consume_token(tokens, current_index)
        if match_token(tokens, current_index, 'DEL', '['):
            current_index = consume_token(tokens, current_index)
            current_index = parse_linhaMatriz(tokens, current_index)
        
    return current_index

# <valores>
def parse_valores(tokens, current_index):
    current_index = parse_valorVetor(tokens, current_index)
    current_index = parse_valores_cont(tokens, current_index)
    return current_index

# <valores_cont>
def parse_valores_cont(tokens, current_index):
    while match_token(tokens, current_index, 'DEL', ','):
        current_index = consume_token(tokens, current_index)
        current_index = parse_valorVetor(tokens, current_index)
    return current_index

# <valorVetor>
def parse_valorVetor(tokens, current_index):
    if match_token(tokens, current_index, 'NRO'):
        current_index = consume_token(tokens, current_index)
    else:
        current_index = parse_acessoVetor(tokens, current_index)
    return current_index

# <acessoVetor>
def parse_acessoVetor(tokens, current_index):
    if match_token(tokens, current_index, 'IDE'):
        current_index = consume_token(tokens, current_index)
        if match_token(tokens, current_index, 'DEL', '['):
            current_index = consume_token(tokens, current_index)
            if match_token(tokens, current_index, 'NRO'):
                current_index = consume_token(tokens, current_index)
            
            if match_token(tokens, current_index, 'DEL', ']'):
                current_index = consume_token(tokens, current_index)
            
    return current_index

# <linhaMatriz>
def parse_linhaMatriz(tokens, current_index):
    if match_token(tokens, current_index, 'DEL', '['):
        current_index = consume_token(tokens, current_index)
        current_index = parse_valores(tokens, current_index)
        if match_token(tokens, current_index, 'DEL', ']'):
            current_index = consume_token(tokens, current_index)
            if match_token(tokens, current_index, 'DEL', ','):
                current_index = consume_token(tokens, current_index)
                current_index = parse_linhaMatriz(tokens, current_index)
            elif match_token(tokens, current_index, 'DEL', ']'):
                current_index = consume_token(tokens, current_index)
        
    return current_index

def main():
    global lista_erros
    global lista_obj
    global tabela_de_simbolos_2 

    raiz_projeto = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pasta_entrada = os.path.join(raiz_projeto, "files")
    
    resultado_lexico = processar_arquivos()
    for name, lista_tokens in resultado_lexico.items():
        if lista_tokens:
            print(f"Arquivo: {name}")
            current_index = 0
            lista_erros = []
            tabela_de_simbolos_2 = main_sintatico()
            current_index = parse_main(lista_tokens, current_index)
            
            caminho_entrada = os.path.join(pasta_entrada, name)
            # Escreve os erros encontrados em um arquivo TXT
            with open(f"{caminho_entrada[:-4]}-saida.txt", "w", encoding="utf-8") as f:
                if lista_erros:
                    f.write("Erro Sintático Encontrado\n")
                    for erro in lista_erros:
                        f.write(f"{erro}\n")
                else:
                    f.write("Análise Semântica concluída com sucesso.\n\n")
                    f.write("Tabela de Símbolos:\n")
                    f.write(json.dumps(tabela_de_simbolos, indent=4, ensure_ascii=False))
    
if __name__ == '__main__':
    main()