"""
Scrapper implementation
"""
import json
from pathlib import Path
import shutil
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from constants import ASSETS_PATH, CRAWLER_CONFIG_PATH
from core_utils.article import Article


class IncorrectURLError(Exception):
    """
    Seed URL does not match standard pattern
    """


class NumberOfArticlesOutOfRangeError(Exception):
    """
    Total number of articles to parse is too big
    """


class IncorrectNumberOfArticlesError(Exception):
    """
    Total number of articles to parse in not integer
    """


class Crawler:
    """
    Crawler implementation
    """
    def __init__(self, seed_urls, max_articles: int):
        self.seed_urls = seed_urls
        self.max_articles = max_articles
        self.urls = []

    def _extract_url(self, article_bs):
        full_urls = []
        all_urls_bs = article_bs.find_all(class_="uho__link uho__link--overlay")
        for url_bs in all_urls_bs:
            url_to_article = url_bs['href']
            full_urls.append('https://www.kommersant.ru'+url_to_article)
        return full_urls

    def find_articles(self):
        """
        Finds articles
        """
        for _, seed_url in enumerate(self.seed_urls):
            response = requests.get(url=seed_url)
            soup = BeautifulSoup(response.text, features="lxml")
            articles_urls_bs = self._extract_url(soup)
            list_of_urls = [url_bs for url_bs in articles_urls_bs if len(self.urls) < self.max_articles]
            for full_url in list_of_urls:
                if len(self.urls) <= self.max_articles:
                    self.urls.append(full_url)

    def get_search_urls(self):
        """
        Returns seed_urls param
        """
        return self.seed_urls

class HTMLParser:
    def __init__(self, article_url, article_id):
        self.article_url = article_url
        self.article_id = article_id
        self.article = Article(article_url, article_id)

    def _fill_article_with_text(self, article_bs):
        text_bs = article_bs.find(class_='doc__text')
        if text_bs is None:
            text_bs = article_bs.find(class_='b-article__text air__text')
        self.article.text = text_bs.text

    def _fill_article_with_meta_information(self, article_bs):
        title_bs = article_bs.find(class_="doc_header__name js-search-mark").text
        self.article.title = title_bs
        print(title_bs)

        date_bs = article_bs.find(class_="doc_header__publish_time").text
        date = datetime.strptime(date_bs, "%d.%m.%Y, %H:%M")
        self.article.date = date

        try:
            author_bs = article_bs.find(class_='doc__text document_authors').text
        except AttributeError:
            author_bs = 'NOT FOUND'
        self.article.author = author_bs

    def parse(self):
        response = requests.get(self.article_url)
        article_bs = BeautifulSoup(response.text, 'html.parser')
        self._fill_article_with_text(article_bs)
        self._fill_article_with_meta_information(article_bs)
        return self.article

def prepare_environment(base_path):
    """
    Creates ASSETS_PATH folder if not created and removes existing folder
    """
    path_for_env = Path(base_path)
    if path_for_env.exists():
        shutil.rmtree(base_path)
    path_for_env.mkdir(parents=True)


def validate_config(crawler_path):
    """
    Validates given config
    """
    with open(crawler_path) as file:
        configuration = json.load(file)

    seed_urls = configuration["seed_urls"]
    total_articles = configuration["total_articles_to_find_and_parse"]

    if not isinstance(total_articles, int) or total_articles <= 0:
        raise IncorrectNumberOfArticlesError
    if not isinstance(seed_urls, list) or not seed_urls:
        raise IncorrectURLError
    http_pattern = "https://www.kommersant.ru"
    for url in configuration["seed_urls"]:
        if http_pattern not in url:
            raise IncorrectURLError
    if total_articles > 100:
        raise NumberOfArticlesOutOfRangeError

    return seed_urls, total_articles


if __name__ == '__main__':
    urls, articles = validate_config(CRAWLER_CONFIG_PATH)
    prepare_environment(ASSETS_PATH)
    crawler = Crawler(urls, articles)
    crawler.find_articles()
    print(crawler.urls)
    A_ID = 1
    for article_url_new in crawler.urls:
        parsing_article = HTMLParser(article_url_new, A_ID)
        parsed_article = parsing_article.parse()
        parsed_article.save_raw()
        A_ID += 1 #sampleline
