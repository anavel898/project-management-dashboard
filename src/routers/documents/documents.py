from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Request, Response, UploadFile
from src.dependecies import get_db
from sqlalchemy.orm import Session
from src.services.document_handler import DocumentHandler
from starlette import status
from src.routers.documents.schemas import Document
from src.services.auth_utils import check_privilege

documents_router = APIRouter()

@documents_router.get("/document/{document_id}")
async def get_document(request: Request,
                       document_id: int,
                       db: Annotated[Session, Depends(get_db)]):
    # check if document exists
    project_id = DocumentHandler.get_document_project(document_id=document_id,
                                                       db=db)
    # check if caller is authorized to get it
    owned = request.state.owned
    participating = request.state.participating
    check_privilege(project_id=project_id,
                    owned_projects=owned,
                    participating_projects=participating)
    # call method
    name, content_type, contents = DocumentHandler.download_document(document_id=document_id, db=db)
    return Response(
        content=contents,
        media_type=content_type,
        headers={
            "Content-Disposition": f"attachment;filename={name}",
            "Content-Type": f"{content_type}"
        }
    )


@documents_router.put("/document/{document_id}", response_model=Document)
async def update_document(request: Request,
                          document_id: int,
                          new_document: UploadFile,
                          db: Annotated[Session, Depends(get_db)]):
    # check if document exists
    project_id = DocumentHandler.get_document_project(document_id=document_id, db=db)
    # check if caller is authorized to update it
    owned = request.state.owned
    participating = request.state.participating
    check_privilege(project_id=project_id,
                    owned_projects=owned,
                    participating_projects=participating)
    user_calling = request.state.username
    content = await new_document.read()
    return DocumentHandler.update_document(document_id=document_id,
                                        doc_name=new_document.filename,
                                        content_type=new_document.content_type,
                                        updating_user=user_calling,
                                        b_content=content,
                                        db=db)


@documents_router.delete("/document/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(request: Request,
                          document_id: int,
                          db: Annotated[Session, Depends(get_db)]):
    # check if document exists
    project_id = DocumentHandler.get_document_project(document_id=document_id, db=db)
    # check owner privileges
    owned = request.state.owned
    participating = request.state.participating
    check_privilege(project_id=project_id,
                    owned_projects=owned,
                    participating_projects=participating)
    DocumentHandler.delete_document(document_id=document_id,
                                    db=db)
    