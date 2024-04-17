import time
import re
import psutil
from bs4 import BeautifulSoup
import requests
import pandas as pd
from urllib.parse import quote, urlparse, urljoin
from dateutil import parser as date_parser
import calendar
from dateutil.parser import ParserError
import urllib
from dateutil import parser as date_parser
import locale
from newspaper import Article
from ChromeDriver import WebDriver
import os
import datetime

class Search_About_News:

    def __init__(self):
        self.driver = None

    def start_driver(self):
        self.driver = WebDriver.start_driver(self)
        return self.driver

    def killDriverZombies(self, driver_pid):
        try:
            parent_process = psutil.Process(driver_pid)
            children = parent_process.children(recursive=True)
            for process in [parent_process] + children:
                process.terminate()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    def get_search_links(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            links = file.readlines()
        return [urllib.parse.unquote(link.strip()) for link in links if link.strip()]

    def get_links_from_file(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            links = file.readlines()
        return [urllib.parse.unquote(link.strip()) for link in links if link.strip()]

    def get_words_from_file(self, words_file_path):
        with open(words_file_path, 'r', encoding='utf-8') as file:
            words = file.readlines()
        return list(set([word.strip() for word in words if word.strip()]))

    def get_publish_date(self, link, word):
        try:
            response = requests.get(link)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                text_content = soup.get_text()

                date_patterns = [
                    r'\b(\d{1,2}/\d{1,2}/\d{2,4})\b',  # Matches dates like 12/31/2022 or 1/1/22
                    r'\b(\d{1,2}\s+\w+\s+\d{2,4})\b',  # Matches dates like 31 December 2022 or 1 Jan 22
                    r'\b(\d{4}-\d{2}-\d{2})\b',  # Matches dates like 2022-12-31
                    r'\b(\d{1,2}\s+\w+\s+\d{4})\b',  # Matches dates like 12 December 2022
                    r'\b(\d{1,2}/\d{1,2}/\d{2,4}\s+\d{1,2}:\d{2})\b',  # Matches dates like 12/31/2022 1:30
                    r'\b(\d{1,2}\s+\w+\s+\d{4}\s+\d{1,2}:\d{2})\b',  # Matches dates like 31 December 2022 1:30
                    r'\b(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})\b',  # Matches dates like 2022-12-31T12:30:00
                    r'\b(\d{1,2}/\d{1,2}/\d{2,4}\s+\d{1,2}:\d{2}:\d{2})\b',  # Matches dates like 12/31/2022 12:30:00
                    r'\b(\d{1,2}\s+\w+\s+\d{4}\s+\d{1,2}:\d{2}:\d{2})\b',
                    r'\b(\d{1,2}\s+[?-?]+\s+\d{4})\b',
                    r'??? ??????:\s+(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})',# Matches dates like ?? ?????? ????
                    r'\b(\d{1,2}/\d{1,2}/\d{2,4})\s+[?-?]+\s+\d{1,2}:\d{2}\b',  # Matches dates like 12/31/2022 1:30
                    # Add more patterns here as needed
                ]

                for pattern in date_patterns:
                    match = re.search(pattern, text_content)
                    if match:
                        date_str = match.group(1)
                        return date_str
                return 'not found'
            else:
                return 'not found'
        except Exception as e:
            print(f"Error getting publish date from {link}: {e}")
            return 'not found'

    def get_response(self, words, links, folder_path):
        found_links = {}
        for word in words:
            found_links[word] = []
            screenshot_counter = 1
            for link in links:
                match_link = False
                URL = f'{link}{word}'
                response = requests.get(URL)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    all_links = soup.find_all('a', href=True)
                    search_url_parsed = urlparse(link)
                    domain = f'{search_url_parsed.scheme}://{search_url_parsed.netloc}'
                    for a_tag in all_links:
                        href = a_tag.get('href')
                        if href:
                            full_link = urljoin(domain, href)
                            if word.lower() in a_tag.get_text().lower():
                                date = self.get_publish_date(full_link, word)
                                found_links[word].append({'link': full_link, 'date': date})
                                match_link = True
                                break

                    if not match_link:
                        if all_links:
                            first_link = urljoin(domain, all_links[0]['href'])
                            date = self.get_publish_date(first_link, word)
                            found_links[word].append({'link': first_link, 'date': date})
                        else:
                            with open('not_found_in_this_links.txt', 'a') as file:
                                file.write(link + '\n')

                else:
                    with open('not_found_in_this_links.txt', 'a') as file:
                        file.write(link + '\n')

            word_folder_path = os.path.join(folder_path, 'screenshots')
            os.makedirs(word_folder_path, exist_ok=True)

            self.start_driver()

            for link_data in found_links[word]:
                try:
                    screenshot_name = f'screenshot{str(screenshot_counter)}.png'
                    screenshot_path = os.path.join(word_folder_path, screenshot_name)
                    self.driver.get(link_data['link'])
                    time.sleep(1)
                    self.driver.save_screenshot(screenshot_path)
                    screenshot_counter += 1
                except Exception as e:
                    print(f"Error taking screenshot of {e}")

        driver_pid = self.driver.service.process.pid
        self.killDriverZombies(driver_pid)
        return found_links

    def main(self):

        words = self.get_words_from_file('news.txt')
        links = self.get_links_from_file('links.txt')

        for word in words:
            folder_name = word.replace(':', '-').replace('"', '')
            folder_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), folder_name)
            os.makedirs(folder_path, exist_ok=True)

            found_links = self.get_response(words, links, folder_path)
            print(found_links)

            data = []
            for link_data_list in found_links.get(word, []):
                if not link_data_list:
                    data.append({'Link': link, 'Date': 'not found'})
                else:
                    if isinstance(link_data_list, dict):
                        link_data_list = [link_data_list]

                    for link_data in link_data_list:
                        data.append(
                            {'Link': link_data.get('link', 'not found'), 'Date': link_data.get('date', 'not found')})

            excel_path = os.path.join(folder_path, f'links_and_dates.xlsx')
            df = pd.DataFrame(data)
            df.to_excel(excel_path, index=False)



if __name__ == '__main__':
    bot = Search_About_News()
    bot.main()


