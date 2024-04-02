import json
import unittest

import src.services.inmem_project_handler as p


class TestProjectMethods(unittest.TestCase):
    arguments = {"name": "Project 1",
                 "ownerId": 1,
                 "description": "toy description 1"}

    def test_project_constructor(self):
        projectInstance = p.Project(1, **self.arguments)
        self.assertEqual(1, projectInstance.id)
        self.assertEqual("Project 1", projectInstance.name)
        self.assertEqual(1, projectInstance.ownerId)
        self.assertEqual("toy description 1", projectInstance.description)
        self.assertIsNone(projectInstance.logo)
        self.assertIsNone(projectInstance.documents)
        self.assertIsNone(projectInstance.contributors)

    def test_to_dict(self):
        projectInstance = p.Project(1, **self.arguments)
        projectAsDict = projectInstance.to_dict()
        expectedDict = self.arguments.copy()
        expectedDict.update(
            {"id": 1, "logo": None, "documents": None, "contributors": None}
        )
        self.assertDictEqual(projectAsDict, expectedDict)

    def test_update_attribute(self):
        projectInstance = p.Project(1, **self.arguments)
        contributorsList = [2, 4]
        projectInstance.update_attribute("contributors", contributorsList)
        self.assertEqual([2, 4], projectInstance.contributors)
        projectAsDict = projectInstance.to_dict()
        expectedDict = self.arguments.copy()
        expectedDict.update(
            {"id": 1, "logo": None, "documents": None, "contributors": [2, 4]}
        )
        self.assertDictEqual(projectAsDict, expectedDict)


class TestInMemProjectHandlerMethods(unittest.TestCase):
    arguments = {"name": "Project 1",
                 "ownerId": 1,
                 "description": "toy description 1"}

    def test_handler_constructor(self):
        handlerInstance = p.InMemProjectHandler()
        allProjects = handlerInstance.allProjects
        self.assertEqual(dict(), allProjects)
        self.assertEqual(0, handlerInstance.projectsNumber)

    def test_handler_create(self):
        handlerInstance = p.InMemProjectHandler()
        handlerInstance.create(**self.arguments)
        createdObjDict = handlerInstance.allProjects[1].to_dict()
        expectedObjDict = p.Project(1, "Project 1", 1,
                                    "toy description 1").to_dict()

        self.assertEqual(1, handlerInstance.projectsNumber)
        self.assertIsInstance(handlerInstance.allProjects[1], p.Project)
        self.assertDictEqual(createdObjDict, expectedObjDict)

    def test_get_all(self):
        handlerInstance = p.InMemProjectHandler()
        handlerInstance.create(**self.arguments)
        expected = json.dumps(
            {
                1: {
                    "id": 1,
                    "name": "Project 1",
                    "ownerId": 1,
                    "description": "toy description 1",
                    "logo": None,
                    "documents": None,
                    "contributors": None,
                }
            }
        )
        self.assertEqual(expected, handlerInstance.get_all())

    def test_get(self):
        handlerInstance = p.InMemProjectHandler()
        handlerInstance.create(**self.arguments)
        expected = json.dumps(
            {
                "id": 1,
                "name": "Project 1",
                "ownerId": 1,
                "description": "toy description 1",
                "logo": None,
                "documents": None,
                "contributors": None,
            }
        )
        self.assertEqual(expected, handlerInstance.get(1))

    def tst_get_failure(self):
        handlerInstance = p.InMemProjectHandler()
        self.assertRaises(p.HTTPException(status_code=400),
                          handlerInstance.get, 3)

    def test_update_info(self):
        handlerInstance = p.InMemProjectHandler()
        handlerInstance.create(**self.arguments)
        attributesToUpdate = {"contributors": [2, 4],
                              "description": "new description"}
        handlerInstance.update_info(1, attributesToUpdate)

        self.assertEqual([2, 4], handlerInstance.allProjects[1].contributors)
        self.assertEqual("new description",
                         handlerInstance.allProjects[1].description)

    def test_update_info_failure(self):
        handlerInstance = p.InMemProjectHandler()
        attributesToUpdate = {"contributors": [2, 4],
                              "description": "new description"}
        self.assertRaises(
            p.HTTPException, handlerInstance.update_info, 3, attributesToUpdate
        )
