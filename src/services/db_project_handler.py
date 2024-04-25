from sqlalchemy import select, update
from sqlalchemy.orm import Session
from src.project_handler_interface import ProjectHandlerInterface
from src.routers.project.schemas import Project, ProjectDocument, ProjectLogo, CoreProjectData, ProjectPermission, SentEmailProjectInvite
from fastapi import HTTPException
from src.services.aws_utils import delete_file_from_s3, download_file_from_s3, upload_file_to_s3, send_email_via_ses
from src.services.invite_utils import create_join_token
from src.services.project_manager_tables import Projects, ProjectAccess, Documents, Users
from uuid import uuid4
from datetime import datetime


class DbProjectHandler(ProjectHandlerInterface):
    def create(self,
               name: str,
               created_by: str,
               description: str,
               db: Session):
        # add new project to Projects table
        new_project = Projects(name=name,
                               created_by=created_by,
                               description=description)
        db.add(new_project)
        db.commit()
        #add new permission of type 'owner' to ProjectAccess
        db.add(ProjectAccess(project_id=new_project.id,
                             username=created_by,
                             access_type="owner"))
        db.commit()
        return self.get(new_project.id, db)

    def get(self, project_id: int, db: Session):
        project = db.get(Projects, project_id)
        # retrieve documents associated to the project
        docs = db.execute(select(Documents.id, Documents.name).where(
            Documents.project_id==project_id))
        docs_list = [{"id": row[0], "name": row[1]} for row in docs.all()]
        
        # retrieve full list of project contributors
        contributors = db.execute(select(ProjectAccess.username).where(
                    ProjectAccess.project_id == project_id))
        contributors_list = [row[0] for row in contributors.all()]
        # create appropriate output format
        # user should just see the name of the file uploaded as logo, not the
        # s3 bucket key built by the app
        logo_format_for_users = None
        if project.logo is not None:
            logo_format_for_users = project.logo[len(f"project-{project_id}-logo-"):]
        project_repr = Project(id=project.id,
                               name=project.name,
                               created_by=project.created_by,
                               created_on=project.created_on,
                               description=project.description,
                               updated_by=project.updated_by,
                               updated_on=project.updated_on,
                               logo=logo_format_for_users,
                               documents= docs_list,
                               contributors=contributors_list)
        return project_repr

    
    def get_all(self, db: Session, accessible_projects: list[int]):
        all_projects = list()
        all_project_raw = db.query(Projects.id,
                                   Projects.name,
                                   Projects.description,
                                   Projects.created_by,
                                   Projects.created_on).filter(
                                       Projects.id.in_(accessible_projects))
        for row in all_project_raw.all():
            proj = CoreProjectData(id = row[0],
                                   name = row[1],
                                   description=row[2],
                                   owner=row[3],
                                   created_on=row[4])
            all_projects.append(proj)
        return all_projects

    
    def delete(self, project_id: int, db: Session):
        project = db.get(Projects, project_id)
        db.delete(project)
        db.commit()
    

    def update_info(self, project_id: int,
                    attributes_to_update: dict,
                    db: Session):
        attributes_to_update.update({"updated_on": datetime.now()})
        q = update(Projects).where(Projects.id == project_id).values(
            attributes_to_update)
        db.execute(q)
        db.commit()
        return self.get(project_id, db)
    

    @staticmethod
    def check_project_exists(project_id: int, db: Session) -> None:
        project = db.get(Projects, project_id)
        if project is None:
            raise HTTPException(status_code=404,
                                detail=f"No project with id {project_id} found")
        else:
            return project

    
    @staticmethod
    def grant_access(project_id: int, username: str, db: Session):
        new_access = ProjectAccess(project_id=project_id,
                                   username=username,
                                   access_type="participant")
        db.add(new_access)
        db.commit()
        perm = ProjectPermission(project_id=project_id,
                                 username=username,
                                 role="participant")
        return perm
        

    @staticmethod
    def get_project_privileges(db: Session, username: str):
        owned_projects = db.execute(select(ProjectAccess.project_id)
                                             .where((ProjectAccess.username == username) &
                                                    (ProjectAccess.access_type == 'owner')))
        participant_projects = db.execute(select(ProjectAccess.project_id)
                                    .where((ProjectAccess.username == username) & 
                                           (ProjectAccess.access_type == 'participant')))
        list_owned_projects = [row[0] for row in owned_projects]
        list_participant_projects = [row[0] for row in participant_projects]
        return list_owned_projects, list_participant_projects


    def associate_document(self,
                           project_id: int,
                           doc_name: str,
                           content_type: str,
                           caller: str,
                           byfile: bytes,
                           db: Session):
        # generate unique uuid
        new_s3_key = uuid4()
        query_for_same_uuid = db.execute(select(Documents).where(Documents.s3_key == str(new_s3_key)))
        # if there is a document with the same key, re-generate the key
        while query_for_same_uuid.all() != []:
            # even though here the database is again called in a loop,
            # the probability of the same uuid being generated twice is tiny.
            # So, this part of the code probably won't be executed ever, but
            # it's still here to prevent key collisions from happening
            new_s3_key = uuid4()
            query_for_same_uuid = db.execute(select(Documents).where(Documents.s3_key == str(new_s3_key)))
        
        new_document = Documents(name=doc_name.strip().replace(" ","-"),
                                 project_id=project_id,
                                 added_by=caller,
                                 content_type=content_type,
                                 s3_key=str(new_s3_key),
                                 added_on=datetime.now())
        db.add(new_document)
        # upload to s3
        try:
            upload_file_to_s3(bucket_name="project-manager-documents",
                              key=str(new_s3_key),
                              bin_file=byfile)
        except Exception as ex:
            raise ex
        
        # commit added document only if upload to s3 was successful
        db.commit()
        # return the created document to the user
        final_document = db.get(Documents, new_document.id)
        return ProjectDocument(id=final_document.id,
                               name=final_document.name,
                               added_by=final_document.added_by,
                               added_on=final_document.added_on,
                               content_type=final_document.content_type,
                               project_id=final_document.project_id)


    def get_docs(self,
                 project_id: int,
                 db: Session):
        all_documents = db.execute(select(Documents.id,
                                          Documents.name,
                                          Documents.added_by,
                                          Documents.added_on,
                                          Documents.content_type)
                                          .where(Documents.project_id == project_id))
        all_docs_formatted = []
        for row in all_documents.all():
            doc = ProjectDocument(id=row[0],
                           name=row[1],
                           added_by=row[2],
                           added_on=row[3],
                           content_type=row[4],
                           project_id=project_id)
            all_docs_formatted.append(doc)
        return all_docs_formatted
    

    def upload_logo(self,
                    project_id: int,
                    logo_name: str,
                    b_content: bytes,
                    logo_poster:str,
                    db: Session) -> ProjectLogo:
        clean_user_provided_name = logo_name.strip().replace(" ","-")
        logo_key = f"project-{project_id}-logo-{clean_user_provided_name}"
        q = update(Projects).where(Projects.id == project_id).values(
                {"logo": logo_key,
                 "updated_by": logo_poster,
                 "updated_on": datetime.now()}
            )
        try:
            db.execute(q)
            upload_file_to_s3("logos-raw", logo_key, b_content)
        except Exception as ex:
            raise ex
        else:
            # commit update of logo field only if upload finished successfully
            db.commit()
        updated_proj = db.get(Projects, project_id)
        name_for_user = updated_proj.logo[len(f"project-{project_id}-logo-"):]
        return ProjectLogo(project_id=updated_proj.id,
                           logo_name=name_for_user,
                           uploaded_by=updated_proj.updated_by,
                           uploaded_on=updated_proj.updated_on)
    

    def download_logo(self,
                      project_id: int,
                      db: Session):
        proj = db.get(Projects, project_id)
        if proj.logo is None:
            raise HTTPException(status_code=404,
                                detail=f"Project with id {project_id} doesn't have a logo")
        name_for_user = proj.logo[len(f"project-{project_id}-logo-"):]
        try:
            contents = download_file_from_s3(bucket_name="logos-processed",
                                         key=proj.logo)
        except Exception as ex:
            raise ex
        return name_for_user, contents
    

    def delete_logo(self,
                    project_id: int,
                    user_calling: str,
                    db: Session):
        proj = db.get(Projects, project_id)
        try:
            # delete from bucket with resized
            delete_file_from_s3("logos-processed", proj.logo)
            # delete from bucket with original images
            delete_file_from_s3("logos-raw", proj.logo)
            q = update(Projects).where(Projects.id == project_id).values(
                {"logo": None,
                 "updated_by": user_calling,
                 "updated_on": datetime.now()}
            )
            db.execute(q)
        except Exception as ex:
            raise ex
        else:
            db.commit()
    

    def email_invite(self,
                     project_id: int,
                     invite_sender_username: str,
                     invite_receiver: str,
                     email: str,
                     db: Session):
        proj = db.get(Projects, project_id)
        owner = db.get(Users, invite_sender_username)
        token_claims = {"sub": invite_receiver, "project": project_id}
        join_token = create_join_token(to_encode=token_claims)
        text = f"""Hello,
        {owner.name} invited you to join the project '{proj.name}'.
        To accept the invite go to: http://<url-where-app-is-running>/join?project_id={project_id}&join_token={join_token}
        This invite is valid for 3 days. This is an automatic email, do not reply to this address. For additional info reply to {owner.email}"""
        message_id = send_email_via_ses(text=text, to_address=email)
        return SentEmailProjectInvite(aws_message_id=message_id,
                                      join_token=join_token)


        