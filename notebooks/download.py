import glob
import os
import random
import requests
import time
from typing import List

from parse import read_html_file, get_language_links, filter_language_links
from parse import get_page_filename


TARGET_LANGS = [
    'de',
    # 'en', # We already have this, as this is the URL in the core dataset
    'it',
    'ko',
    'nl',
    'zh'
]


def sleep(min_sleep_time: int = 10, max_random_time: int = 10) -> None:
    """Sleep for a minimum number of seconds and a random amount of time."""
    sleep_time = min_sleep_time + random.randint(0, max_random_time) + random.random()
    time.sleep(sleep_time)


def download_urls(urls: List[str], page_dir: str) -> None:
    """Download page content for a list of Goodreads
    URLs and write each page to disk"""
    for url in urls:
        sleep(min_sleep_time=10, max_random_time=10)
        response = requests.get(url)
        write_book_page(page_dir, url, response)


def download_review_pages(base_output_dir: str, html_input_dir):
    book_page_files = glob.glob(os.path.join(html_input_dir, '*.html'))

    for fname in book_page_files:
        page_soup = read_html_file(fname)
        links = get_language_links(page_soup)
        links = filter_language_links(links, TARGET_LANGS)
        for link in links:
            lang_dir = os.path.join(base_output_dir, link.attrs['hreflang'])
            if not os.path.isdir(lang_dir):
                os.mkdir(lang_dir)
                print(lang_dir)
            lang_file = get_page_filename(lang_dir, link['href'])
            if os.path.exists(lang_file):
                print('file exists:', lang_file)
                continue
            else:
                print('downloading', link['href'])
                response = requests.get(link['href'])
                write_book_page(lang_dir, link['href'], response)
                sleep(min_sleep_time=10, max_random_time=10)


def write_book_page(page_dir: str, url: str, response: requests.Response) -> None:
    filename = get_page_filename(page_dir, url)
    with open(filename, 'wt') as fh:
        fh.write(response.text)

