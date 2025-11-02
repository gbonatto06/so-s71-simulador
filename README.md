Trabalho realizado pela Universidade Tecnológica Federal do Paraná - Câmpus Curitiba, no curso de Sistemas de Informação.
O trabalho simula o comportamento de um escalonador de um sistema operacional com base em diferentes algoritmos de escalonamento, definidos com base em um arquivo config.txt

Para rodar o projeto utilize no terminal dentro da pasta do projeto e com o arquivo config.txt pronto:'sudo docker run -it --rm -v "$(pwd)":/data --name simulador-app gbonatto06/so-simulator'
Para acessar o container utilize: 'sudo docker exec -it simulador-app /bin/bash' seguido de 'cd/opt/simulator-app' e estara na pasta dos arquivos do container

O grafico de gantt gerado sera copiado para a pasta local que executou o projeto
