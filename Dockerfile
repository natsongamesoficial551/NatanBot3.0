# Usa imagem Python oficial como base
FROM python:3.11-slim

# Define diretório de trabalho no container
WORKDIR /app

# Copia todos os arquivos para o container
COPY . .

# Instala dependências
RUN pip install --no-cache-dir -r requirements.txt

# Expõe a porta que o Flask vai usar
EXPOSE 10000

# Comando para iniciar o bot
CMD ["python", "main.py"]
