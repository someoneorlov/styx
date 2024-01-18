from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import ner_inf_routes

# Create FastAPI app instance
app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include routers (API endpoints)
app.include_router(ner_inf_routes.router, prefix="/ner-inf", tags=["NER_INF"])
# app.include_router(
#     semantic_inf_routes.router, prefix="/semantic-inf", tags=["SEMANTIC_INF"]
# )
# app.include_router(
#     summary_inf_routes.router, prefix="/summary-inf", tags=["SUMMARY_INF"]
# )
