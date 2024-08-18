from sqlalchemy import Column, String, Float

from .BaseModel import BaseModel
from ..session_controller import session_controller


class Employee(BaseModel):
    __tablename__ = 'employee'

    full_name = Column(String, nullable=False, unique=True)
    position = Column(String, nullable=False)
    working_rate = Column(Float, nullable=False)

    @classmethod
    def get_by_id(cls, id: int):
        with cls.mutex:
            session = session_controller.get_session()
            return session.query(cls).filter_by(id=id).first()

    @classmethod
    def get_all(cls):
        with cls.mutex:
            session = session_controller.get_session()
            return session.query(cls).all()

