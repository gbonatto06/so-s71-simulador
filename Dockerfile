# Usamos uma imagem slim do Python
FROM python:3.11-slim


# Instala dependências do sistema para o Matplotlib (backend 'Agg' para PNG)
# Isso é crucial para o Matplotlib rodar sem uma interface gráfica (X Server)
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-tk \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

#Define o diretorio para o codigo fonte
WORKDIR /opt/simulator-app


# Copia o arquivo de requisitos e instala as bibliotecas Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o código da nossa aplicação para dentro do container
COPY . .

# Define o "comando" padrão que será executado
# Isso rodará "python main.py"
ENTRYPOINT ["python", "/opt/simulator-app/main.py"]
