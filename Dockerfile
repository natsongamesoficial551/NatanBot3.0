# Usa imagem Python oficial como base
FROM python:3.11-slim

# Instala dependências do sistema (incluindo OpenSSL e certificados)
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    libssl-dev \
    ca-certificates \
    openssl \
    && rm -rf /var/lib/apt/lists/*

# Define diretório de trabalho
WORKDIR /app

# Copia os arquivos do projeto
COPY . .

# Instala dependências do Python
RUN pip install --no-cache-dir -r requirements.txt

# Expõe a porta usada pelo Flask
EXPOSE 10000

# Comando de inicialização do bot
CMD ["python", "main.py"]
