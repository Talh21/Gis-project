import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
import random
import time

DATABASE_URI = 'postgresql://postgres:210197@localhost/football_matches_db'

BASE_URL = "https://www.fastscore.com"
FIXTURES_URL = [f"{BASE_URL}/israel/ligat-haal/fixtures", f"{BASE_URL}/israel/liga-leumit/fixtures"]

session = requests.Session()

def fetch(url):
    retries = 5
    for i in range(retries):
        try:
            response = session.get(url, timeout=60)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            if i < retries - 1:
                sleep_time = 2 ** i + random.random()  # Exponential backoff with some randomness
                print(f"Retrying in {sleep_time:.2f} seconds...")
                time.sleep(sleep_time)
            else:
                return None

def extract_league_from_url(url):
    match = re.search(r'israel/([^/]+)/fixtures', url)
    if match:
        return match.group(1).replace('-', ' ').title()  # Converts 'liga-leumit' to 'Liga Leumit'
    return None

def parse_match_details(html):
    if not html:
        return None, None, None, None, None

    soup = BeautifulSoup(html, 'html.parser')

    date_span = soup.find('span', attrs={'data-date-match': True})
    day, date_str = date_span.text.strip().split(', ', 1) if date_span else (None, None)

    time_span = soup.find('span', attrs={'data-time-match': True})
    time_text = time_span.text.strip() if time_span else None

    if time_text:
        try:
            time_dt = datetime.strptime(time_text, '%H:%M')
            time_dt_il = time_dt + timedelta(hours=3)
            time_text_il = time_dt_il.strftime('%H:%M')
        except ValueError:
            time_text_il = None
    else:
        time_text_il = None

    stadium_a = soup.find('a', href=re.compile(r'https://www\.fastscore\.com/stadium/'))
    stadium = stadium_a.text.strip() if stadium_a else None

    # Extract matchday
    matchday_div = soup.find('div', class_='col text py-2')
    matchday_text = None
    if matchday_div:
        matchday_search = re.search(r'Matchday (\d+)', matchday_div.text.strip())
        if matchday_search:
            matchday_text = matchday_search.group(1)

    return day, date_str, time_text_il, stadium, matchday_text

def get_all_matches(url):
    league = extract_league_from_url(url)
    matches = []
    page = 1

    while True:
        html = fetch(f"{url}?page={page}")
        if not html:
            break

        soup = BeautifulSoup(html, 'html.parser')
        match_divs = soup.find_all('div', class_='match-grid-match')

        if not match_divs:
            print(f"No matches found on page {page}, stopping.")
            break

        for match in match_divs:
            teams = match.find_all('div', class_='col-12 text-left text-truncate align-self-center p-0')
            if len(teams) == 2:
                home_team, away_team = [team.text.strip() for team in teams]
                preview_url = urljoin(BASE_URL, match.get('data-href', ''))
                matches.append({
                    'home_team': home_team,
                    'away_team': away_team,
                    'PreviewURL': preview_url,
                    'league': league  # Add league to each match
                })

        next_button = soup.find('a', rel='next')
        if not next_button:
            print(f"No 'Next' button found, stopping at page {page}.")
            break

        page += 1

    return matches

def process_match(match):
    html = fetch(match['PreviewURL'])
    day, date, match_time, stadium, matchday = parse_match_details(html)

    if "Hapoel Be'er Sheva" in match['home_team']:
        stadium = "Turner Stadium (Be'er Sheva)"
    
    city = extract_and_clean_city_name(stadium) if stadium else None

    match.update({
        'day': day, 
        'date': date, 
        'time': match_time, 
        'stadium': stadium, 
        'city': city, 
        'matchday': matchday  # Add matchday to match data
    })
    return match

def process_dataframe(df):
    df = df.drop(columns=['PreviewURL'])
    df = df.dropna(subset=['stadium'])
    df['city'] = df['stadium'].apply(extract_and_clean_city_name)
    df['stadium'] = df['stadium'].apply(clean_stadium_name)
    df['date'] = pd.to_datetime(df['date'], errors='coerce', dayfirst=True).dt.strftime('%Y-%m-%d')
    df = df.sort_values(by=['date'], ascending=True)
    df = df.drop_duplicates()
    return df

def extract_and_clean_city_name(stadium_name):
    matches = re.findall(r'\(([^()]+)\)', stadium_name)
    if matches:
        city_name = matches[-1]
        city_name = city_name.replace('-', ' ').replace('Israel', '').strip()
        return city_name
    return None

def clean_stadium_name(stadium_name):
    clean_name = re.sub(r'\s*\(.*', '', stadium_name).strip()
    replacements = {
        "Teddi Malcha Stadium": "Teddy Stadium",
        "Yankele Grundman Stadium" : "Grundman Stadium"

    }
    return replacements.get(clean_name, clean_name)

def update_database(df, engine):
    with engine.connect() as conn:
        with conn.begin():
            conn.execute(text("TRUNCATE TABLE football_fixtures;"))
            df.to_sql('football_fixtures', conn, if_exists='append', index=False)

def main():
    print("Fetching all matches...")
    all_matches = []

    for url in FIXTURES_URL:
        matches = get_all_matches(url)
        if matches:
            all_matches.extend(matches)
        else:
            print(f"Failed to fetch match data from {url}.")

    if not all_matches:
        print("No match data found. Exiting.")
        return

    print(f"Found {len(all_matches)} matches. Processing each match now...\n")

    processed_matches = []
    with ThreadPoolExecutor(max_workers=40) as executor:
        future_to_match = {executor.submit(process_match, match): match for match in all_matches}

        for i, future in enumerate(as_completed(future_to_match), 1):
            match = future_to_match[future]
            try:
                result = future.result()
                processed_matches.append(result)
                if i % 10 == 0:
                    print(f"[{i}/{len(all_matches)}] Matches processed: {i}")
            except Exception as e:
                print(f"Error processing match {match['home_team']} vs {match['away_team']}: {e}")

    df = pd.DataFrame(processed_matches)
    df = process_dataframe(df)
    engine = create_engine(DATABASE_URI)
    update_database(df, engine)

    print("\nData saved to 'DB'")

if __name__ == "__main__":
    main()
