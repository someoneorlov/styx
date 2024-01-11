from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes.extract_entities_routes import router as ner_router

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
app.include_router(ner_router, prefix="/ner", tags=["NER"])

# You can add more routers as your application grows
