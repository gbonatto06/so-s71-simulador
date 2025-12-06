# Simulador de Escalonador de Processos

> **Universidade Tecnológica Federal do Paraná (UTFPR) - Câmpus Curitiba**  
> **Curso:** Sistemas de Informação  
> **Disciplina:** Sistemas Operacionais

Este projeto implementa um **simulador visual de um sistema operacional multitarefa**. Ele permite visualizar o comportamento de diferentes algoritmos de escalonamento, gerando gráficos de Gantt automaticamente e oferecendo modos de execução passo-a-passo com recursos avançados de depuração e "viagem no tempo" (undo).

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

### Visualização e Interatividade

* **Geração de Gráficos:** Gera arquivos PNG do Gráfico de Gantt, diferenciando tempo de execução (cor) e tempo de espera (sombra cinza).
* **Modo Debugger (Passo-a-Passo):**
  * Visualização do estado da CPU e Filas a cada *tick*.
  * **Time Travel (Undo):** Permite voltar no tempo para desfazer ações (`v`).
  * **Inserção Dinâmica:** Permite adicionar novas tarefas durante a execução (`n`).
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

1. **Crie o arquivo de configuração**

   * Crie um arquivo chamado `config.txt` na sua pasta atual.
   * Formato:

     ~~~plaintext
     ALGORITMO;QUANTUM[;ALPHA]
     ID;COR;TEMPO_INGRESSO;DURACAO;PRIORIDADE
     ...
     ~~~

     > **Nota:** O campo opcional `;ALPHA` só deve ser incluído ao usar o `PRIOPEnv`.

   * Exemplo (`config.txt`) utilizando o Envelhecimento:

     ~~~plaintext
     PRIOPEnv;2;2
     T1;red;0;20;1
     T2;blue;2;20;10
     ~~~

2. **Execute o simulador**

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
* `n`: Nova Tarefa. Permite inserir uma tarefa manualmente no meio da execução.
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
    ├── core.py         # Motor da simulação (Loop, TCB, Snapshot)
    ├── schedulers.py   # Implementação dos algoritmos nativos
    ├── parser.py       # Leitor de config e carregador de plugins
    └── gantt.py        # Gerador de gráficos (Matplotlib)
~~~
