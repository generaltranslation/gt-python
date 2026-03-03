"""Main GT class."""


class GT:
    """General Translation core driver class."""

    def __init__(
        self,
        *,
        api_key: str = "",
        project_id: str = "",
        base_url: str = "https://api.gtx.dev",
        source_locale: str = "en",
    ) -> None:
        self.api_key = api_key
        self.project_id = project_id
        self.base_url = base_url
        self.source_locale = source_locale
