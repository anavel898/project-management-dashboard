from abc import ABC, abstractmethod


class ProjectHandlerInterface(ABC):

    @abstractmethod
    def create(
        self,
        name: str,
        created_by: str,
        description: str
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_all(self) -> dict[int, object]:
        raise NotImplementedError

    @abstractmethod
    def get(self, project_id: int) -> object:
        raise NotImplementedError

    @abstractmethod
    def update_info(self, project_id: int, attributesToUpdate: dict) -> object:
        raise NotImplementedError
    
    @abstractmethod
    def delete(self, project_id: int) -> None:
        raise NotImplementedError    
