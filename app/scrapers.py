import requests
from bs4 import BeautifulSoup
from langchain_community.document_loaders import WebBaseLoader


def try_webbaseloader(url):
    try:
        loader = WebBaseLoader([url])
        docs = loader.load()
        if docs:
            return docs[0].page_content
    except:
        return None


def try_requests_bs4(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        html = requests.get(url, headers=headers, timeout=10).text
        soup = BeautifulSoup(html, "html.parser")
        return soup.get_text(" ", strip=True)
    except:
        return None


def try_playwright(url):
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=15000)
            content = page.content()
            browser.close()

        soup = BeautifulSoup(content, "html.parser")
        return soup.get_text(" ", strip=True)
    except:
        return None


def scrape_with_fallbacks(url):
    """
    Order:
    1. WebBaseLoader (fastest)
    2. Requests + BS4 (simple pages)
    3. Playwright headless browser (JS heavy)
    """

    methods = [
        try_webbaseloader,
        try_requests_bs4,
        try_playwright
    ]

    for method in methods:
        data = method(url)
        if data and len(data.strip()) > 50:
            return data

    return None
