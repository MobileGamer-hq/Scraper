from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import json
import csv
import re
import time

# Define the product model (for reference)
product_model = {
    "name": "",
    "price": {"min": None, "max": None},
    "price_text": "",
    "old": {"min": None, "max": None},
    "old_text": "",
    "discount": "",
    "shipping": "",
    "rating": {"no": None, "out": 5},
    "points": 0,
    "img": "",
    "url": ""
}

class Crawler:
    def __init__(self, urls):
        self.urls = urls
        self.driver = webdriver.Chrome(service=Service("chromedriver.exe"))
        self.products = []
        self.search = ""
        self.maxDepth = 5
        self.maxWidth = 10
        self.infos = []
        self.visited = []

    def convert_search_to_url(self, search, sort='relevance'):
        self.search = search.strip().replace(" ", "-")
        search_query = search.strip().replace(" ", "+")
        return f"https://www.jumia.com.ng/catalog/?q={search_query}&sort={sort}#catalog-listing" if sort != 'relevance' else f"https://www.jumia.com.ng/catalog/?q={search_query}"

    def convert_price_string_to_value(self, price_string):
        numeric_string = re.sub(r'[^\d,-]', '', price_string)
        if not numeric_string:
            return {"min": None, "max": None}
        
        values = [int(value.replace(",", "")) for value in numeric_string.split('-') if value]
        return {"min": values[0], "max": values[1] if len(values) > 1 else None}

    def convert_rating_string_to_object(self, rating_string):
        rating_value = re.findall(r'\d+', rating_string)
        return {"no": int(rating_value[0]), "out": 5} if rating_value else {"no": None, "out": 5}

    def scrape_website(self, url):
        self.driver.get(url)
        self.driver.implicitly_wait(10)
        return self.driver.page_source

    def extract_products(self, html):
        soup = BeautifulSoup(html, "html.parser")
        products = []
        
        for element in soup.select('div.-paxs.row._no-g._4cl-3cm-shs article'):
            name = element.select_one('h3.name').get_text(strip=True)
            price_text = element.select_one('div.prc').get_text(strip=True)
            old_text = element.select_one('div.old').get_text(strip=True) if element.select_one('div.old') else ""
            discount = element.select_one('div.bdg._dsct._sm').get_text(strip=True).replace('%', '') if element.select_one('div.bdg._dsct._sm') else "0"
            shipping = element.select_one('div.bdg._glb._xs').get_text(strip=True) if element.select_one('div.bdg._glb._xs') else ""
            img = element.select_one('img').get("data-src")
            url = "https://www.jumia.com.ng" + element.select_one('a.core').get("href")
            rating_text = element.select_one('div.stars._s').get_text(strip=True) if element.select_one('div.stars._s') else ""
            
            product = {
                "name": name,
                "price": self.convert_price_string_to_value(price_text),
                "price_text": price_text,
                "old": self.convert_price_string_to_value(old_text),
                "old_text": old_text,
                "discount": int(discount),
                "shipping": shipping,
                "rating": self.convert_rating_string_to_object(rating_text),
                "points": 0,
                "img": img,
                "url": url
            }
            products.append(product)
        
        return products

    
            
        
        
    def save_as_json(self, data, filename):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        print(f'Data saved as JSON: {filename}')

    def save_as_csv(self, data, filename):
        with open(filename, mode='w', encoding='utf-8', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=data[0].keys() if data else [])
            writer.writeheader()
            writer.writerows(data)

    def read_data(self, filename):
        with open(filename, mode='r', encoding='utf-8') as file:
            data = json.load(file)
        print(f'Data loaded as JSON: {data}')
        return data
    
    def assign_points(self):
        average_price = sum(product['price']['min'] for product in self.products if product['price']['min']) / len([p for p in self.products if p['price']['min']])
        for product in self.products:
            min_price = product['price']['min']
            if min_price is not None:
                product['points'] = 5 * (min_price / average_price) if min_price < average_price else 5 * (average_price / min_price)
        return self.products

    def sort_by_points(self):
        self.products.sort(key=lambda x: x['points'], reverse=True)
        
    def extract_url(self, html):
        soup = BeautifulSoup(html, "html.parser")
        urls = []
        for element in soup.select('a'):
            href = element.get("href")
            if href and href.startswith("/wiki/"):
                full_url = "https://en.wikipedia.org" + href
                urls.append(full_url)
                
        if len(urls) > 10:
            return urls[int(len(urls)/2):int(len(urls)/2) + self.maxWidth]
        return urls
    
    def extract_data(self, html):
        soup = BeautifulSoup(html, "html.parser")
        try:
            title = soup.select_one("title").get_text(strip=True)
            info = {title: []}

            for element in soup.select('p'):            
                info[title].append(element.text)
            return info
        except:
            return None
        
    
    def crawl_page(self, url, depth = 0):
        html = self.scrape_website(url)
        urls = []
        if depth != self.maxDepth:
            urls = self.extract_url(html)
            
        print(urls)
        
        for url in urls:
            self.crawl_page(url, depth + 1)
            
        if url in self.visited:
            pass
        else:
            self.infos.append(self.extract_data(html))
            self.visited.append(url)
            
        
    

    def scrape(self):
        all_products = []
        for url in self.urls:
            html = self.scrape_website(url)
            all_products.extend(self.extract_products(html))

        self.save_as_json(all_products, 'jumia_products.json')
        self.save_as_csv(all_products, 'jumia_products.csv')
        print("Crawling completed.")
        return all_products

    def scrape_single_product(self, url):
        
        html = self.scrape_website(url)
        self.products = self.extract_products(html)
        self.assign_points()
        self.sort_by_points()
        self.save_as_json(self.products, f'./data/json/jumia_single_product-{self.search}.json')
        self.save_as_csv(self.products, f'./data/csv/jumia_single_product-{self.search}.csv')
        print("Crawling completed.")
        return self.products

    def close(self):
        self.driver.quit()
        
    def TestCrawler(self):
        self.maxDepth = 2
        self.maxWidth = 5
        word = input("Enter  a Word: ")
        self.crawl_page(f"https://en.wikipedia.org/wiki/{word}")
        self.save_as_json(crawler.infos, f'./data/crawler/json/Wikipedia-{word}.json')
        self.close()
        
        print(self.visited)
        
        # crawler.read_data(f'./data/crawler/json/Wikipedia-{"Food"}.json')
        
    
    def TestScraper(self):
        # Usage
        product = input("What Product Whould You Like To Scrape: ")
        urls = ["https://www.jumia.com.ng/catalog/?q=laptop"]
        
        self.scrape_single_product(self.convert_search_to_url(product))
        self.close()




    

    
crawler = Crawler([])
crawler.TestScraper()
