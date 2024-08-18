from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session


class SessionController:
    def __init__(self):
        self.session = None
        self.engine = None

    def set_session(self, path):
        try:
            self.engine = create_engine(f'sqlite:///{path}')
            self.session = sessionmaker(bind=self.engine)()
            return self.engine
        except Exception:
            raise Exception('Не удалось изменить сессию. Укажите правильный путь до файла')

    def get_session(self) -> Session:
        return self.session


session_controller = SessionController()