import uvicorn
from app.routes.travel import router as travel_router
from app.routes.payment import router as payment_router
from fastapi import FastAPI

app = FastAPI()

app.include_router(travel_router, prefix="/api", tags=["travel"])
app.include_router(payment_router, tags=["payment"])

if __name__ == "__main__":
    uvicorn.run(app, port=8000, reload=True) 