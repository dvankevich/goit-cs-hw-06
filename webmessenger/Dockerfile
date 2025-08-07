FROM python:3.13-slim

WORKDIR /webmessenger

COPY . /webmessenger

RUN mv /webmessenger/.env.docker /webmessenger/.env && \
  pip install --no-cache-dir -r /webmessenger/requirements.txt

EXPOSE 3000
EXPOSE 5000

CMD ["python", "main.py"]