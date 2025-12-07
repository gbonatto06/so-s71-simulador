from enum import Enum
import copy  # SNAPSHOT

class TaskState(Enum):
    NOVA = 0
    PRONTA = 1
    EXECUTANDO = 2
    TERMINADA = 3
    BLOQUEADA = 4 

class TCB:
    def __init__(self, id, cor, ingresso, duracao, prioridade):
        self.id = id
        self.cor = cor
        self.ingresso = int(ingresso)
        self.duracao = int(duracao)
        self.prioridade = int(prioridade) 
        self.prioridade_dinamica = int(prioridade)
        self.estado = TaskState.NOVA 
        self.tempo_executado = 0
        self.tempo_espera = 0
        self.quantum_utilizado = 0
        self.tick_conclusao = -1
        self.acoes = []

    def __repr__(self):
        return (f"TCB(id={self.id}, pd={self.prioridade_dinamica}, exec={self.tempo_executado}/{self.duracao})")

    def to_debug_str(self):
        return (f"  - {self.id} (Prio Estática: {self.prioridade} | Dinâmica: {self.prioridade_dinamica}):\n"
                f"    Estado: {self.estado.name}\n"
                f"    Progresso: {self.tempo_executado} / {self.duracao}\n"
                f"    Ingresso: {self.ingresso}\n"
                f"    Espera: {self.tempo_espera} ticks")

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
        self.bloqueio_log = []      
        self.io_log = []            
        self.mutex_event_log = [] 
        self.tarefas_concluidas = 0
        self.mutex_estado = {} 
        self.mutex_fila = {}
        self.io_wait = {}           
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

    def get_debug_info(self):
        status_scheduler = "ATIVO" if self.scheduler_called_last_tick else "INATIVO"
        header = f"--- [TICK: {self.relogio_global}] | ESCALONADOR: {status_scheduler} ---"
        log_info = f"EVENTOS DO ÚLTIMO TICK:\n >> {self.ultimo_log}"
        exec_task = self.tarefa_executando.id if self.tarefa_executando else "Nenhuma"
        exec_info = f"CPU: [ {exec_task} ]"
        
        bloq_info = ""
        if self.mutex_fila:
            bloq_str = ", ".join([f"M{k}:{[t.id for t in v]}" for k,v in self.mutex_fila.items() if v])
            if bloq_str: bloq_info = f"\nBLOQUEADOS EM MUTEX: {bloq_str}"
        
        if self.io_wait:
            io_str = ", ".join([f"{tid}({rest}t)" for tid, rest in self.io_wait.items()])
            bloq_info += f"\nEM E/S (WAIT): {io_str}"

        prontos = [t.id for t in self.fila_prontos]
        fila_info = f"FILA DE PRONTOS: {prontos}"
        tasks_info = "\nESTADO DAS TAREFAS:\n" + "\n".join(
            [t.to_debug_str() for t in self.tarefas if t.estado != TaskState.NOVA]
        )
        return "\n".join([header, log_info, exec_info, fila_info + bloq_info, tasks_info])

    # --- Auxiliar para acoes das tarefas ---
    def processar_acoes_da_tarefa(self, t):
        """Processa as ações da tarefa t no tempo atual. Retorna (log_str, bloqueou)."""
        log_acoes = ""
        bloqueou = False
        acoes_agora = [a for a in t.acoes if a['tempo'] == t.tempo_executado]
        
        for acao in acoes_agora:
            tipo = acao['tipo']
            
            if tipo == 'IO':
                duracao_io = acao['duracao_io']
                self.io_wait[t.id] = duracao_io
                t.estado = TaskState.BLOQUEADA
                log_acoes += f" [{t.id} Iniciou E/S ({duracao_io}t)] "
                t.acoes.remove(acao)
                bloqueou = True
                break # Sai, perdeu a CPU

            elif tipo == 'ML': 
                m_id = acao['mutex']
                dono = self.mutex_estado.get(m_id)
                if dono is None:
                    self.mutex_estado[m_id] = t.id
                    log_acoes += f" [Lock M{m_id} Sucesso] "
                    self.mutex_event_log.append({
                        'tick': self.relogio_global, 'task_id': t.id, 'tipo': 'ML', 'mutex': m_id
                    })
                    t.acoes.remove(acao)
                else:
                    log_acoes += f" [Lock M{m_id} FALHA -> Bloqueado] "
                    self.mutex_event_log.append({
                        'tick': self.relogio_global, 'task_id': t.id, 'tipo': 'ML_FAIL', 'mutex': m_id
                    })
                    
                    # Herança
                    dono_id = self.mutex_estado[m_id]
                    t_dono = next((x for x in self.tarefas if x.id == dono_id), None)
                    if t_dono and t.prioridade_dinamica > t_dono.prioridade_dinamica:
                        prio_antiga = t_dono.prioridade_dinamica
                        t_dono.prioridade_dinamica = t.prioridade_dinamica
                        log_acoes += f" [Herança: {t_dono.id} ({prio_antiga}->{t_dono.prioridade_dinamica}) de {t.id}] "

                    t.estado = TaskState.BLOQUEADA
                    if m_id not in self.mutex_fila:
                        self.mutex_fila[m_id] = []
                    self.mutex_fila[m_id].append(t)
                    bloqueou = True
                    break 
                    
            elif tipo == 'MU': 
                m_id = acao['mutex']
                dono = self.mutex_estado.get(m_id)
                if dono == t.id:
                    del self.mutex_estado[m_id]
                    log_acoes += f" [Unlock M{m_id}] "
                    if t.prioridade_dinamica > t.prioridade:
                        t.prioridade_dinamica = t.prioridade
                        log_acoes += f" [Prio Reset: {t.id}] "
                    
                    self.mutex_event_log.append({
                        'tick': self.relogio_global, 'task_id': t.id, 'tipo': 'MU', 'mutex': m_id
                    })
                    t.acoes.remove(acao)
                    if m_id in self.mutex_fila and self.mutex_fila[m_id]:
                        t_acordada = self.mutex_fila[m_id].pop(0)
                        t_acordada.estado = TaskState.PRONTA
                        self.fila_prontos.append(t_acordada)
                        log_acoes += f" [{t_acordada.id} Desbloqueada] "
                else:
                    log_acoes += f" [Erro Unlock M{m_id}: Não é dono] "
                    t.acoes.remove(acao)

        return log_acoes, bloqueou

    def tick(self):
        self.salvar_estado() 
        self.scheduler_called_last_tick = False
        log_eventos_tick = ""
        precisa_escalonar = False

        # 1. Processar Retorno de IO
        tarefas_retornando_io = []
        for tid, tempo_restante in list(self.io_wait.items()):
            self.io_wait[tid] -= 1
            if self.io_wait[tid] <= 0:
                del self.io_wait[tid]
                tarefas_retornando_io.append(tid)
        
        for tid in tarefas_retornando_io:
            t_retorno = next((t for t in self.tarefas if t.id == tid), None)
            if t_retorno:
                t_retorno.estado = TaskState.PRONTA
                self.fila_prontos.append(t_retorno)
                log_eventos_tick += f" [{t_retorno.id} Retornou de E/S] "
                precisa_escalonar = True

        # 2. Ingressos
        for t in self.tarefas:
            if t.estado == TaskState.NOVA and t.ingresso == self.relogio_global:
                t.estado = TaskState.PRONTA
                self.fila_prontos.append(t)
                log_eventos_tick += f" [{t.id} Ingressou] "
                precisa_escalonar = True 

        # Aging
        tem_alpha = hasattr(self.escalonador, 'alpha')
        for t in self.fila_prontos:
            t.tempo_espera += 1
            if tem_alpha:
                t.prioridade_dinamica += self.escalonador.alpha
                if self.tarefa_executando:
                    if t.prioridade_dinamica > self.tarefa_executando.prioridade_dinamica:
                        precisa_escalonar = True
                        log_eventos_tick += f" [Aging: {t.id} > {self.tarefa_executando.id}] "

        preemptar_quantum = False
        tarefa_bloqueou_agora = False
        
        # 3. Processar Ações da Tarefa Atual (INÍCIO DO TICK)
        if self.tarefa_executando:
            t = self.tarefa_executando
            log_acoes, bloqueou = self.processar_acoes_da_tarefa(t)
            log_eventos_tick += log_acoes
            
            if bloqueou:
                self.tarefa_executando = None
                tarefa_bloqueou_agora = True
                precisa_escalonar = True
            else:
                # Verificações de fim de tarefa / quantum
                if t.tempo_executado == t.duracao:
                    t.estado = TaskState.TERMINADA
                    t.tick_conclusao = self.relogio_global 
                    self.tarefas_concluidas += 1
                    log_eventos_tick += f" [{t.id} Terminou] "
                    mutexes_possuidos = [k for k,v in self.mutex_estado.items() if v == t.id]
                    for m_id in mutexes_possuidos:
                        del self.mutex_estado[m_id]
                        if m_id in self.mutex_fila and self.mutex_fila[m_id]:
                            t_acordada = self.mutex_fila[m_id].pop(0)
                            t_acordada.estado = TaskState.PRONTA
                            self.fila_prontos.append(t_acordada)
                            precisa_escalonar = True
                    self.tarefa_executando = None
                    precisa_escalonar = True 
                elif t.quantum_utilizado == self.quantum and self.escalonador.usar_quantum:
                    preemptar_quantum = True 
                    log_eventos_tick += f" [{t.id} Estourou Quantum] "
                    precisa_escalonar = True 

        elif self.fila_prontos:
            precisa_escalonar = True

        # 4. Escalonador
        houve_sorteio = False
        if precisa_escalonar:
            self.scheduler_called_last_tick = True
            proxima_tarefa, houve_sorteio = self.escalonador.decidir(self.fila_prontos, self.tarefa_executando, preemptar_quantum)
            
            if proxima_tarefa and tem_alpha:
                proxima_tarefa.prioridade_dinamica = proxima_tarefa.prioridade
                
            if houve_sorteio: log_eventos_tick += " [SORTEIO] "

            if proxima_tarefa != self.tarefa_executando:
                t_antigo = self.tarefa_executando
                if t_antigo and t_antigo.estado == TaskState.EXECUTANDO:
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

                    # BUG DO TEMPO 0
                    # Se trocamos de tarefa, a nova tarefa (proxima_tarefa) precisa ter suas ações 
                    # do tempo atual (que geralmente é 0) verificadas imediatamente.
                    # Caso contrário, ela só seria verificada no próximo tick com tempo=1.
                    log_acoes_nova, bloqueou_nova = self.processar_acoes_da_tarefa(self.tarefa_executando)
                    log_eventos_tick += log_acoes_nova
                    if bloqueou_nova:
                         self.tarefa_executando = None
                         # Se ela bloqueou logo na entrada, ela não executa neste tick.
                         # O tempo não será incrementado abaixo.
        
        elif self.tarefa_executando and preemptar_quantum:
             self.tarefa_executando.quantum_utilizado = 0
             log_eventos_tick += f" [{self.tarefa_executando.id} Renovou Quantum] "

        # LOGS DE ESTADO (Para o Gantt)
        for t in self.tarefas:
            if t.id in self.io_wait:
                self.io_log.append({'tick': self.relogio_global, 'task_id': t.id})
            elif t.estado == TaskState.BLOQUEADA:
                self.bloqueio_log.append({'tick': self.relogio_global, 'task_id': t.id})

        if self.tarefa_executando:
            t = self.tarefa_executando
            t.tempo_executado += 1
            t.quantum_utilizado += 1 
            self.gantt_log.append({'tick': self.relogio_global, 'task_id': t.id, 'cor': t.cor, 'sorteio': houve_sorteio})
            log_eventos_tick += f" [{t.id} Executou] " 
        else:
            self.gantt_log.append({'tick': self.relogio_global, 'task_id': 'idle', 'cor': '#FFFFFF', 'sorteio': False})
            log_eventos_tick += " [CPU Ociosa] "

        self.relogio_global += 1
        self.ultimo_log = log_eventos_tick
        return log_eventos_tick
