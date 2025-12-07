import os
import sys
import time
import subprocess
import re 
import matplotlib.colors as mcolors
from simulator.parser import carregar_configuracao_arquivo, carregar_plugins
from simulator.gantt import gerar_imagem_gantt
from simulator.core import TCB

# --- Funções Auxiliares de UI ---

def limpar_tela():
    print("\033[H\033[J", end="")

def exibir_menu(arquivo_carregado, qtd_plugins):
    """Mostra o menu principal."""
    limpar_tela()
    print("=" * 60)
    print("        SIMULADOR DE ESCALONADOR DE SISTEMAS OPERACIONAIS")
    print("=" * 60)
    
    arquivo_str = arquivo_carregado if arquivo_carregado else "Nenhum"
    print(f"Arquivo Config: [ {arquivo_str} ]")
    print(f"Plugins Ativos: [ {qtd_plugins} ]\n")
        
    print("  [1] Carregar Arquivo de Configuração (.txt)")
    print("  [2] Executar Simulação (Modo Completo)")
    print("  [3] Executar Simulação (Modo Passo-a-Passo)")
    print("  [4] Editar Arquivo de Configuração (Nano)")
    print("  [5] Carregar Plugins Externos (pasta /extensions)")
    print("  [6] Sair")
    print("-" * 60)

def exibir_debugger(simulador):
    limpar_tela()
    print("="*60)
    print(f"MODO DEBUGGER (PASSO-A-PASSO) - {simulador.escalonador.__class__.__name__}")
    print("="*60)
    print(simulador.get_debug_info())
    print("\n" + "="*60)

def pausar_e_continuar():
    input("\nPressione Enter para voltar ao menu principal...")

# --- Funções de Lógica ---

def carregar_novo_arquivo(plugins_ativos):
    arquivo = input("Digite o caminho do arquivo (ex: config.txt): ").strip()
    if not os.path.exists(arquivo):
        print(f"\nErro: Arquivo '{arquivo}' não encontrado.")
        return None
    simulador_teste = carregar_configuracao_arquivo(arquivo, plugins_ativos)
    if simulador_teste is None:
        print("\nErro: Falha ao processar o arquivo.")
        return None
    print(f"\nArquivo '{arquivo}' validado e carregado com sucesso.")
    return arquivo

def editar_arquivo_config(arquivo_atual, plugins_ativos):
    arquivo_alvo = arquivo_atual
    if not arquivo_alvo:
        arquivo_alvo = input("Digite o nome do arquivo para criar/editar (ex: config.txt): ").strip()
    if not arquivo_alvo: return None
    try:
        subprocess.call(['nano', arquivo_alvo])
        print(f"\nEdição de '{arquivo_alvo}' concluída.")
        if os.path.exists(arquivo_alvo):
            print("Validando alterações...")
            sim = carregar_configuracao_arquivo(arquivo_alvo, plugins_ativos)
            if sim:
                print("Arquivo válido! Carregado automaticamente.")
                return arquivo_alvo
            else:
                print("Aviso: O arquivo editado contém erros.")
        return arquivo_alvo
    except Exception as e:
        print(f"Erro ao abrir editor: {e}")
        return arquivo_atual

def rodar_modo_completo(arquivo_config, plugins_ativos):
    print(f"Iniciando simulação (Modo Completo) de '{arquivo_config}'...")
    
    simulador = carregar_configuracao_arquivo(arquivo_config, plugins_ativos)
    if simulador is None:
        print("Erro fatal: Falha ao recarregar o simulador.")
        return

    nome_saida = input("Digite o nome do arquivo de imagem de saída (ex: gantt.png): ").strip()
    if not nome_saida:
        nome_saida = "gantt_resultado.png"
    
    start_time = time.time()
    
    while not simulador.terminou():
        simulador.tick()
        if simulador.relogio_global % 50 == 0:
            print(f"  ... simulando tick {simulador.relogio_global}", end='\r')

    end_time = time.time()
    
    print("\n" + "="*60)
    print("Simulação concluída.")
    print(f"Tempo total: {end_time - start_time:.4f}s. Tick Final: {simulador.relogio_global - 1}")
    print("="*60)

    try:
        print(f"Gerando gráfico em '{nome_saida}'...")
        gerar_imagem_gantt(
            simulador.gantt_log,
            simulador.tarefas,
            nome_saida,
            simulador.nome_algoritmo_config,
            simulador.bloqueio_log,
            simulador.mutex_event_log,
            simulador.io_log 
        )
        print(f"Gráfico salvo com sucesso.")
    except Exception as e:
        print(f"Erro crítico ao gerar o gráfico: {e}", file=sys.stderr)

def rodar_modo_passo_a_passo(arquivo_config, plugins_ativos):
    print(f"Iniciando simulação (Passo-a-Passo) de '{arquivo_config}'...")
    
    simulador = carregar_configuracao_arquivo(arquivo_config, plugins_ativos)
    if simulador is None:
        print("Erro fatal: Falha ao recarregar o simulador.")
        return

    nome_saida = input("Digite o nome do arquivo de imagem (será atualizado a cada passo): ").strip()
    if not nome_saida:
        nome_saida = "gantt_passo_atual.png"
        
    try:
        while True:
            # 1. Exibir Estado
            exibir_debugger(simulador)
            
            # 2. Gerar Gráfico
            try:
                gerar_imagem_gantt(
                    simulador.gantt_log,
                    simulador.tarefas,
                    nome_saida,
                    simulador.nome_algoritmo_config,
                    simulador.bloqueio_log,
                    simulador.mutex_event_log,
                    simulador.io_log 
                )
                print(f"Gráfico atualizado em '{nome_saida}'")
            except Exception as e:
                print(f"Erro ao gerar gráfico: {e}")

            # 3. Verificar fim
            if simulador.terminou():
                print("\n--- SIMULAÇÃO CONCLUÍDA ---")
            
            # 4. Menu de Opções
            print("\nComandos:")
            print(" [Enter] Avançar Tick")
            print(" [v]     Voltar Tick (Desfazer)")
            print(" [n]     Inserir Nova Tarefa Agora")
            print(" [s]     Sair")
            
            comando = input("Opção: ").lower().strip()

            if comando == 's':
                print("Saindo...")
                break
            
            elif comando == 'v':
                if simulador.voltar_tick():
                    print("Voltando no tempo...")
                else:
                    print(">> Você já está no início (ou no limite do histórico).")
                    time.sleep(1.5)
            
            elif comando == 'n': # insercao dinamica
                print("\n--- INSERIR TAREFA DINÂMICA ---")
                try:
                    simulador.salvar_estado()
                    
                    t_id = input("ID da Tarefa (ex: T_Extra): ").strip()
                    
                    # VALIDAÇÃO DE COR
                    t_cor = input("Cor (ex: red/cyan ou 123456): ").strip()
                    # 1. Normaliza Hex se necessário
                    if re.fullmatch(r'[0-9A-Fa-f]{6}', t_cor): 
                        t_cor = f"#{t_cor}"
                    
                    # 2. Verifica se é válida para o Matplotlib
                    if not mcolors.is_color_like(t_cor):
                        raise ValueError(f"Cor inválida: '{t_cor}'. Use nomes em inglês (red, blue) ou Hex.")
                    # -------------------------
                    
                    t_dur = int(input("Duração (ticks): "))
                    t_prio = int(input("Prioridade (inteiro): "))
                    
                    t_acoes_str = input("Ações (ex: ML1:2;IO:4-5;MU1:6) [Enter p/ vazio]: ").strip()
                    t_acoes_parsed = []
                    
                    if t_acoes_str:
                        itens = [x.strip() for x in t_acoes_str.split(';') if x.strip()]
                        for item in itens:
                            try:
                                if item.startswith("IO:"):
                                    resto = item[3:].split('-')
                                    ini, dur = int(resto[0]), int(resto[1])
                                    t_acoes_parsed.append({'tipo': 'IO', 'tempo': ini, 'duracao_io': dur})
                                else:
                                    tipo = item[:2].upper()
                                    resto = item[2:].split(':')
                                    mutex_id, tempo = int(resto[0]), int(resto[1])
                                    if tipo in ['ML', 'MU']:
                                        t_acoes_parsed.append({'tipo': tipo, 'mutex': mutex_id, 'tempo': tempo})
                            except:
                                print(f"Aviso: Formato inválido '{item}'. Ignorado.")
                        
                        t_acoes_parsed.sort(key=lambda x: x['tempo'])

                    t_ingresso = simulador.relogio_global
                    nova_tcb = TCB(t_id, t_cor, t_ingresso, t_dur, t_prio)
                    nova_tcb.acoes = t_acoes_parsed
                    
                    if simulador.adicionar_tarefa(nova_tcb):
                        print(f"\nSucesso! Tarefa {t_id} inserida.")
                    else:
                        print(f"\nErro: ID duplicado.")
                        simulador.historico.pop()
                    
                    time.sleep(1.5)
                    
                except ValueError as ve:
                    print(f"Erro: {ve}")
                    simulador.historico.pop()
                    time.sleep(2.0)

            else:
                if simulador.terminou():
                    continue 
                simulador.tick()
        
    except KeyboardInterrupt:
        print("\nRetornando ao menu.")
        return

# --- Loop Principal ---

def main():
    arquivo_carregado = None
    plugins_carregados = {} 
    
    while True:
        exibir_menu(arquivo_carregado, len(plugins_carregados))
        escolha = input("Escolha uma opção [1-6]: ").strip()
        
        if escolha == '1':
            novo = carregar_novo_arquivo(plugins_carregados)
            if novo: arquivo_carregado = novo
            pausar_e_continuar()
            
        elif escolha == '2':
            if arquivo_carregado is None:
                print("\nErro: Nenhum arquivo carregado.")
            else:
                rodar_modo_completo(arquivo_carregado, plugins_carregados)
            pausar_e_continuar()

        elif escolha == '3':
            if arquivo_carregado is None:
                print("\nErro: Nenhum arquivo carregado.")
            else:
                rodar_modo_passo_a_passo(arquivo_carregado, plugins_carregados)
            pausar_e_continuar()

        elif escolha == '4':
            print("\nAbrindo editor...")
            time.sleep(1)
            novo = editar_arquivo_config(arquivo_carregado, plugins_carregados)
            if novo: arquivo_carregado = novo
            pausar_e_continuar()

        elif escolha == '5':
            print("\nCarregando plugins da pasta /extensions...")
            novos_plugins = carregar_plugins()
            if novos_plugins:
                plugins_carregados.update(novos_plugins)
                print(f"\nSucesso! {len(novos_plugins)} plugins carregados/atualizados.")
            else:
                print("\nNenhum plugin válido encontrado na pasta 'extensions'.")
            pausar_e_continuar()

        elif escolha == '6':
            print("Saindo do simulador.")
            break
            
        else:
            print(f"\nOpção '{escolha}' inválida.")
            pausar_e_continuar()

if __name__ == "__main__":
    main()
