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
      jobslist=[]
      jobs = {}
      requirements=[]

      for job in data["SearchResult"]["SearchResultItems"]:
          descriptor = job["MatchedObjectDescriptor"]
          jobs.update({"employer":descriptor.get("OrganizationName")})
          jobs.update({"locations":descriptor.get("PositionLocation", [])})
          jobs.update({"schedule":descriptor.get("PositionSchedule")[0]})
          jobs.update({"start":descriptor.get("PositionStartDate")})
          jobs.update({"end":descriptor.get("PositionEndDate")})

          ##
          requirements.append(descriptor.get("UserArea")["Details"]["Education"])
          requirements.append(descriptor.get("UserArea")["Details"]["Requirements"])
          requirements.append(descriptor.get("UserArea")["Details"]["WhoMayApply"]["Name"])
          jobs.update({"requirements":requirements})

      jobslist.append(jobs)
      jobs={}
      return jobslist

    except Exception as e:
        print("Parsing error:", e)
        return {}, "Error parsing USAJOBS API response."

def initialize_db():
  db = sqlite3.connect(DB_FILE)
  c = db.cursor()
  
  c.execute("CREATE TABLE IF NOT EXISTS users(username TEXT, password TEXT, email TEXT, creation_date DATE);")
  c.execute("CREATE TABLE IF NOT EXISTS saved_locations(id TEXT, username TEXT, job_title TEXT, employer TEXT, location TEXT, schedule TEXT, start_date TEXT, end_date TEXT, link TEXT, requirements TEXT, date_saved DATE);")
  # (job_id, username, employer, location_name, schedule, start_date, end_date, link, requirements, date_saved)
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
  if 'username' not in session:
    return redirect(DB_FILE)
    c = db.cursor()
    username = session['username']

    c.execute("SELECT bio, creation_date from users WHERE username = ?", (username, ))
    result = c.fetchone()
    bio = result[0] if result and result[0] else None
    creation_date = result[1] if result else None

    formatted_creation_date = None
    if creation_date:
      dt = datetime.fromtimestamp(creation_date)
      formatted_creation_date = dt.strftime("%B, %d, %Y")

  c.execute("SELECT blog_name FROM blogs WHERE blog_creator = ?", (username,))
  blogs_raw = c.fetchall()

  db.close()
  return render_template("profile.html", username = username, bio = bio, curr_user = session['username'], creation_date = formatted_creation_date)

@app.route("/edit_profile", methods=["GET", "POST"])
def edit_profile():
  if 'username' not in session:
    return redirect(url_for('index'))

  username = session['username']
  db = sqlite3.connect(DB_FILE)
  c = db.cursor()
  
  if request.method == "POST":
    bio = request.form.get("bio")
    if bio is not None:
      c.execute("UPDATE users SET bio = ? WHERE username = ?", (bio, username))
      db.commit()
    db.close() 
    return redirect(url_for('profile'))

  c.execute("SELECT bio FROM users WHERE username = ?", (username, ))
  result = c.fetchone()
  bio = result[0] if result and result[0] else None

  db.close()
  return render_template("edit_profile.html", username = username, bio = bio)

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

        jobs = USAJOBS(keyword, location)

        return render_template(
            "search.html",
            keyword=keyword,
            location=location,
            jobs=jobs
        )

    return render_template("search.html")

@app.route("/job")
def job_detail():
    if 'username' not in session:
        return redirect(url_for('index'))

    job_title = request.args.get("job_title", "")
    employer = request.args.get("employer", "")
    location_name = request.args.get("location_name", "")
    lat = request.args.get("lat")
    lon = request.args.get("lon")
    schedule = request.args.get("schedule", "")
    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")
    link = request.args.get("link", "")
    requirements = request.args.get("requirements", "")

    if not lat or not lon:
        return "No location data available for this job.", 400

    return render_template(
        "job_detail.html",
        job_title=job_title,
        employer=employer,
        location_name=location_name,
        lat=lat,
        lon=lon,
        schedule=schedule,
        start_date=start_date,
        end_date=end_date,
        link=link,
        requirements=requirements
    )

@app.route("/my_jobs", methods=["GET", "POST"])
def my_jobs():
  if 'username' not in session:
    return redirect(url_for('index'))
  
  username = session['username']
  db = sqlite3.connect(DB_FILE)
  c = db.cursor()

  c.execute(
    "SELECT * FROM saved_locations WHERE username = ? ORDER BY date_saved DESC",
    (username)
  )
  saved_jobs = c.fetchall()
  db.close()

  return render_template("my_jobs.html", saved_jobs=saved_jobs)

@app.route("/logout", methods=["GET", "POST"])
def logout():
  return render_template("login.html")

@app.route("/save_job", methods=["GET", "POST"])
def save_job():
  if 'username' not in session:
    return redirect(url_for('index'))
  
  username = session['username']
  job_title = request.form.get("job_title")
  employer = request.form.get("employer")
  location_name = request.form.get("location_name")
  schedule = request.form.get("schedule", "")
  start_date = request.form.get("start_date", "")
  end_date = request.form.get("end_date", "")
  link = request.form.get("link", "")
  requirements = request.form.get("requirements", "")

  db = sqlite3.connect(DB_FILE)
  c = db.cursor()

  job_id = str(time.time())
  date_saved = int(time.time())

  c.execute(
        "INSERT INTO saved_locations VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (job_id, username, job_title, employer, location_name, schedule, start_date, end_date, link, requirements, date_saved)
  )
  db.commit()
  db.close()

  return redirect(url_for('my_jobs'))

if __name__ == "__main__":
  initialize_db()
  app.debug = True
  app.run()
