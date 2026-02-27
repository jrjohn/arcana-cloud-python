"""
Base Repository Interface
Generic CRUD interface following the arcana-cloud-springboot BaseRepository<T,K> pattern.
"""
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List

T = TypeVar('T')
K = TypeVar('K')


class BaseRepository(ABC, Generic[T, K]):
    """
    Generic base Repository interface providing standard CRUD operations.

    Type Parameters:
        T: Entity type
        K: Primary key type
    """

    @abstractmethod
    def save(self, entity: T) -> T:
        """
        Save (create or update) an entity.

        Args:
            entity: Entity to save

        Returns:
            Saved entity (with ID populated for new entities)
        """
        pass

    @abstractmethod
    def find_by_id(self, id: K) -> Optional[T]:
        """
        Find an entity by its primary key.

        Args:
            id: Primary key value

        Returns:
            Entity if found, None otherwise
        """
        pass

    @abstractmethod
    def find_all(self) -> List[T]:
        """
        Retrieve all entities.

        Returns:
            List of all entities
        """
        pass

    @abstractmethod
    def count(self) -> int:
        """
        Count total number of entities.

        Returns:
            Total entity count
        """
        pass

    @abstractmethod
    def delete_by_id(self, id: K) -> bool:
        """
        Delete an entity by its primary key.

        Args:
            id: Primary key value

        Returns:
            True if deleted successfully, False if entity not found
        """
        pass

    @abstractmethod
    def exists_by_id(self, id: K) -> bool:
        """
        Check whether an entity with the given primary key exists.

        Args:
            id: Primary key value

        Returns:
            True if entity exists, False otherwise
        """
        pass
