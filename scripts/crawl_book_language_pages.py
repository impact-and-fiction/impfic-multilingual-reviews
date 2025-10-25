import datetime
import glob
import logging
import os
import time
from typing import List

from parse import get_language_links, filter_language_links

from download import fetch_html
from parse import read_html_file, get_page_filename

# source: https://hreflang.org/list-of-hreflang-codes/

TARGET_LANGS = {
    'it': "Italian",
    'de': "German",
    # 'en': "English",
    'es': "Spanish",
    'fa': "Persian",
    'ps': "Pashto",
    'ur': "Urdu",
    'nl': "Dutch",
    'tr': "Turkish",
    'ja': "Japanese",
    'zh': "Chinese (macro-language label)",
    'pt': "Portuguese",
    'fr': "French",
    'ko': "Korean",
    'ar': "Arabic",
    'no': "Norwegian",
    'da': "Danish",
    'fi': "Finnish",
    'sv': "Swedish",
    'cs': "Czech",
    'pl': "Polish",
    'ru': "Russian",
    'uk': "Ukranian",
    'sk': "Slovak",
    'sl': "Slovenian",
    'sr': "Serbian",
    'el': "Greek",
    'hi': "Hindi",
    'hu': "Hungarian",
    'id': "Indonesian",
}


def crawl_language_pages(canonical_page_files: List[str], lang_base_dir: str,
                         target_langs: List[str] = None):
    for page_filename in canonical_page_files:
        page_soup = read_html_file(page_filename)
        links = get_language_links(page_soup)
        if target_langs is not None and len(target_langs) > 0:
            links = filter_language_links(links, target_langs)
        for link in links:
            crawl_language_page(link, lang_base_dir)
            time.sleep(2)


def crawl_language_page(link, lang_base_dir: str):
    lang_dir = os.path.join(lang_base_dir, link.attrs['hreflang'])
    if not os.path.isdir(lang_dir):
        os.mkdir(lang_dir)
        logging.info(f"creating language directory {lang_dir}")
    lang_file = get_page_filename(lang_dir, link['href'])
    if os.path.exists(lang_file):
        logging.info(f'file exists: {lang_file}')
        return None
    logging.info(f"downloading: {link['href']}")
    try:
        html = fetch_html(link['href'], wait_time=2)
        with open(lang_file, 'wt') as fh_out:
            fh_out.write(html)
    except BaseException as err:
        logging.error(f"Error downloading {link['href']}")
        logging.error(err)


def main():
    canonical_page_dir = '../data/Canonical_book_pages'
    canonical_page_files = glob.glob(os.path.join(canonical_page_dir, '*.html'))
    logging.info(f"num canonical_page_files: {len(canonical_page_files)}")
    lang_base_dir = '../data/Book_language_pages'
    target_langs = list(TARGET_LANGS.keys())
    logging.info(f"target_langs: {target_langs}")
    crawl_language_pages(canonical_page_files, lang_base_dir, target_langs)


if __name__ == "__main__":
    today = datetime.date.today().isoformat()
    logging.basicConfig(format='%(asctime)s %(message)s',
                        filename=f'crawling-book_language_pages-{today}.log',
                        level=logging.DEBUG)
    main()
