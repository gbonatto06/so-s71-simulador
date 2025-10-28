import os
import sys
import time
from simulator.parser import carregar_configuracao_arquivo
from simulator.gantt import gerar_imagem_gantt

# Funções auxiliares da interface

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
    print("  [4] Sair")
    print("-" * 60)

def exibir_debugger(simulador):
    """ Imprime o estado atual e aguarda o usuário """
    limpar_tela()
    print("="*60)
    print(f"MODO DEBUGGER (PASSO-A-PASSO) - {simulador.escalonador.__class__.__name__}")
    print("="*60)
    
    # Puxa as informações de debug do simulador
    print(simulador.get_debug_info())
    
    print("\n" + "="*60)
    try:
        input("Pressione Enter para o próximo tick (ou Ctrl+C para sair)...")
    except KeyboardInterrupt:
        print("\n\nSimulação interrompida pelo usuário.")
        raise # Levanta a exceção para ser tratada pelo loop principal

def pausar_e_continuar():
    """Pede ao usuário para pressionar Enter para voltar ao menu."""
    input("\nPressione Enter para voltar ao menu principal...")

# Funções de Lógica do Menu

def carregar_novo_arquivo():
    """Pede um nome de arquivo, tenta carregá-lo e retorna o nome se for válido."""
    arquivo = input("Digite o caminho do arquivo (ex: config.txt): ").strip()
    
    if not os.path.exists(arquivo):
        print(f"\nErro: Arquivo '{arquivo}' não encontrado.")
        return None
        
    # Tenta carregar o simulador apenas para validar o arquivo
    simulador_teste = carregar_configuracao_arquivo(arquivo)
    
    if simulador_teste is None:
        print("\nErro: Falha ao processar o arquivo. Verifique o formato.")
        return None
    
    print(f"\nArquivo '{arquivo}' validado e carregado com sucesso.")
    return arquivo

def rodar_modo_completo(arquivo_config):
    """Roda o simulador do início ao fim."""
    print(f"Iniciando simulação (Modo Completo) de '{arquivo_config}'...")
    
    # Recarrega o simulador do arquivo para garantir um estado limpo
    simulador = carregar_configuracao_arquivo(arquivo_config)
    if simulador is None:
        print("Erro fatal: Falha ao recarregar o simulador.")
        return

    nome_saida = input("Digite o nome do arquivo de imagem de saída (ex: gantt.png): ").strip()
    if not nome_saida:
        nome_saida = "gantt_resultado.png" # Valor padrão
    
    start_time = time.time()
    
    # Loop principal da simulação
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
            nome_saida
        )
    except Exception as e:
        print(f"Erro crítico ao gerar o gráfico: {e}", file=sys.stderr)

def rodar_modo_passo_a_passo(arquivo_config):
    """Roda o simulador tick por tick com intervenção do usuário."""
    print(f"Iniciando simulação (Passo-a-Passo) de '{arquivo_config}'...")
    
    # Recarrega o simulador
    simulador = carregar_configuracao_arquivo(arquivo_config)
    if simulador is None:
        print("Erro fatal: Falha ao recarregar o simulador.")
        return
        
    try:
        exibir_debugger(simulador) # Mostra o estado inicial (Tick 0)
        
        while not simulador.terminou():
            simulador.tick()
            exibir_debugger(simulador) # Mostra o estado após cada tick
            
        print("--- FIM DA SIMULAÇÃO ---")
        
    except KeyboardInterrupt:
        print("\nRetornando ao menu principal.")
        return # Usuário pressionou Ctrl+C no debugger

# Loop Principal

def main():
    arquivo_carregado = None
    
    while True:
        exibir_menu(arquivo_carregado)
        escolha = input("Escolha uma opção [1-4]: ").strip()
        
        if escolha == '1':
            # Carregar Arquivo
            novo_arquivo = carregar_novo_arquivo()
            if novo_arquivo:
                arquivo_carregado = novo_arquivo
            pausar_e_continuar()
            
        elif escolha == '2':
            # Rodar Completo
            if arquivo_carregado is None:
                print("\nErro: Nenhum arquivo carregado. Use a opção [1] primeiro.")
            else:
                rodar_modo_completo(arquivo_carregado)
            pausar_e_continuar()

        elif escolha == '3':
            # Rodar Passo-a-Passo
            if arquivo_carregado is None:
                print("\nErro: Nenhum arquivo carregado. Use a opção [1] primeiro.")
            else:
                rodar_modo_passo_a_passo(arquivo_carregado)
            pausar_e_continuar()

        elif escolha == '4':
            # Sair
            print("Saindo do simulador.")
            break
            
        else:
            print(f"\nOpção '{escolha}' inválida. Tente novamente.")
            pausar_e_continuar()

if __name__ == "__main__":
    main()
