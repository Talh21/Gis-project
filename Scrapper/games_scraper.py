import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor

BASE_URL = "https://www.fastscore.com"
FIXTURES_URL = f"{BASE_URL}/israel/ligat-haal/fixtures"

session = requests.Session()

def fetch(url):
    try:
        response = session.get(url, timeout=30)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

def parse_match_details(html):
    if not html:
        return "N/A", "N/A", "N/A"
    soup = BeautifulSoup(html, 'lxml')
    
    date_span = soup.find('span', attrs={'data-date-match': True})
    day, date = date_span.text.strip().split(', ', 1) if date_span else ("N/A", "N/A")
    
    stadium_a = soup.find('a', href=re.compile(r'https://www\.fastscore\.com/stadium/'))
    if stadium_a:
        stadium_full = stadium_a.text.strip()
        stadium_match = re.match(r'(.*?Stadium)', stadium_full, re.IGNORECASE)
        stadium = stadium_match.group(1) if stadium_match else "N/A"
    else:
        stadium = "N/A"
    
    return day, date, stadium

def get_all_matches(url):
    matches = []
    page = 1
    while True:
        html = fetch(f"{url}?page={page}")
        if not html:
            break
        soup = BeautifulSoup(html, 'lxml')
        
        match_divs = soup.find_all('div', class_='match-grid-match')
        if not match_divs:
            break
        
        for match in match_divs:
            teams = match.find_all('div', class_='col-12 text-left text-truncate align-self-center p-0')
            if len(teams) == 2:
                home_team, away_team = [team.text.strip() for team in teams]
                preview_url = urljoin(BASE_URL, match.get('data-href', ''))
                matches.append({
                    'Match': f"{home_team} vs {away_team}",
                    'PreviewURL': preview_url
                })
        page += 1
    return matches

def process_match(match):
    html = fetch(match['PreviewURL'])
    day, date, stadium = parse_match_details(html)
    match.update({'Day': day, 'Date': date, 'Stadium': stadium})
    return match

def main():
    all_matches = get_all_matches(FIXTURES_URL)
    if not all_matches:
        print("Failed to fetch match data. Exiting.")
        return
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        processed_matches = list(executor.map(process_match, all_matches))
    
    df = pd.DataFrame(processed_matches)
    df = df.drop(columns=['PreviewURL'])
    
    print(df)
    print(f"\nTotal matches found: {len(processed_matches)}")
    
    df.to_excel('Ligat_HaAl_Fixtures.xlsx', index=False)
    print("\nData saved to 'Ligat_HaAl_Fixtures.xlsx'")

if __name__ == "__main__":
    main()