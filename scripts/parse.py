import glob
import json
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
    review_text_strings = []
    for span in review_text_div.find_all('span'):
        if 'id' in span.attrs and span.attrs['id'].startswith('freeTextContainer'):
            review_text_strings = [p for p in span.stripped_strings]
            # print('freeTextContainer:', sum([len(r) for r in review_text_strings]))
        if 'style' in span.attrs and span.attrs['style'] == 'display:none':
            review_text_strings = [p for p in span.stripped_strings]
            # print('display:none:', sum([len(r) for r in review_text_strings]))
    return review_text_strings


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
    elif re.search(r"\d{9}", edition):
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
    meta_col = page.find('div', id='metacol')
    extra_fields = ['author_name', 'avg_rating', 'num_ratings', 'num_reviews', 'genres']
    for extra_field in extra_fields:
        book_metadata[extra_field] = None
    if meta_col is not None:
        authors = meta_col.find_all('div', class_='authorName__container')
        authors = [author.text.strip() for author in authors]
        book_metadata['author_name'] = authors
    book_meta_div = page.find('div', id='bookMeta')
    if book_meta_div is not None:
        # print('book_meta_div:', book_meta_div.text)
        for span in book_meta_div.find_all('span'):
            if 'itemprop' in span.attrs and span.attrs['itemprop'] == 'ratingValue':
                book_metadata['avg_rating'] = float(span.text)
        for meta in book_meta_div.find_all('meta'):
            if 'itemprop' in meta.attrs and meta.attrs['itemprop'] == 'ratingCount':
                book_metadata['num_ratings'] = int(meta.attrs['content'])
            if 'itemprop' in meta.attrs and meta.attrs['itemprop'] == 'reviewCount':
                book_metadata['num_reviews'] = int(meta.attrs['content'])
    genre = ''
    book_metadata['genres'] = []
    for ele in page.find_all(class_='bookPageGenreLink'):
        if ele.name == 'a':
            if len(genre) > 0:
                genre += ' -- ' + ele.text.strip()
            else:
                genre = ele.text.strip()
        if ele.name == 'div':
            users = ele.text.strip()
            book_metadata['genres'].append({'genre': genre, 'users': users})
            genre = ''
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


def get_pagination_div(soup):
    pagination_div = soup.find('div', class_="pagination")
    if pagination_div is None:
        previous_span = soup.find('span', class_="previous_page disabled")
        pagination_div = previous_span.parent
    return pagination_div


def get_book_list_pagination_urls(soup):
    pagination_div = get_pagination_div(soup)
    page_urls = []
    max_page = 0
    max_page_url = None
    for page_link in pagination_div.find_all('a'):
        if 'href' not in page_link.attrs:
            continue
        page_url = page_link.attrs['href']
        if m := re.match(r".*\?page=(\d+)", page_url):
            page_num = int(m.group(1))
            if page_num > max_page:
                max_page = page_num
                max_page_url = page_url
    for page_num in range(2, max_page+1):
        page_url = max_page_url.replace(f'page={max_page}', f'page={page_num}')
        page_urls.append(page_url)
    return page_urls


def is_book_resource(div):
    return 'data-resource-type' in div.attrs and div.attrs['data-resource-type'] == "Book"


def get_book_resources(tr):
    return [div for div in tr.find_all('div') if is_book_resource(div)]


def get_book_list_books(soup, book_list):
    books = []

    table = soup.find('table')
    trs = table.find_all('tr')
    for tr in trs:
        # print(tr)
        resource_div = get_book_resources(tr)[0]

        book_link = tr.find('a', class_="bookTitle")
        author_link = tr.find('a', class_="authorName")
        book = {
            'book_id': resource_div.attrs['data-resource-id'],
            'book_title': book_link.text,
            'book_url': book_link.attrs['href'],
            'author_name': author_link.text,
            'author_url': author_link.attrs['href'],
            'book_lists': [book_list]
        }
        books.append(book)
    return books


def extract_review_rating(review_content):
    if review_content is None:
        return None
    rating_stars = review_content.find('span', class_='RatingStars')
    if rating_stars is None:
        return None
    rating_string = rating_stars.attrs['aria-label']
    if m := re.match(r"Rating (\d) out of 5", rating_string):
        return int(m.group(1))
    else:
        raise ValueError(f"unexpected rating_star string '{rating_string}'")


def extract_review(review_card):
    review_content = review_card.find('section', class_='ReviewCard__content')
    reviewer_profile = review_card.find(class_='ReviewerProfile__name')
    review_card_row = review_content.find('section', class_="ReviewCard__row")
    review_link = review_card_row.find('a')
    return {
        'review_text': review_card.find('section', class_="ReviewText").text,
        'user_url': reviewer_profile.find('a').attrs['href'],
        'user_name': reviewer_profile.text,
        'review_url': review_link.attrs['href'] if 'href' in review_link.attrs else None,
        'review_date': review_card_row.text,
        'rating': extract_review_rating(review_content)
    }


def extract_reviews(book_id, book_review_file, page):
    lang_dir, filename = os.path.split(book_review_file)
    lang_base_dir, lang = os.path.split(lang_dir)
    base_url = "https://goodreads.com"
    source_url = os.path.join(base_url, f"{lang}/book/show/{filename}")

    reviews = []
    for review_card in page.find_all('article', class_="ReviewCard"):
        review = extract_review(review_card)
        review['book_id'] = book_id
        review['source_url'] = source_url
        review['review_lang'] = lang
        # if review['review_url'] is None:
        #     print(review)
        reviews.append(review)
    return reviews


def extract_enjoyed_books(page):
    carousel = page.find('section', class_="Carousel")
    book_cards = [book_card for book_card in carousel.find_all('div', class_="BookCard")]
    book_links = [book_card.find('a', class_="BookCard__clickCardTarget") for book_card in book_cards]
    book_urls = [book_link.attrs['href'] for book_link in book_links]
    return book_urls
