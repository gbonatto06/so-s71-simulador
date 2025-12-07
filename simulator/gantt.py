import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

def gerar_imagem_gantt(gantt_log, tarefas, nome_arquivo_saida, nome_algoritmo, bloqueio_log=None, mutex_event_log=None, io_log=None):
    if bloqueio_log is None: bloqueio_log = []
    if mutex_event_log is None: mutex_event_log = []
    if io_log is None: io_log = []
    
    if gantt_log:
        tempo_atual = gantt_log[-1]['tick'] + 1
    else:
        tempo_atual = 0

    # Função interna para agrupar logs consecutivos
    def agrupar_logs(logs):
        blocos = []
        if not logs: return blocos
        
        # Ordena primariamente por task_id, depois pelo tick
        logs_ordenados = sorted(logs, key=lambda x: (x['task_id'], x['tick']))
        
        bloco_atual = logs_ordenados[0].copy()
        bloco_atual['start'] = bloco_atual['tick']
        bloco_atual['duration'] = 1
        
        for log in logs_ordenados[1:]:
            # Se for a mesma tarefa e o tick for consecutivo
            if log['task_id'] == bloco_atual['task_id'] and log['tick'] == bloco_atual['start'] + bloco_atual['duration']:
                bloco_atual['duration'] += 1
            else:
                blocos.append(bloco_atual)
                bloco_atual = log.copy()
                bloco_atual['start'] = bloco_atual['tick']
                bloco_atual['duration'] = 1
        blocos.append(bloco_atual)
        return blocos

    # Processar Logs de Execução
    blocos_exec = []
    if gantt_log:
        b_atual = gantt_log[0].copy()
        b_atual['start'] = b_atual['tick']
        b_atual['duration'] = 1
        for log in gantt_log[1:]:
            if log['task_id'] == b_atual['task_id']:
                b_atual['duration'] += 1
            else:
                blocos_exec.append(b_atual)
                b_atual = log.copy()
                b_atual['start'] = b_atual['tick']
                b_atual['duration'] = 1
        blocos_exec.append(b_atual)

    blocos_bloq = agrupar_logs(bloqueio_log)
    blocos_io = agrupar_logs(io_log) 

    # Configurar Gráfico
    fig, gnt = plt.subplots(figsize=(16, 8))

    task_ids = sorted(list(set(t.id for t in tarefas)))
    task_ids.reverse() 
    task_map = {task_id: i for i, task_id in enumerate(task_ids)}
    
    y_altura = 6 
    y_padding = 10 

    gnt.set_ylim(0, len(task_ids) * y_padding + 5)
    gnt.set_yticks([y_padding * i + y_altura/2 for i in range(len(task_ids))])
    gnt.set_yticklabels(task_ids)
    gnt.set_ylabel('Tarefas')

    tempo_max_visual = max(tempo_atual, 20) 
    gnt.set_xlim(0, tempo_max_visual)
    gnt.set_xlabel('Tempo (t)')
    
    passo = 2
    gnt.set_xticks(range(0, tempo_max_visual + 1, passo))
    gnt.set_xticks(range(0, tempo_max_visual + 1, 1), minor=True)
    gnt.grid(True, axis='x', which='minor', linestyle=':', alpha=0.5)
    gnt.grid(True, axis='x', which='major', linestyle='-', alpha=0.8) 
    gnt.grid(False, axis='y')

    # 1. Sombra Espera (Fundo Cinza)
    for t in tarefas:
        if t.id not in task_map: continue 
        if t.ingresso > tempo_atual: continue
        y_pos = task_map[t.id] * y_padding
        inicio = t.ingresso
        if t.tick_conclusao != -1 and t.tick_conclusao <= tempo_atual:
            fim_visual = t.tick_conclusao
        else:
            fim_visual = tempo_atual
        duracao_total = fim_visual - inicio
        if duracao_total > 0:
            gnt.broken_barh([(inicio, duracao_total)], (y_pos, y_altura), facecolors=('lightgray'), edgecolor='grey', alpha=0.5, hatch='///')

    # 2. Bloqueios (Mutex - Vermelho)
    for bloco in blocos_bloq:
        t_id = bloco['task_id']
        if t_id not in task_map: continue
        y_pos = task_map[t_id] * y_padding
        gnt.broken_barh([(bloco['start'], bloco['duration'])], (y_pos, y_altura), facecolors='mistyrose', edgecolor='indianred', alpha=0.7, hatch='XX', zorder=5)

    # 3. Bloqueios (E/S - Amarelo/Laranja) COM TEXTO IO
    for bloco in blocos_io:
        t_id = bloco['task_id']
        if t_id not in task_map: continue
        y_pos = task_map[t_id] * y_padding
        
        # Desenha a barra amarela
        gnt.broken_barh([(bloco['start'], bloco['duration'])], (y_pos, y_altura), facecolors='moccasin', edgecolor='orange', alpha=0.9, hatch='..', zorder=6)
        
        # Adiciona o Texto "IO" no centro da barra
        # Calculamos o centro X e Y do bloco
        center_x = bloco['start'] + (bloco['duration'] / 2)
        center_y = y_pos + (y_altura / 2)
        
        # Usamos uma cor escura (chocolate) para contrastar com o fundo amarelo claro (moccasin)
        gnt.text(center_x, center_y, "IO", ha='center', va='center', fontsize=8, fontweight='bold', color='chocolate', zorder=20)

    # 4. Execução
    for bloco in blocos_exec:
        task_id = bloco['task_id']
        if task_id == 'idle': continue 
        y_pos = task_map[task_id] * y_padding
        gnt.broken_barh([(bloco['start'], bloco['duration'])], (y_pos, y_altura), facecolors=(bloco['cor']), edgecolor='black', zorder=10)

    # 5. Marcadores de Mutex
    for event in mutex_event_log:
        t_id = event['task_id']
        if t_id in task_map:
            y_pos = task_map[t_id] * y_padding
            tick_x = event['tick']
            
            if event['tipo'] == 'ML':
                color, marker, label = 'green', '^', f"ML{event['mutex']}"
            elif event['tipo'] == 'MU':
                color, marker, label = 'blue', 'v', f"MU{event['mutex']}"
            elif event['tipo'] == 'ML_FAIL':
                color, marker, label = 'red', 'X', f"ML{event['mutex']}"
            else:
                continue

            gnt.plot(tick_x + 0.5, y_pos + y_altura, marker=marker, color=color, markersize=9, zorder=25)
            gnt.text(tick_x + 0.5, y_pos + y_altura + 2, label, ha='center', va='bottom', fontsize=9, fontweight='bold', color=color, zorder=25)

    # 6. Sorteio
    if gantt_log:
        for log in gantt_log:
            if log.get('sorteio', False) and log['task_id'] != 'idle':
                t_id = log['task_id']
                if t_id in task_map:
                    y_pos = task_map[t_id] * y_padding
                    tick_x = log['tick']
                    gnt.text(tick_x + 0.5, y_pos + y_altura + 0.5, "*", ha='center', va='center', fontsize=14, fontweight='bold', color='black', zorder=20)

    # Legenda
    patches = [mpatches.Patch(color=t.cor, label=f"{t.id} (Prio: {t.prioridade})") for t in sorted(tarefas, key=lambda x: x.id)]
    patches.append(mpatches.Patch(facecolor='lightgray', edgecolor='grey', hatch='///', label='Em Espera'))
    patches.append(mpatches.Patch(facecolor='indianred', edgecolor='firebrick', hatch='XX', label='Bloqueado (Mutex)'))
    patches.append(mpatches.Patch(facecolor='moccasin', edgecolor='orange', hatch='..', label='Em Operação E/S'))
    patches.append(plt.Line2D([0], [0], marker='*', color='w', label='Decisão por Sorteio', markerfacecolor='black', markersize=10))
    
    # Legendas de Mutex
    patches.append(plt.Line2D([0], [0], marker='^', color='w', label='Mutex Lock (Sucesso)', markerfacecolor='green', markersize=8))
    patches.append(plt.Line2D([0], [0], marker='v', color='w', label='Mutex Unlock', markerfacecolor='blue', markersize=8))
    patches.append(plt.Line2D([0], [0], marker='X', color='w', label='Lock Negado (Bloqueio)', markerfacecolor='red', markersize=8))

    plt.legend(handles=patches, bbox_to_anchor=(1.02, 1), loc='upper left')
    plt.title(f"Gráfico de Gantt (Algoritmo: {nome_algoritmo.upper()})", fontsize=16)

    try:
        plt.savefig(nome_arquivo_saida, bbox_inches='tight')
    except Exception as e:
        print(f"Erro ao salvar o gráfico: {e}")
    plt.close(fig)
