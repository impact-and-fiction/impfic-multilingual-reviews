import json
import os
from typing import Dict, List


from parse import read_html_file, extract_reviews
from parse import read_book_review_files


def map_html_to_json_file(html_filepath: str, json_base_dir: str):
    lang_dir, html_filename = os.path.split(html_filepath)
    json_filename = html_filename.replace('.html', '-reviews.json')
    _, lang = os.path.split(lang_dir)
    json_lang_dir = os.path.join(json_base_dir, lang)
    if os.path.exists(json_lang_dir) is False:
        os.mkdir(json_lang_dir)
    return os.path.join(json_lang_dir, json_filename)


def write_reviews_json(book_files: Dict[str, List[str]], json_base_dir: str):
    for bi, book_id in enumerate(book_files):
        for html_file in book_files[book_id]:
            print(f"{bi+1} of {len(book_files)} books, {html_file}")
            json_file = map_html_to_json_file(html_file, json_base_dir)
            if os.path.exists(json_file):
                continue
            page = read_html_file(html_file)
            reviews = extract_reviews(book_id, html_file, page)
            with open(json_file, 'wt') as fh:
                json.dump(reviews, fh)
    return None


def main():
    json_base_dir = '../../data/reviews/Multilingual/Goodreads/JSON/'
    html_dir = '../../data/reviews/Multilingual/Goodreads/HTML-2025-10-23/'
    book_files = read_book_review_files(html_dir)
    write_reviews_json(book_files, json_base_dir)


if __name__ == "__main__":
    main()
