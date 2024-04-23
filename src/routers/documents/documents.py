from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Request, Response, UploadFile
from src.dependecies import get_db
from sqlalchemy.orm import Session
from src.services.document_handler import DocumentHandler
from starlette import status
from src.routers.documents.schemas import Document


documents_router = APIRouter()

@documents_router.get("/document/{document_id}")
async def get_document(request: Request,
                       document_id: int,
                       db: Annotated[Session, Depends(get_db)]):
    # check if document exists
    try:
        DocumentHandler.check_document_exists(document_id=document_id, db=db)
    except HTTPException as ex:
        raise ex
    # check if caller is authorized to get it
    project_id = DocumentHandler.check_project(document_id=document_id, db=db)
    owned = request.headers["owned"]
    participating = request.headers["participating"]
    if str(project_id) not in owned.split(" ") and str(project_id) not in participating.split(" "):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="You don't have access to this document")
    try:
        name, content_type, contents = DocumentHandler.download_document(document_id=document_id, db=db)
        return Response(
            content=contents,
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment;filename={name}",
                "Content-Type": f"{content_type}"
            }
        )
    except HTTPException as ex:
        raise ex



@documents_router.put("/document/{document_id}", response_model=Document)
async def update_document(request: Request,
                          document_id: int,
                          new_document: UploadFile,
                          db: Annotated[Session, Depends(get_db)]):
    # check if document exists
    try:
        DocumentHandler.check_document_exists(document_id=document_id, db=db)
    except HTTPException as ex:
        raise ex
    
    # check if caller is authorized to update it
    owned = request.headers["owned"]
    participating = request.headers["participating"]
    project_id = DocumentHandler.check_project(document_id=document_id,
                                               db=db)
    if str(project_id) not in owned.split(" ") and str(project_id) not in participating.split(" "):
        raise HTTPException(status)
    user_calling = request.headers["username"]
    content = await new_document.read()
    try:
        return DocumentHandler.update_document(document_id=document_id,
                                        doc_name=new_document.filename,
                                        content_type=new_document.content_type,
                                        updating_user=user_calling,
                                        b_content=content,
                                        db=db)
    except HTTPException as ex:
        raise ex


@documents_router.delete("/document/{document_id}")
async def delete_document(request: Request,
                          document_id: int,
                          db: Annotated[Session, Depends(get_db)]):
    # check if document exists
    try:
        DocumentHandler.check_document_exists(document_id=document_id, db=db)
    except HTTPException as ex:
        raise ex
    # check owner privileges
    owned = request.headers["owned"]
    participating = request.headers["participating"]
    project_id = DocumentHandler.check_project(document_id=document_id,
                                               db=db)
    if str(project_id) not in owned.split(" ") and str(project_id) not in participating.split(" "):
        raise HTTPException(status)
    try:
        DocumentHandler.delete_document(document_id=document_id,
                                        db=db)
        return status.HTTP_204_NO_CONTENT
    except HTTPException as ex:
        raise ex
    