import asyncio
import inspect
import os
import sys
from datetime import datetime, timedelta

import telegram
from kubernetes import client, config
from telegram import Bot
from telegram.ext import ApplicationBuilder

from polarlight_notifier import polarlicht
from polarlight_notifier.logger import create_logger
from polarlight_notifier.state import ConfigmapState

config.load_config()
kubernetes_api_client = client.CoreV1Api()
_state = ConfigmapState(kubernetes_api_client, {})
_state.initialize()


def getenv_or_die(env_variable: str):
    # if we have no frame then we're probably in deep trouble
    logger = create_logger(inspect.currentframe().f_code.co_name)  # type: ignore
    if token := os.getenv(env_variable):
        return token

    logger.error(f"failed to retrieve token from environment (`{env_variable}`)")
    sys.exit(1)


async def send_chance(chance: str, chat_id: str, bot: telegram.Bot):
    message = f"Aktuelle Polarlicht-Wahrscheinlichkeit ist {chance}"
    await bot.send_message(chat_id=chat_id, text=message)


async def send_error(message: str, chat_id: str, bot: telegram.Bot):
    await bot.send_message(chat_id=chat_id, text=message)


def should_notify() -> bool:
    last_update = _state.get("last_update")
    now = datetime.now()
    if not last_update:
        create_logger("should_notify").debug("notify and initialize state")
        _state["last_update"] = str(now.timestamp())
        _state.write()
        return True
    notify_timeout = int(os.getenv("NOTIFY_TIMEOUT_MINUTES") or "1440")

    last_update_time = datetime.fromtimestamp(float(last_update))
    cutoff = now + timedelta(minutes=notify_timeout)

    if cutoff <= last_update_time:
        create_logger("should_notify").debug("notify and update state")
        _state["last_update"] = str(now.timestamp())
        _state.write()
        return True
    else:
        return False


async def main():
    # if we have no frame then we're probably in deep trouble
    logger = create_logger(inspect.currentframe().f_code.co_name)  # type: ignore
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
        logger.debug(f"found change: {chance}")
        if chance.lower() in notify_on_values:
            if should_notify():
                await send_chance(chance, chat_id, bot)
            else:
                logger.info("skip `send_chance` due to notification timeout")
    except polarlicht.MissingChanceException:
        logger.error("missing chance", exc_info=True)
        await send_error("missing chance", notifier_id, bot)


if __name__ == "__main__":
    asyncio.run(main())
