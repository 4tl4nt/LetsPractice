#!/usr/bin/env python

import logging
import os.path

from os.path import isfile, join
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
logging.getLogger("hpack.hpack").setLevel(logging.INFO)
logger = logging.getLogger(__name__)


# Stages
IDLE, WAIT_FOR_ADMIN, WAIT_FOR_SELECT_ROOM, SET_QUEST, NEW_GAME, DEL_GAME, LOAD_GAME, DEL_QUEST = range(8)

MAIN_MENU_TEXT = "Ви війшли як адміністратор"

prefix_path = '.'
game_path = join(prefix_path, "games")


def get_all_files():
    return [f for f in os.listdir(game_path) if isfile(join(game_path, f))]


def load_from_file(file_name):
    with open(join(game_path, file_name), "r", encoding="utf-8") as f:
        all_lines = f.read()
    return [f.strip() for f in all_lines.split("@@@") if f]


def clear_file(file_name):
    with open(join(game_path, file_name), 'w+', encoding="utf-8"):
        pass


def remove_file(file_name):
    os.remove(join(game_path, file_name))


def add_to_file(file_name, text):
    with open(join(game_path, file_name), "a", encoding="utf-8") as f:
        f.write(f"@@@ {text}\n")


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.effective_user.id == 711094148 or update.effective_user.id == 1:
        return await admin_menu(update, context, False)
    else:
        return await user_menu(update, context)


async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, edit_query: bool, text: str = None) -> int:
    keyboard = [
        [
            InlineKeyboardButton("Нова гра", callback_data="new_game")
        ], [
            InlineKeyboardButton("Почати", callback_data="start_game"),
            InlineKeyboardButton("Зупинити", callback_data="stop_game")
        ], [
            InlineKeyboardButton("Загрузити гру", callback_data="load_game")
        ], [
            InlineKeyboardButton("Видалити гру", callback_data="del_game")
        ], [
            InlineKeyboardButton("Переглянути завдання", callback_data="show_quests")
        ], [
            InlineKeyboardButton("Видалити завдання", callback_data="del_quest")
        ], [
            InlineKeyboardButton("Додадти завдання", callback_data="add_quest")
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    if not text:
        if 'game_name' in context.bot_data:
            text = context.bot_data['game_name']
            if context.bot_data['state']:
                text += "(RUNNING)"
            else:
                text += "(STOPPED)"
        else:
            text = MAIN_MENU_TEXT
    if edit_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
    else:
        await context.bot.send_message(update.effective_chat.id, text, reply_markup=reply_markup)
    return WAIT_FOR_ADMIN


async def user_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = []
    if 'state' in context.bot_data and context.bot_data['state']:
        quests = load_from_file(context.bot_data['game_name'])
        for i in range(len(quests)):
            keyboard.append([InlineKeyboardButton(str(i+1), callback_data=f"{i}")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(update.effective_chat.id, "Обери свою команду", reply_markup=reply_markup)
        return WAIT_FOR_SELECT_ROOM
    else:
        await context.bot.send_message(update.effective_chat.id, "Гра ще не почалась...")
        return IDLE


async def game_not_selected_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await admin_menu(update, context, True, "Спочатку створи або загрузи гру")


async def start_game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if "game_name" in context.bot_data:
        context.bot_data["state"] = True
        await update.callback_query.edit_message_text("starting...")
        return await admin_menu(update, context, False)
    else:
        return await game_not_selected_menu(update, context)


async def stop_game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if "game_name" in context.bot_data:
        context.bot_data["state"] = False
        await update.callback_query.edit_message_text("stopping...")
        return await admin_menu(update, context, False)
    else:
        return await game_not_selected_menu(update, context)


async def new_game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show new choice of buttons"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Вигадай ім'я")
    return NEW_GAME


async def new_game_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show new choice of buttons"""
    clear_file(update.message.text)
    context.bot_data["game_name"] = update.message.text
    context.bot_data['state'] = False
    return await admin_menu(update, context, edit_query=False)


async def load_game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show new choice of buttons"""
    query = update.callback_query
    await query.answer()
    keyboard = []
    files = get_all_files()
    if len(files):
        for i in files:
            keyboard.append([InlineKeyboardButton(i, callback_data=f"load_game_{i}")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        # Send message with text and appended InlineKeyboard
        await query.edit_message_text("Обери гру", reply_markup=reply_markup)
        return LOAD_GAME
    else:
        return await admin_menu(update, context, True, "В тебе немає створенних ігор")


async def load_game_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show new choice of buttons"""
    query = update.callback_query
    await query.answer()
    context.bot_data["game_name"] = query.data[10:]
    context.bot_data['state'] = False
    await query.edit_message_text(f"Обрана гра: {context.bot_data['game_name']}")
    return await admin_menu(update, context, edit_query=False)


async def del_game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show new choice of buttons"""
    query = update.callback_query
    await query.answer()
    keyboard = []
    files = get_all_files()
    if len(files):
        for i in files:
            keyboard.append([InlineKeyboardButton(i, callback_data=f"del_game_{i}")])
        keyboard.append([InlineKeyboardButton("Назад", callback_data=f"back")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        # Send message with text and appended InlineKeyboard
        await query.edit_message_text("Обери непотрібну гру", reply_markup=reply_markup)
        return DEL_GAME
    else:
        return await game_not_selected_menu(update, context)


async def del_game_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show new choice of buttons"""
    query = update.callback_query
    await query.answer()
    del_file_name = query.data[9:]
    if 'game_name' in context.bot_data and context.bot_data['game_name'] == del_file_name:
        context.bot_data.pop('game_name')
    await query.edit_message_text(f"Видаляю {del_file_name}")
    remove_file(del_file_name)
    return await admin_menu(update, context, edit_query=False)


async def add_quest(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show new choice of buttons"""
    query = update.callback_query
    await query.answer()
    if "game_name" in context.bot_data:
        await query.edit_message_text("Напиши текст завдання")
        return SET_QUEST
    else:
        return await game_not_selected_menu(update, context)


async def set_quest(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    message = update.message.text
    add_to_file(context.bot_data["game_name"], message)
    return await admin_menu(update, context, edit_query=False)


async def del_quest(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show new choice of buttons"""
    query = update.callback_query
    await query.answer()
    keyboard = []
    files = get_all_files()
    if "game_name" in context.bot_data:
        quests = load_from_file(context.bot_data["game_name"])
        if len(quests):
            for quest_n in range(len(quests)):
                keyboard.append([InlineKeyboardButton(str(quest_n + 1), callback_data=f"del_quest_{quest_n}")])
            keyboard.append([InlineKeyboardButton("Назад", callback_data=f"back")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            # Send message with text and appended InlineKeyboard
            await query.edit_message_text("Обери непотрібне питання", reply_markup=reply_markup)
            return DEL_QUEST
        else:
            return await admin_menu(update, context, True, "В тебе поки що немає створенних завдань")
    else:
        return await game_not_selected_menu(update, context)


async def del_quest_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show new choice of buttons"""
    query = update.callback_query
    await query.answer()
    del_quest_n = int(query.data[10:])
    game_name = context.bot_data["game_name"]
    quests = load_from_file(game_name)
    quest = quests.pop(del_quest_n)
    await query.edit_message_text(f"Видаляю:\n{quest}")
    clear_file(game_name)
    for q in quests:
        add_to_file(game_name, q)
    return await admin_menu(update, context, edit_query=False)


async def show_quests(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show new choice of buttons"""
    query = update.callback_query
    await query.answer()
    if "game_name" in context.bot_data:
        quests = load_from_file(context.bot_data["game_name"])
        if len(quests):
            await query.edit_message_text("Твої завдання:")
            for quest_n in range(len(quests)):
                await context.bot.send_message(update.effective_chat.id, f"{quest_n + 1}\n {quests[quest_n]}")
            return await admin_menu(update, context, False)
        else:
            return await admin_menu(update, context, True, "В тебе поки що немає створенних завдань")
    else:
        return await game_not_selected_menu(update, context)


async def select_room(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show new choice of buttons"""
    query = update.callback_query
    await query.answer()
    task = int(query.data)
    quests = load_from_file(context.bot_data["game_name"])
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


async def back(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await admin_menu(update, context, edit_query=True)


async def call_wrong_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.message.delete()
    return ConversationHandler.END


def main() -> None:
    with open(f"{prefix_path}/key", "r", encoding="utf-8") as f:
        token = f.read()
    application = Application.builder().token(token).build()
    conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(call_wrong_query),
            CommandHandler("start", menu)
        ],
        states={
            WAIT_FOR_SELECT_ROOM: [
                CallbackQueryHandler(select_room),
            ],
            WAIT_FOR_ADMIN: [
                CallbackQueryHandler(new_game, pattern="^new_game$"),
                CallbackQueryHandler(start_game, pattern="^start_game$"),
                CallbackQueryHandler(stop_game, pattern="^stop_game$"),
                CallbackQueryHandler(del_game, pattern="^del_game$"),
                CallbackQueryHandler(load_game, pattern="^load_game$"),
                CallbackQueryHandler(add_quest, pattern="^add_quest$"),
                CallbackQueryHandler(del_quest, pattern="^del_quest$"),
                CallbackQueryHandler(show_quests, pattern="^show_quests$")
            ],
            SET_QUEST: [
                MessageHandler(filters.TEXT, set_quest)
            ],
            NEW_GAME: [
                MessageHandler(filters.TEXT, new_game_name)
            ],
            LOAD_GAME: [
                CallbackQueryHandler(load_game_selected, pattern="^load_game_.*")
            ],
            DEL_GAME: [
                CallbackQueryHandler(del_game_selected, pattern="^del_game_.*"),
                CallbackQueryHandler(back, pattern="^back$")
            ],
            DEL_QUEST: [
                CallbackQueryHandler(del_quest_selected, pattern="^del_quest_.*"),
                CallbackQueryHandler(back, pattern="^back$")
            ]
        },
        fallbacks=[
            CallbackQueryHandler(call_wrong_query),
            CommandHandler("start", menu)
        ],
    )

    application.add_handler(conv_handler)
    application.run_polling()


if __name__ == "__main__":
    main()
