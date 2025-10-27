import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

def gerar_imagem_gantt(gantt_log, tarefas, nome_arquivo_saida):
    """
    Gera o gráfico de Gantt e salva em um arquivo PNG
    """
    if not gantt_log:
        print("Log de Gantt vazio, imagem não gerada.")
        return

    # O log está em ticks: [{'tick': 0, 'task_id': 'T1'}, {'tick': 1, 'task_id': 'T1'}]
    # comprimindo em blocos: [{'task_id': 'T1', 'start': 0, 'duration': 2}]
    
    blocos_comprimidos = []
    if not gantt_log:
        return # Nada a fazer
        
    bloco_atual = gantt_log[0].copy()
    bloco_atual['start'] = bloco_atual['tick']
    bloco_atual['duration'] = 1
    
    for log in gantt_log[1:]:
        if log['task_id'] == bloco_atual['task_id']:
            # Continua o mesmo bloco
            bloco_atual['duration'] += 1
        else:
            # Bloco diferente, salva o anterior e inicia um novo
            blocos_comprimidos.append(bloco_atual)
            bloco_atual = log.copy()
            bloco_atual['start'] = bloco_atual['tick']
            bloco_atual['duration'] = 1
    
    # Adiciona o último bloco
    blocos_comprimidos.append(bloco_atual)
    fig, gnt = plt.subplots(figsize=(16, 8))

    # Pega os IDs únicos das tarefas e os ordena (ex: T1, T2, T3)
    task_ids = sorted(list(set(t.id for t in tarefas)))
    # Inverte para ficar T5, T4, ... T1
    task_ids.reverse() 
    
    # Mapeia ID da tarefa para uma posição Y
    task_map = {task_id: i for i, task_id in enumerate(task_ids)}
    
    y_altura = 9 # Altura de cada barra
    y_padding = 10 # Espaçamento (altura + margem)

    # Configurações do Eixo Y(tarefas)
    gnt.set_ylim(0, len(task_ids) * y_padding)
    gnt.set_yticks([y_padding * i + y_altura/2 for i in range(len(task_ids))])
    gnt.set_yticklabels(task_ids)
    gnt.set_ylabel('Tarefas')

    # Configurações do Eixo X (Tempo)
    tempo_max = gantt_log[-1]['tick'] + 1
    gnt.set_xlim(0, tempo_max)
    gnt.set_xlabel('Tempo (t)')
    
    # Adiciona as linhas de grade verticais pontilhadas
    gnt.set_xticks(range(0, tempo_max + 1), minor=True)
    gnt.grid(True, axis='x', linestyle=':', alpha=0.7)
    gnt.grid(False, axis='y') # Remove grade horizontal

    # parte das barras
    for bloco in blocos_comprimidos:
        task_id = bloco['task_id']
        
        #CPU ociosa nao gera desenho ('idle')
        if task_id == 'idle':
            continue 

        y_pos = task_map[task_id] * y_padding
        x_start = bloco['start']
        x_duration = bloco['duration']
        
        gnt.broken_barh(
            [(x_start, x_duration)], 
            (y_pos, y_altura), 
            facecolors=(bloco['cor']),
            edgecolor='black' # Adiciona a borda preta (como nos exemplos)
        )

    # Adiciona a legenda de cores
    patches = [
        mpatches.Patch(color=t.cor, label=f"{t.id} (Prio: {t.prioridade})") 
        for t in sorted(tarefas, key=lambda x: x.id)
    ]
    plt.legend(handles=patches, bbox_to_anchor=(1.02, 1), loc='upper left')
    
    # Título do Gráfico
    plt.title("Gráfico de Gantt da Execução", fontsize=16)

    # Salva o arquivo
    try:
        plt.savefig(nome_arquivo_saida, bbox_inches='tight')
        print(f"Gráfico de Gantt salvo com sucesso em '{nome_arquivo_saida}'")
    except Exception as e:
        print(f"Erro ao salvar o gráfico: {e}")
        
    plt.close(fig)
