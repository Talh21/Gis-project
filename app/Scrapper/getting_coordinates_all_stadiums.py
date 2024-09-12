import requests
from bs4 import BeautifulSoup
import pandas as pd


class StadiumCoordinates:

    def __init__(self, base_url):
        self.base_url = base_url
        self.data = []

    def get_stadium_links(self):
        response = requests.get(self.base_url)
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

            # Store the extracted information
            self.data.append({
                'Stadium': stadium_name,
                'Stadium_href': 'https://en.wikipedia.org' + stadium_href,
                'City': city_name
            })

    def get_coordinates(self):
        self.get_stadium_links()

        for index, stadium in enumerate(self.data):
            response = requests.get(stadium['Stadium_href'])
            soup = BeautifulSoup(response.content, 'html.parser')
            geo_cor = soup.find('span', class_='geo')
            if geo_cor is not None:
                latitude, longitude = geo_cor.text.split(';')
                self.data[index]['Latitude'] = latitude.strip()
                self.data[index]['Longitude'] = longitude.strip()
            else:
                self.data[index]['Latitude'] = None
                self.data[index]['Longitude'] = None

        # Remove rows where Latitude or Longitude are empty
        self.data = [row for row in self.data if row['Latitude'] and row['Longitude']]

    def save_to_csv(self, filename):
        df = pd.DataFrame(self.data)
        df.to_csv(filename, index=False, na_rep='None')


def main():
    base_url = "https://en.wikipedia.org/wiki/List_of_football_stadiums_in_Israel"
    app = StadiumCoordinates(base_url=base_url)
    app.get_coordinates()
    app.save_to_csv('C:\GIS\Project\GIS\\app\static\data\stadium_coordinates.csv')


if __name__ == "__main__":
    main()
