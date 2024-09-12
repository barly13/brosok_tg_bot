from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer
import threading

from database.session_controller import session_controller

Base = declarative_base()


class BaseModel(Base):
    __abstract__ = True
    id = Column(Integer, nullable=False, unique=True, primary_key=True, autoincrement=True)

    mutex = threading.Lock()

    @classmethod
    def create(cls, **kwargs):
        try:
            session = session_controller.get_session()
            object_new = cls(**kwargs)
            session.add(object_new)
            session.commit()
            return object_new
        except Exception:
            return None

    @classmethod
    def delete(cls, object_id: int) -> bool:
        try:
            session = session_controller.get_session()
            obj = session.query(cls).get(object_id)
            if obj:
                session.delete(obj)
                session.commit()
                return True
            return False
        except Exception:
            return False

    @classmethod
    def update(cls, object_id: int, **kwargs) -> bool:
        try:
            session = session_controller.get_session()
            obj = session.query(cls).get(object_id)
            if obj:
                for attr_name in kwargs:
                    setattr(obj, attr_name, kwargs[attr_name])
                session.commit()
                return True
            return False
        except Exception:
            return False

    @classmethod
    def get_by_id(cls, id: int):
        with cls.mutex:
            session = session_controller.get_session()
            return session.query(cls).get(id)

    @classmethod
    def get_all(cls):
        with cls.mutex:
            session = session_controller.get_session()
            return session.query(cls).all()

    @classmethod
    def delete_all_data(cls):
        try:
            with cls.mutex:
                session = session_controller.get_session()
                session.query(cls).delete()
                session.commit()
        except Exception:
            session.rollback()
