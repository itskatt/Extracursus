# -*- coding: utf-8 -*-
import io
import os
import time
from secrets import token_hex
from datetime import timedelta
from functools import lru_cache

from flask import (Flask, abort, make_response, redirect, render_template,
                   request, send_file, send_from_directory, session)
from flask_assets import Environment
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman

from .intra_client import IntraClient
from .pdf_reader import get_pdf_data

CACHE_DURATION = 900 # 15 minutes

app = Flask(__name__)

app.secret_key = token_hex()
app.permanent_session_lifetime = timedelta(minutes=10) # session will last 10 minutes

Environment(app)
Talisman(app, content_security_policy=None)

limiter = Limiter(
    get_remote_address,
    app=app,
    storage_uri="memory://"
)

active_clients = {}

# PDF caching ----------------------------------------------------
@lru_cache(maxsize=32)
def _dl_pdf_cached(username, semester, ttl_hash=None):
    """
    Dowloads a PDF or returns the one in cache
    """
    client = active_clients[username]
    app.logger.info(f"Dowloading pdf for {username}...")
    pdf = client.get_semester_pdf(semester)
    return pdf

@lru_cache(maxsize=64)
def _parse_pdf_cached(username, semester, ttl_hash=None):
    """
    Dowloads or gets the cached pdf and parses it
    """
    pdf = _dl_pdf_cached(username, semester, ttl_hash)
    return get_pdf_data(pdf)

def _get_ttl_hash(seconds):
    """
    Return the same value withing `seconds` time period
    """
    return round(time.time() / seconds)

def dl_and_parse_pdf(username, semester):
    """
    Will only get and parse a fresh new pdf once every hour
    """
    return _parse_pdf_cached(username, semester, _get_ttl_hash(CACHE_DURATION))

def dl_pdf(username, semester):
    """
    Downloads the pdf
    """
    return _dl_pdf_cached(username, semester, _get_ttl_hash(CACHE_DURATION))


# Index ------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")

# Login -------------------------------------------------------
@app.route("/login", methods=["POST"])
@limiter.limit("5 per minute")
@limiter.limit("1 per second")
def login():
    data = request.get_json()
    if not data:
        data = request.form

    try:
        username = data["username"]
        password = data["password"]
    except (KeyError, TypeError):
        abort(400)

    client = IntraClient()
    app.logger.info(f"Loggin in {username}...")

    # we try to login
    if not client.login(username, password):
        app.logger.info("Failed")
        return {
            "sucess": False
        }

    # login was a sucess
    app.logger.info("Getting semesters...")
    semesters = client.get_semesters()
    app.logger.info("All done!")

    # close the client on fresh login
    if username in active_clients.keys():
        active_clients[username].close()

    active_clients[username] = client
    session["username"] = username

    return {
        "sucess": True,
        "semesters": semesters
    }

# Pretty grades -------------------------------------------------------------
@app.route("/pretty_grades")
def pretty_grades():
    user = session.get("username")
    if not user:
        return redirect("/")

    client = active_clients.get(user)
    if client is None:
        return redirect("/")

    # if no semester is provided, we select the current one
    semester = request.args.get("sem", client.current_semester)

    if semester == "dev" and os.environ["FLASK_DEBUG"] == "1":
        app.logger.info("Using local pdf")
        with open("../semestre_TBFS2T.pdf", "rb",) as f:
            pdf_data = get_pdf_data(f.read())
    else:
        pdf_data = dl_and_parse_pdf(user, semester)
    
    return render_template("pretty_grades.html", semester=semester, pdf_data=pdf_data)

# Load pdf -------------------------------------------------------------------------
@app.route("/load_pdf")
def load_pdf():
    user = session.get("username")
    if not user:
        return redirect("/")

    client = active_clients.get(user)
    if client is None:
        return redirect("/")

    semester = request.args.get("sem", client.current_semester)

    app.logger.info(f"Loading {semester} pdf for {user}...")
    dl_pdf(user, semester)

    return "OK"

# Download PDF ------------------------------------------------------------------
@app.route("/pdf_dl")
def download_pdf():
    user = session.get("username")
    if not user:
        return redirect("/")

    client = active_clients.get(user)
    if client is None:
        return redirect("/")

    semester = request.args.get("sem", client.current_semester)

    pdf = dl_pdf(user, semester)
    return send_file(
        io.BytesIO(pdf),
        download_name=f"semestre_{semester}.pdf",
        as_attachment=True, # force download
        mimetype="application/pdf"
    )

# Whoami -----------------------------------------------------------------------
@app.route("/whoami")
def whoami():
    return session.get("username", "No one is logged in")

# Logout -------------------------------------------------------------------------
@app.route("/logout")
def logout():
    user = session.get("username")
    if user:
        app.logger.info(f"{user} is logging out")

        active_clients[user].close()
        del active_clients[user]
        session.pop("username", None)
        return f"Logged out {user}"
    return "No one to logout"

# Service worker for PWA --------------------------------------------------------
@app.route("/sw.js")
def service_worker():
    response = make_response(send_from_directory("static", "js/sw.js"))
    response.headers["Cache-Control"] = "no-cache"
    return response
