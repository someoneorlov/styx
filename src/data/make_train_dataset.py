# -*- coding: utf-8 -*-
import os
import click
import logging

import pandas as pd

from pathlib import Path
from dotenv import find_dotenv, load_dotenv
from tqdm import tqdm

from REL.entity_disambiguation import EntityDisambiguation
from REL.mention_detection import MentionDetection
from REL.ner import load_flair_ner
from REL.utils import process_results


def preprocessing(row: pd.Series, title: str, article: str) -> dict:
    processed = {"title": [row[title], []], "article": [row[article], []]}
    return processed


def find_mentions(text: str, mention_detection, tagger_ner):
    mentions_dataset, n_mentions = mention_detection.find_mentions(text, tagger_ner)
    return mentions_dataset


def disambiguate_entities(mentions_dataset: pd.DataFrame, entity_disambiguation):
    predictions, timing = entity_disambiguation.predict(mentions_dataset)
    return predictions


def save_output(dataset, output_filepath: str):
    if os.path.exists(output_filepath):
        dataset.to_csv(output_filepath, mode="a", header=False, index=False)
    else:
        dataset.to_csv(output_filepath, index=False)


def save_processed_rows(processed_rows_filepath: str, processed_rows: int):
    with open(processed_rows_filepath, "w") as f:
        f.write(str(processed_rows))


def load_processed_rows(processed_rows_filepath: str):
    if os.path.exists(processed_rows_filepath):
        with open(processed_rows_filepath, "r") as f:
            return int(f.read().strip())
    return 0


@click.command()
@click.argument("input_filepath", type=click.Path(exists=True))
@click.argument("output_filepath", type=click.Path())
@click.argument("base_url", type=click.Path(exists=True))
@click.argument("save_interval")
@click.argument("wiki_version")
@click.argument("model_alias")
@click.argument("title")
@click.argument("article")
def main(
    input_filepath: str,
    output_filepath: str,
    base_url: str,
    save_interval: int,
    wiki_version: str = "wiki_2019",
    model_alias: str = "ed-wiki-2019",
    title: str = "title",
    article: str = "article",
):
    """Runs data processing scripts to turn unprocessed data into
    cleaned data ready to be analyzed.
    """
    logger = logging.getLogger(__name__)
    logger.info("making data set")

    mention_detection = MentionDetection(base_url, wiki_version)
    tagger = load_flair_ner("ner-fast")

    config = {
        "mode": "eval",
        "model_path": model_alias,
    }
    entity_disambiguation = EntityDisambiguation(base_url, wiki_version, config)

    processed_rows_filepath = "num_processed_rows.txt"
    start_index = load_processed_rows(processed_rows_filepath)

    dataset = pd.read_csv(input_filepath)
    annotated_articles = []
    save_interval = int(save_interval)

    for index, row in tqdm(dataset.iterrows(), total=dataset.shape[0]):
        if index < start_index:
            continue

        if len(row[title].split()) > 3300 or len(row[article].split()) > 3300:
            continue

        processed_row = preprocessing(row, title, article)

        # Perform mention detection on headline and body text
        mentions_dataset = find_mentions(processed_row, mention_detection, tagger)

        # Insert plug if title or article mentions are empty
        if not mentions_dataset[title] or not mentions_dataset[article]:
            continue

        # Disambiguate detected mentions
        mentions_disambiguated = disambiguate_entities(
            mentions_dataset, entity_disambiguation
        )
        result = process_results(
            mentions_dataset, mentions_disambiguated, processed_row
        )

        # Filter mentions with the ORG tag
        headline_mentions = [
            mention for mention in result[title] if mention[-1] == "ORG"
        ]
        body_text_mentions = [
            mention for mention in result[article] if mention[-1] == "ORG"
        ]

        # Check if any named entities were found in the headline
        if not headline_mentions or not body_text_mentions:
            continue

        # Mark salient entities
        salient_entities = []
        for body_entity in body_text_mentions:
            if body_entity[3] in [
                headline_entity[3] for headline_entity in headline_mentions
            ]:
                salient_entities.append(body_entity)

        if not salient_entities:
            continue

        salient_entities_list = list(set([entity[3] for entity in salient_entities]))
        # Save the annotated article
        annotated_articles.append(
            {
                "headline": processed_row[title][0],
                "body_text": processed_row[article][0],
                "headline_mentions": headline_mentions,
                "body_text_mentions": body_text_mentions,
                "salient_entities": salient_entities,
                "salient_entities_list": salient_entities_list,
            }
        )

        # Append DataFrame from the annotated_articles list every save_interval rows
        if (index + 1) % save_interval == 0:
            save_output(pd.DataFrame(annotated_articles), output_filepath)
            save_processed_rows(processed_rows_filepath, index + 1)
            annotated_articles = []

    # Append DataFrame from the annotated_articles list, if there are any remaining rows.
    save_output(pd.DataFrame(annotated_articles), output_filepath)
    save_processed_rows(processed_rows_filepath, index + 1)


if __name__ == "__main__":
    log_fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # not used in this stub but often useful for finding various files
    project_dir = Path(__file__).resolve().parents[2]

    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables
    load_dotenv(find_dotenv())

    main()
