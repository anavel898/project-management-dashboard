from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from src.services.documents_utils import delete_file_from_s3, download_file_from_s3
from src.services.project_manager_tables import Documents, Projects

class DocumentHandler():
    @staticmethod
    def download_document(document_id: int, db: Session):
        doc = db.get(Documents, document_id)
        key = doc.s3_key
        name = doc.name
        content_type = doc.content_type
        contents = download_file_from_s3(bucket_name="project-manager-documents",
                                         key=key)
        return (name, content_type, contents)
    
    @staticmethod
    def update_document(document_id: int, to_update: dict, db: Session):
        """It's not clear weather update document means upload different
        document associated with the same id, or change some detail in the db
        regarding the document (for example its name)"""
        raise NotImplementedError

    @staticmethod
    def delete_document(document_id: int, db: Session):
        doc = db.get(Documents, document_id)
        try:
            delete_file_from_s3(bucket_name="project-manager-documents",
                                               key=doc.s3_key)
        except Exception as ex:
            raise ex
        db.delete(doc)
        db.commit()

    @staticmethod
    def check_document_exists(document_id: int, db: Session):
        doc = db.get(Documents, document_id)
        if doc is None:
            raise HTTPException(status_code=404,
                                detail=f"No document with id {document_id} found")

    @staticmethod
    def check_project(document_id: int, db: Session):
        doc = db.get(Documents, document_id)
        return doc.project_id