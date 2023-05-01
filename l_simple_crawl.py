from bs4 import BeautifulSoup
import requests
import os
import json
import shutil
import time


class IncorrectURLError(Exception):
    """
    Custom error
    """


class UnknownConfigError(Exception):
    """
    Most general error
    """


class PageParser:
    def __init__(self, url, articles_per_page):
        self.url = url
        self.articles_num = articles_per_page

        self.urls = []
        self.soup = None
        self.id_stop = 0

    def parse(self):
        response = requests.get(self.url, headers=HEADERS)
        if not response:
            raise IncorrectURLError(self.url)
        page_soup = BeautifulSoup(response.content, features='lxml')
        self.soup = page_soup.find('body')

    def find_articles(self):
        self.parse()
        articles_soup = self.soup.find_all('a', class_='poemlink')
        for article in articles_soup[:self.articles_num]:
            self.urls.append('https://proza.ru'+article.attrs['href'])
        else:
            self.id_stop = len(self.urls)


class ArticleParser:
    def __init__(self, url, article_id):
        self.url = url
        self.article_id = article_id

        self.title = ''
        self.author = ''
        self.text = []

    def parse(self):
        response = requests.get(self.url, headers=HEADERS)
        if not response:
            raise IncorrectURLError
        page_soup = BeautifulSoup(response.content, features='lxml')
        article_soup = page_soup.find('body')

        self.title = article_soup.find('index').find('h1').contents[0]
        self.author = article_soup.find('div', class_='titleauthor').find('em').find('a').contents[0]
        text = article_soup.find('div', class_='text').contents
        self.text = [str(piece).replace('\n', '').replace('\t', '') for piece in text
                     if str(piece)[0] != '<' and str(piece) != '\n']

    def write_info(self):
        article_meta_name = "{}_meta.json".format(self.article_id)
        article_txt_name = "{}_raw.txt".format(self.article_id)

        with open(os.path.join(ASSETS_PATH, article_txt_name), 'w', encoding='utf-8') as file:
            file.write(''.join(self.text))

        meta = {
                'id': self.article_id,
                'url': self.url,
                'title': self.title,
                'author': self.author,
            }

        with open(os.path.join(ASSETS_PATH, article_meta_name), "w", encoding='utf-8') as file:
            json.dump(meta,
                      file,
                      sort_keys=False,
                      indent=4,
                      ensure_ascii=False,
                      separators=(',', ': '))


def prepare_environment(base_path):
    """
    Creates ASSETS_PATH folder if not created and removes existing folder
    """
    shutil.rmtree(base_path, ignore_errors=True)
    try:
        os.makedirs(base_path, mode=0o777)
    except OSError as error:
        raise UnknownConfigError from error


def generate_links(base_link):
    links = [base_link]
    for i in range(2, 13):
        if i < 10:
            i = '0'+str(i)
        links.append(base_link.replace('month=01', f'month={str(i)}'))
    return links


if __name__ == '__main__':
    PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__))
    ASSETS_PATH = os.path.join(PROJECT_ROOT, 'articles')
    #prepare_environment(ASSETS_PATH)

    #URL_HEAD = 'https://proza.ru/texts/list.html?topic=all&type=selected&year=2022&month=01&day=1'
    URL_HEAD = 'https://proza.ru/texts/list.html?topic=all&type=selected&year=2020&month=01&day=1'
    all_year_links = generate_links(URL_HEAD)[:5]
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.41 YaBrowser/21.2.0.1099 Yowser/2.5 Safari/537.36"
    }

    # stop_id = 0
    stop_id = 704
    for cur_url in all_year_links:
        crawler_current = PageParser(cur_url, 30)
        crawler_current.find_articles()
        time.sleep(1)

        for ind, article_url in enumerate(crawler_current.urls):
            parser = ArticleParser(url=article_url, article_id=stop_id+ind+1)
            parser.parse()
            parser.write_info()

        stop_id += crawler_current.id_stop
