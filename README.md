Simulador de Escalonador de Processos (SO)
Universidade Tecnológica Federal do Paraná (UTFPR) - Câmpus Curitiba > Curso: Sistemas de Informação

Disciplina: Sistemas Operacionais

Este projeto implementa um simulador visual de um sistema operacional multitarefa. Ele permite visualizar o comportamento de diferentes algoritmos de escalonamento, gerando gráficos de Gantt e oferecendo modos de execução passo-a-passo com recursos avançados de depuração.

Funcionalidades
Algoritmos Suportados:

FIFO (First-In, First-Out): Não-preemptivo.
Round Robin (RR): Ativado automaticamente ao selecionar FIFO com Quantum > 0.
SRTF (Shortest Remaining Time First): Preemptivo.
Prioridade Preemptivo (PRIORIDADEP): Preemptivo (Maior número = Maior prioridade).
Plugins Externos: Capacidade de carregar algoritmos personalizados via Python.
Visualização: Gera gráficos de Gantt em PNG automaticamente, diferenciando tempo de execução (cor) e tempo de espera (cinza/sombra).

Modo Passo-a-Passo Interativo:

Visualização do estado da CPU e Filas a cada tick.
Time Travel (Undo): Permite voltar no tempo para desfazer ações.
Inserção Dinâmica: Permite adicionar novas tarefas durante a execução.
Geração de gráfico em tempo real a cada passo.
Portabilidade Total: Execução via Docker, garantindo funcionamento em qualquer máquina Linux sem instalação de dependências.

Pré-requisitos
A única ferramenta necessária é o Docker.

Bash

sudo apt update
sudo apt install docker.io -y

Como Rodar (Guia Rápido)
A imagem do projeto já está compilada e hospedada no Docker Hub. Você não precisa baixar o código-fonte, apenas criar um arquivo de configuração.

1. Crie o arquivo de configuração
Crie um arquivo chamado config.txt na sua pasta atual.

Formato:

Linha 1: ALGORITMO;QUANTUM
Linhas seguintes: ID;COR;TEMPO_INGRESSO;DURACAO;PRIORIDADE

Exemplo (config.txt):

Plaintext

SRTF;3
T1;red;0;5;2
T2;green;1;4;5
T3;blue;2;2;1
2. Execute o Simulador
Abra o terminal na pasta onde você salvou o config.txt e rode:

Bash

sudo docker run -it --rm -v "$(pwd)":/data gbonatto06/so-simulator
-it: Ativa o modo interativo (para o menu).
--rm: Remove o container ao sair (para não ocupar espaço).
-v "$(pwd)":/data: Mapeia sua pasta atual (host) para a pasta de dados do container. É assim que ele lê seu config.txt e salva o gráfico gantt.png no seu computador.


O Menu Interativo
Ao iniciar, você verá as seguintes opções:

[1] Carregar Arquivo: Digite o nome do seu arquivo (ex: config.txt).
[2] Executar (Modo Completo): Roda a simulação inteira e gera o gráfico final.
[3] Executar (Modo Passo-a-Passo): O modo "Debugger".

Enter: Avança um tick no tempo no modo passo a passo.
v: Volta um tick (Desfazer/Undo).
n: Nova Tarefa. Permite inserir uma tarefa manualmente no meio da execução.

[4] Editar Arquivo: Abre o editor nano dentro do container para você ajustar o config.txt sem precisar sair.
[5] Carregar Plugins: (Veja seção Avançada abaixo).


Funcionalidades Avançadas
1. Algoritmos Personalizados (Plugins)
Você pode criar seu próprio escalonador em Python e injetá-lo no simulador sem recompilar nada.

Crie uma pasta chamada extensions no seu computador.

Crie um arquivo Python (ex: loteria.py) dentro dela. Sua classe deve herdar de Scheduler.

Execute o Docker mapeando essa pasta também:

Bash

sudo docker run -it --rm \
  -v "$(pwd)":/data \
  -v "$(pwd)/extensions":/opt/simulator-app/extensions \
  gbonatto06/so-simulator
No menu, escolha a opção [5] Carregar Plugins.

No config.txt, use o nome da sua classe (ex: LOTERIA;3).

2. Acesso ao Código (Desenvolvedor)
Se você precisar inspecionar o código-fonte rodando dentro do container para fins de apresentação ou auditoria:

Inicie o container com um nome fixo:

Bash

sudo docker run -it --rm -v "$(pwd)":/data --name simulador-app gbonatto06/so-simulator
Abra um segundo terminal e execute:

Bash

sudo docker exec -it simulador-app /bin/bash
Navegue até a pasta do código:

Bash

cd /opt/simulator-app
ls -l


Estrutura do Projeto (Para Desenvolvedores)
Se você baixar o código-fonte, a estrutura é organizada da seguinte forma:

/
├── main.py             # Ponto de entrada e interface CLI (Menu)
├── Dockerfile          # Receita da imagem Docker
├── requirements.txt    # Dependências Python (matplotlib)
└── simulator/          # Biblioteca Core (Package)
    ├── __init__.py     # Marcador de pacote
    ├── core.py         # Motor da simulação (Loop, TCB, Snapshot)
    ├── schedulers.py   # Implementação dos algoritmos nativos
    ├── parser.py       # Leitor de config e carregador de plugins
    └── gantt.py        # Gerador de gráficos (Matplotlib)
