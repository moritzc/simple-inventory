FROM python:3.11-slim

WORKDIR /code
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY ./app ./app
COPY ./static ./static

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
