import logging
import os

from .models.BaseModel import Base
from .session_controller import session_controller


class DBManager:
    def __init__(self):
        self.root_dir = None

    def init(self, root_dir: str = '.'):
        self.root_dir = root_dir

    @staticmethod
    def get_session():
        return session_controller.get_session()

    @staticmethod
    def __default_db_name() -> str:
        return 'database.db'

    def start_app(self, db_file_name: str = '') -> bool:
        try:
            if db_file_name == '' or db_file_name is None:
                db_file_name = self.__default_db_name()

            db_path = os.path.abspath(os.path.join(self.root_dir, db_file_name))
            if os.path.isfile(db_path):
                session_controller.set_session(db_path)
            else:
                engine = session_controller.set_session(db_path)
                Base.metadata.create_all(bind=engine)
                return True

        except BaseException as exc:
            logging.error(f'Не удалось запустить БД-менеджер. {exc}')
            return False


db_manager = DBManager()