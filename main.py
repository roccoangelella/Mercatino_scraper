import requests
from bs4 import BeautifulSoup
import re
import polars as pl
import numpy as np
import os
import csv

class MercatinoScraper:
    def __init__(self, url):
        self.url = url
        self.filename = self.get_filename()
        self.current_items=set()
        self.file = open(self.filename, 'w', newline='', encoding='utf-8')
        self.load_existing_items()
        
        self.newitems=[]

    def get_filename(self):
        match = re.search(r'kw(.*?)(?:gp2|rp2|\.html)', self.url)
        if match:
            return f'{match.group(1)}.csv'
        return 'result.csv'

    def load_existing_items(self):
        if os.path.exists(self.filename) and os.path.getsize(self.filename) > 0:
            with open(self.filename,'r',encoding='utf-8') as file:
                reader=csv.reader(file)
                next(reader,None)
            for row in reader:
                if len(row)>=3:
                    self.current_items.add(row[0],row[1],row[2])

    def scrape_website(self, url):
        try:
            response = requests.get(url)
            response.raise_for_status()
            return BeautifulSoup(response.text, 'html.parser')
        except requests.exceptions.RequestException as e:
            print(f"Error fetching the website: {e}")
            return None

    def scrape_page(self, link):
        soup = self.scrape_website(link)
        if soup is None:
            return

        box = soup.find_all('span', class_='box_prod_inner')
        where = soup.find_all('span', class_='place')

        for item in range(len(box)):
            title = box[item].find('span', class_='tit').text.replace(',', ' ')
            price = box[item].find('span', class_='prz').text.replace(',', ' ')
            place = where[item].text

            title_clean = title.encode('ascii', errors='ignore').decode()
            
            if price[0] == '€':
                price=price[1:-3]
                
            new_item=(title_clean,price,place)
            if new_item not in self.current_items:
                self.file.write(f'\n{title_clean},{price},{place}')
                self.current_items.add(new_item)
                self.newitems.append([new_item[0],new_item[1],new_item[2]])
            
    def get_total_pages(self):
        soup = self.scrape_website(self.url)
        if soup:
            try:
                return int(soup.find_all('div', class_='input')[6].text.split()[-1])
            except (IndexError, ValueError):
                print("Couldn't determine total number of pages.")
        return 1

    def scrape_all_pages(self):
        n_pages = self.get_total_pages()
        self.scrape_page(self.url)

        for x in range(2, n_pages + 1):
            curr_link = f'{self.url[:-5]}-pg{x}.html'
            self.scrape_page(curr_link)

    def close_file(self):
        self.file.close()

def main():
    link = input('Inserisci il link di Mercatino Musicale da monitorare: ')
    scraper = MercatinoScraper(link)
    scraper.scrape_all_pages()
    scraper.close_file()



if __name__ == "__main__":
    main()
