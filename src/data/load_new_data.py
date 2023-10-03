import feedparser
import logging
import time
import requests
from requests.exceptions import HTTPError
from newspaper import Article
from datetime import datetime
import pandas as pd

# Set up the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.FileHandler("app.log")
handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


def get_final_url(url):
    try:
        response = requests.get(url, timeout=10, allow_redirects=True)
        return response.url
    except requests.RequestException as e:
        logger.error(f"Error resolving redirect URL {url}: {e}")
        return None


def download_article(url):
    retries = 3
    delay = 5
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    headers = {"User-Agent": user_agent}

    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.text
        except HTTPError as http_err:
            logger.error(f"HTTP error occurred for {url}: {http_err}")
        except Exception as err:
            logger.error(f"An error occurred for {url}: {err}")
        time.sleep(delay)
        delay *= 2
    return None


def scrape_news_from_feed(feed_url, limit=20):
    articles = []
    failed_parses = []
    feed = feedparser.parse(feed_url)

    for i, entry in enumerate(feed.entries):
        print(i)
        if i == limit:
            break

        google_news_url = entry.link
        article_url = get_final_url(google_news_url)

        if article_url:
            downloaded_article = download_article(article_url)
            article = Article(article_url)
            article.set_html(downloaded_article)
            try:
                article.parse()
                publish_date = article.publish_date
                publish_date_source = "parsed"
                if publish_date is None and entry["published_parsed"] is not None:
                    publish_date = datetime.fromtimestamp(
                        mktime(entry["published_parsed"])
                    )
                    publish_date_source = "approximated"
                elif publish_date is None:
                    publish_date = datetime.now()
                    publish_date_source = "current_time"

                publish_date_str = publish_date.strftime("%Y-%m-%d %H:%M:%S")

                articles.append(
                    {
                        "title": article.title,
                        "text": article.text,
                        "publish_date": publish_date_str,
                        "publish_date_source": publish_date_source,
                        "authors": article.authors,
                        "canonical_link": article.canonical_link,
                        "feed_link": article_url,
                        "media_link": entry["source"]["href"],
                        "media_title": entry["source"]["title"],
                    }
                )
            except Exception as err:
                logger.error(f"An unexpected error occurred for {article_url}: {err}")
        else:
            failed_parses.append(
                {
                    "title": entry.title,
                    "text": None,
                    "publish_date": datetime.fromtimestamp(
                        mktime(entry["published_parsed"])
                    ).strftime("%Y-%m-%d %H:%M:%S")
                    if entry["published_parsed"] is not None
                    else datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "publish_date_source": "approximated"
                    if entry["published_parsed"] is not None
                    else "current_time",
                    "authors": None,
                    "canonical_link": None,
                    "feed_link": article_url,
                    "media_link": entry["source"]["href"],
                    "media_title": entry["source"]["title"],
                    "exception_class": None,
                    "exception_text": None,
                }
            )

    return articles, failed_parses


# Execute the scraper
feed_url = "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtVnVHZ0pWVXlnQVAB?hl=en-US&gl=US&ceid=US%3Aen"
limit = 20

articles, failed_parses = scrape_news_from_feed(feed_url, limit)

# Convert articles and failed_parses to DataFrames for easy analysis and saving
articles_df = pd.DataFrame(articles)
failed_parses_df = pd.DataFrame(failed_parses)

# Save to Excel for your analysis
articles_df.to_excel("new_articles_df.xlsx", index=False)
failed_parses_df.to_excel("new_failed_parses_df.xlsx", index=False)
