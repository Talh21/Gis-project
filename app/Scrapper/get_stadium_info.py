from sqlalchemy import create_engine, text
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

# Database connection
DATABASE_URI = 'postgresql://postgres:210197@localhost/football_matches_db'
engine = create_engine(DATABASE_URI)


# Function to extract information from the infobox
def extract_info(infobox, label):
    row = infobox.find('th', string=label)
    if row:
        return row.find_next_sibling('td').get_text(strip=True)
    return None



def extract_image_url(infobox):
    image_tag = infobox.find('td', class_='infobox-image')
    if image_tag:
        img = image_tag.find('img')
        if img and 'src' in img.attrs:
            src = img['src']
            if src.startswith('//'):
                src = 'https:' + src  # Handle relative URLs
            
            # Check if URL ends with .jpg or .jpeg
            if src.lower().endswith(('.jpg', '.jpeg')):
                return src
            
    return None

def clean_capacity(capacity):
    if pd.isna(capacity):
        return None
    capacity = str(capacity).replace('[1]', '')
    return capacity.split(' ')[0]

def clean_opened_date(opened):
    if opened:
        return str(opened).split(';', 1)[0]
    return None

def update_city_column():
    with engine.connect() as conn:
        # Fetch stadium names and corresponding city names from stadium_coordinates
        query = text('SELECT stadium, city FROM stadium_coordinates')
        result = conn.execute(query)
        
        # Prepare an update statement
        update_statement = text("""
            UPDATE stadium_info
            SET city = src.city
            FROM stadium_coordinates src
            WHERE stadium_info.stadium = src.stadium
        """)
        
        # Execute the update statement
        conn.execute(update_statement)
        print("City column updated successfully.")

def update_database(df, engine):
    # Connect to the database
    with engine.connect() as conn:
        # Start a transaction
        with conn.begin():
            # Clear the existing data from the table
            conn.execute(text("TRUNCATE TABLE stadium_info;"))
            
            # Insert new data into the table
            df.to_sql('stadium_info', conn, if_exists='append', index=False)

def update_city_column():
    with engine.connect() as conn:
        # Fetch stadium names and corresponding city names from stadium_coordinates
        with conn.begin():
            query = text('SELECT stadium, city FROM stadium_coordinates')
            result = conn.execute(query)
            
            # Prepare an update statement
            update_statement = text("""
                UPDATE stadium_info
                SET city = src.city
                FROM stadium_coordinates src
                WHERE stadium_info.stadium = src.stadium
            """)
            
            # Execute the update statement
            conn.execute(update_statement)
            print("City column updated successfully.")


# Main function to scrape stadium data
def main():
    stadium_info_list = []

    query = text('SELECT stadium, stadium_href FROM stadium_coordinates')
    with engine.connect() as conn:
        result = conn.execute(query)
        for row in result:
            # Send a GET request to the URL
            response = requests.get(row[1])
            # Parse the HTML content
            soup = BeautifulSoup(response.content, 'html.parser')

            # Find the infobox (table with stadium information)
            infobox = soup.find('table', class_='infobox vcard')

            # Initialize a dictionary to hold the extracted data
            stadium_info = {
                'stadium': row[0],
                'url': row[1],
                'capacity': extract_info(infobox, 'Capacity'),
                'field_size': extract_info(infobox, 'Field size'),
                'opened_date': extract_info(infobox, 'Opened'),
                'image_url': extract_image_url(infobox)
            }
            
            # Append the dictionary to the list
            stadium_info_list.append(stadium_info)
    
    return stadium_info_list


# Function to clean and process DataFrame
def processDataFrame(stadium_info_list):
    df = pd.DataFrame(stadium_info_list)
    df['capacity'] = df['capacity'].apply(clean_capacity)
    df['opened_date'] = df['opened_date'].apply(clean_opened_date)
    df = df.drop_duplicates()
    return df

if __name__ == "__main__":
    # Scrape the stadium data
    stadium_info_list = main()

    # Process the DataFrame
    df = processDataFrame(stadium_info_list)

    update_database(df, engine)
    update_city_column()