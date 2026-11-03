FROM python:3.12-slim

WORKDIR /code

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Solo se copia lo necesario (así el .env nunca entra en la imagen)
COPY app ./app
COPY run.py .

EXPOSE 5000

# --host 0.0.0.0 es necesario para que el puerto sea accesible desde fuera del contenedor
CMD ["flask", "--app", "run", "run", "--host", "0.0.0.0", "--port", "5000"]
