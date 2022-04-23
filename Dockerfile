FROM python:3.9-slim

ADD ./ /simple-image-server
WORKDIR /simple-image-server/

CMD exec apt-get update
RUN pip install --no-cache-dir -r ./requirements.txt

CMD ["python", "-u", "-m", "src"]
