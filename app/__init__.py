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
    if not filename.startswith("key_") or not filename.endswith(".txt"):
      continue
    filepath = os.path.join(KEYS_DIR, filename)
    api_name = filename[4:-4]
    api_name_upper = api_name.upper()

    try:
      with open(filepath, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f.readlines()]
        key_value = next((line for line in lines if line), "")
    except Exception as e:
      print(f"Failed to read {filename}: {e}")
      continue

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
    return [], "Error contacting USAJOBS API."

  try:
    jobslist = []
    items = data.get("SearchResult", {}).get("SearchResultItems", [])

    user_loc = (location or "").strip().lower()

    for job in items:
      descriptor = job.get("MatchedObjectDescriptor", {})
      jobs = {}

      jobs["job_title"] = descriptor.get("PositionTitle", "")
      jobs["employer"] = descriptor.get("OrganizationName", "")

      locations = descriptor.get("PositionLocation", []) or []
      locations2 = []
      for l in locations:
        try:
          if not user_loc or (l.get("LocationName", "").lower().find(user_loc) != -1):
            locations2.append(l)
        except Exception:
          continue
      jobs["locations"] = locations2

      schedule = ""
      sched_list = descriptor.get("PositionSchedule", [])
      if isinstance(sched_list, list) and sched_list:
        if isinstance(sched_list[0], dict):
          schedule = sched_list[0].get("Name", "")
        else:
          schedule = str(sched_list[0])
      jobs["schedule"] = schedule

      jobs["start"] = (descriptor.get("PositionStartDate", "") or "")[0:10]
      jobs["end"] = (descriptor.get("PositionEndDate", "") or "")[0:10]
      jobs["link"] = (descriptor.get("ApplyURI") or [""])[0]
      jobs["source"] = "usajobs"

      rem = descriptor.get("PositionRemuneration", [])
      salary_min = None
      salary_max = None
      if isinstance(rem, list) and rem and isinstance(rem[0], dict):
        r0 = rem[0]
        try:
          salary_min = float(r0.get("MinimumRange")) if r0.get("MinimumRange") else None
        except (ValueError, TypeError):
          salary_min = None
        try:
          salary_max = float(r0.get("MaximumRange")) if r0.get("MaximumRange") else None
        except (ValueError, TypeError):
          salary_max = None

      if salary_min is not None or salary_max is not None:
        jobs["salary"] = {"min": salary_min, "max": salary_max}

      jobslist.append(jobs)

    return jobslist, None

  except KeyError as e:
    print("Parsing error:", e)
    return [], "Error parsing USAJOBS API response."

def RISEJOBS(page=1, keyword="", location=""):
    url = "https://api.joinrise.io/api/v1/jobs/public"
    params = {
        "page": page,
        "limit": 200,
        "sortedBy": "United States of America",
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print("RISEJOBS request failed:", e)
        return [], "Error contacting RISEJOBS API."

    jobslist = []
    location_lower = location.lower().strip() if location else ""
    keyword_lower = keyword.lower().strip() if keyword else ""

    try:
        for c in data.get("result", {}).get("jobs", []):
            owner = c.get("owner", {})
            
            if page == 1:
              print("RISE keys:", list(c.keys()))
              print("title sample:", c.get("title"))
              print("has description?", "description" in c, "descHtml?", "descriptionHtml" in c, "descText?", "descriptionText" in c)
              break

            title = (c.get("title") or "").lower()
            company = (owner.get("companyName") or "").lower()

            bk = c.get("descriptionBreakdown") or {}
            kw_list = bk.get("keywords") if isinstance(bk, dict) else []
            kw_text = " ".join([str(x).lower() for x in kw_list]) if isinstance(kw_list, list) else ""

            if keyword_lower:
                if (keyword_lower not in title) and (keyword_lower not in company) and (keyword_lower not in kw_text):
                    continue
            
            # Location filtering
            if location_lower:
                job_location = c.get("locationAddress", "")
                if job_location and location_lower not in job_location.lower():
                    continue
            
            jobs = {}
            
            jobs["job_title"] = c.get("title", "")
            jobs["employer"] = owner.get("companyName", "")
            jobs["source"] = "RISEJOBS"
            
            locations = []
            if c.get("locationAddress"):
                loc_dict = {"LocationName": c["locationAddress"]}
                if c.get("locationCoordinates"):
                    coords = c["locationCoordinates"]
                    loc_dict["Latitude"] = coords.get("lat")
                    loc_dict["Longitude"] = coords.get("lon")
                
                locations.append(loc_dict)
            
            jobs["locations"] = locations
            
            jobs["link"] = c.get("url", "")
            
            description_breakdown = c.get("descriptionBreakdown", {})
            salary_min = description_breakdown.get("salaryRangeMinYearly")
            salary_max = description_breakdown.get("salaryRangeMaxYearly")
            
            if salary_min or salary_max:
                jobs["salary"] = {
                    "min": salary_min,
                    "max": salary_max
                }
            
            jobslist.append(jobs)
        
        return jobslist, None
        
    except Exception as e:
        print("RISEJOBS parsing error:", e)
        return [], "Error parsing RISEJOBS API response."

def initialize_db():
  db = sqlite3.connect(DB_FILE)
  c = db.cursor()

  c.execute("CREATE TABLE IF NOT EXISTS users(username TEXT PRIMARY KEY, email TEXT, password TEXT, creation_date DATE, bio TEXT);")
  c.execute("CREATE TABLE IF NOT EXISTS saved_jobs(id TEXT PRIMARY KEY, username TEXT, job_title TEXT, employer TEXT, location TEXT, schedule TEXT, start_date TEXT, end_date TEXT, link TEXT, date_saved INTEGER, status TEXT DEFAULT 'not_applied', lat TEXT, lon TEXT);")
  c.execute("CREATE TABLE IF NOT EXISTS search_history(id TEXT, username TEXT, timestamp DATE, job_title TEXT, filters_applied TEXT);")
  c.execute("CREATE TABLE IF NOT EXISTS job_views(id TEXT PRIMARY KEY, username TEXT, job_title TEXT, employer TEXT, location TEXT, schedule TEXT, start_date TEXT, end_date TEXT, link TEXT, timestamp INTEGER, lat TEXT, lon TEXT);")

  try:
    c.execute("ALTER TABLE saved_jobs ADD COLUMN status TEXT DEFAULT 'not_applied';")
  except:
    pass

  try:
    c.execute("ALTER TABLE saved_jobs ADD COLUMN lat TEXT;")
  except:
    pass

  try:
    c.execute("ALTER TABLE saved_jobs ADD COLUMN lon TEXT;")
  except:
    pass

  try:
    c.execute("ALTER TABLE job_views ADD COLUMN lat TEXT;")
  except:
    pass

  try:
    c.execute("ALTER TABLE job_views ADD COLUMN lon TEXT;")
  except:
    pass

  db.commit()
  db.close()

@app.route("/", methods=['GET', 'POST'])
def index():
  if 'username' in session:
    return redirect(url_for('homepage'))
  else:
    return render_template("login.html", text="")

@app.route("/login", methods=["GET", "POST"])
def login():
  if request.method == 'POST':
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')

    if not username or not password:
      return render_template('login.html', text="Please enter both username and password")
    
    db = sqlite3.connect(DB_FILE)
    c = db.cursor()
    c.execute("SELECT username, email, password FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    db.close()

    if not user or user[2] != password:
      text = "Login failed. Invalid username or password."
      return render_template('login.html', text=text)
    
    session['username'] = username
    return redirect(url_for('homepage'))
  
  return render_template('login.html', text="")

@app.route("/register", methods=["GET", "POST"])
def register():
  if request.method == 'POST':
    db = sqlite3.connect(DB_FILE)
    c = db.cursor()
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')

    if not username or not email or not password:
      db.close()
      return render_template('register.html', text="All fields are required!")

    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    existing_user = c.fetchone()

    if existing_user:
      db.close()
      text = "This username is already taken, try another one!"
      return render_template('register.html', text=text)

    creation_date = int(time.time())

    c.execute(
        "INSERT INTO users VALUES (?, ?, ?, ?, ?)",
        (username, email, password, creation_date, '')
    )
    db.commit()
    db.close()
    session['username'] = username
    return redirect(url_for('homepage'))
  
  return render_template('register.html', text="")

@app.route("/homepage", methods=["GET", "POST"])
def homepage():
  if 'username' not in session:
    return redirect(url_for('index'))

  username = session['username']
  db = sqlite3.connect(DB_FILE)
  c = db.cursor()

  c.execute(
    """SELECT job_title, employer, location, schedule, start_date, end_date, link, MAX(timestamp) as timestamp, lat, lon
       FROM job_views
       WHERE username = ?
       GROUP BY job_title, employer, location, schedule, start_date, end_date, link
       ORDER BY timestamp DESC
       LIMIT 5""",
    (username,)
  )
  recent_jobs = c.fetchall()
  db.close()

  return render_template("homepage.html", username=username, recent_jobs=recent_jobs)

@app.route("/profile", methods=["GET", "POST"])
def profile():
  if 'username' not in session:
    return redirect(url_for('index'))

  db = sqlite3.connect(DB_FILE)
  c = db.cursor()
  username = session['username']

  c.execute("SELECT bio, creation_date from users WHERE username = ?;", (username,))
  result = c.fetchone()
  bio = result[0] if result and result[0] else None
  creation_date = result[1] if result else None

  formatted_creation_date = None
  if creation_date:
    dt = datetime.fromtimestamp(creation_date)
    formatted_creation_date = dt.strftime("%B %d, %Y")

  # Calculate account statistics
  # Total jobs viewed
  c.execute("SELECT COUNT(DISTINCT job_title || employer || location) FROM job_views WHERE username = ?", (username,))
  total_viewed = c.fetchone()[0]

  # Total jobs saved
  c.execute("SELECT COUNT(*) FROM saved_jobs WHERE username = ?", (username,))
  total_saved = c.fetchone()[0]

  # Total applications (jobs marked as applied)
  c.execute("SELECT COUNT(*) FROM saved_jobs WHERE username = ? AND status = 'applied'", (username,))
  total_applied = c.fetchone()[0]

  db.close()
  return render_template("profile.html", username=username, bio=bio, curr_user=session['username'],
                         creation_date=formatted_creation_date, total_viewed=total_viewed,
                         total_saved=total_saved, total_applied=total_applied)

@app.route("/edit_profile", methods=["GET", "POST"])
def edit_profile():
  if 'username' not in session:
    return redirect(url_for('index'))

  username = session['username']

  if request.method == "POST":
    bio = request.form.get("bio", "").strip()

    db = sqlite3.connect(DB_FILE)
    c = db.cursor()
    c.execute("UPDATE users SET bio = ? WHERE username = ?", (bio, username))
    db.commit()
    db.close()

    return redirect(url_for('profile'))

  db = sqlite3.connect(DB_FILE)
  c = db.cursor()
  c.execute("SELECT bio FROM users WHERE username = ?", (username,))
  result = c.fetchone()
  bio = result[0] if result and result[0] else ""
  db.close()

  return render_template("edit_profile.html", username=username, bio=bio)

@app.route("/search", methods=["GET", "POST"])
def search():
    if 'username' not in session:
        return redirect(url_for('index'))

    if request.method == "POST":
        keyword = request.form.get("keyword", "").strip()
        location = request.form.get("location", "").strip()
        source = request.form.get("source", "both").strip().lower()
        
        if not keyword and not location:
            return render_template("search.html", error="Please enter a keyword or location to search.")

        db = sqlite3.connect(DB_FILE)
        c = db.cursor()
        search_id = str(time.time())
        filters_applied = f"location={location};source={source}"
        c.execute(
            "INSERT INTO search_history VALUES (?, ?, ?, ?, ?)",
            (search_id, session['username'], int(time.time()), keyword, filters_applied)
        )
        db.commit()
        db.close()

        jobs = []
        error = None

        if source in ["usajobs", "both"]:
            usa_jobs, usa_error = USAJOBS(keyword, location)
            if usa_jobs:
                jobs.extend(usa_jobs)
            if usa_error and not error:
                error = usa_error
        
        if source in ["risejobs", "both"]:
          for page in range(1, 6):
            rise_jobs, rise_error = RISEJOBS(page=page, keyword=keyword, location=location)

            if rise_jobs:
                jobs.extend(rise_jobs)

            if rise_error and not error:
              error = rise_error

        return render_template(
            "search.html",
            keyword=keyword,
            location=location,
            source=source,
            jobs=jobs,
            error=error
        )

    return render_template("search.html")

@app.route("/job")
def job_detail(error=""):
    if 'username' not in session:
        return redirect(url_for('index'))

    job_title = request.args.get("job_title", "")
    employer = request.args.get("employer", "")
    location_name = request.args.get("location_name", "")

    lat = request.args.get("lat", type=float)
    lon = request.args.get("lon", type=float)

    schedule = request.args.get("schedule", "")
    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")
    link = request.args.get("link", "")
    source = request.args.get("source", "")

    salary_min = request.args.get("salary_min", type=float)
    salary_max = request.args.get("salary_max", type=float)

    if job_title and employer:
        username = session['username']
        db = sqlite3.connect(DB_FILE)
        c = db.cursor()

        view_id = str(time.time())
        timestamp = int(time.time())

        c.execute(
            "INSERT INTO job_views VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (view_id, username, job_title, employer, location_name, schedule, start_date, end_date, link, timestamp, lat, lon)
        )
        db.commit()
        db.close()

    has_map = (lat is not None and lon is not None)

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
        source=source,
        salary_min=salary_min,
        salary_max=salary_max,
        error=error,
        has_map=has_map
    )

@app.route("/saved_jobs", methods=["GET", "POST"])
def saved_jobs():
  if 'username' not in session:
    return redirect(url_for('index'))
  error = request.args.get('error', "")
  username = session['username']
  db = sqlite3.connect(DB_FILE)
  c = db.cursor()

  c.execute(
    "SELECT * FROM saved_jobs WHERE username = ? ORDER BY date_saved DESC",
    (username,)
  )
  saved_jobs = c.fetchall()
  db.close()

  return render_template("saved_jobs.html", saved_jobs=saved_jobs,error=error)

@app.route("/logout", methods=["GET", "POST"])
def logout():
  session.clear()
  return redirect(url_for('index'))

@app.route("/save_job", methods=["POST"])
def save_job():
  if 'username' not in session:
    return redirect(url_for('index'))

  username = session['username']
  job_title = request.form.get("job_title", "")
  employer = request.form.get("employer", "")
  location_name = request.form.get("location_name", "")
  schedule = request.form.get("schedule", "")
  start_date = request.form.get("start_date", "")
  end_date = request.form.get("end_date", "")
  link = request.form.get("link", "")
  
  lat = request.form.get("lat", "")
  lon = request.form.get("lon", "")

  if not job_title or not employer:
    return redirect(url_for('search'))

  db = sqlite3.connect(DB_FILE)
  c = db.cursor()

  c.execute("SELECT * FROM saved_jobs WHERE username=? AND job_title=? AND employer=? AND location=? AND schedule=? AND start_date=? AND end_date=? AND link=?", (username,job_title,employer,location_name,schedule,start_date,end_date,link))
  check=c.fetchall()

  if check:
    db.close()
    return redirect(url_for('saved_jobs', error="This job is already saved"))
  
  job_id = str(time.time())
  date_saved = int(time.time())

  c.execute("INSERT INTO saved_jobs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (job_id, username, job_title, employer, location_name, schedule, start_date, end_date, link, date_saved, 'not_applied', lat, lon))

  db.commit()
  db.close()

  return redirect(url_for('saved_jobs'))

@app.route("/toggle_status", methods=["POST"])
def toggle_status():
  if 'username' not in session:
    return redirect(url_for('index'))

  job_id = request.form.get("job_id", "")
  username = session['username']

  db = sqlite3.connect(DB_FILE)
  c = db.cursor()

  # Get current status
  c.execute("SELECT status FROM saved_jobs WHERE id = ? AND username = ?", (job_id, username))
  result = c.fetchone()

  if result:
    current_status = result[0]
    new_status = 'applied' if current_status == 'not_applied' else 'not_applied'

    c.execute("UPDATE saved_jobs SET status = ? WHERE id = ? AND username = ?", (new_status, job_id, username))
    db.commit()

  db.close()
  return redirect(url_for('saved_jobs'))

@app.route("/remove_job", methods=["POST"])
def remove_job():
  if 'username' not in session:
    return redirect(url_for('index'))

  job_id = request.form.get("job_id", "")
  username = session['username']

  db = sqlite3.connect(DB_FILE)
  c = db.cursor()

  c.execute("DELETE FROM saved_jobs WHERE id = ? AND username = ?", (job_id, username))
  db.commit()
  db.close()

  return redirect(url_for('saved_jobs'))

if __name__ == "__main__":
  initialize_db()
  app.debug = True
  app.run()
