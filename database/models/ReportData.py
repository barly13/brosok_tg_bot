from sqlalchemy import Column, String, ForeignKey

from .BaseModel import BaseModel
from ..session_controller import session_controller


class ReportData(BaseModel):
    __tablename__ = 'report_data'

    employee_id = Column(ForeignKey('employee.id'), nullable=False)
    actual_performance = Column(String, nullable=False)
    obtained_result = Column(String, nullable=False)

    @classmethod
    def is_report_data_has_not_employee(cls, employee_id: int) -> bool:
        session = session_controller.get_session()
        return session.query(cls).filter_by(employee_id=employee_id).count() == 0
