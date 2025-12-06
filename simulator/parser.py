import os
import sys
import importlib.util
import inspect
import re
from simulator.core import Simulator, TCB
from simulator.schedulers import FIFO, SRTF, PriorityPreemptive, PriorityAging, RoundRobin, Scheduler

def _normalizar_cor(cor_str):
    cor_limpa = cor_str.strip()
    if re.fullmatch(r'[0-9A-Fa-f]{6}', cor_limpa):
        return f"#{cor_limpa}"
    return cor_limpa

def carregar_plugins(diretorio_plugins="extensions"):
    plugins = {}
    if not os.path.isdir(diretorio_plugins): return plugins
    abs_path = os.path.abspath(diretorio_plugins)
    if abs_path not in sys.path: sys.path.append(abs_path)

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
                            plugins[nome.upper()] = obj
            except Exception: pass
    return plugins

def obter_escalonador(algoritmo_nome, quantum, alpha=0, plugins_externos=None):
    algoritmo_upper = algoritmo_nome.upper()
    
    if plugins_externos and algoritmo_upper in plugins_externos:
        cls = plugins_externos[algoritmo_upper]
        try: return cls(alpha)
        except TypeError: return cls()

    if algoritmo_upper == 'FIFO':
        return RoundRobin() if quantum > 0 else FIFO()
    elif algoritmo_upper == 'SRTF':
        return SRTF()
    elif algoritmo_upper == 'PRIORIDADEP': 
        return PriorityPreemptive()
    elif algoritmo_upper == 'PRIOPENV':
        return PriorityAging(alpha)
    elif algoritmo_upper in ['RR', 'ROUNDROBIN']:
        return RoundRobin()
    return None

def carregar_configuracao_arquivo(caminho_arquivo, plugins_externos=None):
    try:
        with open(caminho_arquivo, 'r') as f:
            linhas = [linha.strip() for linha in f.readlines() if linha.strip()]
        if len(linhas) < 2: raise ValueError("Arquivo inválido.")
            
        linha_sistema = linhas[0].split(';')
        algoritmo_nome = linha_sistema[0].strip()
        quantum = int(linha_sistema[1].strip())
        
        alpha = 0
        if len(linha_sistema) >= 3:
            try: alpha = int(linha_sistema[2].strip())
            except ValueError: alpha = 0
        
        escalonador = obter_escalonador(algoritmo_nome, quantum, alpha, plugins_externos)
        if not escalonador: raise ValueError(f"Algoritmo '{algoritmo_nome}' desconhecido.")
        
        simulador = Simulator(escalonador, quantum)
        simulador.nome_algoritmo_config = algoritmo_nome
        if algoritmo_nome.upper() == 'PRIOPENV':
             simulador.nome_algoritmo_config += f" (Alpha={alpha})"

        for i, linha in enumerate(linhas[1:], start=2):
            partes = linha.strip().split(';')
            if len(partes) < 5: raise ValueError(f"Linha {i} mal formatada.")
            
            tcb = TCB(
                partes[0].strip(), 
                _normalizar_cor(partes[1]), 
                int(partes[2]), 
                int(partes[3]), 
                int(partes[4])
            )
            
            # Parsing de acoes do mutex
            # As ações vêm após a prioridade (índice 5 em diante)
            if len(partes) > 5:
                acoes_cruas = partes[5:]
                acoes_parseadas = []
                for item in acoes_cruas:
                    item = item.strip()
                    if not item: continue
                    
                    # Esperado: MLxx:tt ou MUxx:tt
                    try:
                        tipo = item[:2].upper() # ML ou MU
                        resto = item[2:].split(':')
                        mutex_id = int(resto[0])
                        tempo = int(resto[1])
                        
                        if tipo not in ['ML', 'MU']:
                            print(f"Aviso: Ação desconhecida '{item}' na linha {i}. Ignorada.")
                            continue
                            
                        acoes_parseadas.append({
                            'tipo': tipo,
                            'mutex': mutex_id,
                            'tempo': tempo
                        })
                    except (ValueError, IndexError):
                        print(f"Aviso: Formato inválido de ação '{item}' na linha {i}. Ignorada.")
                
                # Mesmos tempos -> ordem do arquivo.
                # O sort do Python é estável, então se ordenarmos por tempo, 
                # a ordem relativa de tempos iguais se mantém.
                acoes_parseadas.sort(key=lambda x: x['tempo'])
                tcb.acoes = acoes_parseadas

            simulador.adicionar_tarefa(tcb)
            
        print(f"Sistema: {algoritmo_nome}, Q={quantum}, Alpha={alpha}, Tasks={len(simulador.tarefas)}")
        return simulador
    except Exception as e:
        print(f"Erro: {e}")
        return None
