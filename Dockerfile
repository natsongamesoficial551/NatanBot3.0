# Usa imagem Python oficial como base
FROM python:3.11-slim

# Instala dependências do sistema (inclusive OpenSSL e CA certs)
RUN apt-get update && apt-get install -y \
    ca-certificates \
    openssl \
    && rm -rf /var/lib/apt/lists/*

# Define diretório de trabalho
WORKDIR /app

# Copia os arquivos do projeto
COPY . .

# Instala dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Expõe a porta (se necessário)
EXPOSE 10000

# Comando de execução do bot
CMD ["python", "main.py"]
