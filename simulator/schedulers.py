from abc import ABC, abstractmethod
from simulator.core import TaskState
# ABC (Abstract Base Class) nos permite criar uma interface
# Isso garante que todo escalonador tenha o método 'decidir'
class Scheduler(ABC):
    """
    Interface abstrata para todos os escalonadores.
    """
    @abstractmethod
    def decidir(self, fila_prontos, tarefa_atual, mudanca_contexto_obrigatoria):
        """
        Decide qual tarefa deve ser executada no próximo tick.
        Retorna a TCB da tarefa escolhida ou None se a fila estiver vazia.
        """
        pass

class FIFO(Scheduler):
    """ 
    Escalonador First-In, First-Out. 
    Ele só toma uma decisão se a tarefa atual terminar ou o quantum estourar.
    """
    def decidir(self, fila_prontos, tarefa_atual, mudanca_contexto_obrigatoria):
        # FIFO não é preemptivo, então se a tarefa atual existe e não 
        # terminou ou sofreu quantum, ela continua.
        if tarefa_atual and not mudanca_contexto_obrigatoria:
            return tarefa_atual
        
        # Se a CPU está livre e há tarefas na fila:
        if fila_prontos:
            # Encontra a tarefa que está esperando há mais tempo
            # (maior tempo_espera == chegou primeiro na fila)
            tarefa_escolhida = max(fila_prontos, key=lambda t: t.tempo_espera)
            return tarefa_escolhida
        
        # Se a fila está vazia e a tarefa atual terminou, não retorna nada
        return None

class SRTF(Scheduler):
    """ 
    Shortest Remaining Time First (Preemptivo). 
    A cada tick, ele verifica se há uma tarefa com tempo restante menor.
    """
    def decidir(self, fila_prontos, tarefa_atual, mudanca_contexto_obrigatoria):
        # Sendo preemptivo, ele reconsidera a decisão a cada tick.
        
        # Lista de todos os candidatos (quem está na fila + quem está executando)
        candidatos = list(fila_prontos)
        if tarefa_atual:
            # Garante que a tarefa atual só é re-adicionada se não terminou
            if tarefa_atual.estado == TaskState.EXECUTANDO:
                candidatos.append(tarefa_atual)
        
        if not candidatos:
            return None # Ninguém para executar
            
        # Função para calcular o tempo restante
        def tempo_restante(t):
            return t.duracao - t.tempo_executado
            
        # Ordena pelo tempo restante (o menor primeiro)
        candidatos.sort(key=tempo_restante)
        
        # Retorna o que tem o menor tempo restante
        return candidatos[0] 

class PriorityPreemptive(Scheduler):
    """ 
    Prioridade Preemptivo. 
    A cada tick, verifica se há alguém mais prioritário.
    (Assumimos que número MAIOR = MAIOR prioridade)
    """
    def decidir(self, fila_prontos, tarefa_atual, mudanca_contexto_obrigatoria):
        
        candidatos = list(fila_prontos)
        if tarefa_atual:
            # Garante que a tarefa atual só é re-adicionada se não terminou
            if tarefa_atual.estado == TaskState.EXECUTANDO:
                candidatos.append(tarefa_atual)

        if not candidatos:
            return None # Ninguém para executar
        
        # Ordena pela prioridade, com 'reverse=True'
        # Assim, o número maior fica em primeiro.
        candidatos.sort(key=lambda t: t.prioridade, reverse=True)
        
        # Retorna o de maior prioridade
        return candidatos[0]
