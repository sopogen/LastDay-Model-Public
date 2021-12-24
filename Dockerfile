
FROM python:3.7.5-alpine3.10

ENV LANG C.UTF-8

RUN apk update && \
    apk add --no-cache bash build-base gcc linux-headers libffi-dev \
    jq curl-dev openssl-dev

WORKDIR /home
COPY . .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8001
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--reload", "--port", "8001"]