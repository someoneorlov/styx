import argparse
import feedparser
import logging
import time
import requests
from requests.exceptions import HTTPError
from newspaper import Article
from datetime import datetime


# Set up the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.FileHandler("app.log")
handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


def get_final_url(url):
    """
    Resolve and return the final URL after all redirects.
    """
    try:
        response = requests.get(url, timeout=10, allow_redirects=True)
        return response.url
    except requests.RequestException as e:
        logger.error(f"Error resolving redirect URL {url}: {e}")
        return None


def download_article(url):
    """
    Download the content of the article and return as text.
    """
    retries = 3
    delay = 5
    user_agent = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/91.0.4472.124 Safari/537.36"
    )

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


def scrape_news_from_feed(feed_url, limit=10000):
    """
    Scrape news articles from a given Google News RSS feed.

    Parameters:
    - feed_url: URL of the Google News RSS feed.
    - limit: Maximum number of articles to scrape.

    Returns:
    - A list of dictionaries containing information about each article.
    """
    logger.info("Starting the news scraping process...")

    all_articles = []
    feed = feedparser.parse(feed_url)

    logger.info(f"Successfully parsed the RSS feed. Found {len(feed.entries)} entries.")

    for i, entry in enumerate(feed.entries):
        if i == limit:
            break

        google_news_url = entry.link
        article_url = get_final_url(google_news_url)

        logger.info(f"Attempting to download article from URL: {article_url}")

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
                    "Essential fields are empty, possibly due to "
                    "bot protection or bad parse"
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
            logger.info(f"Successfully scraped article: {article.title}")

        except Exception as err:
            logger.error(f"An unexpected error occurred for {article_url}: {err}")
            data.update(
                {
                    "exception_class": type(err).__name__,
                    "exception_text": str(err),
                }
            )

        all_articles.append(data)

    logger.info(f"Completed scraping. Total articles scraped: {len(all_articles)}")
    return all_articles


def main(feed_url, limit=10000):
    articles = scrape_news_from_feed(feed_url, limit)
    # Handle the articles, like printing or saving them


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Scrape news from a given RSS feed URL."
    )
    parser.add_argument("feed_url", help="The RSS feed URL to scrape news from.")
    parser.add_argument(
        "--limit", type=int, default=10000, help="Maximum number of articles to scrape."
    )
    args = parser.parse_args()
    main(args.feed_url, args.limit)
