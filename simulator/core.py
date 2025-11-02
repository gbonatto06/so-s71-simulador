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
        # Parâmetros do arquivo de config que sao lidos pelo parser.py
        self.id = id
        self.cor = cor
        self.ingresso = int(ingresso)
        self.duracao = int(duracao)
        self.prioridade = int(prioridade)
        # Atributos de estado
        self.estado = TaskState.NOVA #
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
        """ Retorna string formatada para o debugger passo a passo
	com as informacoes da tarefa armazenada na TCB e os atributos
	de estado
	"""
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
        self.relogio_global = 0		#inicia um novo relogio global
        self.quantum = int(quantum)	#quantum enviado pelo parser do config.txt
        self.escalonador = escalonador	#definido o escalonador eviado pelo parser.py
        self.nome_algoritmo_config = "Desconhecido"  #Usado para imprimir o nome do algoritmo no grafico de gantt
        self.tarefas = []              # Lista mestre de todos os TCBs
        self.fila_prontos = []         # Fila de tarefas PRONTAS
        self.tarefa_executando = None  #a cpu comeca vazia
        self.gantt_log = []            # Log para gerar o gráfico
        self.tarefas_concluidas = 0

    def adicionar_tarefa(self, tcb):
        self.tarefas.append(tcb)     #adiciona a tarefa na lista de tarefas do sim.

    def terminou(self):
        """ Verifica se todas as tarefas foram concluídas observando a
	    lista de tarefas
	"""
        return self.tarefas_concluidas == len(self.tarefas)

    def get_debug_info(self):
        """ Retorna o estado atual do sistema para o debugger 
	apresentado no modo passo a passo
	"""
        header = f"--- [TICK: {self.relogio_global}] ---"
        
        exec_task = self.tarefa_executando.id if self.tarefa_executando else "Nenhuma"
        exec_info = f"CPU: [ {exec_task} ]"
        #puxa as informacoes  do simulador e imprime da lista de tarefas
	#as que nao sao prontas
        prontos = [t.id for t in self.fila_prontos]
        fila_info = f"FILA DE PRONTOS: {prontos}"
        tasks_info = "\nESTADO DAS TAREFAS:\n" + "\n".join(
            [t.to_debug_str() for t in self.tarefas if t.estado != TaskState.NOVA]
        )
        return "\n".join([header, exec_info, fila_info, tasks_info])
	#junta as informacoes da string de saida formatada para mostrar a execucao
	#passo a passo

    def tick(self):
        """
        Realiza os  "tick`s" do relógio global.
        """
        #nao e utilizada pois no main.py nao salvamos ela em uma variavel
	#e nem imprimimos, mas deixei aqui como uma ferramenta de log
	#para debug durante a construcao
        log_eventos_tick = f"[Tick {self.relogio_global}]:"
        
        # Verifica ingresso de novas tarefas
        # Tarefas que chegam 'agora` podem competir pela CPU
	# Caso contrario estariamos disperdicando 1 tick da CPU
        for t in self.tarefas:
	#compara o estado da tarefa com o tempo do relogio, caso valide
	#adiciona a tarefa para lista de pronta
            if t.estado == TaskState.NOVA and t.ingresso == self.relogio_global:
                t.estado = TaskState.PRONTA
                self.fila_prontos.append(t)
                log_eventos_tick += f" Tarefa {t.id} ingressou;"
		#mais uma variavel de log para debug na construcao

        # Atualizar tempos de espera de quem está na fila
        for t in self.fila_prontos:
            t.tempo_espera += 1

        # Verificar estado da tarefa atual (se ela terminou ou foi preemptada)
        preemptar_quantum = False
        tarefa_terminou = False
        
        if self.tarefa_executando:
            t = self.tarefa_executando	#pegamos a informacao da tarefa atual
            
            # Verificação de Término
	    # Comparamos as variaveis da TCB da tarefa atual
            if t.tempo_executado == t.duracao:
                t.estado = TaskState.TERMINADA #se verdadeiro entao ela terminou
                t.tick_conclusao = self.relogio_global # Terminou antes deste tick
                self.tarefas_concluidas += 1
                log_eventos_tick += f" Tarefa {t.id} terminou;"
                self.tarefa_executando = None
                tarefa_terminou = True #acionamos a flag de que a tarefa terminou
				       #para ativar a decisao do escalonador
            
            # Verificação de Quantum
		#Comparamos o quantum para verificar se a tarefa estourou seu
		#tempo de CPU
            elif t.quantum_utilizado == self.quantum:
                preemptar_quantum = True #flag ativada para decisao do escalonador
		#nenhum dos tres escalonador usa a preempcao por quantum
		#mas construindo o core com essa ferramenta seria facil implementar
		#um escalonador Round Robin 
                log_eventos_tick += f" Tarefa {t.id} sofreu preempção (quantum);"


        # Decisão de Escalonamento
        # Os preemptivos usarão as novas infos da fila
	# Sera decidido pelo escalonador implementado no schedulers.py
        proxima_tarefa = self.escalonador.decidir(
            self.fila_prontos, #passamos a fila de prontos
            self.tarefa_executando, #a tarefa atual
            preemptar_quantum or tarefa_terminou #flags acionadas nas verificacoes
        )

        # Troca de Contexto
	# Recebendo o retorno dos escalonadores, avaliamos a troca de contexto
	# com a tarefa atual
        if proxima_tarefa != self.tarefa_executando:
            
            # Se a tarefa antiga existe e não terminou, devolve para a fila
            t_antigo = self.tarefa_executando
            if t_antigo and not tarefa_terminou:
                t_antigo.estado = TaskState.PRONTA
                t_antigo.quantum_utilizado = 0	#implementado para acompanhar
						#um escalonador RR
                self.fila_prontos.append(t_antigo)
                log_eventos_tick += f" Tarefa {t_antigo.id} voltou para Prontos (preemptada);"
            
            # Nova tarefa assume a CPU
            self.tarefa_executando = proxima_tarefa
            if self.tarefa_executando: #caso seja uma decisao de `idle` a condicional
				       #barra a troca
                if self.tarefa_executando in self.fila_prontos:
                     self.fila_prontos.remove(self.tarefa_executando)
                #Removemos da fila de prontos a tarefa que ganhou a cPU
                self.tarefa_executando.estado = TaskState.EXECUTANDO
                self.tarefa_executando.quantum_utilizado = 0
                log_eventos_tick += f" Escalonador escolheu {self.tarefa_executando.id};"

        # Executar o tick
        # Processa a tarefa que ganhou a CPU para este tick)
        if self.tarefa_executando:
            t = self.tarefa_executando
            t.tempo_executado += 1
            t.quantum_utilizado += 1 #Variavel nao utilizada pois nao temos 
				     #um escalonador Round Robin
            
            # Adiciona ao log do Gantt para desenhar o grafico no gantt.py
            self.gantt_log.append({'tick': self.relogio_global, 'task_id': t.id, 'cor': t.cor})
            log_eventos_tick += f" Tarefa {t.id} executou;" #variavel de debug 
        else:
            # CPU ociosa
            self.gantt_log.append({'tick': self.relogio_global, 'task_id': 'idle', 'cor': '#FFFFFF'})
            log_eventos_tick += " CPU ociosa;"

        # Avançar o relógio global
        self.relogio_global += 1
        return log_eventos_tick
