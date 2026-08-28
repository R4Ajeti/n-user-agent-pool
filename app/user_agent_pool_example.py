from core.service.verbose_chrome_user_agent_pool_service import (
    VerboseChromeUserAgentPoolService,
)


def main() -> None:
    verboseChromeUserAgentPoolService = VerboseChromeUserAgentPoolService()
    verboseChromeUserAgentPoolService.run()

    print("Final selected user-agent:", verboseChromeUserAgentPoolService.finalValueStr)
    print("Ranked user-agent list:", verboseChromeUserAgentPoolService.rankedUserAgentList)


if __name__ == "__main__":
    main()
