from enum import Enum


class AbsenceReasons(Enum):
    NoReason = (0, 'Работа')
    Vacation = (1, 'Отпуск')
    SickLeave = (2, 'Больничный')
    BusinessTrip = (3, 'Командировка')

    def __init__(self, num: int, desc: str):
        self.num = num
        self.desc = desc

    @classmethod
    def get_desc_from_num(cls, num: int) -> str:
        for absence_reason in cls:
            if absence_reason.num == num:
                return absence_reason.desc

        return cls.NoReason.desc

