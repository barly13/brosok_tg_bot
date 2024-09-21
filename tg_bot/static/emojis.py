from enum import Enum


class Emoji(Enum):
    Error = '❌'
    Success = '✅'
    Point = '•'
    Warning = '⚠️'
    Waiting = '🕐'
    MainMenu = '🏠'
    ReportMenu = '🧾'
    ShowText = '👁'
    Start = '▶️'
    Stop = '⏸️'
    EditText = '✏️'
    Note = '📝'
    TechnicalSpecification = '📄'
    New = '🆕'
    RecordOn = '🔴'
    RecordOff = '⚪'
    Delete = '🗑️'
    Cancel = '❎'
    Picture = '🖼'
    RobotEmoji = '🤖'
    SicknessEmoji = '😷'
    VacationEmoji = '🌴'
    BusinessTripEmoji = '💼'
    EmployeeEmoji = '🧑‍💻'
    PenEmoji = '🖊️'
    WrenchEmoji = '🔧'
    CalendarEmoji = '📅'
    RightArrowEmoji = '➡️'
    DownArrowEmoji = '⬇️'
    CheckMarkEmoji = '📌'

    def __str__(self):
        return self.value
