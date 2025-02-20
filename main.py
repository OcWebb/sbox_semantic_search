from fastapi import FastAPI
import uvicorn
from routes import package_routes, index_routes, search_routes

app = FastAPI()

app.include_router(package_routes.router)
app.include_router(index_routes.router)
app.include_router(search_routes.router)

if __name__ == "__main__":
    print("Swagger UI available at http://localhost:8080/docs")
    uvicorn.run(app, host="localhost", port=8080)