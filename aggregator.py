import feedparser
import datetime
import json
import os
import re
import requests
from bs4 import BeautifulSoup
from email.utils import parsedate_to_datetime

# The database file to keep history of all competitions (even expired ones)
DB_FILE = "competitions_db.json"

# Expanded dictionary of keywords to cast the widest net possible
KEYWORDS = [
    'protein', 'proteomic', 'hackathon', 'competition', 'challenge', 
    'binder', 'ligand', 'docking', 'alphafold', 'rosetta', 'design',
    'amino acid', 'peptide', 'enzyme', 'synthetic biology', 'kaggle',
    'biomolecular', 'drug discovery', 'structural biology'
]

# RSS Sources for broad news scraping
RSS_SOURCES = {
    "Adaptyv Bio / Proteinbase": "https://www.adaptyvbio.com/blog/rss.xml",
    "Oxford BLOPIG": "https://blopig.com/blog/feed/",
    "BMC Proteomics": "https://clinicalproteomicsjournal.biomedcentral.com/articles/most-recent/rss.xml",
    "Nature Proteomics": "https://www.nature.com/subjects/proteomics.rss",
    "PLOS CompBio": "https://journals.plos.org/ploscompbiol/feed/atom",
}

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_db(db):
    with open(DB_FILE, 'w') as f:
        json.dump(db, f, indent=4)

def parse_date(date_str):
    try:
        return parsedate_to_datetime(date_str).strftime("%Y-%m-%d")
    except:
        return datetime.datetime.now().strftime("%Y-%m-%d")

def guess_dates(text, start_date):
    """Attempt to find a deadline date using Regex in the text"""
    # Look for dates formatted as YYYY-MM-DD
    dates = re.findall(r'\b(202\d-[0-1]\d-[0-3]\d)\b', text)
    if dates:
        dates.sort()
        end_date = dates[-1] # Assume the furthest date mentioned is the deadline
    else:
        # Default deadline to 30 days from publish if no exact date is found
        s = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        end_date = (s + datetime.timedelta(days=30)).strftime("%Y-%m-%d")
    return start_date, end_date

def fetch_rss_competitions(db):
    for name, url in RSS_SOURCES.items():
        print(f"Fetching RSS: {name}...")
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                text_to_search = (entry.title + " " + entry.get('summary', '')).lower()
                # If ANY of our keywords are in the article
                if any(key in text_to_search for key in KEYWORDS):
                    link = entry.link
                    # Only process if we haven't seen this competition before
                    if link not in db:
                        pub_date = parse_date(entry.get('published', ''))
                        start, end = guess_dates(text_to_search, pub_date)
                        db[link] = {
                            'source': name,
                            'title': entry.title,
                            'link': link,
                            'start_date': start,
                            'end_date': end
                        }
        except Exception as e:
            print(f"Failed to fetch {name}: {e}")

def fetch_biohackathons(db):
    """Custom Web Scraper for non-RSS sites like biohackathons.github.io"""
    print("Scraping biohackathons.github.io...")
    try:
        res = requests.get("https://biohackathons.github.io/")
        soup = BeautifulSoup(res.text, 'html.parser')
        
        for a in soup.find_all('a', href=True):
            title = a.text.strip()
            link = a['href']
            # If the link text mentions our keywords
            if any(key in title.lower() for key in KEYWORDS) and len(title) > 5:
                if link.startswith('/'): 
                    link = "https://biohackathons.github.io" + link
                if link not in db and link.startswith('http'):
                    today = datetime.datetime.now().strftime("%Y-%m-%d")
                    db[link] = {
                        'source': 'BioHackathons Ecosystem',
                        'title': title,
                        'link': link,
                        'start_date': today,
                        'end_date': (datetime.datetime.now() + datetime.timedelta(days=14)).strftime("%Y-%m-%d")
                    }
    except Exception as e:
        print(f"Scraper failed: {e}")

def get_color_and_time(end_date_str):
    """Calculates time left and returns CSS colors for UI Badges"""
    try:
        end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d")
        now = datetime.datetime.now()
        delta = (end_date - now).days
        
        if delta < 0:
            return "#e0e0e0", "#666666", "Expired" # Grey background, dark text
        elif delta <= 7:
            return "#ffebee", "#c62828", f"Ending Soon ({delta} days)" # Red/Pink
        elif delta <= 30:
            return "#fff8e1", "#f57f17", f"Active ({delta} days left)" # Orange/Yellow
        else:
            return "#e8f5e9", "#2e7d32", f"Active ({delta} days left)" # Green
    except:
        return "#ffffff", "#000000", "Unknown Status"

def generate_html(db):
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Global Proteomics & Protein Design Competitions</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; max-width: 900px; margin: 40px auto; line-height: 1.6; padding: 0 20px; background-color: #f9fafb; color: #333; }}
            h1 {{ color: #111; text-align: center; }}
            .info-text {{ text-align: center; color: #666; font-size: 0.9em; margin-bottom: 30px; }}
            .card {{ background: white; border-radius: 8px; padding: 20px; margin-bottom: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); display: flex; flex-direction: column; border-left: 5px solid #0284c7; }}
            .card.expired {{ border-left: 5px solid #e0e0e0; opacity: 0.7; }}
            .card-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }}
            .source {{ font-size: 0.8em; font-weight: bold; text-transform: uppercase; color: #888; }}
            .badge {{ padding: 6px 12px; border-radius: 20px; font-size: 0.85em; font-weight: bold; }}
            .title {{ font-size: 1.2em; font-weight: bold; margin-bottom: 10px; }}
            .title a {{ color: #111; text-decoration: none; }}
            .title a:hover {{ color: #2563eb; text-decoration: underline; }}
            .dates {{ font-size: 0.85em; color: #555; display: flex; gap: 15px; margin-top: 5px; }}
            .dates span {{ background: #f3f4f6; padding: 4px 8px; border-radius: 4px; }}
        </style>
    </head>
    <body>
        <h1>🧬 Protein Competition Tracker</h1>
        <p class="info-text">Aggregating hackathons, design challenges, and databases.<br>Last updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
    """
    
    # Sort the database: Active competitions first, then sort by deadline, then expired at bottom
    entries = list(db.values())
    entries.sort(key=lambda x: (
        datetime.datetime.strptime(x['end_date'], "%Y-%m-%d") < datetime.datetime.now(), 
        x['end_date']
    ))

    for item in entries:
        bg_color, text_color, status_text = get_color_and_time(item['end_date'])
        expired_class = "expired" if "Expired" in status_text else ""
        
        html_content += f"""
        <div class="card {expired_class}">
            <div class="card-header">
                <span class="source">{item['source']}</span>
                <span class="badge" style="background-color: {bg_color}; color: {text_color};">{status_text}</span>
            </div>
            <div class="title">
                <a href="{item['link']}" target="_blank">{item['title']}</a>
            </div>
            <div class="dates">
                <span><strong>Start:</strong> {item['start_date']}</span>
                <span><strong>Deadline:</strong> {item['end_date']}</span>
            </div>
        </div>
        """
    
    html_content += "</body></html>"
    
    with open("index.html", "w", encoding='utf-8') as f:
        f.write(html_content)

if __name__ == "__main__":
    # 1. Load historical database
    db = load_db()
    
    # 2. Scrape new data
    fetch_rss_competitions(db)
    fetch_biohackathons(db)
    
    # 3. Save database and generate UI
    save_db(db)
    generate_html(db)
    print("Database and HTML updated successfully!")