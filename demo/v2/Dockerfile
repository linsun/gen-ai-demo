FROM python:3

WORKDIR /app

RUN apt-get update && apt-get install -y \
  build-essential \
  curl \
  software-properties-common \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --upgrade -r requirements.txt

COPY . .

EXPOSE 8001

HEALTHCHECK CMD curl --fail http://localhost:8001/_stcore/health

ENTRYPOINT ["streamlit", "run", "Hello.py", "--server.port=8001", "--server.address=0.0.0.0"]