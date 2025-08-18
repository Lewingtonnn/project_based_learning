FROM python:3.10-slim-buster
WORKDIR /db_app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "db_app:app", "--host", "0.0.0.0", "--port", "8000"]