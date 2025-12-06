Trabalho realizado pela Universidade Tecnológica Federal do Paraná - Câmpus Curitiba, no curso de Sistemas de Informação. O trabalho simula o comportamento de um escalonador de um sistema operacional com base em diferentes algoritmos de escalonamento, definidos com base em um arquivo config.txt.

Para rodar o projeto crie um arquivo config.txt contendo: “escalonador”;”quantum” “ID_Tarefa”;”Cor da tarefa”;”Tempo de entrada”;”Duracao”;”Prioridade”

Utilize o terminal dentro de uma pasta com o arquivo config.txt pronto:'sudo docker run -it --rm -v "$(pwd)":/data --name simulador-app gbonatto06/so-simulator' Para acessar o container utilize: 'sudo docker exec -it simulador-app /bin/bash' seguido de 'cd/opt/simulator-app' e estará na pasta dos arquivos do container.

Os arquivos enviados no moodle foram todos os arquivos de código exceto os arquivos de init.py que é um arquivo em branco, apenas para dizer que a pasta "simulator" é uma biblioteca.

Os arquivos core.py, schedulers.py, gantt.py, parser.py devem estar dentro de uma pasta "simulator". O restante deve ficar na pasta raiz.

O grafico de gantt gerado será copiado para a pasta local que executou o projeto.
