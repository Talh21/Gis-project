import requests
from bs4 import BeautifulSoup
import pandas as pd
from sqlalchemy import create_engine

class StadiumCoordinates:

    def __init__(self, base_url, db_url):
        self.base_url = base_url
        self.db_url = db_url
        self.data = []

    def get_stadium_links(self):
        try:
            response = requests.get(self.base_url)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Failed to retrieve data from {self.base_url}: {e}")
            return
        
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find the table with stadium information
        table_element = soup.find('table', {'class': 'wikitable'})
        if not table_element:
            print("Table not found")
            return

        rows = table_element.find_all('tr')

        for row in rows[1:]:  # Skip the header row
            cells = row.find_all('td')
            if len(cells) < 5:
                continue

            # Extract stadium name and link
            stadium_link = cells[2].find('a', href=True)
            stadium_name = stadium_link.text if stadium_link else 'Unknown'
            stadium_href = stadium_link['href'] if stadium_link else ''

            # Extract city name
            city_link = cells[4].find('a', href=True)
            city_name = city_link.text if city_link else 'Unknown'

            # Ensure the stadium link is properly formed
            full_stadium_href = f'https://en.wikipedia.org{stadium_href}' if stadium_href else ''

            # Store the extracted information
            self.data.append({
                'stadium': stadium_name,
                'stadium_href': full_stadium_href,
                'city': city_name
            })

    def get_coordinates(self):
        self.get_stadium_links()

        for index, stadium in enumerate(self.data):
            try:
                response = requests.get(stadium['stadium_href'])
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')
            except requests.exceptions.RequestException as e:
                print(f"Failed to retrieve coordinates for {stadium['stadium']}: {e}")
                self.data[index]['latitude'] = None
                self.data[index]['longitude'] = None
                continue
            
            # Extract coordinates from the page
            geo_cor = soup.find('span', class_='geo')
            if geo_cor:
                try:
                    l, longitude = geo_cor.text.split(';')
                    self.data[index]['latitude'] = l.strip()
                    self.data[index]['longitude'] = longitude.strip()
                except ValueError:
                    self.data[index]['latitude'] = None
                    self.data[index]['longitude'] = None
            else:
                self.lata[index]['latitude'] = None
                self.data[index]['longitude'] = None

        # Remove rows where l or longitude are empty
        self.data = [row for row in self.data if row['latitude'] and row['longitude']]

    def save_to_db(self):
        # Convert the list of dictionaries to a DataFrame
        df = pd.DataFrame(self.data)

        # Create a connection to the PostgreSQL database
        engine = create_engine(self.db_url)

        # Save the DataFrame to the stadium_coordinates table
        try:
            df.to_sql('stadium_coordinates', engine, schema='stadium_coordinates', if_exists='append', index=False)
            print("Data successfully saved to the database.")
        except Exception as e:
            print(f"Failed to save data to the database: {e}")


def main():
    base_url = "https://en.wikipedia.org/wiki/List_of_football_stadiums_in_Israel"
    
    # PostgreSQL connection URL (replace with your actual database credentials)
    db_url = 'postgresql://postgres:210197@localhost/football_matches_db'

    app = StadiumCoordinates(base_url=base_url, db_url=db_url)
    app.get_coordinates()
    
    # Save directly to the database
    app.save_to_db()


if __name__ == "__main__":
    main()
