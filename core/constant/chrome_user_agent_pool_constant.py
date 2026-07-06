CORE_LOGGER_NAME_STR = "n_user_agent_pool"
PACKAGE_USER_AGENT_STR = "n-user-agent-pool/0.1.0"

CHROME_FOR_TESTING_LATEST_PATCH_VERSION_URL_STR = (
    "https://googlechromelabs.github.io/chrome-for-testing/"
    "latest-patch-versions-per-build.json"
)
CHROME_FOR_TESTING_LAST_KNOWN_GOOD_VERSION_URL_STR = (
    "https://googlechromelabs.github.io/chrome-for-testing/"
    "last-known-good-versions.json"
)

DEFAULT_TIMEOUT_SECOND_INT = 10
DEFAULT_USER_AGENT_COUNT_INT = 1
MAX_CHROME_VERSION_COUNT_INT = 24

CHROME_FOR_TESTING_BUILDS_KEY_STR = "builds"
CHROME_FOR_TESTING_CHANNELS_KEY_STR = "channels"
CHROME_FOR_TESTING_VERSION_KEY_STR = "version"

CHROME_RELEASE_CHANNEL_LIST = ["Stable", "Beta", "Dev", "Canary"]
DEFAULT_CHROME_RELEASE_CHANNEL_STR = "Stable"

CHROME_USER_AGENT_TEMPLATE_STR = (
    "Mozilla/5.0 ({platformFragment}) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/{chromeVersion} Safari/537.36"
)

SUPPORTED_DESKTOP_PLATFORM_FRAGMENT_BY_FAMILY_DICT = {
    "Windows": [
        "Windows NT 10.0; Win64; x64",
        "Windows NT 10.0; WOW64",
        "Windows NT 10.0; ARM64",
    ],
    "macOS": [
        "Macintosh; Intel Mac OS X 10_15_7",
        "Macintosh; Intel Mac OS X 11_7_10",
        "Macintosh; Intel Mac OS X 12_7_6",
        "Macintosh; Intel Mac OS X 13_6_9",
        "Macintosh; Intel Mac OS X 14_7_1",
        "Macintosh; Intel Mac OS X 15_2",
    ],
    "Linux": [
        "X11; Linux x86_64",
        "X11; Ubuntu; Linux x86_64",
        "X11; Fedora; Linux x86_64",
        "X11; Debian; Linux x86_64",
        "X11; Linux aarch64",
        "X11; Linux armv7l",
    ],
}

SUPPORTED_DESKTOP_PLATFORM_FRAGMENT_LIST = [
    "Windows NT 10.0; Win64; x64",
    "Windows NT 10.0; WOW64",
    "Windows NT 10.0; ARM64",
    "Macintosh; Intel Mac OS X 10_15_7",
    "Macintosh; Intel Mac OS X 11_7_10",
    "Macintosh; Intel Mac OS X 12_7_6",
    "Macintosh; Intel Mac OS X 13_6_9",
    "Macintosh; Intel Mac OS X 14_7_1",
    "Macintosh; Intel Mac OS X 15_2",
    "X11; Linux x86_64",
    "X11; Ubuntu; Linux x86_64",
    "X11; Fedora; Linux x86_64",
    "X11; Debian; Linux x86_64",
    "X11; Linux aarch64",
    "X11; Linux armv7l",
]

KEY_VAL_BASE_URL_ENV_STR = "KEY_VAL_BASE_URL"
KEY_VAL_AUTH_TOKEN_ENV_STR = "KEY_VAL_AUTH_TOKEN"
KEY_VAL_HTTP_GET_METHOD_STR = "GET"
KEY_VAL_HTTP_PUT_METHOD_STR = "PUT"
KEY_VAL_JSON_CONTENT_TYPE_STR = "application/json"
KEY_VAL_TEXT_CONTENT_TYPE_STR = "text/plain; charset=utf-8"
KEY_VAL_AUTHORIZATION_HEADER_STR = "Authorization"
KEY_VAL_KEY_HASH_ALGORITHM_STR = "sha256"

KEY_VAL_USER_AGENT_LIST_KEY_STR = "n_user_agent_pool_latest_user_agent_list"
KEY_VAL_LAST_RANDOM_USER_AGENT_KEY_STR = "n_user_agent_pool_last_random_user_agent"
KEY_VAL_CHANNEL_VERSION_MAP_KEY_STR = "n_user_agent_pool_channel_version_map"

USER_AGENT_LIST_JSON_KEY_STR = "userAgentList"
USER_AGENT_JSON_KEY_STR = "userAgent"
CHANNEL_VERSION_MAP_JSON_KEY_STR = "channelVersionMap"
