FROM python:3.11-alpine

WORKDIR /app

COPY . .
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8080

CMD ["waitress-serve", "--port=8080", "extracursus:app"]
