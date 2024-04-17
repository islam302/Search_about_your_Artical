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

    def get_screen_shots(self, found_links, folder_path):
        for word, links in found_links.items():
            word_folder_path = os.path.join(folder_path, 'screenshots')
            os.makedirs(word_folder_path, exist_ok=True)
            for link in links:
                try:
                    self.driver.get(link)
                    time.sleep(1)
                    screenshot_name = link.replace('/', '_').replace(':', '_') + ".png"
                    screenshot_path = os.path.join(word_folder_path, screenshot_name)
                    self.driver.save_screenshot(screenshot_path)
                except Exception as e:
                    print(f"Error taking screenshot of {link}: {e}")

    def get_publish_date(self, link, word):
        try:
            response = requests.get(link)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                text_content = soup.get_text()

                date_patterns = [
                    # English date formats
                    r'\b(\d{1,2}/\d{1,2}/\d{2,4})\b',  # Matches dates like 12/31/2022 or 1/1/22
                    r'\b(\d{1,2}\s+\w+\s+\d{2,4})\b',  # Matches dates like 31 December 2022 or 1 Jan 22
                    r'\b(\d{4}-\d{2}-\d{2})\b',  # Matches dates like 2022-12-31
                    r'\b(\d{1,2}\s+\w+\s+\d{4})\b',  # Matches dates like 12 December 2022
                    r'\b(\d{1,2}/\d{1,2}/\d{2,4}\s+\d{1,2}:\d{2})\b',  # Matches dates like 12/31/2022 1:30
                    r'\b(\d{1,2}\s+\w+\s+\d{4}\s+\d{1,2}:\d{2})\b',  # Matches dates like 31 December 2022 1:30
                    r'\b(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})\b',  # Matches dates like 2022-12-31T12:30:00
                    r'\b(\d{1,2}/\d{1,2}/\d{2,4}\s+\d{1,2}:\d{2}:\d{2})\b',  # Matches dates like 12/31/2022 12:30:00
                    r'\b(\d{1,2}\s+\w+\s+\d{4}\s+\d{1,2}:\d{2}:\d{2})\b',
                    r'\b(\d{1,2}\s+[?-?]+\s+\d{4})\b',  # Matches dates like ?? ?????? ????
                    r'\b(\d{1,2}/\d{1,2}/\d{2,4})\s+[?-?]+\s+\d{1,2}:\d{2}\b',  # Matches dates like 12/31/2022 1:30
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

    def get_screen_shots(self, found_links, folder_path):
        for links in found_links:
            word_folder_path = os.path.join(folder_path, 'screenshots')
            os.makedirs(word_folder_path, exist_ok=True)
            for link_counter, link in enumerate(links, start=1):
                try:
                    self.driver.get(link)
                    time.sleep(1)
                    screenshot_name = f'screenshot{link_counter}.png'
                    screenshot_path = os.path.join(word_folder_path, screenshot_name)
                    self.driver.save_screenshot(screenshot_path)
                except Exception as e:
                    print(f"Error taking screenshot of {link}: {e}")

    def get_searching_links(self, words, links, folder_path):
        found_links = {}
        for word in words:
            found_links[word] = []
            for link in links:
                search_url = f"{link}{word}"
                print(search_url)
                response = requests.get(search_url)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, "html.parser")
                    links = soup.find_all("a")
                    links_found = 0
                    for link in links:
                        href = link.get("href")
                        if href.startswith("/url?q="):
                            extracted_link = href.replace("/url?q=", "").split("&sa=")[0]
                            full_link = urljoin(search_url, extracted_link)
                            if word.lower() in extracted_link.lower():
                                date = self.get_publish_date(full_link, word)
                                found_links[word].append({'link': extracted_link, 'date': date})
                                links_found += 1
                                if links_found >= 10:
                                    break
        return found_links

    # def get_searching_links(self, words, links, folder_path):
    #     found_links = {}
    #     for word in words:
    #         found_links[word] = []
    #         for link in links:
    #             search_url = f"{link}{word}"
    #             response = requests.get(search_url)
    #             if response.status_code == 200:
    #                 base_url = urlparse(link).scheme + '://' + urlparse(link).netloc  # Extract base URL from the link
    #                 soup = BeautifulSoup(response.content, 'html.parser')
    #                 search_results = soup.find_all('a', href=True)
    #                 extracted_links = [result['href'] for result in search_results if result['href'].startswith('http')]
    #                 link_counter = 0
    #                 for extracted_link in extracted_links:
    #                     if link_counter >= 10:
    #                         break
    #                     full_link = urljoin(base_url, extracted_link)
    #                     if word.lower() in extracted_link.lower():
    #                         date = self.get_publish_date(full_link, word)
    #                         found_links[word].append({'link': extracted_link, 'date': date})
    #                         link_counter += 1
    #     return found_links

    def main(self):
        links = self.get_search_links('countries.txt')
        words = self.get_words_from_file('news.txt')

        for word in words:
            folder_name = word.replace(':', '-').replace('"', '')
            folder_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), folder_name)
            os.makedirs(folder_path, exist_ok=True)
            self.start_driver()
            found_links = self.get_searching_links([word], links, folder_path)
            print(found_links)

            data = []
            for link_data_list in found_links.get(word, []):
                if not link_data_list:
                    data.append({'Link': 'not found', 'Date': 'not found'})
                else:
                    if isinstance(link_data_list, dict):
                        link_data_list = [link_data_list]

                    for link_data in link_data_list:
                        data.append(
                            {'Link': link_data.get('link', 'not found'), 'Date': link_data.get('date', 'not found')})

            excel_path = os.path.join(folder_path, f'links_and_dates.xlsx')
            df = pd.DataFrame(data)
            df.to_excel(excel_path, index=False)

        driver_pid = self.driver.service.process.pid
        self.killDriverZombies(driver_pid)


if __name__ == '__main__':
    bot = Search_About_News()
    bot.main()




    # def create_google_search_links(self, countries):
    #     google_links = []
    #     for country in countries:
    #         try:
    #             country_obj = pycountry.countries.lookup(country)
    #             zip_code = country_obj.alpha_2.lower()
    #             google_links.append(f"https://www.google.com.{zip_code}/")
    #         except LookupError:
    #             print(f"Country '{country}' not found. Skipping...")
    #     return google_links
    #
    # def search_and_get_links(self, query, num_results=10):
    #     try:
    #         search_results = search(query, num_results=num_results, lang='en')
    #         return list(search_results)
    #     except Exception as e:
    #         print(f"An error occurred: {e}")
    #         return []
    #
    # def search_for_word_in_google(self, words, arab_countries_google_urls):
    #     result_links = {}
    #     for word in words:
    #         result_links[word] = []
    #         for url in arab_countries_google_urls:
    #             search_url = f'{url}search?q={word}'
    #             try:
    #                 response = requests.get(search_url)
    #                 if response.status_code == 200:
    #                     soup = BeautifulSoup(response.content, "html.parser")
    #                     links = soup.find_all("a")
    #                     links_found = 0
    #                     for link in links:
    #                         href = link.get("href")
    #                         if href.startswith("/url?q="):
    #                             result_links[word].append(href.replace("/url?q=", "").split("&sa=")[0])
    #                             links_found += 1
    #                             if links_found >= 10:
    #                                 break
    #             except requests.exceptions.RequestException as e:
    #                 continue
    #
    #     return result_links
