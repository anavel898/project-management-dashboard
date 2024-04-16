from abc import ABC, abstractmethod


class ProjectHandlerInterface(ABC):

    @abstractmethod
    def create(
        self,
        name: str,
        created_by: str,
        description: str,
        db: object
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_all(self, db: object) -> dict[int, object]:
        raise NotImplementedError

    @abstractmethod
    def get(self, project_id: int, db: object) -> object:
        raise NotImplementedError

    @abstractmethod
    def update_info(self,
                    project_id: int,
                    attributes_to_update: dict,
                    db: object) -> object:
        raise NotImplementedError
    
    @abstractmethod
    def delete(self, project_id: int, db: object) -> None:
        raise NotImplementedError    
