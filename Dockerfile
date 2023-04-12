
FROM python:3

RUN apt-get update && \
    apt-get install -y python3-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "./seu_script.py" ]

