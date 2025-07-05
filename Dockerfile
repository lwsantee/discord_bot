FROM python:3.13-slim 

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

COPY . /bot 
WORKDIR /bot 
RUN pip install -r requirements.txt

CMD ["python", "bot.py"]
