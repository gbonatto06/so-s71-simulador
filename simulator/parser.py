import os
import sys
import importlib.util
import inspect
import re
import matplotlib.colors as mcolors
from simulator.core import Simulator, TCB
from simulator.schedulers import FIFO, SRTF, PriorityPreemptive, PriorityAging, RoundRobin, Scheduler

def _normalizar_cor(cor_str):
    cor_limpa = cor_str.strip()
    
    # 1. Se for Hexadecimal sem '#', adiciona
    if re.fullmatch(r'[0-9A-Fa-f]{6}', cor_limpa):
        cor_limpa = f"#{cor_limpa}"
    
    # 2. Validação, o Matplotlib consegue desenhar isso?
    # Isso barra "azul", "vermelho", strings aleatórias, etc.
    if not mcolors.is_color_like(cor_limpa):
        raise ValueError(f"Cor '{cor_str}' inválida. Use HEX (#RRGGBB) ou nomes em Inglês (red, blue, etc).")
        
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
            
            # O _normalizar_cor agora lança exceção se a cor for inválida
            # Isso será capturado pelo 'except Exception as e' abaixo
            tcb = TCB(
                partes[0].strip(), 
                _normalizar_cor(partes[1]), 
                int(partes[2]), 
                int(partes[3]), 
                int(partes[4])
            )
            
            # Parsing de acoes (Mutex e IO)
            if len(partes) > 5:
                acoes_cruas = partes[5:]
                acoes_parseadas = []
                for item in acoes_cruas:
                    item = item.strip()
                    if not item: continue
                    
                    try:
                        # Verifica se é I/O
                        if item.startswith("IO:"):
                            # Formato IO:xx-yy
                            resto = item[3:].split('-') # xx, yy
                            inicio_io = int(resto[0])
                            duracao_io = int(resto[1])
                            
                            # Validação de tempo e Duração Mínima
                            if inicio_io >= tcb.duracao:
                                raise ValueError(f"Tempo da E/S {item} ({inicio_io}) excede duração da tarefa.")
                            
                            if duracao_io < 1:
                                raise ValueError(f"Duração da E/S {item} deve ser no mínimo 1 (Req 3.4).")

                            acoes_parseadas.append({
                                'tipo': 'IO',
                                'tempo': inicio_io,
                                'duracao_io': duracao_io,
                                'ordem_original': len(acoes_parseadas) # Auxiliar para estabilidade (Req 3.5)
                            })

                        else:
                            # Processamento padrão Mutex (ML/MU)
                            tipo = item[:2].upper() 
                            resto = item[2:].split(':')
                            mutex_id = int(resto[0])
                            tempo = int(resto[1])
                            
                            if tipo not in ['ML', 'MU']:
                                print(f"Aviso: Ação desconhecida '{item}' na linha {i}. Ignorada.")
                                continue
                            
                            if tempo >= tcb.duracao:
                                raise ValueError(f"Tempo da ação {item} ({tempo}) excede duração da tarefa.")

                            acoes_parseadas.append({
                                'tipo': tipo,
                                'mutex': mutex_id,
                                'tempo': tempo,
                                'ordem_original': len(acoes_parseadas) # Auxiliar para estabilidade
                            })

                    except (ValueError, IndexError) as e:
                        if "excede duração" in str(e) or "Req 3.4" in str(e):
                            raise e 
                        print(f"Aviso: Formato inválido de ação '{item}' na linha {i}. Ignorada.")
                
                # Ordenação estável.
                # Primeiro por tempo, depois pela ordem original de aparição na linha.
                acoes_parseadas.sort(key=lambda x: (x['tempo'], x['ordem_original']))
                
                # Removemos a chave auxiliar para não sujar o objeto TCB
                for acao in acoes_parseadas:
                    del acao['ordem_original']

                tcb.acoes = acoes_parseadas

            simulador.adicionar_tarefa(tcb)
            
        print(f"Sistema: {algoritmo_nome}, Q={quantum}, Alpha={alpha}, Tasks={len(simulador.tarefas)}")
        return simulador
    except Exception as e:
        print(f"Erro: {e}")
        return None
