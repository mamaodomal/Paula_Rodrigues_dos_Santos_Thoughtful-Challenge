from robocorp.tasks import task
from RPA.Browser.Selenium import Selenium
from RPA.Excel.Files import Files
import re
from datetime import datetime, timedelta
import requests
import os

class NewsScraper:
    def __init__(self):
        self.browser = Selenium()
        self.excel = Files()
        self.excel_path = "./output/news_data.xlsx"

        os.makedirs('./output/img', exist_ok=True)

        if not os.path.exists(self.excel_path):
            self.excel.create_workbook(path=self.excel_path, fmt="xlsx")
            self.excel.save_workbook()
            self.excel.open_workbook(self.excel_path)
            self.excel.create_worksheet('news_data')

            self.excel.append_rows_to_worksheet([['title', 'date', 'description', 'image name', 'search count', 'contains money']], 'news_data')

        else:
            self.excel.open_workbook(self.excel_path)
        
    def start_browser(self, url):
        self.browser.open_available_browser(url)
    
    def search_news(self, search_term, category, months):
        # search_box = self.browser.find_element('//*[@id="ybar-sbq"]')
        # search_box.send_keys(search_term)
        # self.browser.find_element('//*[@id="ybar-search"]').click()
        
        # self.filter_news(category)
        
        today = datetime.today()
        start_date = today - timedelta(days=30*months)
        news_items = self.browser.find_elements('//*[@id="web"]/ol/li')
        for item in news_items:
            text = item.text.split('\n')
            title = text[0]
            dateTransform = text[1]
            date_hours = self.parse_date(dateTransform)
            description = '\n'.join(text[2:])
            image_name = self.download_image(item)
            
            # Processamento de dados
            search_count = len(re.findall(search_term, title, re.IGNORECASE)) + \
                           len(re.findall(search_term, description, re.IGNORECASE))
            contains_money = bool(re.search(r'\$\d+', title + description))
            
            self.log_data(title, date_hours, description, image_name, search_count, contains_money)
    
    def parse_date(self, dateTransform):
        dateMatch = re.search(r'(\d+ hours? ago)', dateTransform)
        if dateMatch:
            dateHourStr = dateMatch.group(1)
            if 'hour' in dateHourStr:
                hours = int(dateHourStr.split()[0])
                return datetime.now() - timedelta(hours=hours)
        return datetime.now()

    def filter_news(self, category):
        self.browser.wait_until_element_is_visible(category, timeout=100)
        category_filter = self.browser.find_element(category)
        category_filter.click()
    
    def download_image(self, item):
        image_url = self.browser.find_element(locator="//div/ul/li/a/img", parent=item).get_attribute("src")
        image_name = image_url.split("/")[-1]


        if image_url:
            response = requests.get(image_url)
            if response.status_code == 200:
                with open(f"./output/img/{image_name}.jpg", 'wb') as file:
                    file.write(response.content)
        return image_name
    
    def log_data(self, title, date, description, image_name, search_count, contains_money):
        self.excel.append_rows_to_worksheet([[title, date.strftime('%Y-%m-%d %H:%M:%S'), description, image_name, search_count, contains_money]], 'news_data')
        self.excel.save_workbook()
    
    def close_browser(self):
        self.browser.close_browser()

xpath_dict = {
    "News": '//*[@id="horizontal-bar"]/ol/li[1]/div/div[1]/ul/li[2]/a',
    "Videos": '//*[@id="horizontal-bar"]/ol/li[1]/div/div[1]/ul/li[3]/a',
    "Images": '//*[@id="horizontal-bar"]/ol/li[1]/div/div[1]/ul/li[4]/a',
}
@task
def minimal_task():
    scraper = NewsScraper()
    # scraper.start_browser('https://search.yahoo.com/search?p=Donald+Trump&fr=uh3_news_web&fr2=p%3Anews%2Cm%3Asb&.tsrc=uh3_news_web')
    scraper.start_browser('https://news.search.yahoo.com/search;_ylt=AwrNOmai1ctmA1MJyYhXNyoA;_ylu=Y29sbwNiZjEEcG9zAzEEdnRpZAMEc2VjA3BpdnM-?p=Donald+Trump&fr2=piv-web&.tsrc=uh3_news_web&fr=uh3_news_web')
    scraper.search_news('Donald Trump', xpath_dict['News'], 1)
    # scraper.close_browser()