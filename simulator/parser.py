from simulator.core import Simulator, TCB
from simulator.schedulers import FIFO, SRTF, PriorityPreemptive

def carregar_configuracao_arquivo(caminho_arquivo):
    """
    Lê o arquivo de configuração e inicializa o Simulador.
    """
    try:
        with open(caminho_arquivo, 'r') as f:
            # Lê todas as linhas, removendo espaços em branco e linhas vazias
            linhas = [linha.strip() for linha in f.readlines() if linha.strip()]
            
        if len(linhas) < 2:
            raise ValueError("Arquivo de configuração deve ter pelo menos 2 linhas (sistema + 1 tarefa).")
            
        # Linha 1: Configurações do Sistema
        linha_sistema = linhas[0].split(';')
        if len(linha_sistema) < 2:
            raise ValueError("Linha de sistema mal formatada. Esperado: algoritmo;quantum")
            
        algoritmo = linha_sistema[0].strip()
        quantum = int(linha_sistema[1].strip())
        
        # Seleciona o escalonador
        if algoritmo.upper() == 'FIFO':
            escalonador = FIFO()
        elif algoritmo.upper() == 'SRTF':
            escalonador = SRTF()
        elif algoritmo.upper() == 'Prioridade'.upper(): # Usamos .upper() para ser flexível
            escalonador = PriorityPreemptive()
        else:
            raise ValueError(f"Algoritmo de escalonamento '{algoritmo}' desconhecido.")
            
        # Cria o Simulador
        simulador = Simulator(escalonador, quantum)
        
        # Linhas 2..N: Tarefas
        for i, linha in enumerate(linhas[1:], start=2):
            partes = linha.strip().split(';')
            
            # Validação básica da linha da tarefa
            # id;cor;ingresso;duracao;prioridade;lista_eventos
            if len(partes) < 5:
                raise ValueError(f"Linha {i} (tarefa) mal formatada. Esperado pelo menos 5 campos.")
                
            tcb = TCB(
                id=partes[0].strip(),
                cor=partes[1].strip(),
                ingresso=partes[2].strip(),
                duracao=partes[3].strip(),
                prioridade=partes[4].strip()
            )
            simulador.adicionar_tarefa(tcb)
            
        print(f"Sistema carregado: {algoritmo}, Quantum={quantum}, Tarefas={len(simulador.tarefas)}")
        return simulador
        
    except FileNotFoundError:
        print(f"Erro: Arquivo '{caminho_arquivo}' não encontrado.")
        return None
    except ValueError as e:
        print(f"Erro de Valor ao processar arquivo (linha ou tipo de dado): {e}")
        return None
    except Exception as e:
        print(f"Erro inesperado ao processar arquivo de configuração: {e}")
        return None
