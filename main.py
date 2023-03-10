#!/usr/bin/env python
# pylint: disable=unused-argument, wrong-import-position
# This program is dedicated to the public domain under the CC0 license.

"""Simple inline keyboard bot with multiple CallbackQueryHandlers.

This Bot uses the Application class to handle the bot.
First, a few callback functions are defined as callback query handler. Then, those functions are
passed to the Application and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.
Usage:
Example of a bot that uses inline keyboard that has multiple CallbackQueryHandlers arranged in a
ConversationHandler.
Send /start to initiate the conversation.
Press Ctrl-C on the command line to stop the bot.
"""
import logging
import os.path

from telegram import __version__ as TG_VER

try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {TG_VER}. To view the "
        f"{TG_VER} version of this example, "
        f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
    )
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler, MessageHandler, filters,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG
)
logger = logging.getLogger(__name__)

# Stages
IDLE, WAIT_FOR_ADMIN, WAIT_FOR_SELECT_ROOM, SET_QUEST = range(4)
# Callback data
ONE, TWO, THREE, FOUR = range(4)


def file_exist():
    return os.path.exists("quests.txt")


def load_from_file():
    with open("quests.txt", "r", encoding="utf-8") as f:
        all_lines = f.read()
    return [f.strip() for f in all_lines.split("@@@") if f]


def clear_file():
    with open("quests.txt", 'w', encoding="utf-8"):
        pass


def add_to_file(text):
    with open("quests.txt", "a", encoding="utf-8") as f:
        f.write(f"@@@ {text}\n")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send message on `/start`."""
    # Get user that sent /start and log his name
    logger.info("User started the conversation.")
    # Build InlineKeyboard where each button has a displayed text
    # and a string as callback_data
    # The keyboard is a list of button rows, where each row is in turn
    # a list (hence `[[...]]`).
    if update.effective_user.id == 711094148 or update.effective_user.id == 1:
        keyboard = [
            [
                InlineKeyboardButton("Нова гра", callback_data="new_game")
            ], [
                InlineKeyboardButton("Додадти завдання", callback_data="add_quest")
            ], [
                InlineKeyboardButton("Переглянути завдання", callback_data="show_quests")
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        # Send message with text and appended InlineKeyboard
        await context.bot.send_message(update.effective_chat.id, "Start handler, Choose a route", reply_markup=reply_markup)
        return WAIT_FOR_ADMIN
    else:
        keyboard = []
        quests = load_from_file()
        for i in range(len(quests)):
            keyboard.append([InlineKeyboardButton(str(i+1), callback_data=f"{i}")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        # Send message with text and appended InlineKeyboard
        await context.bot.send_message(update.effective_chat.id, "Обери свою команду", reply_markup=reply_markup)
        return WAIT_FOR_SELECT_ROOM


async def new_game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show new choice of buttons"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Нову гру створенно!")
    clear_file()
    return await start(update, context)


async def add_quest(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show new choice of buttons"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Напиши текст завдання")
    return SET_QUEST


async def set_quest(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    message = update.message.text
    add_to_file(message)
    return await start(update, context)


async def show_quests(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show new choice of buttons"""
    query = update.callback_query
    await query.answer()
    if file_exist():
        quests = load_from_file()
        if len(quests):
            await query.edit_message_text("Твої завдання:")
            for quest_n in range(len(quests)):
                await context.bot.send_message(update.effective_chat.id, f"{quest_n + 1}\n {quests[quest_n]}")
        else:
            await query.edit_message_text("В тебе поки що немає створенних завдань")
    else:
        await query.edit_message_text("Запусти нову гру")
    return await start(update, context)


async def select_room(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show new choice of buttons"""
    query = update.callback_query
    await query.answer()
    task = int(query.data)
    quests = load_from_file()
    await query.edit_message_text(f"Завдання твоєї команди({task + 1}):\n{quests[task]}")
    return IDLE


async def end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Returns `ConversationHandler.END`, which tells the
    ConversationHandler that the conversation is over.
    """
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text="See you next time!")
    return ConversationHandler.END


prefix_path = '.'


def main() -> None:
    with open(f"{prefix_path}/key", "r", encoding="utf-8") as f:
        token = f.read()
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(token).build()

    # Setup conversation handler with the states FIRST and SECOND
    # Use the pattern parameter to pass CallbackQueries with specific
    # data pattern to the corresponding handlers.
    # ^ means "start of line/string"
    # $ means "end of line/string"
    # So ^ABC$ will only allow 'ABC'
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            WAIT_FOR_SELECT_ROOM: [
                CallbackQueryHandler(select_room),
            ],
            WAIT_FOR_ADMIN: [
                CallbackQueryHandler(new_game, pattern="^new_game$"),
                CallbackQueryHandler(add_quest, pattern="^add_quest$"),
                CallbackQueryHandler(show_quests, pattern="^show_quests$")
            ],
            SET_QUEST: [
                MessageHandler(filters.TEXT, set_quest)
            ]
        },
        fallbacks=[CommandHandler("start", start)],
    )

    # Add ConversationHandler to application that will be used for handling updates
    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()
