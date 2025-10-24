import glob
import os
from typing import List

from parse import get_language_links, filter_language_links
from download import fetch_html, write_book_page


def extract_links(html_dir: str, lang_base_dir: str, target_langs: List[str]):
    from download import sleep
    from parse import read_html_file, get_page_filename

    book_page_files = glob.glob(os.path.join(html_dir, '*.html'))

    for fname in book_page_files:
        page_soup = read_html_file(fname)
        links = get_language_links(page_soup)
        links = filter_language_links(links, target_langs)
        for link in links:
            lang_dir = os.path.join(lang_base_dir, link.attrs['hreflang'])
            if not os.path.isdir(lang_dir):
                os.mkdir(lang_dir)
                print(lang_dir)
            lang_file = get_page_filename(lang_dir, link['href'])
            if os.path.exists(lang_file):
                print('file exists:', lang_file)
                continue
            else:
                print('downloading', link['href'])
                html = fetch_html(link['href'], wait_time=2)
                write_book_page(lang_dir, link['href'], html)
                sleep(min_sleep_time=2, max_random_time=0)


def main():
    target_langs = [
        'it',  # Italian
        'de',  # German
        'en',  # English
        'es',  # Spanish
        'fa',  # Persian
        'ps',  # Pashto
        'ur',  # Urdu
        'nl',  # Dutch
        'tr',  # Turkish
        'ja',  # Japanese
        'zh',  # Chinese (macro-language label)

        'pt',  # Portuguese
        'fr',  # French
        'ko',  # Korean
        'ar',  # Arabic
        'no',  # Norwegian
        'da',  # Danish
        'fi',  # Finnish
        'sv',  # Swedish
        'cs',  # Czech
        'pl',  # Polish
        'ru',  # Russian
        'uk',  # Ukranian
        'sk',  # Slovak
        'sl',  # Slovenian
        'sr',  # Serbian
        'el',  # Greek
        'hi',  # Hindi
        'hu',  # Hungarian
        'id',  # Indonesian
    ]

    html_dir = '../../data/reviews/Multilingual/Goodreads/HTML-2025-10-23/Canonical_book_pages/'
    lang_dir = '../../data/reviews/Multilingual/Goodreads/HTML-2025-10-23/'
    extract_links(html_dir, lang_dir, target_langs)


if __name__ == "__main__":
    main()
