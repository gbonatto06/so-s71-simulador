from enum import Enum

class TaskState(Enum):
    """ Define os possíveis estados de uma tarefa. """
    NOVA = 0      # Recém-criada, aguardando ingresso
    PRONTA = 1    # Na fila de prontos, aguardando CPU
    EXECUTANDO = 2 # Atualmente na CPU
    TERMINADA = 3 # Execução concluída

class TCB:
    """
    Task Control Block (TCB)
    Armazena todas as informações de uma tarefa.
    """
    def __init__(self, id, cor, ingresso, duracao, prioridade):
        # Parâmetros do arquivo de config
        self.id = id
        self.cor = cor
        self.ingresso = int(ingresso)
        self.duracao = int(duracao)
        self.prioridade = int(prioridade)
        # Atributos de estado
        self.estado = TaskState.NOVA
        self.tempo_executado = 0
        self.tempo_espera = 0
        self.quantum_utilizado = 0
        self.tick_conclusao = -1

    def __repr__(self):
        """ Representação textual para debug. """
        return (
            f"TCB(id={self.id}, estado={self.estado.name}, "
            f"exec={self.tempo_executado}/{self.duracao}, "
            f"prio={self.prioridade})"
        )

    def to_debug_str(self):
        """ Retorna string formatada para o debugger"""
        return (
            f"  - {self.id} (Prio: {self.prioridade}):\n"
            f"    Estado: {self.estado.name}\n"
            f"    Progresso: {self.tempo_executado} / {self.duracao}\n"
            f"    Ingresso: {self.ingresso}\n"
            f"    Espera: {self.tempo_espera} ticks"
        )

class Simulator:
    """
    Gerencia o relógio, as tarefas e o escalonador.
    """
    def __init__(self, escalonador, quantum):
        self.relogio_global = 0
        self.quantum = int(quantum)
        self.escalonador = escalonador
        self.tarefas = []              # Lista mestre de todos os TCBs
        self.fila_prontos = []         # Fila de tarefas PRONTAS
        self.tarefa_executando = None
        self.gantt_log = []            # Log para gerar o gráfico
        self.tarefas_concluidas = 0

    def adicionar_tarefa(self, tcb):
        self.tarefas.append(tcb)

    def terminou(self):
        """ Verifica se todas as tarefas foram concluídas """
        return self.tarefas_concluidas == len(self.tarefas)

    def get_debug_info(self):
        """ Retorna o estado atual do sistema para o debugger """
        header = f"--- [TICK: {self.relogio_global}] ---"
        
        exec_task = self.tarefa_executando.id if self.tarefa_executando else "Nenhuma"
        exec_info = f"CPU: [ {exec_task} ]"
        
        prontos = [t.id for t in self.fila_prontos]
        fila_info = f"FILA DE PRONTOS: {prontos}"
        tasks_info = "\nESTADO DAS TAREFAS:\n" + "\n".join(
            [t.to_debug_str() for t in self.tarefas if t.estado != TaskState.NOVA]
        )
        return "\n".join([header, exec_info, fila_info, tasks_info])

    def tick(self):
        """
        Avança um "tick" do relógio global.
        """
        
        log_eventos_tick = f"[Tick {self.relogio_global}]:"
        
        # Verifica ingresso de novas tarefas
        # Tarefas que chegam 'agora' podem competir pela CPU
        for t in self.tarefas:
            if t.estado == TaskState.NOVA and t.ingresso == self.relogio_global:
                t.estado = TaskState.PRONTA
                self.fila_prontos.append(t)
                log_eventos_tick += f" Tarefa {t.id} ingressou;"

        # Atualizar tempos de espera de quem está na fila
        for t in self.fila_prontos:
            t.tempo_espera += 1

        # Verificar estado da tarefa atual (se ela terminou ou foi preemptada)
        preemptar_quantum = False
        tarefa_terminou = False
        
        if self.tarefa_executando:
            t = self.tarefa_executando
            
            # Verificação de Término
            if t.tempo_executado == t.duracao:
                t.estado = TaskState.TERMINADA
                t.tick_conclusao = self.relogio_global # Terminou antes deste tick
                self.tarefas_concluidas += 1
                log_eventos_tick += f" Tarefa {t.id} terminou;"
                self.tarefa_executando = None
                tarefa_terminou = True
            
            # Verificação de Quantum
            elif t.quantum_utilizado == self.quantum:
                preemptar_quantum = True
                log_eventos_tick += f" Tarefa {t.id} sofreu preempção (quantum);"


        # Decisão de Escalonamento
        # (Sempre decide, mas os preemptivos usarão as novas infos da fila)
        proxima_tarefa = self.escalonador.decidir(
            self.fila_prontos, 
            self.tarefa_executando, 
            preemptar_quantum or tarefa_terminou
        )

        # Troca de Contexto
        if proxima_tarefa != self.tarefa_executando:
            
            # Se a tarefa antiga existe e não terminou, devolve para a fila
            t_antigo = self.tarefa_executando
            if t_antigo and not tarefa_terminou:
                t_antigo.estado = TaskState.PRONTA
                t_antigo.quantum_utilizado = 0
                self.fila_prontos.append(t_antigo)
                log_eventos_tick += f" Tarefa {t_antigo.id} voltou para Prontos (preemptada);"
            
            # Nova tarefa assume a CPU
            self.tarefa_executando = proxima_tarefa
            if self.tarefa_executando:
                if self.tarefa_executando in self.fila_prontos:
                     self.fila_prontos.remove(self.tarefa_executando)
                
                self.tarefa_executando.estado = TaskState.EXECUTANDO
                self.tarefa_executando.quantum_utilizado = 0
                log_eventos_tick += f" Escalonador escolheu {self.tarefa_executando.id};"

        # Executar o tick
        # Processa a tarefa que ganhou a CPU para este tick)
        if self.tarefa_executando:
            t = self.tarefa_executando
            t.tempo_executado += 1
            t.quantum_utilizado += 1
            
            # Adiciona ao log do Gantt
            self.gantt_log.append({'tick': self.relogio_global, 'task_id': t.id, 'cor': t.cor})
            log_eventos_tick += f" Tarefa {t.id} executou;"
        else:
            # CPU ociosa
            self.gantt_log.append({'tick': self.relogio_global, 'task_id': 'idle', 'cor': '#FFFFFF'})
            log_eventos_tick += " CPU ociosa;"

        # Avançar o relógio
        self.relogio_global += 1
        return log_eventos_tick
