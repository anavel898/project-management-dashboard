from fastapi import FastAPI

from .routers.project import projects
# from .routers.project.projects import router

app = FastAPI()

app.include_router(projects.router)


@app.get("/")
async def root():
    return {"message": "Hello World"}
