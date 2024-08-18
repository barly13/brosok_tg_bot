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
    EmployeeEmoji = '🧑‍💻'
    PenEmoji = '🖊️'
    WrenchEmoji = '🔧'

    def __str__(self):
        return self.value
