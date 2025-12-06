import os
import sys
import importlib.util
import inspect
import re
from simulator.core import Simulator, TCB
from simulator.schedulers import FIFO, SRTF, PriorityPreemptive, PriorityAging, RoundRobin, Scheduler

def _normalizar_cor(cor_str):
    """
    Verifica se a cor está no formato Hexadecimal sem '#'
    Se estiver sem, adiciona o '#' para o Matplotlib entender.
    """
    cor_limpa = cor_str.strip()
    if re.fullmatch(r'[0-9A-Fa-f]{6}', cor_limpa):
        return f"#{cor_limpa}"
    return cor_limpa

def carregar_plugins(diretorio_plugins="extensions"):
    """
    Varre o diretório e RETORNA os plugins encontrados.
    """
    plugins = {}
    
    if not os.path.isdir(diretorio_plugins):
        print(f"Aviso: Diretório '{diretorio_plugins}' não encontrado.")
        return plugins

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

def obter_escalonador(algoritmo_nome, quantum, alpha=0, plugins_externos=None):
    """
    Decide qual classe instanciar. 
    Agora aceita 'alpha' para escalonadores com envelhecimento.
    """
    algoritmo_upper = algoritmo_nome.upper()
    
    # 1. Verifica nos PLUGINS PASSADOS
    if plugins_externos and algoritmo_upper in plugins_externos:
        print(f"Usando escalonador via Plugin: {algoritmo_upper}")
        cls = plugins_externos[algoritmo_upper]
        
        # Tenta instanciar passando 'alpha'. Se o plugin não aceitar args, tenta sem.
        try:
            return cls(alpha)
        except TypeError:
            return cls()

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
    
    # Prioridade com Envelhecimento
    elif algoritmo_upper == 'PRIOPENV':
        return PriorityAging(alpha)

    elif algoritmo_upper in ['RR', 'ROUNDROBIN']:
        return RoundRobin()

    # 3. Falha
    return None

def carregar_configuracao_arquivo(caminho_arquivo, plugins_externos=None):
    """
    Lê o arquivo de configuração.
    Lê ALGORITMO, QUANTUM e o opcional ALPHA.
    """
    try:
        with open(caminho_arquivo, 'r') as f:
            linhas = [linha.strip() for linha in f.readlines() if linha.strip()]
            
        if len(linhas) < 2:
            raise ValueError("Arquivo de configuração deve ter pelo menos 2 linhas.")
            
        # Linha 1: Configurações do Sistema (ALGO;QUANTUM;ALPHA)
        linha_sistema = linhas[0].split(';')
        if len(linha_sistema) < 2:
            raise ValueError("Linha de sistema mal formatada (Requer: ALGO;QUANTUM).")
            
        algoritmo_nome = linha_sistema[0].strip()
        
        try:
            quantum = int(linha_sistema[1].strip())
        except ValueError:
            raise ValueError(f"Quantum inválido: {linha_sistema[1]}")
            
        # Leitura do Alpha (Opcional, padrão 0)
        alpha = 0
        if len(linha_sistema) >= 3:
            try:
                alpha = int(linha_sistema[2].strip())
            except ValueError:
                print(f"Aviso: Alpha '{linha_sistema[2]}' inválido. Usando 0.")
                alpha = 0
        
        # Busca o escalonador passando o alpha
        escalonador = obter_escalonador(algoritmo_nome, quantum, alpha, plugins_externos)
        
        if escalonador is None:
            msg = f"Algoritmo '{algoritmo_nome}' não encontrado."
            if not plugins_externos:
                msg += " (Plugins não carregados)."
            raise ValueError(msg)
        
        # Inicializa o Simulador
        simulador = Simulator(escalonador, quantum)
        simulador.nome_algoritmo_config = algoritmo_nome
        # Se for o algoritmo novo, adiciona info do alpha no nome para o gráfico
        if algoritmo_nome.upper() == 'PRIOPENV':
             simulador.nome_algoritmo_config += f" (Alpha={alpha})"

        # Linhas 2..N: Tarefas
        for i, linha in enumerate(linhas[1:], start=2):
            partes = linha.strip().split(';')
            if len(partes) < 5:
                raise ValueError(f"Linha {i} mal formatada.")
            
            cor_processada = _normalizar_cor(partes[1])

            try:
                tcb = TCB(
                    id=partes[0].strip(),
                    cor=cor_processada,       
                    ingresso=int(partes[2]),  
                    duracao=int(partes[3]),   
                    prioridade=int(partes[4]) 
                )
                simulador.adicionar_tarefa(tcb)
            except ValueError as ve:
                raise ValueError(f"Erro de conversão numérica na linha {i}: {ve}")
            
        print(f"Sistema carregado: {algoritmo_nome}, Quantum={quantum}, Alpha={alpha}, Tarefas={len(simulador.tarefas)}")
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
