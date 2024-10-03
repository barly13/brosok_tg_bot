from enum import Enum


class AbsenceReasons(Enum):
    NoReason = ('no_reason', 'Работа')
    Vacation = ('vacation', 'Отпуск')
    Sickness = ('sickness', 'Больничный')
    BusinessTrip = ('business_trip', 'Командировка')

    def __init__(self, callback_info: str, desc: str):
        self.callback_info = callback_info
        self.desc = desc

    @classmethod
    def get_description_from_callback_info(cls, callback_info: str) -> str:
        for absence_reason in cls:
            if absence_reason.callback_info == callback_info:
                return absence_reason.desc

        return cls.NoReason.desc
