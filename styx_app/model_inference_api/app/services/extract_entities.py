import requests
from styx_packages.styx_logger.logging_config import setup_logger

logger = setup_logger(__name__)


def extract_salient_entities(
    data: list,
    API_URL: str = "http://rel:5555/api",
    title: str = "title",
    article: str = "text",
    id: str = "id",
):
    logger.info(f"Starting entity extraction for {len(data)} articles")

    annotated_articles = []
    processed_ids = []

    for row in data:
        row = row.dict()

        if len(row[title].split()) > 3300 or len(row[article].split()) > 3300:
            logger.warning(
                f"Skipping article {row[id]} due to length constraints. "
                f"Title length: {len(row[title].split())}, "
                f"Article length: {len(row[article].split())}"
            )
            continue

        try:
            # Perform mention detection on headline and body text
            el_title = requests.post(
                API_URL, json={"text": row[title], "spans": []}
            ).json()
            el_article = requests.post(
                API_URL, json={"text": row[article], "spans": []}
            ).json()
        except Exception as e:
            logger.error(
                f"Failed to extract entities for article {row[id]}: {e}", exc_info=True
            )
            logger.error(f"Failed to extract entities for article {row[id]}: {e}")
            continue

        # Filter mentions with the ORG tag
        headline_mentions_org = [
            mention for mention in el_title if mention[-1] == "ORG"
        ]
        body_text_mentions_org = [
            mention for mention in el_article if mention[-1] == "ORG"
        ]

        # Mark salient entities
        salient_entities_org = []
        for body_entity in body_text_mentions_org:
            if body_entity[3] in [
                headline_entity[3] for headline_entity in headline_mentions_org
            ]:
                salient_entities_org.append(body_entity)

        if salient_entities_org:
            salient_entities_org_set = set(
                [entity[3] for entity in salient_entities_org]
            )
        else:
            salient_entities_org_set = {"None"}

        # Save the annotated article
        annotated_articles.append(
            {
                "raw_news_id": row[id],
                "headline_mentions": el_title,
                "body_text_mentions": el_article,
                "salient_entities_org": salient_entities_org,
                "salient_entities_set": salient_entities_org_set,
            }
        )
        processed_ids.append(row[id])
    logger.info(
        f"Successfully processed {len(annotated_articles)} "
        f"articles with IDs: IDs: {processed_ids}"
    )

    return annotated_articles
