# Simulador de Escalonador de Processos

> **Universidade Tecnológica Federal do Paraná (UTFPR) - Câmpus Curitiba** > **Curso:** Sistemas de Informação  
> **Disciplina:** Sistemas Operacionais

Este projeto implementa um **simulador visual de um sistema operacional multitarefa**. Ele permite visualizar o comportamento de diferentes algoritmos de escalonamento, **operações de Entrada/Saída (E/S) e sincronização por Mutex**, gerando gráficos de Gantt automaticamente e oferecendo modos de execução passo-a-passo com recursos avançados de depuração e "viagem no tempo" (undo).

---

## Índice

* [Funcionalidades](#funcionalidades)
* [Pré-requisitos](#pré-requisitos)
* [Como Rodar (Guia Rápido)](#como-rodar-guia-rápido)
* [Menu Interativo](#menu-interativo)
* [Funcionalidades Avançadas](#funcionalidades-avançadas)
* [Estrutura do Projeto](#estrutura-do-projeto)

---

## Funcionalidades

### Algoritmos Suportados

* **FIFO (First-In, First-Out):** Não-preemptivo.
* **Round Robin (RR):** Ativado automaticamente ao selecionar FIFO com `Quantum > 0`.
* **SRTF (Shortest Remaining Time First):** Preemptivo.
* **Prioridade Preemptivo (PRIORIDADEP):** Preemptivo (Maior número = Maior prioridade).
* **Prioridade com Envelhecimento (PRIOPEnv):** Preemptivo. Utiliza o parâmetro **Alpha** para prevenir inanição (_starvation_).
* **Plugins Externos:** Capacidade de carregar algoritmos personalizados via Python sem recompilar.

### Simulação de Recursos e E/S

* **Operações de E/S Assíncronas:** Simula tarefas que liberam a CPU para realizar operações de disco/rede (representadas visualmente no gráfico).
* **Sincronização (Mutex):** Suporte a bloqueio e desbloqueio de recursos compartilhados (`Lock`/`Unlock`), incluindo lógica de **Herança de Prioridade** para evitar inversão de prioridade.

### Visualização e Interatividade

* **Geração de Gráficos:** Gera arquivos PNG do Gráfico de Gantt detalhado:
  * **Cores Sólidas:** Tempo de execução (CPU).
  * **Sombra Cinza:** Tempo de espera na fila de prontos.
  * **Amarelo/Laranja (IO):** Tempo de bloqueio por Entrada/Saída.
  * **Vermelho/Rosa:** Tempo de bloqueio aguardando liberação de Mutex.
  * **Marcadores:** Triângulos indicam aquisição (`ML`) e liberação (`MU`) de recursos.
* **Modo Debugger (Passo-a-Passo):**
  * Visualização do estado da CPU, Filas e Tarefas Bloqueadas a cada *tick*.
  * **Time Travel (Undo):** Permite voltar no tempo para desfazer ações (`v`).
  * **Inserção Dinâmica:** Permite adicionar novas tarefas (com ações de Mutex ou E/S) durante a execução (`n`).
  * Atualização do gráfico em tempo real.
* **Portabilidade Total:** Execução via Docker, garantindo funcionamento em qualquer máquina Linux.

---

## Pré-requisitos

A única ferramenta necessária é o **Docker**.

~~~bash
sudo apt update
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
~~~

---

## Como Rodar (Guia Rápido)

A imagem do projeto já está compilada e hospedada no Docker Hub. Você não precisa baixar o código-fonte, apenas criar um arquivo de configuração.

1. **Baixe a imagem do Docker Hub (opcional, mas recomendado)**

   * Isso garante que você está usando a versão mais recente da imagem:

     ~~~bash
     sudo docker pull gbonatto06/so-simulator:latest
     ~~~

2. **Crie o arquivo de configuração**

   * Crie um arquivo chamado `config.txt` na sua pasta atual.
   * Formato:

     ~~~plaintext
     ALGORITMO;QUANTUM[;ALPHA]
     ID;COR;TEMPO_INGRESSO;DURACAO;PRIORIDADE[;ACOES...]
     ...
     ~~~

     > **Nota:** O campo opcional `;ALPHA` só deve ser incluído ao usar algoritmos com envelhecimento como o `PRIOPEnv`.

   * **Definindo Ações (E/S e Mutex):**
     As ações são opcionais e separadas por ponto-e-vírgula no final da linha. O tempo é sempre relativo ao início da execução da tarefa.
     * **E/S (Input/Output):** `IO:inicio-duracao`
       * Ex: `IO:2-5` (No tempo de execução 2, sai para E/S por 5 ticks).
     * **Mutex Lock:** `MLid:tempo`
       * Ex: `ML1:0` (Tenta pegar o Mutex 1 no tempo 0).
     * **Mutex Unlock:** `MUid:tempo`
       * Ex: `MU1:4` (Libera o Mutex 1 no tempo 4).

   * Exemplo Completo (`config.txt`):

     ~~~plaintext
     ROUNDROBIN;4
     T_CpuPura; #e74c3c; 0; 10; 1
     T_IO;      #3498db; 0; 8;  2; IO:2-5
     T_Mutex;   #2ecc71; 2; 8;  3; ML1:1; MU1:6
     ~~~

3. **Execute o simulador**

   * Abra o terminal na pasta onde você salvou o `config.txt` e rode:

     ~~~bash
     sudo docker run -it --rm -v "$(pwd)":/data gbonatto06/so-simulator
     ~~~

   * Entendendo o comando:
     * `-it`: Ativa o modo interativo (necessário para ver o menu).
     * `--rm`: Remove o container automaticamente ao sair (economiza espaço).
     * `-v "$(pwd)":/data`: **Crucial.** Mapeia sua pasta atual (host) para a pasta de dados do container.  
       É assim que o simulador lê seu `config.txt` e salva o gráfico `gantt.png` no seu computador.

---

## Menu Interativo

Ao iniciar, você verá as seguintes opções no terminal:

* `[1] Carregar Arquivo`: Digite o nome do seu arquivo (ex: `config.txt`).
* `[2] Executar (Modo Completo)`: Roda a simulação inteira e gera o gráfico final.
* `[3] Executar (Modo Passo-a-Passo)`: Entra no modo *Debugger*.
* `[4] Editar Arquivo`: Abre o editor `nano` dentro do container para ajustar o `config.txt` sem sair.
* `[5] Carregar Plugins`: Carrega algoritmos externos (veja abaixo).

### Comandos do Modo Passo-a-Passo

* `Enter`: Avança um *tick* no tempo.
* `v`: Volta um *tick* (Desfazer / Undo).
* `n`: Nova Tarefa. Permite inserir uma tarefa manualmente no meio da execução (suporta sintaxe de E/S).
* `s`: Sair do modo passo-a-passo.

---

## Funcionalidades Avançadas

### 1. Algoritmos Personalizados (Plugins)

Você pode injetar seu próprio escalonador escrito em Python sem recompilar a imagem.

1. Crie uma pasta chamada `extensions` no seu computador.
2. Crie um arquivo Python (ex: `loteria.py`) dentro dela.  
   *Sua classe deve herdar de `Scheduler`.*
3. Execute o Docker mapeando essa pasta extra:

   ~~~bash
   sudo docker run -it --rm \
     -v "$(pwd)":/data \
     -v "$(pwd)/extensions":/opt/simulator-app/extensions \
     gbonatto06/so-simulator
   ~~~

4. No menu, escolha a opção `[5] Carregar Plugins`.
5. No `config.txt`, use o nome da sua classe (ex: `LOTERIA;3`).

### 2. Acesso ao Código (Desenvolvedor)

Para inspecionar o código-fonte rodando dentro do container:

1. Inicie o container com um nome fixo:

   ~~~bash
   sudo docker run -it --rm -v "$(pwd)":/data --name simulador-app gbonatto06/so-simulator
   ~~~

2. Abra um segundo terminal e execute:

   ~~~bash
   sudo docker exec -it simulador-app /bin/bash
   ~~~

3. Navegue até a pasta do código:

   ~~~bash
   cd /opt/simulator-app
   ls -l
   ~~~

---

## Estrutura do Projeto

Se você baixar o código-fonte, esta é a organização:

~~~plaintext
├── main.py             # Ponto de entrada e interface CLI (Menu)
├── Dockerfile          # Receita da imagem Docker
├── requirements.txt    # Dependências Python (matplotlib)
└── simulator/          # Biblioteca Core (Package)
    ├── __init__.py     # Marcador de pacote
    ├── core.py         # Motor da simulação (Loop, TCB, Snapshot, E/S, Mutex)
    ├── schedulers.py   # Implementação dos algoritmos nativos
    ├── parser.py       # Leitor de config e carregador de plugins
    └── gantt.py        # Gerador de gráficos (Matplotlib)
~~~
