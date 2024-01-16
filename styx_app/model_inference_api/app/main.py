from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes.extract_entities_routes import router as extract_entities

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
app.include_router(extract_entities, prefix="/ner", tags=["NER"])
