'''
Kalimul Kaif, David Lee, Ethan Saldanha, Mottaqi Abedin
MKED
SoftDev 2025
P01 -- ArRESTed Development
2025-12-22
Time spent: 2 hr
'''
from flask import Flask, request, session, redirect, url_for, render_template
import csv
import sqlite3
import random
import time
import os
import requests
from datetime import datetime

app = Flask(__name__)

app.secret_key = "secret_key_testing"
DB_FILE = "api_website.db"
KEYS_DIR = os.path.join(os.path.dirname(__file__), "keys")

def load_api_keys():
  keys = {}

  if not os.path.isdir(KEYS_DIR):
    print("No Keys directory found. API calls will not occur.")
    return keys

  for filename in os.listdir(KEYS_DIR):
    if not filename.startswith("key_") or not  filename.endswith(".txt"):
      continue
    filepath = os.path.join(KEYS_DIR, filename)
    api_name = filename[4:-4]
    api_name_upper = api_name.upper()

    try:
      with open(filepath, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f.readlines()]
        key_value = next((line for line in lines if line), "")
    except Exception as e:
      print(f"Failed to read {filename}")

    if not key_value:
      print(f"{filename} is empty. No key for '{api_name_upper}'.")
      continue

    keys[api_name_upper] = key_value
    print(f"loaded key {api_name_upper}")

  print("API_KEYS loaded:", list(keys.keys()))
  return keys


API_KEYS = load_api_keys()

def get_api_key(name):
  name_upper = name.upper()
  key = API_KEYS.get(name_upper)
  if key is None:
    print(f"API key for '{name}' is missing. Any features will not work.")
  return key

def USAJOBS(keyword, location):
    url = "https://data.usajobs.gov/api/search"
    headers = {
        "User-Agent": "esaldanha60@stuy.edu",
        "Authorization-Key": get_api_key("us-govt-jobs")
    }
    params = {
        "LocationName": location,
        "ResultsPerPage": 50,
        "Keyword": keyword
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=6)
        data = response.json()
    except Exception as e:
        print("USAJOBS request failed:", e)
        return {}, "Error contacting USAJOBS API."

    employers = {}  # employer_name -> list of (locationName, lat, lon)
    user_loc = (location or "").strip().lower()

    try:
        for job in data["SearchResult"]["SearchResultItems"]:
          descriptor = job["MatchedObjectDescriptor"]
          employer = descriptor.get("OrganizationName", "Unknown Employer")
          locations = descriptor.get("PositionLocation", [])
          if employer not in employers:
            employers[employer] = []
          for loc in locations:
            name = loc.get("LocationName")
            lat = loc.get("Latitude")
            lon = loc.get("Longitude")
            if not name:
              continue
            if user_loc and user_loc not in name.lower():
              continue
            
            if lat is not None and lon is not None:
              employers[employer].append((name, lat, lon))

        return employers, None

    except Exception as e:
        print("Parsing error:", e)
        return {}, "Error parsing USAJOBS API response."

def initialize_db():
  db = sqlite3.connect(DB_FILE)
  c = db.cursor()

  c.execute("CREATE TABLE IF NOT EXISTS users(username TEXT, password TEXT, email TEXT, creation_date DATE);")
  c.execute("CREATE TABLE IF NOT EXISTS saved_locations(id TEXT, username TEXT, state TEXT, city TEXT, job_title TEXT, avg_salary INTEGER, weather_condition TEXT, date_saved DATE);")
  c.execute("CREATE TABLE IF NOT EXISTS search_history(id TEXT, username TEXT, timestamp DATE, job_title TEXT, filters_applied TEXT);")

  db.commit()
  db.close()

@app.route("/", methods=['GET', 'POST'])
def index():
  if 'username' in session:
    return redirect(url_for('homepage'))
  else:
    text = ""
    return render_template("login.html", text=text)

@app.route("/login", methods=["GET", "POST"])
def login():
  if request.method == 'POST':
    username = request.form['username']
    password = request.form['password']
    db = sqlite3.connect(DB_FILE)
    c = db.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    db.close()

    if user == None or user[0] != username or user[1] != password:
      print("username/password do not match our records")
      text = "login failed, create new acc?"
      return render_template('login.html', text=text)
    elif user[0] == username and user[1] == password:
      session['username'] = username
      return redirect(url_for('homepage'))
    else:
      return redirect(url_for('index'))
  return redirect(url_for('index'))

@app.route("/register", methods=["GET", "POST"])
def register():
  if request.method == 'POST':
    db = sqlite3.connect(DB_FILE)
    c = db.cursor()
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']

    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    existing_user = c.fetchone()

    if existing_user:
      db.close()
      text = "username already taken, try another one!"
      return render_template('register.html', text = text)

    creation_date = int(time.time())

    c.execute(
        "INSERT INTO users VALUES (?, ?, ?, ?)",
        (username, email, password, creation_date)
    )
    db.commit()
    db.close()
    session['username'] = username
    return redirect(url_for('homepage'))
  return render_template('register.html')

@app.route("/homepage", methods=["GET", "POST"])
def homepage():
  if 'username' not in session:
    return redirect(url_for('index'))
  return render_template("homepage.html", username=session['username'])

@app.route("/profile", methods=["GET", "POST"])
def profile():
  return render_template("profile.html")

@app.route("/search", methods=["GET", "POST"])
def search():
    if 'username' not in session:
        return redirect(url_for('index'))

    if request.method == "POST":
        keyword = request.form.get("keyword", "").strip()
        location = request.form.get("location", "").strip()

        db = sqlite3.connect(DB_FILE)
        c = db.cursor()
        search_id = str(time.time())
        filters_applied = f"location={location}"
        c.execute(
            "INSERT INTO search_history VALUES (?, ?, ?, ?, ?)",
            (search_id, session['username'], int(time.time()), keyword, filters_applied)
        )
        db.commit()
        db.close()

        employers, error = USAJOBS(keyword, location)

        return render_template(
            "search.html",
            keyword=keyword,
            location=location,
            employers=employers,
            error=error
        )

    return render_template("search.html")

@app.route("/job")
def job_detail():
    if 'username' not in session:
        return redirect(url_for('index'))

    employer = request.args.get("employer", "Unknown Employer")
    location_name = request.args.get("location_name", "Unknown Location")
    lat = request.args.get("lat")
    lon = request.args.get("lon")

    if not lat or not lon:
        return "No location data available for this job.", 400

    return render_template(
        "job_detail.html",
        employer=employer,
        location_name=location_name,
        lat=lat,
        lon=lon,
    )

@app.route("/my_jobs", methods=["GET", "POST"])
def my_jobs():
  return render_template("my_jobs.html")

@app.route("/logout", methods=["GET", "POST"])
def logout():
  return render_template("login.html")

if __name__ == "__main__":
  initialize_db()
  app.debug = True
  app.run()
