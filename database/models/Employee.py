from sqlalchemy import Column, String, Float, JSON, update
from typing import List

from tg_bot.routers.reports.backend.absence_reasons_enum import AbsenceReasons
from .BaseModel import BaseModel
from ..session_controller import session_controller


class Employee(BaseModel):
    __tablename__ = 'employee'

    full_name = Column(String, nullable=False, unique=True)
    position = Column(String, nullable=False)
    working_rate = Column(Float, nullable=False)
    absence_reason = Column(String, nullable=False, default=AbsenceReasons.NoReason.desc)

    @classmethod
    def update_all_absence_reasons(cls):
        session = session_controller.get_session()

        all_employees = cls.get_all()

        for employee in all_employees:
            absence_reason = employee.absence_reason
            if '|' in absence_reason:
                parts = absence_reason.split('|')
                updated_absence_reason = '|'.join(parts[1:])
                session.execute(
                    update(cls).where(cls.id == employee.id).values(absence_reason=updated_absence_reason)
                )
            else:
                session.execute(
                    update(cls).where(cls.id == employee.id).values(absence_reason=AbsenceReasons.NoReason.desc)
                )

        session.commit()
