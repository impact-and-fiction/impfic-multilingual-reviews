import datetime
import glob
import json
import logging
import os
import re
import time

import pandas as pd
from bs4 import BeautifulSoup

from download import fetch_html
from parse import get_book_list_books


def extract_book_list_books():
    book_list_dir = "../data/Book_list_pages"
    book_list_files = glob.glob(os.path.join(book_list_dir, '*.html'))
    print(f"number of book_list_files: {len(book_list_files)}")

    book_map = {}
    for blf in book_list_files:
        with open(blf, 'rt') as fh_in:
            print(blf)
            _, filename = os.path.split(blf)
            if m := re.match(r"^(.*) \((\d+) books\)", filename):
                book_list = m.group(1)
            soup = BeautifulSoup(fh_in, features='xml')
            books = get_book_list_books(soup, book_list)
            for book in books:
                if book['book_id'] in book_map:
                    book_map[book['book_id']]['book_lists'].append(book_list)
                else:
                    book_map[book['book_id']] = book
            num_books = len(book_map)
            print(f"{num_books: >6} books, blf: {blf}")
    return book_map


def get_books_json():
    book_file = '../data/books.json'
    if os.path.exists(book_file) is False:
        book_map = extract_book_list_books()
        with open(book_file, 'wt') as fh:
            json.dump(book_map)
    else:
        with open(book_file, 'rt') as fh:
            book_map = json.load(fh)
    return book_map


def get_metadata_book_ids():
    metadata_file = '../data/Shared_Meta_EN_fin_LOBO_v0_2.csv'
    dtype = {
        'ISBN': str
    }
    df = pd.read_csv(metadata_file, index_col=0, dtype=dtype)
    return list(df.gr_EN_link)


def main():
    canonical_dir = '../data/Canonical_book_pages'
    book_map = get_books_json()
    print(f"number of book_map book_ids: {len(book_map)}")
    metadata_book_ids = set(get_metadata_book_ids())
    print(f"number of metadata book_ids: {len(metadata_book_ids)}")
    for bi, book_id in enumerate(book_map):
        if book_id in metadata_book_ids:
            print(f"duplicate: {book_id} {book_map[book_id]}")
            continue
        book_url = book_map[book_id]['book_url']
        try:
            filename = f"{os.path.split(book_url)[-1]}.html"
            filepath = os.path.join(canonical_dir, filename)
            if os.path.exists(filepath):
                continue
            logging.info(f"{bi+1} of {len(book_map)} - fetching HTML for book_id {book_id}")
            html = fetch_html(book_url, wait_time=2)
            with open(filepath, 'wt') as fh_out:
                fh_out.write(html)
        except BaseException as err:
            logging.error(f"Error fetching HTML for book_id {book_id}: {err}")
            continue


if __name__ == "__main__":
    today = datetime.date.today().isoformat()
    logging.basicConfig(format='%(asctime)s %(message)s',
                        filename=f'crawling-canonical_book_pages-{today}.log',
                        #encoding='utf-8',
                        level=logging.DEBUG)
    main()
