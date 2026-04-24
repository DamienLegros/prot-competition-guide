import feedparser
import datetime

# The most active sources for protein design and proteomics news/competitions
SOURCES = {
    "Adaptyv Bio Blog": "https://www.adaptyvbio.com/blog/rss.xml",
    "Oxford Protein Informatics (BLOPIG)": "https://blopig.com/blog/feed/",
    "BMC Proteomics": "https://clinicalproteomicsjournal.biomedcentral.com/articles/most-recent/rss.xml",
    "Nature Proteomics": "https://www.nature.com/subjects/proteomics.rss",
}

def fetch_competitions():
    all_entries = []
    for name, url in SOURCES.items():
        print(f"Fetching from {name}...")
        feed = feedparser.parse(url)
        for entry in feed.entries:
            # Filter for competition-related keywords
            keywords = ['competition', 'hackathon', 'challenge', 'binder', 'design', 'prize']
            if any(key in entry.title.lower() or key in entry.summary.lower() for key in keywords):
                all_entries.append({
                    'source': name,
                    'title': entry.title,
                    'link': entry.link,
                    'date': entry.published if 'published' in entry else "Recent"
                })
    return all_entries

def generate_html(competitions):
    html_content = f"""
    <html>
    <head>
        <title>Proteomics Competition Aggregator</title>
        <style>
            body {{ font-family: sans-serif; max-width: 800px; margin: 40px auto; line-height: 1.6; padding: 0 20px; }}
            .entry {{ border-bottom: 1px solid #eee; padding: 15px 0; }}
            .source {{ color: #007bff; font-weight: bold; font-size: 0.8em; }}
            .date {{ color: #666; font-size: 0.8em; }}
            a {{ text-decoration: none; color: #333; }}
            a:hover {{ color: #007bff; }}
        </style>
    </head>
    <body>
        <h1>Protein Design & Proteomics Competitions</h1>
        <p>Last updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
        <hr>
    """
    
    for item in competitions:
        html_content += f"""
        <div class="entry">
            <span class="source">[{item['source']}]</span> 
            <span class="date">{item['date']}</span><br>
            <a href="{item['link']}" target="_blank"><strong>{item['title']}</strong></a>
        </div>
        """
    
    html_content += "</body></html>"
    
    with open("index.html", "w") as f:
        f.write(html_content)

if __name__ == "__main__":
    comps = fetch_competitions()
    generate_html(comps)
    print("Aggregator updated successfully!")