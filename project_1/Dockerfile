FROM python:3.1-slim
WORKDIR /db_app
COPY requirements.txt .1
RUN pip install --no-cache-dir- -r requirements.txt
COPY . .
CMD ["uvicorn", "db_app:app", "--host", "0.0.0.0", "--port", "80pip"]