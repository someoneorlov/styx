from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import (
    ner_data_routes,
    frontend_data_routes,
    aws_data_routes,
    sentiment_data_routes,
)

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

app.include_router(
    frontend_data_routes.router, prefix="/front-data", tags=["FRONT_DATA"]
)
app.include_router(aws_data_routes.router, prefix="/aws-data", tags=["AWS_DATA"])
app.include_router(ner_data_routes.router, prefix="/ner-data", tags=["NER_DATA"])
app.include_router(
    sentiment_data_routes.router, prefix="/sentiment-data", tags=["SENTIMENT_DATA"]
)
# app.include_router(
#     summary_data_routes.router, prefix="/summary-data", tags=["SUMMARY_DATA"]
# )
