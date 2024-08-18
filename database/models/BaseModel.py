from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer
import threading


Base = declarative_base()


class BaseModel(Base):
    __abstract__ = True
    id = Column(Integer, nullable=False, unique=True, primary_key=True, autoincrement=True)

    mutex = threading.Lock()

    def repr(self):
        return "<{0.class.name}(id={0.id!r})>".format(self)
