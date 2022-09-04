FROM python:3

WORKDIR /usr/src/app

ADD app/main.py .

COPY requirements.txt ./
COPY app/data.json ./

RUN pip install --no-cache-dir -r requirements.txt

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]