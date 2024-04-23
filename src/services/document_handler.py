from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.orm import Session
from src.services.documents_utils import delete_file_from_s3, download_file_from_s3, upload_file_to_s3
from src.services.project_manager_tables import Documents, Projects
from src.routers.documents.schemas import Document
from datetime import datetime

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
    def update_document(document_id: int,
                        doc_name: str,
                        content_type: str,
                        updating_user: str,
                        b_content: bytes,
                        db: Session):
        # create dict of attributes to update
        fields_to_update = {"name": doc_name.strip().replace(" ", "-"),
                            "added_by": updating_user,
                            "content_type": content_type,
                            "added_on": datetime.now()}
        # get s3_key from db
        key = db.get(Documents, document_id).s3_key
        try:
            q = update(Documents).where(Documents.id == document_id).values(
                fields_to_update)
            db.execute(q)
            # try uploading new doc with old key to s3
            upload_file_to_s3(bucket_name="project-manager-documents",
                              key=key,
                              bin_file=b_content)
        except Exception as ex:
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