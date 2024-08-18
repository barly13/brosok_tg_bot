class Response:
    def __init__(self, value=None, message: str | None = None, error: bool = False):
        self.value = value
        self.message = message
        self.error = error
