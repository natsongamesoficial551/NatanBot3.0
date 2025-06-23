FROM debian:bullseye-slim

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-venv \
    build-essential libssl-dev libffi-dev \
    curl ca-certificates openssl \
 && rm -rf /var/lib/apt/lists/*

# Diretório de trabalho
WORKDIR /app

# Copiar arquivos
COPY . .

# Instalar dependências do projeto
RUN pip3 install --upgrade pip
RUN pip3 install --no-cache-dir -r requirements.txt

# Expor porta para Flask
EXPOSE 10000

# Iniciar o bot
CMD ["python3", "main.py"]
