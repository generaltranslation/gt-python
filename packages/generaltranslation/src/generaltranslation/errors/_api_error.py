class ApiError(Exception):
    def __init__(self, error: str, code: int, message: str):
        super().__init__(error)
        self.code = code
        self.message = message
