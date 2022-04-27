# Extracursus

## Motivation

The website that my university uses to handle our grades is old and not practical to use
on mobile. To view our grades, we don't only have to zoom a lot to be able to interact
with the site, but also download a PDF.

Since I was tired of going through all of this each time I wanted to view my grades on my
phone, and that I've wanted to practice using Flask I've decided to build this simple
app. Below you will find some instruction on how to download and run a working copy
of it. Have fun!

## Installation

To get a running copy of *Extracursus*, please follow the following instructions:

1. ### Clone this repository

   ```sh
   git clone https://github.com/itskatt/extracursus
   ```

2. ### Install requirements
   - #### Python
     This app has been tested succesfully on Python `3.8.8` and `3.10.2`,
     but any version above `3.6.x` should work.

   - #### Pip requirements
   
      ```sh
      pip install -r --user requirements.txt
      ```

      *Note: if you wish not to pollute your environement, you can use a [virtual environement](https://docs.python.org/3/library/venv.html)*

3. ### Configure a secret key  
   First generate it

   ```py
   >>> import secrets
   >>> secrets.token_hex()
   '18e5c6edc1c5...'
   ```

   Then set it as an environment variable to be able tu use it

   ```sh
   export FLASK_SECRET_KEY=18e5c6edc1c5...
   ```

Congratulations, you have successfully installed the app, now you can either:
   - Run the app in debug mode (for development):
     
     ```sh
     export FLASK_ENV=development
     export FLASK_APP=extracursus
     flask run
     ```

   - Run the app in production mode (when deployed on a server)
     
     ```sh
     waitress-serve --port=8080 extracursus:app
     ```

## Licence

See [LICENCE](LICENCE)
