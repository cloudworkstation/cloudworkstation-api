FROM python:3.7-alpine

RUN apk --update --no-cache add python3-dev libffi-dev gcc musl-dev make libevent-dev build-base

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py ./

# run app
CMD [ "python", "wrapper.py" ]