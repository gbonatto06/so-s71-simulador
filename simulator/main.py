import argparse
import os
import sys
import time
from simulator.parser import carregar_configuracao_arquivo
from simulator.gantt import gerar_imagem_gantt

def exibir_debugger(simulador):
    """ Imprime o estado atual e aguarda o usuário """
    # Limpa a tela
    print("\033[H\033[J", end="")
    
    print("="*60)
    print(f"MODO DEBUGGER - {simulador.escalonador.__class__.__name__}")
    print("="*60)
    
    # Puxa as informações de debug do simulador
    print(simulador.get_debug_info())
    
    print("\n" + "="*60)
    try:
        input("Pressione Enter para o próximo tick (ou Ctrl+C para sair)...")
    except KeyboardInterrupt:
        print("\n\nSimulação interrompida pelo usuário.")
        sys.exit(0)

def main():
    parser = argparse.ArgumentParser(
        description="Simulador de Escalonador de SO.",
        epilog="Exemplo: python3 main.py config.txt --modo passo-a-passo"
    )
    
    # Argumento posicional obrigatório
    parser.add_argument(
        "arquivo_config", 
        help="Caminho para o arquivo de configuração da simulação."
    )
    
    # Argumentos opcionais
    parser.add_argument(
        "--modo", 
        choices=['passo-a-passo', 'completo'], 
        default='completo', 
        help="Modo de execução."
    )
    parser.add_argument(
        "--saida", 
        default='gantt_resultado.png', 
        help="Nome do arquivo de imagem de saída."
    )
    
    args = parser.parse_args()

    # Carregamento do arquivo parser
    
    if not os.path.exists(args.arquivo_config):
        print(f"Erro: Arquivo de configuração '{args.arquivo_config}' não encontrado.", file=sys.stderr)
        sys.exit(1)

    print(f"Carregando simulação de '{args.arquivo_config}'...")
    simulador = carregar_configuracao_arquivo(args.arquivo_config)
    
    if simulador is None:
        print("Falha ao carregar o simulador. Verifique o arquivo de configuração.", file=sys.stderr)
        sys.exit(1)

    # Execuão
    
    print(f"Iniciando simulação no modo: {args.modo}")
    start_time = time.time()
    
    if args.modo == 'passo-a-passo':
        # Exibe o estado inicial antes do primeiro 'tick()'
        exibir_debugger(simulador)

    # Loop principal da simulação
    while not simulador.terminou():
        log_tick = simulador.tick()
        
        if args.modo == 'passo-a-passo':
            print(log_tick) # imprimir o log do tick
            exibir_debugger(simulador)
        elif args.modo == 'completo':
            # Imprime um "progresso" simples
            if simulador.relogio_global % 50 == 0:
                print(f" ... simulando tick {simulador.relogio_global}", end='\r')

    # Resultados
    
    end_time = time.time()
    print("\n" + "="*60)
    print("Simulação concluída.")
    print(f"Tempo total de simulação (real): {end_time - start_time:.4f} segundos.")
    print(f"Relógio final do sistema (ticks): {simulador.relogio_global - 1}")
    print("="*60)

    # Geração do gráfico
    try:
        print(f"Gerando gráfico de Gantt em '{args.saida}'...")
        gerar_imagem_gantt(
            simulador.gantt_log,
            simulador.tarefas,
            args.saida
        )
    except Exception as e:
        print(f"Erro crítico ao gerar o gráfico: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
