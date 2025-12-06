from enum import Enum
import copy  #SNAPSHOT

class TaskState(Enum):
    """ Define os possíveis estados de uma tarefa. """
    NOVA = 0      # Recém-criada, aguardando ingresso
    PRONTA = 1    # Na fila de prontos, aguardando CPU
    EXECUTANDO = 2 # Atualmente na CPU
    TERMINADA = 3 # Execução concluída

class TCB:
    """
    Task Control Block (TCB)
    """
    def __init__(self, id, cor, ingresso, duracao, prioridade):
        self.id = id
        self.cor = cor
        self.ingresso = int(ingresso)
        self.duracao = int(duracao)
        self.prioridade = int(prioridade) # Prioridade Estática
        self.prioridade_dinamica = int(prioridade) # Dinâmica (Aging)
        
        self.estado = TaskState.NOVA 
        self.tempo_executado = 0
        self.tempo_espera = 0
        self.quantum_utilizado = 0
        self.tick_conclusao = -1

    def __repr__(self):
        return (
            f"TCB(id={self.id}, pd={self.prioridade_dinamica}, "
            f"exec={self.tempo_executado}/{self.duracao})"
        )

    def to_debug_str(self):
        return (
            f"  - {self.id} (Prio Estática: {self.prioridade} | Dinâmica: {self.prioridade_dinamica}):\n"
            f"    Estado: {self.estado.name}\n"
            f"    Progresso: {self.tempo_executado} / {self.duracao}\n"
            f"    Ingresso: {self.ingresso}\n"
            f"    Espera: {self.tempo_espera} ticks"
        )

class Simulator:
    def __init__(self, escalonador, quantum):
        self.relogio_global = 0
        self.quantum = int(quantum)
        self.escalonador = escalonador
        self.nome_algoritmo_config = "Desconhecido"
        self.tarefas = []
        self.fila_prontos = []
        self.tarefa_executando = None
        self.gantt_log = []
        self.tarefas_concluidas = 0
        
        self.historico = []
        self.scheduler_called_last_tick = False
        self.ultimo_log = "Simulação Iniciada."

    def adicionar_tarefa(self, tcb):
        for t in self.tarefas:
            if t.id == tcb.id: return False 
        self.tarefas.append(tcb)
        return True

    def terminou(self):
        return self.tarefas_concluidas == len(self.tarefas)

    # Undo
    def salvar_estado(self):
        historico_temp = self.historico
        self.historico = [] 
        snapshot = copy.deepcopy(self)
        self.historico = historico_temp
        self.historico.append(snapshot)

    def voltar_tick(self):
        if not self.historico: return False
        ultimo_estado = self.historico.pop()
        historico_atual = self.historico
        self.__dict__.update(ultimo_estado.__dict__)
        self.historico = historico_atual
        return True

    # --------------------------------------------------

    def get_debug_info(self):
        status_scheduler = "ATIVO" if self.scheduler_called_last_tick else "INATIVO"
        header = f"--- [TICK: {self.relogio_global}] | ESCALONADOR: {status_scheduler} ---"
        log_info = f"EVENTOS DO ÚLTIMO TICK:\n >> {self.ultimo_log}"
        exec_task = self.tarefa_executando.id if self.tarefa_executando else "Nenhuma"
        exec_info = f"CPU: [ {exec_task} ]"
        prontos = [t.id for t in self.fila_prontos]
        fila_info = f"FILA DE PRONTOS: {prontos}"
        tasks_info = "\nESTADO DAS TAREFAS:\n" + "\n".join(
            [t.to_debug_str() for t in self.tarefas if t.estado != TaskState.NOVA]
        )
        return "\n".join([header, log_info, exec_info, fila_info, tasks_info])

    def tick(self):
        self.salvar_estado() 
        self.scheduler_called_last_tick = False
        log_eventos_tick = ""
        precisa_escalonar = False

        # Verifica ingresso
        for t in self.tarefas:
            if t.estado == TaskState.NOVA and t.ingresso == self.relogio_global:
                t.estado = TaskState.PRONTA
                self.fila_prontos.append(t)
                log_eventos_tick += f" [{t.id} Ingressou] "
                precisa_escalonar = True 

        # Atualizar tempos de espera e Envelhecimento
        tem_alpha = hasattr(self.escalonador, 'alpha')
        
        for t in self.fila_prontos:
            t.tempo_espera += 1
            if tem_alpha:
                t.prioridade_dinamica += self.escalonador.alpha
                if self.tarefa_executando:
                    if t.prioridade_dinamica > self.tarefa_executando.prioridade_dinamica:
                        precisa_escalonar = True
                        log_eventos_tick += f" [Aging: {t.id}({t.prioridade_dinamica}) > {self.tarefa_executando.id}({self.tarefa_executando.prioridade_dinamica})] "

        # Verificar estado da tarefa atual
        preemptar_quantum = False
        tarefa_terminou = False
        
        if self.tarefa_executando:
            t = self.tarefa_executando
            if t.tempo_executado == t.duracao:
                t.estado = TaskState.TERMINADA
                t.tick_conclusao = self.relogio_global 
                self.tarefas_concluidas += 1
                log_eventos_tick += f" [{t.id} Terminou] "
                self.tarefa_executando = None
                tarefa_terminou = True 
                precisa_escalonar = True 
            
            # Verifica se o algoritmo usa quantum
            elif t.quantum_utilizado == self.quantum and self.escalonador.usar_quantum:
                preemptar_quantum = True 
                log_eventos_tick += f" [{t.id} Estourou Quantum] "
                precisa_escalonar = True 

        elif self.fila_prontos:
            precisa_escalonar = True

        # Decisão de Escalonamento
        houve_sorteio = False
        if precisa_escalonar:
            self.scheduler_called_last_tick = True
            
            proxima_tarefa, houve_sorteio = self.escalonador.decidir(
                self.fila_prontos, 
                self.tarefa_executando, 
                preemptar_quantum or tarefa_terminou 
            )

            # Rejuvenescimento (Aging)
            if proxima_tarefa and tem_alpha:
                proxima_tarefa.prioridade_dinamica = proxima_tarefa.prioridade
                
            if houve_sorteio:
                log_eventos_tick += " [SORTEIO] "

            if proxima_tarefa != self.tarefa_executando:
                t_antigo = self.tarefa_executando
                if t_antigo and not tarefa_terminou:
                    t_antigo.estado = TaskState.PRONTA
                    t_antigo.quantum_utilizado = 0     
                    self.fila_prontos.append(t_antigo)
                    log_eventos_tick += f" [{t_antigo.id} -> Prontos] "
                
                self.tarefa_executando = proxima_tarefa
                if self.tarefa_executando: 
                    if self.tarefa_executando in self.fila_prontos:
                         self.fila_prontos.remove(self.tarefa_executando)
                    
                    self.tarefa_executando.estado = TaskState.EXECUTANDO
                    self.tarefa_executando.quantum_utilizado = 0
                    log_eventos_tick += f" [Escalonador escolheu {self.tarefa_executando.id}] "
        
        elif self.tarefa_executando and preemptar_quantum:
             self.tarefa_executando.quantum_utilizado = 0
             log_eventos_tick += f" [{self.tarefa_executando.id} Renovou Quantum] "

        # Executar
        if self.tarefa_executando:
            t = self.tarefa_executando
            t.tempo_executado += 1
            t.quantum_utilizado += 1 
            
            self.gantt_log.append({
                'tick': self.relogio_global, 
                'task_id': t.id, 
                'cor': t.cor,
                'sorteio': houve_sorteio
            })
            log_eventos_tick += f" [{t.id} Executou] " 
        else:
            self.gantt_log.append({
                'tick': self.relogio_global, 
                'task_id': 'idle', 
                'cor': '#FFFFFF',
                'sorteio': False
            })
            log_eventos_tick += " [CPU Ociosa] "

        self.relogio_global += 1
        self.ultimo_log = log_eventos_tick
        return log_eventos_tick
