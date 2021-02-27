FROM python:3.8-alpine

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py .

# run gunicorn
CMD [ "gunicorn", "--bind", "0.0.0.0:5000", "--forwarded-allow-ips=\"*\"", "app:app"]