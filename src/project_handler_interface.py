from abc import ABC, abstractmethod


class ProjectHandlerInterface(ABC):

    @abstractmethod
    def create(
        self,
        name: str,
        createdBy: int,
        description: str
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_all(self) -> dict[int:object]:
        raise NotImplementedError

    @abstractmethod
    def get(self, projectId: int) -> object:
        raise NotImplementedError

    @abstractmethod
    def update_info(self, projectId: int, attributesToUpdate: dict) -> object:
        raise NotImplementedError
    
    @abstractmethod
    def delete(self, projectId: int) -> None:
        raise NotImplementedError    
