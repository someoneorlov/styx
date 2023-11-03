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
    all_articles = []
    feed = feedparser.parse(feed_url)

    for i, entry in enumerate(feed.entries):
        print(i)
        if i == limit:
            break

        google_news_url = entry.link
        article_url = get_final_url(google_news_url)

        data = {
            "title": entry.title,
            "text": None,
            "publish_date": None,
            "publish_date_source": None,
            "authors": None,
            "canonical_link": None,
            "feed_link": google_news_url,
            "media_link": entry["source"]["href"],
            "media_title": entry["source"]["title"],
            "is_parsed": False,
            "exception_class": None,
            "exception_text": None,
        }

        if not article_url:
            logger.error(f"Failed to resolve final URL for: {google_news_url}")
            data.update(
                {
                    "exception_class": "URLResolutionError",
                    "exception_text": "Failed to resolve final URL",
                }
            )
            all_articles.append(data)
            continue

        downloaded_article = download_article(article_url)
        article = Article(article_url)

        if downloaded_article:
            article.set_html(downloaded_article)
        else:
            try:
                article.download()
            except Exception as e:
                logger.error(f"Failed to download article {article_url}: {str(e)}")
                data.update(
                    {
                        "exception_class": type(e).__name__,
                        "exception_text": str(e),
                    }
                )
                all_articles.append(data)
                continue

        try:
            article.parse()

            if not all([article.title, article.text, article.canonical_link]):
                raise ValueError(
                    "Essential fields are empty, possibly due to bot protection or bad parse"
                )

            publish_date = article.publish_date
            publish_date_source = "parsed"
            if publish_date is None and entry["published_parsed"] is not None:
                publish_date = datetime.fromtimestamp(
                    time.mktime(entry["published_parsed"])
                )
                publish_date_source = "approximated"
            elif publish_date is None:
                publish_date = datetime.now()
                publish_date_source = "current_time"

            publish_date_str = publish_date.strftime("%Y-%m-%d %H:%M:%S")

            data.update(
                {
                    "title": article.title,
                    "text": article.text,
                    "publish_date": publish_date_str,
                    "publish_date_source": publish_date_source,
                    "authors": article.authors,
                    "canonical_link": article.canonical_link,
                    "is_parsed": True,
                }
            )

        except Exception as err:
            logger.error(f"An unexpected error occurred for {article_url}: {err}")
            data.update(
                {
                    "exception_class": type(err).__name__,
                    "exception_text": str(err),
                }
            )

        all_articles.append(data)

    return all_articles


# Execute the scraper
feed_url = "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtVnVHZ0pWVXlnQVAB?hl=en-US&gl=US&ceid=US%3Aen"
limit = 20

articles = scrape_news_from_feed(feed_url, limit)

articles_df = pd.DataFrame(articles)

# Save to Excel for your analysis
articles_df.to_excel("unified_articles_df.xlsx", index=False)
