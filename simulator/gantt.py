import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

def gerar_imagem_gantt(gantt_log, tarefas, nome_arquivo_saida, nome_algoritmo):
    """
    Gera o gráfico de Gantt.
    Agora respeita o tempo atual (não desenha futuro) e tem eixo X fixo inicial.
    """
    
    # 1. Descobrir o Tempo Atual da Simulação
    if gantt_log:
        # Se tem logs, o tempo é o último tick registrado + 1
        tempo_atual = gantt_log[-1]['tick'] + 1
    else:
        # Se não tem log, estamos no tempo 0
        tempo_atual = 0

    # --- Processar o Log (Execução) ---
    blocos_comprimidos = []
    if gantt_log:
        bloco_atual = gantt_log[0].copy()
        bloco_atual['start'] = bloco_atual['tick']
        bloco_atual['duration'] = 1
        
        for log in gantt_log[1:]:
            if log['task_id'] == bloco_atual['task_id']:
                bloco_atual['duration'] += 1
            else:
                blocos_comprimidos.append(bloco_atual)
                bloco_atual = log.copy()
                bloco_atual['start'] = bloco_atual['tick']
                bloco_atual['duration'] = 1
        blocos_comprimidos.append(bloco_atual)

    # --- Configurar o Gráfico ---
    fig, gnt = plt.subplots(figsize=(16, 8))

    # Lista todas as tarefas no eixo Y (mesmo as futuras, para sabermos que existem)
    task_ids = sorted(list(set(t.id for t in tarefas)))
    task_ids.reverse() 
    
    task_map = {task_id: i for i, task_id in enumerate(task_ids)}
    
    y_altura = 6 
    y_padding = 10 

    gnt.set_ylim(0, len(task_ids) * y_padding + 5)
    gnt.set_yticks([y_padding * i + y_altura/2 for i in range(len(task_ids))])
    gnt.set_yticklabels(task_ids)
    gnt.set_ylabel('Tarefas')

    # Tamanho Mínimo do Eixo X Predefinido
    # Usa o maior entre: Tempo Atual ou 20
    tempo_max_visual = max(tempo_atual, 20) 
    
    gnt.set_xlim(0, tempo_max_visual)
    gnt.set_xlabel('Tempo (t)')
    
    # Forçar intervalo de 2 em 2 nos números
    passo = 2
        
    # Define os números principais: 0, 2, 4, 6...
    gnt.set_xticks(range(0, tempo_max_visual + 1, passo))
    
    # Mantém as linhas de grade finas de 1 em 1 para precisão visual
    gnt.set_xticks(range(0, tempo_max_visual + 1, 1), minor=True)
    
    # A grade pontilhada segue os Minor Ticks (de 1 em 1)
    gnt.grid(True, axis='x', which='minor', linestyle=':', alpha=0.5)
    gnt.grid(True, axis='x', which='major', linestyle='-', alpha=0.8) 
    gnt.grid(False, axis='y')

    # --- Desenhar a "Sombra" (Tempo de Espera) ---
    for t in tarefas:
        if t.id not in task_map: continue 

        # Se a tarefa só vai chegar no futuro (ingresso > tempo_atual),
        # não desenhamos nada dela ainda.
        if t.ingresso > tempo_atual:
            continue

        y_pos = task_map[t.id] * y_padding
        inicio = t.ingresso
        
        # O fim visual da sombra é o tempo atual (se ela ainda não acabou)
        # ou o tick de conclusão (se ela já acabou)
        if t.tick_conclusao != -1 and t.tick_conclusao <= tempo_atual:
            fim_visual = t.tick_conclusao
        else:
            fim_visual = tempo_atual
            
        duracao_total = fim_visual - inicio
        
        if duracao_total > 0:
            gnt.broken_barh(
                [(inicio, duracao_total)],
                (y_pos, y_altura),
                facecolors=('lightgray'), 
                edgecolor='grey',
                alpha=0.5, 
                hatch='///' 
            )

    # --- Desenhar as Barras de Execução (Coloridas) ---
    for bloco in blocos_comprimidos:
        task_id = bloco['task_id']
        if task_id == 'idle': continue 

        # Desenha apenas o que já aconteceu
        y_pos = task_map[task_id] * y_padding
        x_start = bloco['start']
        x_duration = bloco['duration']
        
        gnt.broken_barh(
            [(x_start, x_duration)], 
            (y_pos, y_altura), 
            facecolors=(bloco['cor']),
            edgecolor='black',
            zorder=10 
        )

    # Legenda e Título
    patches = [
        mpatches.Patch(color=t.cor, label=f"{t.id} (Prio: {t.prioridade})") 
        for t in sorted(tarefas, key=lambda x: x.id)
    ]
    patches.append(mpatches.Patch(facecolor='lightgray', edgecolor='grey', hatch='///', label='Em Espera/Suspenso'))
    
    plt.legend(handles=patches, bbox_to_anchor=(1.02, 1), loc='upper left')
    plt.title(f"Gráfico de Gantt (Algoritmo: {nome_algoritmo.upper()})", fontsize=16)

    try:
        plt.savefig(nome_arquivo_saida, bbox_inches='tight')
    except Exception as e:
        print(f"Erro ao salvar o gráfico: {e}")
        
    plt.close(fig)
