from lexico import processar_arquivos
import os
import json

global lista_erros

tabela_de_simbolos = {}
pilha_escopos = []

def entrar_escopo(nome_escopo):
    pilha_escopos.append(nome_escopo)
    if nome_escopo not in tabela_de_simbolos:
        tabela_de_simbolos[nome_escopo] = {}

def sair_escopo():
    try:
        pilha_escopos.pop()
    except:
        pass

def declarar_simbolo(nome, categoria, tipo, linha, parametros=None, tipo_retorno=None, funcoes=[]):
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
        "funcoes": funcoes
    }

def inicializar_analise():
    global tabela_de_simbolos, pilha_escopos
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
            parametros = None,
            tipo_retorno = None,
            funcoes = []
        )
    
    if match_token(tokens, current_index, "DEL", "{"):
        current_index = consume_token(tokens, current_index)
        current_index = parse_escopoMain(tokens, current_index)

    if match_token(tokens, current_index, "DEL", "}"):
        current_index = consume_token(tokens, current_index)

    # 8. Sai do escopo 'main'
    sair_escopo()
    print(tabela_de_simbolos)
    '''print(tabela_de_simbolos['global'])
    print(tabela_de_simbolos['Orangotango'])
    print(tabela_de_simbolos['Toin'])'''

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
                parametros = None,
                tipo_retorno = None,
                funcoes = []
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
            current_index = consume_token(tokens, current_index)  # id
            current_index = consume_token(tokens, current_index)  # =
            current_index = parse_expressao(tokens, current_index)
            if match_token(tokens, current_index, 'DEL', ';'):
                current_index = consume_token(tokens, current_index)
                return parse_escopoMain2(tokens, current_index)
            
        elif lookahead == '[':
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
        current_index = parse_defVar(tokens, current_index)
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
            current_index = consume_token(tokens, current_index)  # id
            current_index = consume_token(tokens, current_index)  # =
            current_index = parse_expressao(tokens, current_index)
            if match_token(tokens, current_index, 'DEL', ';'):
                current_index = consume_token(tokens, current_index)
                return parse_codigo(tokens, current_index)
            
        elif lookahead == '[':
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
        
        if current_token(tokens, current_index)[2] not in tabela_de_simbolos[pilha_escopos[-1]]:
            declarar_simbolo(
                nome = current_token(tokens, current_index)[2],
                categoria = "const",
                tipo = None,
                linha = current_token(tokens, current_index)[0],
                parametros = None,
                tipo_retorno = None,
                funcoes = []
            )

        current_index = parse_defConst(tokens, current_index)
        current_index = parse_defComeco(tokens, current_index)
    elif match_token(tokens, current_index, 'PRE', 'variables'):

        if current_token(tokens, current_index)[2] not in tabela_de_simbolos[pilha_escopos[-1]]:
            declarar_simbolo(
                nome = current_token(tokens, current_index)[2],
                categoria = "variables",
                tipo = None,
                linha = current_token(tokens, current_index)[0],
                parametros = None,
                tipo_retorno = None,
                funcoes = []
            )

        current_index = parse_defVar(tokens, current_index)
        current_index = parse_defComeco(tokens, current_index)
    elif match_token(tokens, current_index, 'PRE', 'methods'):
        nome = current_token(tokens, current_index)[2]
        linha = current_token(tokens, current_index)[0]

        current_index, funcoes = parse_methods(tokens, current_index)
        if nome not in tabela_de_simbolos[pilha_escopos[-1]]:
            declarar_simbolo(
                nome = nome,
                categoria = "methods",
                tipo = None,
                linha = linha,
                parametros = None,
                tipo_retorno = None,
                funcoes = funcoes
            )
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

        if current_token(tokens, current_index)[2] not in tabela_de_simbolos[pilha_escopos[-1]]:
            declarar_simbolo(
                nome = current_token(tokens, current_index)[2],
                categoria = "variables",
                tipo = None,
                linha = current_token(tokens, current_index)[0],
                parametros = None,
                tipo_retorno = []
            )

        current_index = parse_defVar(tokens, current_index)
        current_index = parse_defComeco2(tokens, current_index)
    elif match_token(tokens, current_index, 'PRE', 'methods'):
        nome = current_token(tokens, current_index)[2]
        linha = current_token(tokens, current_index)[0]

        current_index, funcoes = parse_methods(tokens, current_index)
        if nome not in tabela_de_simbolos[pilha_escopos[-1]]:
            declarar_simbolo(
                nome = nome,
                categoria = "methods",
                tipo = None,
                linha = linha,
                parametros = None,
                tipo_retorno = None,
                funcoes = funcoes
            )
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
            current_index, funcoes = parse_listaMetodos(tokens, current_index)
            if match_token(tokens, current_index, 'DEL', '}'):
                current_index = consume_token(tokens, current_index)
    return current_index, funcoes

# <listaMetodos>
def parse_listaMetodos(tokens, current_index):
    funcoes = []
    while current_token(tokens, current_index)[2] in ["int", "string", "float", "boolean", "void"]:  # tipo
        tipo = current_token(tokens, current_index)[2]
        linha = current_token(tokens, current_index)[0]
        current_index = consume_token(tokens, current_index)
        if match_token(tokens, current_index, 'IDE'):
            nome = current_token(tokens, current_index)[2]
            current_index = consume_token(tokens, current_index)
            if match_token(tokens, current_index, 'DEL', '('):
                current_index = consume_token(tokens, current_index)
                current_index, lista = parse_listaParametros(tokens, current_index)
                if match_token(tokens, current_index, 'DEL', ')'):
                    current_index = consume_token(tokens, current_index)
                    if match_token(tokens, current_index, 'DEL', '{'):
                        current_index = consume_token(tokens, current_index)
                        current_index = parse_codigo(tokens, current_index)
                        if match_token(tokens, current_index, 'DEL', '}'):
                            current_index = consume_token(tokens, current_index)
                            metodo = {
                                nome: {
                                'categoria': "método",
                                'tipo': tipo,
                                'linha' : linha,
                                'parametros' : lista,
                                'tipo_retorno' : tipo,
                                'funcoes': []
                                }
                            }
                            
                            funcoes.append(metodo)
        else:
            break
    return current_index, funcoes

# <listaParametros>
def parse_listaParametros(tokens, current_index):
    lista = []

    while current_token(tokens, current_index)[2] in ["int", "string", "float", "boolean"] or match_token(tokens, current_index, "IDE"):
        tipo = current_token(tokens, current_index)[2]
        current_index = consume_token(tokens, current_index)

        if match_token(tokens, current_index, 'IDE'):
            nome = current_token(tokens, current_index)[2]
            current_index = consume_token(tokens, current_index)

            lista.append((tipo, nome))

            if match_token(tokens, current_index, 'DEL', ','):
                current_index = consume_token(tokens, current_index)
            else:
                break  # Sai do loop se não houver vírgula
        else:
            raise SyntaxError("Esperado nome do parâmetro após tipo")

    return current_index, lista

def parse_defConst(tokens, current_index):
    if match_token(tokens, current_index, 'PRE', 'const'):
        current_index = consume_token(tokens, current_index)

    if match_token(tokens, current_index, 'DEL', '{'):
        current_index = consume_token(tokens, current_index)
        current_index = parse_listaConst(tokens, current_index)
        if match_token(tokens, current_index, 'DEL', '}'):
            current_index = consume_token(tokens, current_index)
    return current_index

def parse_defVar(tokens, current_index):
    if match_token(tokens, current_index, 'PRE', 'variables'):
        current_index = consume_token(tokens, current_index)
    
    if match_token(tokens, current_index, 'DEL', '{'):
        current_index = consume_token(tokens, current_index)
        current_index = parse_listaConst(tokens, current_index)
        if match_token(tokens, current_index, 'DEL', '}'):
            current_index = consume_token(tokens, current_index)
        
    return current_index

# <listaConst>
def parse_listaConst(tokens, current_index):
    if current_token(tokens, current_index)[2] in ["int", "float", "string", "boolean"] and match_token(tokens, current_index + 1, "IDE") and match_token(tokens, current_index + 2, "DEL", "["):
        current_index = parse_declVetor(tokens, current_index)
        current_index = parse_listaConst(tokens, current_index)
    elif current_token(tokens, current_index)[2] in ["int", "float", "string", "boolean"]:
        current_index = consume_token(tokens, current_index)
        current_index = parse_listaItens(tokens, current_index)
        if match_token(tokens, current_index, 'DEL', ';'):
            current_index = consume_token(tokens, current_index)
            current_index = parse_listaConst(tokens, current_index)
    elif match_token(tokens, current_index, 'IDE'):
        current_index = consume_token(tokens, current_index)
        current_index = parse_listaItens(tokens, current_index)
        if match_token(tokens, current_index, 'DEL', ';'):
            current_index = consume_token(tokens, current_index)
            current_index = parse_listaConst(tokens, current_index)
    return current_index

# <listaItens>
def parse_listaItens(tokens, current_index):
    if match_token(tokens, current_index, 'IDE'):
        current_index = consume_token(tokens, current_index)
        current_index = parse_possFinal(tokens, current_index)
        current_index = parse_listaItens2(tokens, current_index)
    
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
            if not match_token(tokens, current_index + 4, 'DEL', '['):
                current_index = parse_acessoVetor(tokens, current_index)
            
        elif lookahead == '.':
            current_index = parse_chamadaAtributo(tokens, current_index)
        
    elif match_token(tokens, current_index, 'NRO') or match_token(tokens, current_index, 'CAC') or match_token(tokens, current_index, 'PRE', 'true') or match_token(tokens, current_index, 'PRE', 'false') or match_token(tokens, current_index, 'IDE'):
        current_index = consume_token(tokens, current_index)
    
    return current_index

def parse_declVetor(tokens, current_index):
    if match_token(tokens, current_index, 'PRE'):  # tipo
        current_index = consume_token(tokens, current_index)
        if match_token(tokens, current_index, 'IDE'):
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
    raiz_projeto = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pasta_entrada = os.path.join(raiz_projeto, "files")
    
    resultado_lexico = processar_arquivos()
    for name, lista_tokens in resultado_lexico.items():
        if lista_tokens:
            print(f"Arquivo: {name}")
            current_index = 0
            lista_erros = []
            inicializar_analise()
            current_index = parse_main(lista_tokens, current_index)
            
            caminho_entrada = os.path.join(pasta_entrada, name)
            # Escreve os erros encontrados em um arquivo TXT
            with open(f"{caminho_entrada[:-4]}-saida.txt", "w", encoding="utf-8") as f:
                if lista_erros:
                    f.write("Erro Sintático Encontrado\n")
                    for erro in lista_erros:
                        f.write(f"{erro}\n")
                else:
                    f.write("Análise Sintática concluída com sucesso.\n\n")
                    f.write("Tabela de Símbolos:\n")
                    f.write(json.dumps(tabela_de_simbolos, indent=4, ensure_ascii=False))

if __name__ == '__main__':
    main()