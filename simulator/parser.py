import os
import sys
import importlib.util
import inspect
import re
from simulator.core import Simulator, TCB
from simulator.schedulers import FIFO, SRTF, PriorityPreemptive, RoundRobin, Scheduler

def _normalizar_cor(cor_str):
    """
    Verifica se a cor está no formato Hexadecimal sem '#'
    Se estiver sem, adiciona o '#' para o Matplotlib entender.
    Se for uma cor nomeada (ex: "red") ou já tiver '#', mantém como está.
    """
    cor_limpa = cor_str.strip()
    
    # Regex para verificar se são exatamente 6 caracteres hexadecimais (0-9, A-F)
    if re.fullmatch(r'[0-9A-Fa-f]{6}', cor_limpa):
        return f"#{cor_limpa}"
    
    return cor_limpa

def carregar_plugins(diretorio_plugins="extensions"):
    """
    Varre o diretório e RETORNA os plugins encontrados.
    Não afeta o sistema globalmente, apenas retorna o dicionário.
    """
    plugins = {}
    
    if not os.path.isdir(diretorio_plugins):
        print(f"Aviso: Diretório '{diretorio_plugins}' não encontrado.")
        return plugins

    # Adiciona ao path apenas se ainda não estiver
    abs_path = os.path.abspath(diretorio_plugins)
    if abs_path not in sys.path:
        sys.path.append(abs_path)

    print(f"--- Procurando Plugins em '{diretorio_plugins}' ---")
    
    for arquivo in os.listdir(diretorio_plugins):
        if arquivo.endswith(".py") and arquivo != "__init__.py":
            caminho_completo = os.path.join(diretorio_plugins, arquivo)
            nome_modulo = arquivo[:-3] 
            
            try:
                spec = importlib.util.spec_from_file_location(nome_modulo, caminho_completo)
                if spec and spec.loader:
                    modulo = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(modulo)
                    
                    for nome, obj in inspect.getmembers(modulo, inspect.isclass):
                        if issubclass(obj, Scheduler) and obj is not Scheduler:
                            print(f" -> Plugin Carregado: {nome}")
                            plugins[nome.upper()] = obj
            except Exception as e:
                print(f" -> Erro ao carregar plugin '{arquivo}': {e}")
                
    print("-----------------------------------------------")
    return plugins

def obter_escalonador(algoritmo_nome, quantum, plugins_externos=None):
    """
    Decide qual classe instanciar. 
    Agora aceita um dicionário opcional de plugins_externos.
    """
    algoritmo_upper = algoritmo_nome.upper()
    
    # 1. Verifica nos PLUGINS PASSADOS (Se houver)
    if plugins_externos and algoritmo_upper in plugins_externos:
        print(f"Usando escalonador via Plugin: {algoritmo_upper}")
        return plugins_externos[algoritmo_upper]()

    # 2. Verifica NATIVOS
    if algoritmo_upper == 'FIFO':
        if quantum > 0:
            print(f"Nota: FIFO com Quantum {quantum} -> Ativando Round Robin.")
            return RoundRobin()
        return FIFO()

    elif algoritmo_upper == 'SRTF':
        return SRTF()

    elif algoritmo_upper == 'PRIORIDADEP': 
        return PriorityPreemptive()

    elif algoritmo_upper in ['RR', 'ROUNDROBIN']:
        return RoundRobin()

    # 3. Falha
    return None

def carregar_configuracao_arquivo(caminho_arquivo, plugins_externos=None):
    """
    Lê o arquivo de configuração.
    Agora aceita o argumento 'plugins_externos' para passar para o factory.
    """
    try:
        with open(caminho_arquivo, 'r') as f:
            linhas = [linha.strip() for linha in f.readlines() if linha.strip()]
            
        if len(linhas) < 2:
            raise ValueError("Arquivo de configuração deve ter pelo menos 2 linhas.")
            
        # Linha 1: Configurações do Sistema
        linha_sistema = linhas[0].split(';')
        if len(linha_sistema) < 2:
            raise ValueError("Linha de sistema mal formatada.")
            
        algoritmo_nome = linha_sistema[0].strip()
        
        # Conversão segura de quantum
        try:
            quantum = int(linha_sistema[1].strip())
        except ValueError:
            raise ValueError(f"Quantum inválido: {linha_sistema[1]}")
        
        # Busca o escalonador
        escalonador = obter_escalonador(algoritmo_nome, quantum, plugins_externos)
        
        if escalonador is None:
            msg = f"Algoritmo '{algoritmo_nome}' não encontrado."
            if not plugins_externos:
                msg += " (Nenhum plugin foi carregado. Use a opção de carregar plugins no menu se este for um algoritmo externo)."
            raise ValueError(msg)
        
        # Inicializa o Simulador
        simulador = Simulator(escalonador, quantum)
        simulador.nome_algoritmo_config = algoritmo_nome

        # Linhas 2..N: Tarefas
        for i, linha in enumerate(linhas[1:], start=2):
            partes = linha.strip().split(';')
            if len(partes) < 5:
                raise ValueError(f"Linha {i} mal formatada.")
            
            # Tratamento da COR
            cor_processada = _normalizar_cor(partes[1])

            # Criação do TCB com conversão de tipos
            # Isso é crucial para que o algoritmo consiga somar/subtrair tempos
            try:
                tcb = TCB(
                    id=partes[0].strip(),
                    cor=cor_processada,       # Cor normalizada, aceita com # e sem
                    ingresso=int(partes[2]),  # Int
                    duracao=int(partes[3]),   # Int
                    prioridade=int(partes[4]) # Int
                )
                simulador.adicionar_tarefa(tcb)
            except ValueError as ve:
                raise ValueError(f"Erro de conversão numérica na linha {i}: {ve}")
            
        print(f"Sistema carregado: {algoritmo_nome}, Quantum={quantum}, Tarefas={len(simulador.tarefas)}")
        return simulador
        
    except FileNotFoundError:
        print(f"Erro: Arquivo '{caminho_arquivo}' não encontrado.")
        return None
    except ValueError as e:
        print(f"Erro de Valor: {e}")
        return None
    except Exception as e:
        print(f"Erro inesperado: {e}")
        return None
