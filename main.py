# Imports
# ---------------------------------------------------------------------------- #
from datetime import date
from os import getenv
from random import choices

from flask import Flask, render_template, request
import requests as req

# App Config.
# ---------------------------------------------------------------------------- #
app = Flask(__name__)
# app.config.from_object('config')

# Constants
# ---------------------------------------------------------------------------- #
SHEETY_TOKEN = getenv("SHEETY_TOKEN")
ENDPOINT = getenv("SHEETY_ENDPOINT")
PORT = getenv("PORT")
DUMMY_DATA = {
    "website": "",
    "user": "",
    "length": "10",
    "a_flag": True,
    "d_flag": True,
    "s_flag": True,
    "login_link": "",
    "password": "",
}


# Functions
# ---------------------------------------------------------------------------- #
def fetch_data():
    website = request.form.get("website")
    user = request.form.get("user")
    length = request.form.get("length")
    a_flag = request.form.get("a_flag")
    d_flag = request.form.get("d_flag")
    s_flag = request.form.get("s_flag")
    login_link = request.form.get("login_link")
    password = request.form.get("password")
    return {
        "website": website,
        "user": user,
        "length": length,
        "a_flag": a_flag,
        "d_flag": d_flag,
        "s_flag": s_flag,
        "login_link": login_link,
        "password": password,
    }


def generate_password(**kwargs):
    length = int(kwargs["length"])
    chars = ""
    if kwargs["a_flag"]:
        chars += "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    if kwargs["d_flag"]:
        chars += "01234567890123456789"
    if kwargs["s_flag"]:
        chars += "-_.!~*'()-_.!~*'()"
    return "".join(choices(chars, k=length))


def search_password(**kwargs):
    headers = {"Authorization": SHEETY_TOKEN}
    params = {
        "filter[website]": kwargs["website"],
        "filter[username/email]": kwargs["user"]
    }
    response = req.get(ENDPOINT, headers=headers, params=params).json()
    response = response["main"][0] if response["main"] else None
    if response:
        hash = response["hash"].split(":")
        return {
            "length": hash[1],
            "a_flag": "a" in hash[0],
            "d_flag": "d" in hash[0],
            "s_flag": "s" in hash[0],
            "password": hash[2],
            "login_link": response["loginLink"]
        }
    return {"password": ""}


def save_password(**kwargs):
    headers = {
        "Authorization": SHEETY_TOKEN,
        "Content-Type": "application/json",
    }
    flags = ""
    if kwargs["a_flag"]:
        flags += "a"
    if kwargs["d_flag"]:
        flags += "d"
    if kwargs["s_flag"]:
        flags += "s"
    body = {
        "main": {
            "website": kwargs["website"],
            "username/email": kwargs["user"],
            "createdAt": str(date.today()),
            "hash": f"{flags}:{kwargs['length']}:{kwargs['password']}",
            "loginLink": kwargs["login_link"]
        }
    }
    response = req.post(ENDPOINT, headers=headers, json=body)
    return response.status_code, response.json()


# Controllers
# ---------------------------------------------------------------------------- #
@app.route('/')
def home():
    data = DUMMY_DATA
    return render_template('index.html', **data)


@app.route("/search", methods=["post"])
def search():
    data = fetch_data()
    data.update(search_password(**data))
    print(data)
    if not data["password"]:
        data["hasAlert"] = True
        data["alert"] = "⚠️ No password found."
    return render_template('index.html', **data)


@app.route("/generate", methods=["post"])
def generate():
    data = fetch_data()
    data["password"] = generate_password(**data)
    return render_template('index.html', **data)


@app.route("/save", methods=["post"])
def save():
    data = fetch_data()
    data["hasAlert"] = True
    if not data["password"]:
        data["alert"] = "⚠️ Password is needed to save."
        return render_template('index.html', **data)
    status_code, reply = save_password(**data)
    print(status_code, reply)
    data["alert"] = "🆗 Password is saved."
    data.update(DUMMY_DATA)
    return render_template('index.html', **data)


# Launch
# ---------------------------------------------------------------------------- #
app.run(host='0.0.0.0', port=PORT, debug=True)
