FROM python:3.9

WORKDIR /app
RUN mkdir -p /tmp

COPY . /app

RUN pip install --upgrade -r requirements.txt

EXPOSE 8001

HEALTHCHECK CMD curl --fail http://localhost:8001/_stcore/health

ENTRYPOINT ["streamlit", "run", "Hello.py", "--server.port=8001", "--server.address=0.0.0.0"]