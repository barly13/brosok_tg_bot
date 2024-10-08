from sqlalchemy import Column, String, Float, JSON, update
from typing import List
from datetime import datetime

from tg_bot.routers.reports.backend.absence_reasons_enum import AbsenceReasons
from .BaseModel import BaseModel
from ..session_controller import session_controller


class Employee(BaseModel):
    __tablename__ = 'employee'

    full_name = Column(String, nullable=False, unique=True)
    position = Column(String, nullable=False)
    working_rate = Column(Float, nullable=False)
    absence_reason = Column(String, nullable=False, default=AbsenceReasons.NoReason.desc)
    # absence_period_or_dates = Column(JSON, nullable=False, default={'no_data': ''})

    @classmethod
    def update_all_absence_reasons(cls):
        session = session_controller.get_session()
        session.execute(
            update(cls).values(absence_reason=AbsenceReasons.NoReason.desc)
        )

        session.commit()
