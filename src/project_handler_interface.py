from abc import ABC, abstractmethod


class ProjectHandlerInterface(ABC):

    @abstractmethod
    def create(
        self,
        name: str,
        createdBy: int,
        description: str,
        logo: str = None,
        documents: str = None,
        contributors: list[int] = None,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_all(self):
        raise NotImplementedError

    @abstractmethod
    def get(self, projectId: int) -> object:
        raise NotImplementedError

    @abstractmethod
    def update_info(self, projectId: int, attributesToUpdate: dict) -> None:
        raise NotImplementedError
    
    @abstractmethod
    def delete(self, projectId: int) -> None:
        raise NotImplementedError    
