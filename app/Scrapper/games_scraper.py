import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta

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
        return "N/A", "N/A", "N/A", "N/A"

    soup = BeautifulSoup(html, 'html.parser')

    date_span = soup.find('span', attrs={'data-date-match': True})
    day, date_str = date_span.text.strip().split(', ', 1) if date_span else ("N/A", "N/A")

    time_span = soup.find('span', attrs={'data-time-match': True})
    time_text = time_span.text.strip() if time_span else "N/A"

    # Convert the time text to a datetime object and adjust for Israel Time Zone
    if time_text != 'N/A':
        try:
            time_dt = datetime.strptime(time_text, '%H:%M')
            time_dt_il = time_dt + timedelta(hours=3)
            time_text_il = time_dt_il.strftime('%H:%M')
        except ValueError:
            time_text_il = 'N/A'
    else:
        time_text_il = 'N/A'

    stadium_a = soup.find('a', href=re.compile(r'https://www\.fastscore\.com/stadium/'))
    stadium = stadium_a.text.strip() if stadium_a else "N/A"

    return day, date_str, time_text_il, stadium

def get_all_matches(url):
    matches = []
    page = 1
    while True:
        html = fetch(f"{url}?page={page}")
        if not html:
            break

        soup = BeautifulSoup(html, 'html.parser')
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
    day, date, match_time, stadium = parse_match_details(html)

    if "Hapoel Be'er Sheva" in match['Match'].split(' vs ')[0]:
        stadium = "Turner Stadium (Be'er Sheva)"
        #city = "Be'er Sheva"
    
    city = extract_and_clean_city_name(stadium)

    match.update({'Day': day, 'Date': date, 'Time': match_time, 'Stadium': stadium, 'City': city})
    return match

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
        "Teddi Malcha Stadium": "Teddy Stadium"
    }
    return replacements.get(clean_name, clean_name)

def process_dataframe(df):
    df = df.drop(columns=['PreviewURL'])
    df = df[df['Stadium'] != 'N/A']
    df['City'] = df['Stadium'].apply(extract_and_clean_city_name)
    df['Stadium'] = df['Stadium'].apply(clean_stadium_name)
    df['Date'] = pd.to_datetime(df['Date'], dayfirst=True).dt.strftime('%Y-%m-%d')
    df = df.sort_values(by=['Date'], ascending=True)
    return df

def main():
    print("Fetching all matches...")
    all_matches = get_all_matches(FIXTURES_URL)
    if not all_matches:
        print("Failed to fetch match data. Exiting.")
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
                print(f"Error processing match {match['Match']}: {e}")

    df = pd.DataFrame(processed_matches)
    df = process_dataframe(df)

    df.to_csv('C:\GIS\Project\GIS\\app\static\data\Ligat_HaAl_Fixtures.csv', index=False)
    print("\nData saved to 'Ligat_HaAl_Fixtures.csv'")

if __name__ == "__main__":
    main()
