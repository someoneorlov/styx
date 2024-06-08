# Styx: Advanced News Analysis Service

Styx is an advanced machine learning project aimed at providing detailed news analysis centered around companies. It not only lists related news in chronological order but also summarizes articles and evaluates their sentiment to determine if they have a positive or negative impact.

## About The Project

Styx addresses the challenge of filtering and analyzing news content to focus specifically on how it relates to particular companies. It leverages named entity recognition (NER) to identify company mentions accurately and assesses the relevance of news articles to these entities. This approach ensures users receive tailored news insights, summaries, and sentiment analysis, providing a deeper understanding of a company's news ecosystem.

## Application's backend architecture
<center>
<img src='static/img/styx_architecture.heic' width=800>
</center> 

## Technologies and Tools

The project is built using a robust stack of technologies and tools designed for scalability, efficiency, and ease of development.

The architectural design of the project comprises two main components. The first is a dedicated Ubuntu EC2-like server, which houses the core infrastructure services. The second is located in the AWS cloud and is responsible for the entire ML pipeline of the project.

<img src="static/img/server-square-cloud-svgrepo-com-lines.svg" title="aws" width="50" height="50"/>&nbsp; ### Remote server part:
- **Data Collection and Processing**: Python scripts for scraping and initial data processing.
- **Database**: PostgreSQL for data storage, with Flyway for database migrations ensuring schema consistency across environments.
- **Backend API**: FastAPI for serving data through RESTful endpoints, ensuring fast responses and asynchronous handling.
- **Machine Learning**: REL for named entity recognition and linking, MLFlow for experiment tracking.
- **Orchestration and Workflow Management**: Airflow for managing ETL processes and automating data pipeline tasks.
- **Containerization**: Docker for creating isolated environments, with Docker Compose for multi-container orchestration.
- **Monitoring**: Prometheus for monitoring system metrics, Grafana for dashboards, and Alertmanager for alerts.
- **Version Control and CI/CD**: Git for version control, with GitHub Actions for continuous integration and deployment pipelines.
- **Frontend**: React for the UI.
- **Web Server**: Nginx.

<img src="static/img/amazonwebservices-original-wordmark.svg" title="aws" width="50" height="50"/>&nbsp; ### AWS part:
- **Data Storage**: Configured AWS RDS for main data storage and Flyway for database migrations, ensuring smooth schema management.
- **Artifact Storage**: S3 for storing all artifacts, including models, datasets, and functions code.
- **Data Flow**: Developed data processing workflows using AWS Step Functions, Amazon EventBridge, ECS tasks, and AWS Lambda for data transfer and inference.
- **Infrastructure Management**: Utilized ECS clusters and custom Docker images for consistent environment setups across services.
- **Container Registry**: ECR for managing and storing Docker images.
- **Experiment Tracking**: Configured MLFlow on AWS to track experiments, manage models, and store artifacts across environments.
- **Model Training**: Set up AWS SageMaker for model training and experimenting, deploying to different endpoints for test and production.
- **Model Deployment**: Integrated SageMaker endpoints for model predictions, storing results in RDS DB.


## ML Part of the Project

- **Named Entity Recognition**: The project utilizes the REL library and the approach described in Grönberg, D. (2021). Extracting Salient Named Entities from Financial News Articles.
- **News Summarization**: Baseline fine-tuned FLAN-T5-small model using Hugging Face libraries to generate concise summaries of news articles.
- **Sentiment Analysis**: Baseline CatBoost classifier for sentiment analysis to evaluate the positive or negative tone of news related to specified companies.

## Future Plans

Moving forward, the project will focus on enhancing its capabilities and user experience:

1. **Advanced ML Models**: Integrate more sophisticated ML models, fine-tune open-source LLM models, build multi-agent solutions, and compare them with proprietary models like GPT-4.
2. **User Feedback Loop**: Establish mechanisms for collecting user feedback to continually refine and improve the service.
3. **Comprehensive Monitoring and Error Handling**: Expand monitoring and alerting systems to ensure high availability and reliability.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Project Organization

    ├── LICENSE
    ├── README.md              <- The top-level README for developers using this project.
    ├── AWS
    │   ├── ecs                <- ECS Tasks defenitions and scripts.
    │   ├── flyway             <- Flyway confing and SQL scripts.
    │   ├── lambda             <- Lambda functions and layers packages.
    │   ├── sagemaker          <- Model inference and endpoint scripts.
    │   └── step_functions     <- StepFunctions state machines defenitions.
    │
    ├── alertmanager           <- Configuration for Alertmanager to handle alerts sent by Prometheus.
    │
    ├── dags                   <- Airflow DAGs for orchestrating ETL tasks.
    │
    ├── data
    │   ├── external           <- Data from third party sources.
    │   ├── interim            <- Intermediate data that has been transformed.
    │   ├── processed          <- The final, canonical data sets for modeling.
    │   └── raw                <- The original, immutable data dump.
    │
    ├── docker-compose.yml     <- Defines and runs multi-container Docker applications.
    ├── Dockerfile.*           <- Dockerfiles for various services (Airflow, Flyway, Jupyter, Postgres).
    │
    ├── docs                   <- Sphinx project for documentation.
    │
    ├── grafana                <- Grafana dashboards and provisioning for monitoring.
    │   ├── dashboards
    │   └── provisioning
    │
    ├── init_db_prod           <- Scripts and templates for initializing the production database.
    ├── init_db_test           <- Scripts and templates for initializing the test database.
    │
    ├── notebooks              <- Jupyter notebooks. Naming convention is a number (for ordering),
    │                             the creator's initials, and a short `-` delimited description, e.g.
    │                             `1.0-jqp-initial-data-exploration`.
    │
    ├── prometheus             <- Prometheus alerting rules and configuration
    │
    ├── pyproject.toml         <- Project metadata and dependencies file for Poetry.
    │
    ├── references             <- Data dictionaries, manuals, and all other explanatory materials.
    │
    ├── reports                <- Generated analysis as HTML, PDF, LaTeX, etc.
    │   └── figures            <- Generated graphics and figures to be used in reporting
    │
    ├── requirements           <- Dependencies
    │
    ├── scripts                <- Scripts for various setup tasks and operations.
    │
    ├── sql                    <- SQL scripts and templates for database setup and migrations.
    │
    ├── src                    <- Source code for core libraries or utilities that do not fit the service-based architecture.
    │
    ├── styx_app               <- Main application code for the project, including API services.
    │   ├── data_provider_api
    │   ├── frontend
    │   ├── model_inference_api
    │   ├── ner_services
    │   ├── nginx
    │   └── scraper_service
    │
    └── styx_packages          <- Auxilliary custom libraries.
