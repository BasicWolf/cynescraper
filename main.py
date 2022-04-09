import json
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import List

from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By

SCRAPE_FROM_PAGE_NUMBER = 1
SCRAPE_TO_PAGE_NUMBER = 1
BASE_URL = 'https://thecynefin.co/'

driver: WebDriver

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s %(asctime)s %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    setup_chrome_driver()
    # scrape_articles()
    save_article_page_to_pdf('https://thecynefin.co/cynefin-st-davids-2022-1-of-2/')
    driver.quit()


def scrape_articles():
    for page_number in range(SCRAPE_FROM_PAGE_NUMBER, SCRAPE_FROM_PAGE_NUMBER + 1):
        for article_url in scrape_articles_urls_from_page(page_number):
            save_article_page_to_pdf(article_url)


def scrape_articles_urls_from_page(page_number: int) -> List[str]:
    logger.info('Fetching articles urls from page %d', page_number)
    page_url = f'{BASE_URL}/our-thinking/page/{page_number}/'
    driver.get(page_url)
    articles_links_elements = driver.find_elements(
        By.XPATH,
        '//a[text()="Read More"]'
    )
    articles_urls = [
        elem.get_attribute('href')
        for elem in articles_links_elements
    ]
    logger.info('Found %d articles on page %d', len(articles_urls), page_number)
    yield from articles_urls


def save_article_page_to_pdf(url: str):
    logger.info('Processing article %s', url)
    driver.get(url)
    remove_unneccesary_article_page_elements()
    apply_printer_friendly_styles()

    article_path_dirname = Path(url).name
    article_publish_date = get_article_publish_date()
    article_publish_date_as_filename_prefix = article_publish_date.strftime('%Y-%m-%d')
    print_page(f'{article_publish_date_as_filename_prefix}-{article_path_dirname}')


def remove_unneccesary_article_page_elements():
    remove_header()
    remove_array_previous()
    remove_array_next()
    remove_extra_sections()


def remove_header():
    driver.execute_script('document.getElementsByTagName("header")[0].remove()')


def remove_array_previous():
    driver.execute_script('''
        Array.from(document.getElementsByClassName('anpn-prev'))
            .forEach((elem) => elem.remove());
    ''')


def remove_array_next():
    driver.execute_script('''
        Array.from(document.getElementsByClassName('anpn-next'))
            .forEach((elem) => elem.remove());
    ''')


def remove_extra_sections():
    """
    Every Cynefin article page is divided into 6 secions.
    First two sections contain the header image and the article text.
    The rest are Disqus, related articles, about and footer.
    """
    driver.execute_script('''
        Array.from(document.getElementsByTagName('section'))
            .splice(2,4).forEach((elem) => elem.remove());
    ''')


def get_article_publish_date() -> datetime:
    publish_date_as_text = driver.find_element(By.ID, 'span-36-14').text
    return datetime.strptime(publish_date_as_text, '%B %d, %Y')


def apply_printer_friendly_styles():
    """
    WebKit has a bug in "Print to PDF" functionality:
    a text lines on the edge of a page may be split
    between two pages.
    We try to apply some CSS to fix this behaviour.
    """
    driver.execute_script('''
        Array.from(document.getElementsByClassName('oxy-stock-content-styles'))
            .forEach((elem) => {
                elem.style.display = 'block'; 
                elem.style.pageBreakInside = 'avoid';
            });
    ''')


def print_page(file_name_without_extension: str):
    file_name = f'{file_name_without_extension}.pdf'
    logger.debug('Printing %s', file_name)
    driver.execute_script(f'document.title = "{file_name}";')
    driver.execute_script('window.print();')
    wait_for_pdf_save_process_to_complete()


def wait_for_pdf_save_process_to_complete():
    time.sleep(5)


def setup_chrome_driver():
    global driver
    chrome_options = webdriver.ChromeOptions()
    settings = {
        'recentDestinations': [{
            'id': 'Save as PDF',
            'origin': 'local',
            'account': '',
        }],
        'selectedDestinationId': 'Save as PDF',
        'version': 2,
        'isHeaderFooterEnabled': False,
        'isCssBackgroundEnabled': True
    }
    prefs = {'printing.print_preview_sticky_settings.appState': json.dumps(settings)}
    chrome_options.add_experimental_option('prefs', prefs)
    chrome_options.add_argument('--kiosk-printing')
    driver = webdriver.Chrome(
        options=chrome_options
    )


if __name__ == '__main__':
    main()

