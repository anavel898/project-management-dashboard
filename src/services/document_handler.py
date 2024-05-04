from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from src.logs.logger import get_logger
from .documents_utils import S3Service
from .project_manager_tables import Documents, Projects
from src.routers.documents.schemas import Document
from datetime import datetime
from .common_utils import reformat_filename
from dotenv import load_dotenv
import os


load_dotenv()
DOCUMENTS_BUCKET = os.getenv("DOCUMENTS_BUCKET")
logger = get_logger(__name__)

class DocumentHandler():
    @staticmethod
    def download_document(document_id: int, db: Session):
        doc = db.get(Documents, document_id)
        key = doc.s3_key
        name = doc.name
        content_type = doc.content_type
        s3_service = S3Service(DOCUMENTS_BUCKET)
        try:
            contents = s3_service.download_file_from_s3(key=key)
        except Exception as ex:
            logger.error(f"Failed to download document {document_id}")
            raise ex
        return (name, content_type, contents)
    

    @staticmethod
    def update_document(document_id: int,
                        doc_name: str,
                        content_type: str,
                        updating_user: str,
                        b_content: bytes,
                        db: Session):
        # create dict of attributes to update
        fields_to_update = {"name": reformat_filename(doc_name),
                            "added_by": updating_user,
                            "content_type": content_type,
                            "added_on": datetime.now()}
        # get s3_key from db
        key = db.get(Documents, document_id).s3_key
        s3_service = S3Service(DOCUMENTS_BUCKET)
        try:
            q = update(Documents).where(Documents.id == document_id).values(
                fields_to_update)
            db.execute(q)
            # try uploading new doc with old key to s3
            s3_service.upload_file_to_s3(key=key, bin_file=b_content, content_type=content_type)
        except Exception as ex:
            logger.error(f"Failed to update document {document_id}")
            raise ex
        else:
            # if upload was successful, commit db changes
            db.commit()
        # return updated document object
        updated_doc = db.get(Documents, document_id)
        return Document(id=updated_doc.id,
                        name=updated_doc.name,
                        added_by=updated_doc.added_by,
                        added_on=updated_doc.added_on,
                        project_id=updated_doc.project_id,
                        content_type=updated_doc.content_type)
        

    @staticmethod
    def delete_document(document_id: int, db: Session):
        doc = db.get(Documents, document_id)
        s3_service = S3Service(DOCUMENTS_BUCKET)
        try:
            s3_service.delete_file_from_s3(key=doc.s3_key)
        except Exception as ex:
            logger.error(f"Failed to delete document {document_id}")
            raise ex
        db.delete(doc)
        db.commit()


    @staticmethod
    def get_document_project(document_id: int, db: Session):
        doc = db.get(Documents, document_id)
        if doc is None:
            logger.error(f"Operation attempted with a non-existent document with id {document_id}")
            raise HTTPException(status_code=404,
                                detail=f"No document with id {document_id} found")
        return doc.project_id
