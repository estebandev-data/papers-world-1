# Usa una imagen base de Python
FROM python:3.10-slim

# Establece el directorio de trabajo
WORKDIR /app

# Copia e instala dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo el código fuente del repositorio
COPY . .

# Comando para ejecutar la aplicación con Gunicorn
# Esto inicia la aplicación Flask usando Gunicorn
CMD exec gunicorn --bind :$PORT --workers 1 app:app