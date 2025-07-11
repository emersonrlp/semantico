from lexico import processar_arquivos
from sintatico import main_sintatico
import os

raiz_projeto = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
pasta_entrada = os.path.join(raiz_projeto, "files")

resultados_gerais = {}

for nome_arquivo in os.listdir(pasta_entrada):
    if nome_arquivo.endswith(".txt") and not nome_arquivo.endswith("-saida.txt"):
        resultado = processar_arquivos(nome_arquivo)
        print(resultado.values())
        tabela = main_sintatico(nome_arquivo)