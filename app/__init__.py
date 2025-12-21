'''
Kalimul Kaif, David Lee, Ethan Saldanha, Mottaqi Abedin
MKED
SoftDev 2025
P01 -- ArRESTed Development
2025-12-22
Time spent: 0 hr
'''
from flask import Flask, request, session, redirect, url_for, render_template
import requests
import csv
import sqlite3
import random
import time
import os
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

    cmd = f"SELECT * FROM users WHERE username = '{username}'"
    c.execute(cmd)
    existing_user = c.fetchone()

    if existing_user:
      db.close()
      text = "username already taken, try another one!"
      return render_template('register.html', text = text)

    creation_date = int(time.time())

    cmd = f"INSERT into users VALUES ('{username}', '{email}', '{password}', '{creation_date}')"
    c.execute(cmd)
    db.commit()
    db.close()
    session['username'] = username
    return redirect(url_for('homepage'))
  return render_template('register.html')

@app.route("/homepage", methods=["GET", "POST"])
def homepage():
  if 'username' not in session:
    return redirect(url_for('index'))
  return render_template("homepage.html")

@app.route("/profile", methods=["GET", "POST"])
def profile():
  return render_template("profile.html")

@app.route("/search", methods=["GET", "POST"])
def search():
  return render_template("search.html")

@app.route("/my_jobs", methods=["GET", "POST"])
def my_jobs():
  return render_template("my_jobs.html")

@app.route("/logout", methods=["GET", "POST"])
def logout():
  return render_template("login.html")

USAUPPERLAT=49.38
USALOWERLAT=24.40
USAUPPERLONG=-66.93
USALOWERLONG=-125.0

def USAJOBS(keyword="Defense",location="Virginia"):
    url = "https://data.usajobs.gov/api/search"
    headers = {
        "User-Agent": "esaldanha60@stuy.edu",
        #"Authorization-Key":"5nx2mFDQDGYXgRcd/eISsYXOhm9WoVVGAKiveLyd47A="
        "Authorization-Key": get_api_key("us-govt-jobs")
    }
    params = {
        "LocationName": location,
        "ResultsPerPage": 50,
        "Keyword":keyword
    }
    #Position Title
# Apply Link
# Location (lat, long)
# Organization name
# Position schedule (full time/part time, etc.)
# Qualification summary
# Position start and end date
# Position Requirements [pull the entirety of details]

    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    jobslist=[]
    jobdata = {}   # employer_name -> list of (location name, lat, lon)
    for job in data["SearchResult"]["SearchResultItems"]:
        descriptor = job["MatchedObjectDescriptor"]
        jobdata.update({"employer":descriptor.get("OrganizationName")})
        jobdata.update({"locations":descriptor.get("PositionLocation", [])})
        jobdata.update({"schedule":descriptor.get("PositionSchedule")[0]})
        jobdata.update({"start":descriptor.get("PositionStartDate")})
        jobdata.update({"end":descriptor.get("PositionEndDate")})
        jobdata.update({"link":descriptor.get("ApplyURI")})
        jobdata.update({"salary":descriptor.get("PositionRemuneration")})
        #print(data["SearchResult"].keys())
       
        print(descriptor["PositionRemuneration"])
        jobslist.append(jobdata)
        
        jobdata={}
    return jobslist
#print(USAJOBS())
#USAJOBS()





def RISEJOBS():
    url= "https://api.joinrise.io/api/v1/jobs/public?page=1&limit=20000&sort=asc&sortedBy=createdAt&includeDescription=true&isTrending=true"
    params = {
        "page":3,
        "limit": 200,
        "sortedBy":"United States of America"
    }
    jobslist=[]
    jobdata = {}   # employer_name -> list of (location name, lat, lon)
    response=requests.get(url, params=params)
    data=response.json()
    count=0
    coords=[]
    jobdata={}
    loc=[]
    link=""
    location=""
    lat=""
    long=""
    employer=""
    schedule=""
    start=""
    end=""
    requirements=""
    # print(data)
    # print("/n/n/n/n")
    # print(data["result"])
    for c in data["result"]["jobs"]:
        count+=1
        owner=c["owner"]
        try:
            #jobdata.append(c["descriptionBreakdown"]["oneSentenceJobSummary"])
            if(c["locationAddress"] is not None):
                location=c["locationAddress"]
                loc.append(location)
            if(c["locationCoordinates"] is not None):
                locCoord=c["locationCoordinates"]
                coords.append(c["locationCoordinates"])
                lat=locCoord["latitude"]
                long=locCoord["longitude"]
                loc.append(coords)
        except KeyError:
            loc.append("Remote Job")
        jobdata.update({"employer":owner.get("companyName")})
        jobdata.update({"locations":loc})
        loc=[]
#         jobdata.update({"schedule":owner.get("PositionSchedule")[0]})
#         jobdata.update({"start":owner.get("PositionStartDate")})
#         jobdata.update({"end":owner.get("PositionEndDate")})
        jobdata.update({"link":c.get("url")})
        salary={"salaryMin":c["descriptionBreakdown"].get("salaryRangeMinYearly"),"salaryMax":c["descriptionBreakdown"].get("salaryRangeMaxYearly")}
        jobdata.update({"salary":salary})
        jobslist.append(jobdata)
        jobdata={}
    print(count)
    return jobslist

print(RISEJOBS())

if __name__ == "__main__":
  initialize_db()
  app.debug = True
  app.run()
