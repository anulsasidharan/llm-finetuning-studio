from fastapi import APIRouter

api_router = APIRouter()

# Route modules are registered here as they land under api/v1/routes/.
# Example (auth lands in PHASE1-WEEK2-012):
# from api.v1.routes import auth
# api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
