import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

def gerar_imagem_gantt(gantt_log, tarefas, nome_arquivo_saida, nome_algoritmo):
    """
    Gera o gráfico de Gantt com indicação de Sorteio.
    """
    
    if gantt_log:
        tempo_atual = gantt_log[-1]['tick'] + 1
    else:
        tempo_atual = 0

    # --- Processar o Log (Execução) ---
    blocos_comprimidos = []
    if gantt_log:
        bloco_atual = gantt_log[0].copy()
        bloco_atual['start'] = bloco_atual['tick']
        bloco_atual['duration'] = 1
        # 'sorteio' no bloco será True se ALGUM tick do bloco teve sorteio?
        # É mais preciso desenhar o sorteio tick a tick. Vamos tratar separadamente.
        
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

    # --- Desenhar Sombra (Espera) ---
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
            gnt.broken_barh(
                [(inicio, duracao_total)],
                (y_pos, y_altura),
                facecolors=('lightgray'), 
                edgecolor='grey',
                alpha=0.5, 
                hatch='///' 
            )

    # --- Desenhar Barras de Execução ---
    for bloco in blocos_comprimidos:
        task_id = bloco['task_id']
        if task_id == 'idle': continue 

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

    # --- Desenhar Indicador de Sorteio (Estrela) ---
    # Iteramos sobre o log bruto para ser preciso no tick exato
    if gantt_log:
        for log in gantt_log:
            if log.get('sorteio', False) and log['task_id'] != 'idle':
                t_id = log['task_id']
                if t_id in task_map:
                    y_pos = task_map[t_id] * y_padding
                    tick_x = log['tick']
                    
                    # Desenha um asterisco (*) no centro do tick, acima da barra
                    gnt.text(
                        tick_x + 0.5,     # Centro do tick
                        y_pos + y_altura + 0.5, # Um pouco acima da barra
                        "*", 
                        ha='center', va='center', 
                        fontsize=14, fontweight='bold', color='black',
                        zorder=20
                    )

    # Legenda
    patches = [
        mpatches.Patch(color=t.cor, label=f"{t.id} (Prio: {t.prioridade})") 
        for t in sorted(tarefas, key=lambda x: x.id)
    ]
    patches.append(mpatches.Patch(facecolor='lightgray', edgecolor='grey', hatch='///', label='Em Espera'))
    
    # Adiciona legenda para o Sorteio
    # Criamos um "artista" fantasma para a legenda
    legenda_sorteio = plt.Line2D([0], [0], marker='*', color='w', label='Decisão por Sorteio',
                          markerfacecolor='black', markersize=10)
    patches.append(legenda_sorteio)

    plt.legend(handles=patches, bbox_to_anchor=(1.02, 1), loc='upper left')
    plt.title(f"Gráfico de Gantt (Algoritmo: {nome_algoritmo.upper()})", fontsize=16)

    try:
        plt.savefig(nome_arquivo_saida, bbox_inches='tight')
    except Exception as e:
        print(f"Erro ao salvar o gráfico: {e}")
        
    plt.close(fig)
