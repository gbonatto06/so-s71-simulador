import os
import sys
import time
import subprocess
from simulator.parser import carregar_configuracao_arquivo
from simulator.gantt import gerar_imagem_gantt

# --- Funções Auxiliares de UI ---

def limpar_tela():
    """Limpa o terminal."""
    print("\033[H\033[J", end="")

def exibir_menu(arquivo_carregado):
    """Mostra o menu principal."""
    limpar_tela()
    print("=" * 60)
    print("        SIMULADOR DE ESCALONADOR DE SISTEMAS OPERACIONAIS")
    print("=" * 60)
    
    if arquivo_carregado:
        print(f"Arquivo Carregado: [ {arquivo_carregado} ]\n")
    else:
        print("Arquivo Carregado: [ Nenhum ]\n")
        
    print("  [1] Carregar Arquivo de Configuração (.txt)")
    print("  [2] Executar Simulação (Modo Completo)")
    print("  [3] Executar Simulação (Modo Passo-a-Passo)")
    print("  [4] Editar Arquivo de Configuração (Nano)")
    print("  [5] Sair")
    print("-" * 60)

def exibir_debugger(simulador):
    """ Imprime o estado atual (apenas visualização). """
    limpar_tela()
    print("="*60)
    print(f"MODO DEBUGGER (PASSO-A-PASSO) - {simulador.escalonador.__class__.__name__}")
    print("="*60)
    
    # Puxa as informações de debug do simulador
    print(simulador.get_debug_info())
    print("\n" + "="*60)

def pausar_e_continuar():
    """Pede ao usuário para pressionar Enter para voltar ao menu."""
    input("\nPressione Enter para voltar ao menu principal...")

# --- Funções de Lógica do Menu ---

def carregar_novo_arquivo():
    """Pede um nome de arquivo, tenta carregá-lo e retorna o nome se for válido."""
    arquivo = input("Digite o caminho do arquivo (ex: config.txt): ").strip()
    
    if not os.path.exists(arquivo):
        print(f"\nErro: Arquivo '{arquivo}' não encontrado.")
        return None
        
    simulador_teste = carregar_configuracao_arquivo(arquivo)
    
    if simulador_teste is None:
        print("\nErro: Falha ao processar o arquivo. Verifique o formato.")
        return None
    
    print(f"\nArquivo '{arquivo}' validado e carregado com sucesso.")
    return arquivo

def editar_arquivo_config(arquivo_atual):
    """Abre o editor nano para editar o arquivo de configuração."""
    arquivo_alvo = arquivo_atual
    
    if not arquivo_alvo:
        arquivo_alvo = input("Digite o nome do arquivo para criar/editar (ex: config.txt): ").strip()
    
    if not arquivo_alvo:
        print("Operação cancelada.")
        return None

    try:
        # Abre o nano e espera o usuário fechar
        subprocess.call(['nano', arquivo_alvo])
        print(f"\nEdição de '{arquivo_alvo}' concluída.")
        
        # Tenta validar o arquivo logo após a edição
        if os.path.exists(arquivo_alvo):
            print("Validando alterações...")
            sim = carregar_configuracao_arquivo(arquivo_alvo)
            if sim:
                print("Arquivo válido! Carregado automaticamente.")
                return arquivo_alvo
            else:
                print("Aviso: O arquivo editado contém erros de formato.")
        return arquivo_alvo
        
    except Exception as e:
        print(f"Erro ao abrir editor: {e}")
        return arquivo_atual

def rodar_modo_completo(arquivo_config):
    """Roda o simulador do início ao fim."""
    print(f"Iniciando simulação (Modo Completo) de '{arquivo_config}'...")
    
    simulador = carregar_configuracao_arquivo(arquivo_config)
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
    print(f"Tempo total de simulação (real): {end_time - start_time:.4f} segundos.")
    print(f"Relógio final do sistema (ticks): {simulador.relogio_global - 1}")
    print("="*60)

    try:
        print(f"Gerando gráfico de Gantt em '{nome_saida}'...")
        gerar_imagem_gantt(
            simulador.gantt_log,
            simulador.tarefas,
            nome_saida,
            simulador.nome_algoritmo_config
        )
        print(f"Gráfico de Gantt salvo com sucesso em '{nome_saida}'")
    except Exception as e:
        print(f"Erro crítico ao gerar o gráfico: {e}", file=sys.stderr)

def rodar_modo_passo_a_passo(arquivo_config):
    """Roda o simulador com opção de avançar, voltar e gerar gráfico a cada passo."""
    print(f"Iniciando simulação (Passo-a-Passo) de '{arquivo_config}'...")
    
    simulador = carregar_configuracao_arquivo(arquivo_config)
    if simulador is None:
        print("Erro fatal: Falha ao recarregar o simulador.")
        return

    nome_saida = input("Digite o nome do arquivo de imagem (será atualizado a cada passo): ").strip()
    if not nome_saida:
        nome_saida = "gantt_passo_atual.png"
        
    try:
        while True:
            exibir_debugger(simulador)
            
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

            if simulador.terminou():
                print("\n--- SIMULAÇÃO CONCLUÍDA ---")
            
            comando = input("\n[Enter]=Avançar | [v]=Voltar | [s]=Sair: ").lower().strip()

            if comando == 's':
                print("Saindo do modo passo-a-passo...")
                break
            elif comando == 'v':
                sucesso = simulador.voltar_tick()
                if sucesso:
                    print("Voltando um passo no tempo...")
                else:
                    print(">> Você já está no início da simulação! Não dá para voltar.")
                    time.sleep(1.5)
            else:
                if simulador.terminou():
                    print("Simulação já terminou. Use 'v' para voltar ou 's' para sair.")
                    time.sleep(1.5)
                    continue 
                simulador.tick()
        
    except KeyboardInterrupt:
        print("\nRetornando ao menu principal.")
        return

# --- Loop Principal ---

def main():
    arquivo_carregado = None
    
    while True:
        exibir_menu(arquivo_carregado)
        escolha = input("Escolha uma opção [1-5]: ").strip() # Atualizado para 1-5
        
        if escolha == '1':
            novo_arquivo = carregar_novo_arquivo()
            if novo_arquivo:
                arquivo_carregado = novo_arquivo
            pausar_e_continuar()
            
        elif escolha == '2':
            if arquivo_carregado is None:
                print("\nErro: Nenhum arquivo carregado. Use a opção [1] primeiro.")
            else:
                rodar_modo_completo(arquivo_carregado)
            pausar_e_continuar()

        elif escolha == '3':
            if arquivo_carregado is None:
                print("\nErro: Nenhum arquivo carregado. Use a opção [1] primeiro.")
            else:
                rodar_modo_passo_a_passo(arquivo_carregado)
            pausar_e_continuar()

        elif escolha == '4': # LÓGICA DE EDIÇÃO
            print("\nAbrindo editor...")
            time.sleep(1)
            novo_arquivo = editar_arquivo_config(arquivo_carregado)
            if novo_arquivo:
                arquivo_carregado = novo_arquivo
            pausar_e_continuar()

        elif escolha == '5':
            print("Saindo do simulador.")
            break
            
        else:
            print(f"\nOpção '{escolha}' inválida. Tente novamente.")
            pausar_e_continuar()

if __name__ == "__main__":
    main()
