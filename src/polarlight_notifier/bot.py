import inspect
import os
import sys

import telegram
from telegram import Bot
from telegram.ext import ApplicationBuilder

from polarlight_notifier import polarlicht
from polarlight_notifier.logger import create_logger


def getenv_or_die(env_variable: str):
    # if we have no frame then we're probably in deep trouble
    logger = create_logger(inspect.currentframe().f_code.co_name)  # type: ignore
    if token := os.getenv(env_variable):
        return token

    logger.error(f"failed to retrieve token from environment (`{env_variable}`)")
    sys.exit(1)


def send_chance(chance: str, chat_id: str, bot: telegram.Bot):
    message = f"Aktuelle Polarlicht-Wahrscheinlichkeit ist {chance}"
    bot.send_message(chat_id=chat_id, message=message)


def send_error(message: str, chat_id: str, bot: telegram.Bot):
    bot.send_message(chat_id=chat_id, message=message)


def main():
    bot_token = getenv_or_die("TOKEN")
    application = ApplicationBuilder().token(bot_token).build()
    bot: Bot = application.bot

    chat_id = getenv_or_die("CHAT_ID")
    notifier_id = getenv_or_die("NOTIFIER_ID")
    notify_on_values = [
        value.strip().lower()
        for value in getenv_or_die("NOTIFY_ON_ALERT_CHANCE_VALUES").split(",")
    ]
    try:
        chance = polarlicht.get_probability()
        if chance.lower() in notify_on_values:
            send_chance(chance, chat_id, bot)
            send_chance(chance, notifier_id, bot)
    except polarlicht.MissingChanceException:
        send_error("missing chance", notifier_id, bot)


if __name__ == "__main__":
    main()
