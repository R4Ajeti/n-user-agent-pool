class ChromeUserAgentPoolError(Exception):
    pass


class ChromeUserAgentPoolUnavailableError(ChromeUserAgentPoolError):
    pass


class ChromeVersionPayloadError(ChromeUserAgentPoolError):
    pass
