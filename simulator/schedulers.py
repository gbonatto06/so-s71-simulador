import random
from abc import ABC, abstractmethod
from simulator.core import TaskState

class Scheduler(ABC):
    """
    Interface abstrata para todos os escalonadores.
    """
    @property
    def usar_quantum(self):
        """
        Define se este algoritmo deve respeitar o limite de Quantum.
        Padrão: False (para FIFO, SRTF, Prioridade, etc).
        """
        return False

    @abstractmethod
    def decidir(self, fila_prontos, tarefa_atual, mudanca_contexto_obrigatoria):
        pass

def _escolher_com_desempate(candidatos, tarefa_atual, func_metrica_primaria):
    """
    Função Helper que aplica as regras de desempate globais.
    """
    if not candidatos:
        return None, False

    lista_pontuada = []
    
    for t in candidatos:
        metrica = func_metrica_primaria(t)
        nao_eh_atual = 0 if (tarefa_atual and t.id == tarefa_atual.id) else 1
        ingresso = t.ingresso
        duracao = t.duracao
        fator_sorte = random.random()
        
        score = (metrica, nao_eh_atual, ingresso, duracao, fator_sorte)
        lista_pontuada.append((score, t))
    
    lista_pontuada.sort(key=lambda x: x[0])
    
    vencedor = lista_pontuada[0][1]
    score_vencedor = lista_pontuada[0][0]
    
    houve_sorteio = False
    if len(lista_pontuada) > 1:
        score_vice = lista_pontuada[1][0]
        if score_vencedor[:-1] == score_vice[:-1]:
            houve_sorteio = True
            
    return vencedor, houve_sorteio

class FIFO(Scheduler):
    def decidir(self, fila_prontos, tarefa_atual, mudanca_contexto_obrigatoria):
        if tarefa_atual: return tarefa_atual, False
        if not fila_prontos: return None, False
        return _escolher_com_desempate(fila_prontos, None, lambda t: t.ingresso)

class SRTF(Scheduler):
    def decidir(self, fila_prontos, tarefa_atual, mudanca_contexto_obrigatoria):
        candidatos = list(fila_prontos)
        if tarefa_atual and tarefa_atual.estado == TaskState.EXECUTANDO:
            candidatos.append(tarefa_atual)
        return _escolher_com_desempate(candidatos, tarefa_atual, lambda t: (t.duracao - t.tempo_executado))

class PriorityPreemptive(Scheduler):
    def decidir(self, fila_prontos, tarefa_atual, mudanca_contexto_obrigatoria):
        candidatos = list(fila_prontos)
        if tarefa_atual and tarefa_atual.estado == TaskState.EXECUTANDO:
            candidatos.append(tarefa_atual)
        
        # Usar Prioridade Dinâmica
        # Isso permite que a Herança de Prioridade feita no Core tenha efeito.
        # Se não houver herança nem aging, a dinâmica é igual à estática, então não quebra nada.
        return _escolher_com_desempate(candidatos, tarefa_atual, lambda t: -t.prioridade_dinamica)

class PriorityAging(Scheduler):
    def __init__(self, alpha):
        self.alpha = int(alpha)

    def decidir(self, fila_prontos, tarefa_atual, mudanca_contexto_obrigatoria):
        candidatos = list(fila_prontos)
        if tarefa_atual and tarefa_atual.estado == TaskState.EXECUTANDO:
            candidatos.append(tarefa_atual)
        
        def calcular_metricas(t):
            p_dinamica = t.prioridade_dinamica
            p_estatica = t.prioridade
            return (-p_dinamica, -p_estatica)

        return _escolher_com_desempate(candidatos, tarefa_atual, calcular_metricas)

class RoundRobin(Scheduler):
    
    @property
    def usar_quantum(self):
        """ Apenas o Round Robin utiliza preempção por tempo (Quantum). """
        return True

    def decidir(self, fila_prontos, tarefa_atual, mudanca_contexto_obrigatoria):
        if tarefa_atual and not mudanca_contexto_obrigatoria:
            return tarefa_atual, False
        if not fila_prontos:
            if tarefa_atual and tarefa_atual.estado == TaskState.EXECUTANDO:
                return tarefa_atual, False
            return None, False
        return _escolher_com_desempate(fila_prontos, None, lambda t: t.ingresso)
