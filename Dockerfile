# FROM nikolaik/python-nodejs
FROM nikolaik/python-nodejs:python3.10-nodejs20


WORKDIR /app

COPY --from=mongo:latest /usr/bin/mongodump /usr/bin/mongodump

RUN apt-get update && apt-get install -y curl git lsof

RUN curl https://ed-webapp-public-assets.s3.ca-central-1.amazonaws.com/mongo_crypt_v1_ubuntu64.so -o mongo_crypt_v1_ubuntu64.so

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "main.py"]
