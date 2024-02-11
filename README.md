# Styx: Advanced News Analysis Service

Styx is an advanced machine learning project aimed at providing detailed news analysis centered around companies. It not only lists related news in chronological order but also summarizes articles and evaluates their sentiment to determine if they have a positive or negative impact.

## About The Project

Styx addresses the challenge of filtering and analyzing news content to focus specifically on how it relates to particular companies. It leverages named entity recognition (NER) to identify company mentions accurately and assesses the relevance of news articles to these entities. This approach ensures users receive tailored news insights, summaries, and sentiment analysis, providing a deeper understanding of a company's news ecosystem.

## Technologies and Tools

This project is built using a robust stack of technologies and tools designed for scalability, efficiency, and ease of development:

- **Data Collection and Processing**: Python scripts for scraping and initial data processing.
- **Database**: PostgreSQL for data storage, with Flyway for database migrations ensuring schema consistency across environments.
- **Backend API**: FastAPI for serving data through RESTful endpoints, ensuring fast responses and asynchronous handling.
- **Machine Learning**: REL for named entity recognition and linking, with plans to expand to advanced models for summarization and sentiment analysis.
- **Orchestration and Workflow Management**: Airflow for managing ETL processes and automation of data pipeline tasks.
- **Containerization**: Docker for creating isolated environments, with Docker Compose for multi-container orchestration.
- **Monitoring**: Prometheus for monitoring system metrics, Grafana for dashboards, and Alertmanager for alerts.
- **Version Control and CI/CD**: Git for version control, with GitHub Actions for continuous integration and deployment pipelines.

### Existing Services

- **Scraping Service**: Automates the collection of news articles from various sources using predefined Google News Feed URLs. It leverages Python scripts to parse news content and store relevant information in the PostgreSQL database. This service is orchestrated using Airflow to run at scheduled intervals, ensuring the database is continually updated with the latest news articles.
- **Data Provider API**: Interfaces with the PostgreSQL database for data retrieval and updates, ensuring efficient data management.
- **Model Inference API**: Integrates the NER functionality, providing endpoints for processing and analyzing news articles.


## ML Part of the Project

Currently, the project utilizes the REL library for named entity recognition, focusing on identifying company names within news articles. The next steps involve expanding the ML component to include:

- **News Summarization**: Developing models to generate concise summaries of news articles.
- **Sentiment Analysis**: Implementing sentiment analysis to evaluate the positive or negative tone of news related to specified companies.

## Future Plans

Moving forward, the project will focus on enhancing its capabilities and user experience:

1. **Advanced ML Models**: Integrate more sophisticated ML models for summarization and sentiment analysis.
2. **Frontend Development**: Design and implement a user-friendly interface for interacting with the service.
3. **User Feedback Loop**: Establish mechanisms for collecting user feedback to continually refine and improve the service.
4. **Comprehensive Monitoring and Error Handling**: Expand monitoring and alerting systems to ensure high availability and reliability.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Project Organization

    ├── LICENSE
    ├── README.md          <- The top-level README for developers using this project.
    ├── alertmanager       <- Configuration for Alertmanager to handle alerts sent by Prometheus.
    │
    ├── dags               <- Airflow DAGs for orchestrating ETL tasks.
    │
    ├── data
    │   ├── external       <- Data from third party sources.
    │   ├── interim        <- Intermediate data that has been transformed.
    │   ├── processed      <- The final, canonical data sets for modeling.
    │   └── raw            <- The original, immutable data dump.
    │
    ├── docker-compose.yml <- Defines and runs multi-container Docker applications.
    ├── Dockerfile.*       <- Dockerfiles for various services (Airflow, Flyway, Jupyter, Postgres).
    │
    ├── docs               <- Sphinx project for documentation.
    │
    ├── grafana            <- Grafana dashboards and provisioning for monitoring.
    │   ├── dashboards
    │   └── provisioning
    │
    ├── init_db_prod       <- Scripts and templates for initializing the production database.
    ├── init_db_test       <- Scripts and templates for initializing the test database.
    │
    ├── notebooks          <- Jupyter notebooks. Naming convention is a number (for ordering),
    │                         the creator's initials, and a short `-` delimited description, e.g.
    │                         `1.0-jqp-initial-data-exploration`.
    │
    ├── prometheus         <- Prometheus alerting rules and configuration
    │
    ├── pyproject.toml     <- Project metadata and dependencies file for Poetry.
    │
    ├── references         <- Data dictionaries, manuals, and all other explanatory materials.
    │
    ├── reports            <- Generated analysis as HTML, PDF, LaTeX, etc.
    │   └── figures        <- Generated graphics and figures to be used in reporting
    │
    ├── requirements       <- Dependencies
    │
    ├── scripts            <- Scripts for various setup tasks and operations.
    │
    ├── sql                <- SQL scripts and templates for database setup and migrations.
    │
    ├── src                <- Source code for core libraries or utilities that do not fit the service-based architecture.
    │
    └── styx_app           <- Main application code for the project, including API services.
        ├── model_inference_api
        ├── data_provider_api
        └── scraper_service
