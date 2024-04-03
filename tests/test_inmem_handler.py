from datetime import datetime

import json

import unittest

import src.services.inmem_project_handler as p


class TestProjectMethods(unittest.TestCase):
    test_project = {"name": "Project 1",
                 "createdBy": 1,
                 "description": "toy description 1"}

    def test_project_constructor(self):
        creationTime = datetime.now()
        projectInstance = p.Project(1, createdOn=creationTime,
                                    **self.test_project)
        self.assertEqual(1, projectInstance.id)
        self.assertEqual("Project 1", projectInstance.name)
        self.assertEqual(1, projectInstance.createdBy)
        self.assertEqual("toy description 1", projectInstance.description)
        self.assertIsNone(projectInstance.updatedBy)
        self.assertIsNone(projectInstance.updatedOn)
        self.assertIsNone(projectInstance.logo)
        self.assertIsNone(projectInstance.documents)
        self.assertIsNone(projectInstance.contributors)

    def test_to_dict(self):
        creationTime = datetime.now()
        projectInstance = p.Project(1, createdOn=creationTime,
                                    **self.test_project)
        projectAsDict = projectInstance.to_dict()
        expectedDict = self.test_project.copy()
        expectedDict.update(
            {"id": 1, "logo": None, "documents": None, "contributors": None, 
             "updatedBy": None, "updatedOn": None,
             "createdOn": creationTime.isoformat()
             }
        )
        self.assertDictEqual(projectAsDict, expectedDict)

    def test_update_attribute(self):
        creationTime = datetime.now()
        projectInstance = p.Project(1, createdOn=creationTime,
                                    **self.test_project)
        contributorsList = [2, 4]
        projectInstance.update_attribute("contributors", contributorsList)
        self.assertEqual([2, 4], projectInstance.contributors)
        projectAsDict = projectInstance.to_dict()
        expectedDict = self.test_project.copy()
        expectedDict.update(
            {"id": 1, "logo": None, "documents": None, "contributors": [2, 4],
             "updatedBy": None, "updatedOn": None,
             "createdOn": creationTime.isoformat()
             }
        )
        self.assertDictEqual(projectAsDict, expectedDict)


class TestInMemProjectHandlerMethods(unittest.TestCase):
    test_project = {"name": "Project 1",
                 "createdBy": 1,
                 "description": "toy description 1"}

    def test_handler_constructor(self):
        handlerInstance = p.InMemProjectHandler()
        allProjects = handlerInstance.allProjects
        self.assertEqual(dict(), allProjects)
        self.assertEqual(0, handlerInstance.projectsNumber)

    def test_handler_create(self):
        handlerInstance = p.InMemProjectHandler()
        timestamp = datetime.now()
        handlerInstance.create(**self.test_project)

        self.assertEqual(1, handlerInstance.projectsNumber)
        createdProject = handlerInstance.allProjects[1]
        self.assertIsInstance(createdProject, p.Project)
        # checking if attributes of created Project match expected values
        self.assertEqual(1, createdProject.id)
        self.assertEqual("Project 1", createdProject.name)
        self.assertEqual(1, createdProject.createdBy)
        self.assertLessEqual(timestamp, createdProject.createdOn)
        self.assertEqual("toy description 1", createdProject.description)
        self.assertIsNone(createdProject.updatedOn)
        self.assertIsNone(createdProject.updatedBy)
        self.assertIsNone(createdProject.logo)
        self.assertIsNone(createdProject.documents)
        self.assertIsNone(createdProject.contributors)
    


    def test_get_all(self):
        handlerInstance = p.InMemProjectHandler()
        handlerInstance.create(**self.test_project)
        self.assertIsInstance(handlerInstance.get_all(), str)
        self.assertIsInstance(json.loads(handlerInstance.get_all()), dict)

        returnedAsDict = json.loads(handlerInstance.get_all())
        self.assertEqual(1, len(returnedAsDict.items()))
        returnedProject = returnedAsDict["1"]
        # checking if attributes of converted projects match expected values
        self.assertEqual(1, returnedProject["id"])
        self.assertEqual("Project 1", returnedProject["name"])
        self.assertEqual(1, returnedProject["createdBy"])
        self.assertEqual("toy description 1", returnedProject["description"])
        self.assertIsNone(returnedProject["updatedBy"])
        self.assertIsNone(returnedProject["updatedOn"])
        self.assertIsNone(returnedProject["logo"])
        self.assertIsNone(returnedProject["documents"])
        self.assertIsNone(returnedProject["contributors"])
        
    def test_get_all_w_multiple(self):
        handlerInstance = p.InMemProjectHandler()
        handlerInstance.create(**self.test_project)
        handlerInstance.create("Project 2", 1, "toy description 2")
        handlerInstance.create("Project 3", 1, "toy description 3")

        self.assertIsInstance(handlerInstance.get_all(), str)
        self.assertIsInstance(json.loads(handlerInstance.get_all()), dict)

        returnedAsDict = json.loads(handlerInstance.get_all())
        self.assertEqual(3, len(returnedAsDict.items()))

    def test_get(self):
        handlerInstance = p.InMemProjectHandler()
        handlerInstance.create(**self.test_project)

        returnedProject = json.loads(handlerInstance.get(1))
        self.assertEqual(1, returnedProject["id"])
        self.assertEqual("Project 1", returnedProject["name"])
        self.assertEqual(1, returnedProject["createdBy"])
        self.assertEqual("toy description 1", returnedProject["description"])
        self.assertIsNone(returnedProject["updatedBy"])
        self.assertIsNone(returnedProject["updatedOn"])
        self.assertIsNone(returnedProject["logo"])
        self.assertIsNone(returnedProject["documents"])
        self.assertIsNone(returnedProject["contributors"])

    def test_get_failure(self):
        handlerInstance = p.InMemProjectHandler()
        self.assertRaises(p.HTTPException,
                          handlerInstance.get, 3)

    def test_update_info(self):
        handlerInstance = p.InMemProjectHandler()
        handlerInstance.create(**self.test_project)
        attributesToUpdate = {"contributors": [2, 4],
                              "description": "new description"}
        timestamp =datetime.now()
        handlerInstance.update_info(1, attributesToUpdate)

        self.assertEqual([2, 4], handlerInstance.allProjects[1].contributors)
        self.assertEqual("new description",
                         handlerInstance.allProjects[1].description)
        self.assertLessEqual(timestamp,
                             handlerInstance.allProjects[1].updatedOn)
        

    def test_update_info_failure(self):
        handlerInstance = p.InMemProjectHandler()
        attributesToUpdate = {"contributors": [2, 4],
                              "description": "new description"}
        self.assertRaises(
            p.HTTPException, handlerInstance.update_info, 3, attributesToUpdate
        )
