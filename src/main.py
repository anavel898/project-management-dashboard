from fastapi import FastAPI
from .routers.project import projects
from .routers.auth import auth


app = FastAPI()
app.include_router(projects.project_router)
app.include_router(auth.auth_router)

@app.get("/")
async def root():
    return {"message": "hello from root!"}

# @app.get("/items")
# async def read_items(token: Annotated[str, Depends(oauth2_scheme)]):
#     return {"token": token}
