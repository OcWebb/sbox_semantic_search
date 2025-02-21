from fastapi import FastAPI
import uvicorn
from routes import package_routes, index_routes, search_routes
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.gzip import GZipMiddleware

app = FastAPI()

app.include_router(package_routes.router)
app.include_router(index_routes.router)
app.include_router(search_routes.router)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])
# app.add_middleware(HTTPSRedirectMiddleware)
app.add_middleware(GZipMiddleware)

if __name__ == "__main__":
    print("Swagger UI available at http://localhost:8080/docs")
    uvicorn.run(app, host="localhost", port=8080)