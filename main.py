import settings
from handler import *
import random


def main():
    try:
        log("Starting...")
        handler = Handler(
            settings.username,
            settings.password,
            settings.content_id,
            settings.author_id,
            settings.words_blacklist,
            settings.users_blacklist,
            settings.users_whitelist,
            settings.links_blacklist
        )
        log("Working..")

        while True:
            time.sleep(random.randint(settings.checking_interval_sec_min, settings.checking_interval_sec_max))
            handler.parse_comments()
    except (KeyboardInterrupt, SystemExit):
        log("Shutting down")


if __name__ == "__main__":
    main()
