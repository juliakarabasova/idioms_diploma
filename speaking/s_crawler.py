from bs4 import BeautifulSoup
import requests
import os
import json
import shutil
import wget
import zipfile
import glob

from sub_reader import SrtProcessor


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

    def parse(self):
        response = requests.get(self.url, headers=HEADERS)
        if not response:
            raise IncorrectURLError(self.url)
        page_soup = BeautifulSoup(response.content, features='lxml')
        self.soup = page_soup.find('body')

    def find_articles(self):
        self.parse()
        articles_soup = self.soup.find_all('a', class_='bnone')
        for article in articles_soup[:self.articles_num]:
            self.urls.append('https://www.opensubtitles.org' + article.attrs['href'])


class ArticleParser:
    def __init__(self, url, article_id):
        self.url = url
        self.article_id = article_id
        self.title = ''
        self.text = ''
        self.download_link = ''

    def parse(self):
        response = requests.get(self.url, headers=HEADERS)
        if not response:
            raise IncorrectURLError
        page_soup = BeautifulSoup(response.content, features='lxml')
        article_soup = page_soup.find('body')

        download = article_soup.find('a', download='download')
        add_title = article_soup.find('img', alt="Название релиза", title="Название релиза")
        try:
            self.title = download.attrs['data-product-title'] + add_title.next_element
        except AttributeError:
            self.title = download.attrs['data-product-title']
        print(self.title)
        self.download_link = 'https://www.opensubtitles.org' + download.attrs['href']

    def write_info(self):
        article_meta_name = "{}_meta.json".format(self.article_id)

        wget.download(self.download_link, out=ZIP_PATH + '\\' + self.title + '.zip')

        with zipfile.ZipFile(ZIP_PATH + '\\' + self.title + '.zip') as myzip:
            files = list(text_file.filename for text_file in myzip.infolist())
            right_file = [file for file in files if file.endswith('.srt') or file.endswith('.ass')][0]
            print(right_file)
            with myzip.open(right_file, 'r') as myfile:
                with open(ZIP_PATH + '\\' + self.title + '.srt', 'wb') as f:
                    self.text = myfile.read()
                    print('TEXT BEFORE: ', self.text[:20])
                    f.write(self.text)

        meta = {
                'id': self.article_id,
                'url': self.url,
                'title': self.title,
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


if __name__ == '__main__':
    PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__))
    ASSETS_PATH = os.path.join(PROJECT_ROOT, 'subtitles')
    ZIP_PATH = os.path.join(ASSETS_PATH, 'zips')

    # prepare_environment(ASSETS_PATH)    # CLEANS THE PATH, KEEP IN MIND (!!!)
    # prepare_environment(ZIP_PATH)

    # URL_HEAD = 'https://www.opensubtitles.org/ru/search/sublanguageid-rus/searchonlytvseries-on/movielanguage-russian/moviecountry-russia/subformat-srt'
    URL_HEAD = 'https://www.opensubtitles.org/ru/search/sublanguageid-rus/searchonlytvseries-on/movielanguage-russian/moviecountry-russia/subformat-srt/offset-240'
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.41 YaBrowser/21.2.0.1099 Yowser/2.5 Safari/537.36"
    }

    crawler_current = PageParser(URL_HEAD, 40)
    crawler_current.find_articles()

    start_ind = 240
    for ind, article_url in enumerate(crawler_current.urls):
        parser = ArticleParser(url=article_url, article_id=start_ind+ind+1)
        parser.parse()
        parser.write_info()

        processor = SrtProcessor(start_ind+ind+1, parser.title, ZIP_PATH+'\\')
        processor.process()
        processor.save_processed(ASSETS_PATH+'\\')
