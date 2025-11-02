from logic import DB_Manager
from config import *
from telebot import TeleBot
import sqlite3

bot = TeleBot(TOKEN)

user_state = {}

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, 
        "Привет! Я бот-викторина.\n\n"
        "1. /register — зарегистрироваться\n"
        "2. /question — получить вопрос\n"
        "3. /rating — топ игроков\n"
        "4. Отвечай текстом — +1 балл за правильный!"
    )

@bot.message_handler(commands=['register'])
def register(message):
    telegram_id = message.from_user.id
    name = message.from_user.full_name

    if manager.get_participant_id(telegram_id):
        bot.send_message(message.chat.id, f"Ты уже зарегистрирован как *{name}*!\n\n/question — начать", parse_mode="Markdown")
        return

    manager.add_participant(telegram_id, name)
    bot.send_message(message.chat.id, f"Ты зарегистрирован как *{name}*!\n\n/question — получить вопрос", parse_mode="Markdown")

@bot.message_handler(commands=['question'])
def question(message):
    telegram_id = message.from_user.id
    participant_id = manager.get_participant_id(telegram_id)

    if not participant_id:
        bot.send_message(message.chat.id, "Сначала /register")
        return

    problem = manager.get_random_unused_problem(participant_id)
    if not problem:
        bot.send_message(message.chat.id, "Ты ответил на все вопросы!")
        return
    
    user_state[telegram_id] = {"problem_id": problem[0]}
    manager.check_all_answers(participant_id)

    bot.send_message(message.chat.id, f"*Вопрос:*\n\n{problem[1]}\n\n_Напиши ответ_", parse_mode="Markdown")

@bot.message_handler(commands=['rating'])
def rating(message):
    top = manager.get_rating(10)
    if not top:
        bot.send_message(message.chat.id, "Рейтинг пуст. Будь первым!")
        return

    text = "*Топ-10 игроков:*\n\n"
    for i, (name, score) in enumerate(top, 1):
        text += f"{i}. {name} — *{score}* баллов\n"
    
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(func=lambda m: True)
def answer(message):
    user_id = message.from_user.id
    if user_id not in user_state:
        return

    problem_id = user_state[user_id]["problem_id"]
    user_answer = message.text.strip()

    is_correct = manager.check_answer(problem_id, user_answer)
    manager.save_answer(user_id, problem_id, user_answer, is_correct)

    if is_correct:
        bot.send_message(message.chat.id, "Правильно! +1 балл!")
    else:
        conn = sqlite3.connect(manager.database)
        cur = conn.cursor()
        cur.execute("SELECT correct_answer FROM Problems WHERE problem_id = ?", (problem_id,))
        correct = cur.fetchone()[0]
        conn.close()
        bot.send_message(message.chat.id, f"Неправильно.\nПравильный ответ: *{correct}*", parse_mode="Markdown")

    del user_state[user_id]
    bot.send_message(message.chat.id, "Ещё вопрос? — /question\n/rating — посмотреть топ")

if __name__ == '__main__':
    manager = DB_Manager()
    manager.del_table_problems()
    manager.create_tables()
    questions = [
        ("Посчитайте предметы: Сколько яблок будет, если у вас 3 красных яблока и 2 зеленых яблока?В ответе только цифра", "5"),
        ("Что дальше? 2, 4, 6, 8, ___", "10"),
        (" В честь кого названа теорема a² + b² = c²?", "пифагор"),
        ("47 + 38 = ?", "85"),
        ("3/4 - 1/2 = ?", "1/4"),
        ("1, 4, 9, 16, 25, ?", "36"),
        ("1, 1, 2, 3, 5, 8, ? ", "13"),
        ("Чему равен модуль числа -7,8?", "7,8"),
        ("В какую степень нужно возвести число 3, чтобы получить число 81?", "4"),
        ("Округлите десятичную дробь 3,65478 до сотых чисел.", "3,65"),
        ("Как называется отрезок, который соединяет две произвольные точки на окружности?", "хорда"),
        ("Что получится, если число 286 умножить на 0?", "0")

    ]
    for q, a in questions:
        manager.add_problem(q, a)
    bot.infinity_polling()
