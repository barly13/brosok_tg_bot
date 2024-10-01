from enum import Enum


class Emoji(Enum):
    Error = '❌'
    Success = '✅'
    Warning = '⚠️'
    FourAndHalfAM = '🕟'
    SixAM = '🕕'
    TwoAM = '🕑'
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
    MakerEmoji = '👷🏼‍♂️'
    PenEmoji = '🖊️'
    WrenchEmoji = '🔧'
    CalendarEmoji = '📅'
    RightArrowEmoji = '➡️'
    DownArrowEmoji = '⬇️'
    CheckMarkEmoji = '📌'

    def __str__(self):
        return self.value
