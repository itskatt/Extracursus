# -*- coding: utf-8 -*-
import os
import time
from datetime import timedelta
from functools import lru_cache

from flask import Flask, abort, redirect, render_template, request, session

from intra_client import IntraClient
from pdf_reader import get_grades

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "development key DO NOT USE OUTSIDE OF DEV")
app.permanent_session_lifetime = timedelta(minutes=10) # session will last 10 minutes

active_clients = {}

# PDF caching ----------------------------------------------------
@lru_cache()
def get_and_parse_pdf_for_cached(username, semester, ttl_hash=None):
    client = active_clients[username]
    app.logger.info(f"Dowloading pdf for {username}...")
    pdf = client.get_semester_pdf(semester)
    return get_grades(pdf)

def get_ttl_hash(seconds):
    """
    Return the same value withing `seconds` time period
    """
    return round(time.time() / seconds)

def get_and_parse_pdf_for(username, semester):
    """
    Will only get and parse a fresh new pdf once every hour
    """
    return get_and_parse_pdf_for_cached(username, semester, get_ttl_hash(3600))


# Index ------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")

# Login -------------------------------------------------------
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    try:
        username = data["username"]
        password = data["password"]
    except KeyError:
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
    semesters = client.get_semesters() # TODO: save object
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
    semester = request.args.get("sem", client.semesters[0])

    subjects = get_and_parse_pdf_for(user, semester)
    return render_template("pretty_grades.html", semester=semester, subjects=subjects)

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

# Testing/Debuging -------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
