from datetime import datetime

import unittest

import src.services.inmem_project_handler as p


class TestProjectMethods(unittest.TestCase):
    test_project = {"name": "Project 1",
                 "created_by": "avel",
                 "description": "toy description 1"}

    def test_update_attribute(self):
        creationTime = datetime.now()
        projectInstance = p.Project(id=1, **self.test_project)
        projectInstance.update_attribute("description", "updated description")
        self.assertEqual("updated description", projectInstance.description)
        project_as_dict = projectInstance.model_dump()
        expected_dict = self.test_project.copy()
        expected_dict.update(
            {"id": 1, "description": "updated description",
             "logo": None, "documents": None, "contributors": None,
             "updated_by": None, "updated_on": None,
             "created_on": creationTime
             }
        )
        self.assertDictEqual(project_as_dict, expected_dict)


class TestInMemProjectHandlerMethods(unittest.TestCase):
    test_project = {"name": "Project 1",
                 "created_by": "avel",
                 "description": "toy description 1"}

    def test_handler_constructor(self):
        handlerInstance = p.InMemProjectHandler()
        all_projects = handlerInstance.all_projects
        self.assertEqual(dict(), all_projects)
        self.assertEqual(0, handlerInstance.projects_number)

    def test_handler_create(self):
        handlerInstance = p.InMemProjectHandler()
        timestamp = datetime.now()
        handlerInstance.create(**self.test_project)

        self.assertEqual(1, handlerInstance.projects_number)
        created_project = handlerInstance.all_projects[1]
        self.assertIsInstance(created_project, p.Project)
        # checking if attributes of created Project match expected values
        self.assertEqual(1, created_project.id)
        self.assertEqual("Project 1", created_project.name)
        self.assertEqual("avel", created_project.created_by)
        self.assertLessEqual(timestamp, created_project.created_on)
        self.assertEqual("toy description 1", created_project.description)
        self.assertIsNone(created_project.updated_on)
        self.assertIsNone(created_project.updated_by)
        self.assertIsNone(created_project.logo)
        self.assertEqual([], created_project.documents)
        self.assertEqual(["avel"], created_project.contributors)
    
    def test_get_all(self):
        handlerInstance = p.InMemProjectHandler()
        handlerInstance.create(**self.test_project)
        returned = handlerInstance.get_all()
        self.assertIsInstance(returned, dict)
        self.assertEqual(1, len(returned))
        returnedProject = returned[1]
        # checking if attributes of returned projects match expected values
        self.assertEqual(1, returnedProject.id)
        self.assertEqual("Project 1", returnedProject.name)
        self.assertEqual("avel", returnedProject.created_by)
        self.assertEqual("toy description 1", returnedProject.description)
        self.assertIsNone(returnedProject.updated_by)
        self.assertIsNone(returnedProject.updated_on)
        self.assertIsNone(returnedProject.logo)
        self.assertEqual([], returnedProject.documents)
        self.assertEqual(["avel"], returnedProject.contributors)
        
    def test_get_all_w_multiple(self):
        handlerInstance = p.InMemProjectHandler()
        # setting up multiple projects
        handlerInstance.create(**self.test_project)
        handlerInstance.create("Project 2", "janedoe", "toy description 2")
        handlerInstance.create("Project 3", "avel", "toy description 3")
        # calling tested method
        returned = handlerInstance.get_all()
        # checking returned object
        self.assertIsInstance(returned, dict)
        self.assertEqual(3, len(returned))

    def test_get(self):
        handlerInstance = p.InMemProjectHandler()
        handlerInstance.create(**self.test_project)

        returnedProject = handlerInstance.get(1)
        self.assertEqual(1, returnedProject.id)
        self.assertEqual("Project 1", returnedProject.name)
        self.assertEqual("avel", returnedProject.created_by)
        self.assertEqual("toy description 1", returnedProject.description)
        self.assertIsNone(returnedProject.updated_by)
        self.assertIsNone(returnedProject.updated_on)
        self.assertIsNone(returnedProject.logo)
        self.assertEqual([], returnedProject.documents)
        self.assertEqual(["avel"], returnedProject.contributors)

    def test_get_failure(self):
        handlerInstance = p.InMemProjectHandler()
        self.assertRaises(p.HTTPException,
                          handlerInstance.get, 565)

    def test_update_info(self):
        handlerInstance = p.InMemProjectHandler()
        handlerInstance.create(**self.test_project)
        attributesToUpdate = {"contributors": [2, 4],
                              "description": "new description"}
        timestamp =datetime.now()
        handlerInstance.update_info(1, attributesToUpdate)

        self.assertEqual([2, 4], handlerInstance.all_projects[1].contributors)
        self.assertEqual("new description",
                         handlerInstance.all_projects[1].description)
        self.assertLessEqual(timestamp,
                             handlerInstance.all_projects[1].updated_on)
        
    def test_update_info_failure(self):
        handlerInstance = p.InMemProjectHandler()
        attributesToUpdate = {"contributors": [2, 4],
                              "description": "new description"}
        self.assertRaises(
            p.HTTPException, handlerInstance.update_info, 3, attributesToUpdate
        )

    def test_delete_failure(self):
        handlerInstance = p.InMemProjectHandler()
        self.assertRaises(p.HTTPException, handlerInstance.delete, 8)

    def test_delete(self):
        handlerInstance = p.InMemProjectHandler()
        handlerInstance.create(**self.test_project)
        handlerInstance.delete(1)
        self.assertRaises(p.HTTPException,
                          handlerInstance.get, 1)
