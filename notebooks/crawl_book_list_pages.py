import glob
import os
import re

from bs4 import BeautifulSoup

from download import fetch_html
from parse import get_book_list_pagination_urls


def main():
    book_list_dir = "../../data/reviews/Multilingual/Goodreads/HTML-2025-10-22/Book_list_pages"
    book_list_files = glob.glob(os.path.join(book_list_dir, '* _ Goodreads.html'))
    print(f"number of book_list_files: {len(book_list_files)}")

    for blf in book_list_files:
        with open(blf, 'rt') as fh_in:
            print(blf)
            _, filename = os.path.split(blf)
            if m := re.match(r"^(.*) \((\d+) books\)", filename):
                book_list = m.group(1)
            soup = BeautifulSoup(fh_in, features='xml')
            pagination_urls = get_book_list_pagination_urls(soup)
            for url in pagination_urls[book_list]:
                page_num = url.split('?page=')[-1]
                html = fetch_html(url)
                page_filename = blf.replace('.html', f'--page{page_num}')
                if page_filename == blf:
                    raise ValueError(f"paginated filename '{page_filename}' cannot be the same as original filename")
                with open(page_filename, 'wt') as fh_out:
                    fh_out.write(html)
    return None


if __name__ == "__main__":
    main()
