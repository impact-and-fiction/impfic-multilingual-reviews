import glob
import os
import re
from collections import defaultdict
from typing import Dict, List, Union

import pandas as pd
from bs4 import BeautifulSoup


def get_review_text(review: BeautifulSoup) -> Union[List[str], None]:
    """Extract paragraphs of review text from a BeautifulSoup review element."""
    review_text_div = review.find('div', class_="reviewText")
    if review_text_div is None:
        return None
    for span in review_text_div.find_all('span'):
        if 'id' in span.attrs and span.attrs['id'].startswith('freeTextContainer'):
            return [p for p in span.stripped_strings]
        if 'style' in span.attrs and span.attrs['style'] == 'display:none':
            return [p for p in span.stripped_strings]
    return None


def parse_review(book_id: str, review_lang: str, review: BeautifulSoup) -> Dict[str, any]:
    """Extract review data from a BeautifulSoup review element."""
    user_link = review.find('a', class_="user")
    date_link = review.find('a', class_="reviewDate")
    review_date = date_link.text
    user_url = user_link.attrs['href']
    user_name = user_link.attrs['name']
    edition_link = review.find('a', class_="lightGreyText")
    rating = len(review.find_all('span', class_="staticStar"))
    review_text = get_review_text(review)
    edition = None
    if edition_link:
        edition = edition_link.attrs['title']
    return {
        'username': user_name,
        'userurl': user_url,
        'goodreads_book_id': book_id,
        'goodreads_book_num': re.match(r"(\d+)", book_id).group(1),
        'review_date': review_date,
        'rating': rating,
        'edition': edition,
        'review_lang': review_lang,
        'review_text': '\n\n'.join(review_text) if isinstance(review_text, list) else None
    }


def read_html_file(html_file: str) -> BeautifulSoup:
    """Read a HTML file and return the content as a BeautifulSoup instance."""
    with open(html_file, 'rt') as fh:
        return BeautifulSoup(fh, "lxml")


def read_book_review_files(html_dir: str) -> Dict[str, List[str]]:
    html_files = glob.glob(os.path.join(html_dir, '**/*.html'))

    book_files = defaultdict(list)

    for html_file in html_files:
        filedir, filename = os.path.split(html_file)
        _, lang = os.path.split(filedir)
        book_id = filename.replace('.html', '')
        if '?' in book_id:
            print(filedir, filename)
        book_files[book_id].append(html_file)
    return book_files


def get_book_review_divs(book_file: str) -> List[BeautifulSoup]:
    """Extract all the DIV elements containing a review from a Goodreads book review page."""
    page = read_html_file(book_file)
    return page.find_all('div', class_="review")


def get_review_language(book_review_file: str) -> str:
    """Extract the language code from a book review filename."""
    return book_review_file.split('HTML/')[-1][:2]


def get_book_reviews(book_id: str, book_review_file: str, page: BeautifulSoup) -> List[Dict[str, any]]:
    """Extract all book reviews from a Goodreads book review page."""
    review_lang = get_review_language(book_review_file)
    try:
        review_divs = page.find_all('div', class_="review")
        return [parse_review(book_id, review_lang, review_div) for review_div in review_divs]
    except Exception as err:
        print(err)
        print('Error parsing HTML of file', book_review_file)
        raise


def parse_edition_isbn(edition):
    if pd.isna(edition):
        return None
    if m := re.search(r"(978\d{9}[0-9Xx])", edition):
        return m.group(1)
    if m := re.search(r"\b(\d{9}[0-9Xx])", edition):
        return m.group(1)
    elif m := re.search(r"\d{9}", edition):
        print('Error:', edition)
    return None


def get_canonical_url(page: BeautifulSoup) -> Union[str, None]:
    """Return the canonical URL for a book on Goodreads from the review page."""
    for link in page.find_all('link'):
        # print('LINK:', link)
        # print(link.attrs)
        if 'rel' in link.attrs and 'canonical' in link.attrs['rel']:
            return link.attrs['href']
    return None


def get_book_metadata(book_id: str, book_review_file: str, page: BeautifulSoup) -> Dict[str, any]:
    """Extract book metadata from a Goodreads book review page."""
    meta_eles = page.find_all('meta')
    book_metadata = {
        'goodreads_book_id': book_id,
        'goodreads_book_num': re.match(r"(\d+)", book_id).group(1),
        'source_url': get_canonical_url(page),
        'review_file_language': get_review_language(book_review_file),
    }
    og_attrs = ['title', 'description', 'url', 'image', 'type']
    books_attrs = ['author', 'isbn', 'page_count']
    for attr in og_attrs + books_attrs:
        book_metadata[f'book_{attr}'] = None
    for meta in meta_eles:
        if 'property' not in meta.attrs:
            continue
        # print(meta.attrs['property'])
        for og_attr in og_attrs:
            # print('\tog_attr:', og_attr, f'og:{og_attr}')
            if meta.attrs['property'] == f'og:{og_attr}':
                # print('\t\tMATCH')
                book_metadata[f'book_{og_attr}'] = meta.attrs['content']
        for books_attr in books_attrs:
            if meta.attrs['property'] == f'books:{books_attr}':
                book_metadata[f'book_{books_attr}'] = meta.attrs['content']

    # print(book_metadata)
    # print(len(meta_eles))
    return book_metadata


def get_language_links(page_soup: BeautifulSoup) -> List[BeautifulSoup]:
    """Extract the language link elements from a Goodreads book review page."""
    return [link for link in page_soup.head.find_all('link') if 'alternate' in link.attrs['rel']]


def filter_language_links(links: List[BeautifulSoup], target_langs: list[str]) -> List[BeautifulSoup]:
    """Filter the list of language link elements for a given list of language codes."""
    return [link for link in links if 'hreflang' in link.attrs and link.attrs['hreflang'] in target_langs]


def get_page_filename(base_dir: str, url: str) -> str:
    """Generate the output filename from a Goodreads book review page URL and a given base directory."""
    base_url, book_name = os.path.split(url)
    return os.path.join(base_dir, f'{book_name}.html')
