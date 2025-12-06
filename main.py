import os
import sys
import time
import subprocess
import re  # validar a cor Hexadecimal

# Importamos também a função de carregar plugins explicitamente
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
    # A string retornada aqui já contém o status do escalonador (definido no core.py)
    print(simulador.get_debug_info())
    print("\n" + "="*60)

def pausar_e_continuar():
    input("\nPressione Enter para voltar ao menu principal...")

# --- Funções de Lógica ---

def carregar_novo_arquivo(plugins_ativos):
    """Pede um nome de arquivo e valida usando os plugins ativos."""
    arquivo = input("Digite o caminho do arquivo (ex: config.txt): ").strip()
    
    if not os.path.exists(arquivo):
        print(f"\nErro: Arquivo '{arquivo}' não encontrado.")
        return None
        
    # Passamos os plugins para validar se o algoritmo do config existe
    simulador_teste = carregar_configuracao_arquivo(arquivo, plugins_ativos)
    
    if simulador_teste is None:
        print("\nErro: Falha ao processar o arquivo. Verifique o formato ou se o plugin necessário foi carregado.")
        return None
    
    print(f"\nArquivo '{arquivo}' validado e carregado com sucesso.")
    return arquivo

def editar_arquivo_config(arquivo_atual, plugins_ativos):
    """Abre o editor nano."""
    arquivo_alvo = arquivo_atual
    if not arquivo_alvo:
        arquivo_alvo = input("Digite o nome do arquivo para criar/editar (ex: config.txt): ").strip()
    
    if not arquivo_alvo: return None

    try:
        subprocess.call(['nano', arquivo_alvo])
        print(f"\nEdição de '{arquivo_alvo}' concluída.")
        
        if os.path.exists(arquivo_alvo):
            print("Validando alterações...")
            # Valida com os plugins atuais
            sim = carregar_configuracao_arquivo(arquivo_alvo, plugins_ativos)
            if sim:
                print("Arquivo válido! Carregado automaticamente.")
                return arquivo_alvo
            else:
                print("Aviso: O arquivo editado contém erros (ou requer plugin não carregado).")
        return arquivo_alvo
    except Exception as e:
        print(f"Erro ao abrir editor: {e}")
        return arquivo_atual

def rodar_modo_completo(arquivo_config, plugins_ativos):
    """Roda o simulador (passando os plugins)."""
    print(f"Iniciando simulação (Modo Completo) de '{arquivo_config}'...")
    
    # Recarrega usando os plugins
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
            simulador.nome_algoritmo_config
        )
        print(f"Gráfico salvo com sucesso.")
    except Exception as e:
        print(f"Erro crítico ao gerar o gráfico: {e}", file=sys.stderr)

def rodar_modo_passo_a_passo(arquivo_config, plugins_ativos):
    """Roda o simulador com opção de avançar, voltar, inserir tarefas e gerar gráfico."""
    print(f"Iniciando simulação (Passo-a-Passo) de '{arquivo_config}'...")
    
    # Recarrega usando os plugins
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
                    simulador.nome_algoritmo_config
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
            
            elif comando == 'n': #insercao dinamica
                print("\n--- INSERIR TAREFA DINÂMICA ---")
                try:
                    # 1. Salva o estado atual antes de mexer
                    simulador.salvar_estado()
                    
                    t_id = input("ID da Tarefa (ex: T_Extra): ").strip()
                    t_cor = input("Cor (ex: magenta, 123456 ou FF00DD): ").strip()
                    
                    # Validação de Cor Hexadecimal
                    # Se o usuário digitou Hex sem #, adicionamos o #
                    if re.fullmatch(r'[0-9A-Fa-f]{6}', t_cor):
                        t_cor = f"#{t_cor}"
                    # ----------------------------------------------------------------

                    t_dur = int(input("Duração (ticks): "))
                    t_prio = int(input("Prioridade (inteiro): "))
                    
                    t_ingresso = simulador.relogio_global
                    
                    # Cria e adiciona
                    nova_tcb = TCB(t_id, t_cor, t_ingresso, t_dur, t_prio)
                    
                    # Tenta adicionar (verifica ID duplicado)
                    if simulador.adicionar_tarefa(nova_tcb):
                        print(f"\nSucesso! Tarefa {t_id} inserida no tempo {t_ingresso}.")
                        print("Pressione [Enter] no próximo passo para que ela seja processada.")
                    else:
                        print(f"\nErro: A tarefa '{t_id}' já existe! Inserção cancelada.")
                        simulador.historico.pop() # Remove snapshot redundante
                    
                    time.sleep(2)
                    
                except ValueError:
                    print("Erro: Duração e Prioridade devem ser números inteiros!")
                    simulador.historico.pop() # Remove snapshot redundante
                    time.sleep(1.5)

            else:
                # AVANÇAR
                if simulador.terminou():
                    print("Simulação finalizada. Use 'v', 'n' ou 's'.")
                    time.sleep(1)
                    continue 
                simulador.tick()
        
    except KeyboardInterrupt:
        print("\nRetornando ao menu.")
        return

# --- Loop Principal ---

def main():
    arquivo_carregado = None
    plugins_carregados = {} # Dicionário para armazenar plugins ativos na sessão
    
    while True:
        exibir_menu(arquivo_carregado, len(plugins_carregados))
        escolha = input("Escolha uma opção [1-6]: ").strip()
        
        if escolha == '1':
            # Passamos os plugins para a validação
            novo = carregar_novo_arquivo(plugins_carregados)
            if novo: arquivo_carregado = novo
            pausar_e_continuar()
            
        elif escolha == '2':
            if arquivo_carregado is None:
                print("\nErro: Nenhum arquivo carregado.")
            else:
                # Passamos os plugins para a execução
                rodar_modo_completo(arquivo_carregado, plugins_carregados)
            pausar_e_continuar()

        elif escolha == '3':
            if arquivo_carregado is None:
                print("\nErro: Nenhum arquivo carregado.")
            else:
                # Passamos os plugins para a execução
                rodar_modo_passo_a_passo(arquivo_carregado, plugins_carregados)
            pausar_e_continuar()

        elif escolha == '4':
            print("\nAbrindo editor...")
            time.sleep(1)
            # Passamos plugins para validação pós-edição
            novo = editar_arquivo_config(arquivo_carregado, plugins_carregados)
            if novo: arquivo_carregado = novo
            pausar_e_continuar()

        elif escolha == '5':
            # AÇÃO DE CARREGAR PLUGINS
            print("\nCarregando plugins da pasta /extensions...")
            novos_plugins = carregar_plugins() # Chama a função do parser
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
