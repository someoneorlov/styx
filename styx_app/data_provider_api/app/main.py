from fastapi import FastAPI
from .routes import ner_data_routes

app = FastAPI()

app.include_router(ner_data_routes.router, prefix="/ner-data", tags=["NER_DATA"])
# app.include_router(
#     semantic_data_routes.router, prefix="/semantic-data", tags=["SEMANTIC_DATA"]
# )
# app.include_router(
#     summary_data_routes.router, prefix="/summary-data", tags=["SUMMARY_DATA"]
# )
