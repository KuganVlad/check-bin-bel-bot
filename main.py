from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram import executor
import resources
import sqlite3
import logging

logging.basicConfig(filename='bot.log', level=logging.ERROR,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')



# Создание соединения с базой данных
conn = sqlite3.connect('belbin.db')
cursor = conn.cursor()

# Создание таблицы
cursor.execute('''
    CREATE TABLE IF NOT EXISTS cards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bin TEXT UNIQUE,
        type_card TEXT,
        dop_type_card TEXT,
        bank TEXT
    )
''')

class YourState(StatesGroup):
    wait_bin_number = State()

import configparser

config = configparser.ConfigParser()
config.read("config.ini")
TOKEN = config['Telegram']['bot_token']

storage = MemoryStorage()
bot = Bot(token=f'{TOKEN}')
dp = Dispatcher(bot, storage=storage)


def get_bank(bin_number):
    conn = sqlite3.connect('belbin.db')
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM cards WHERE bin LIKE '%{bin_number}%' ")
    result = cursor.fetchall()
    conn.commit()
    conn.close()
    return result


@dp.message_handler(commands=['start'])
async def start_question(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = [
        "Новый запрос",
        ]
    keyboard.add(*buttons)
    await message.answer("Привет! Для получения информации по BIN нажмите 'Новый запрос' или перейдите в раздел помощи (/help)", reply_markup=keyboard)


@dp.message_handler(commands=['help'])
async def start_question(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = [
        "Новый запрос",
    ]
    keyboard.add(*buttons)
    await message.answer("Данный бот, позволяет получить информацию о принадлежности банковской платёжной карты к "
                         "банку осуществляющему свою деятельность на территории Республики Беларусь по BIN номеру"
                         "При возникновении каких-либо проблем или наличии предложений свяжитесь с разработчиком"
                         "https://t.me/ulad_ku", reply_markup=keyboard)

@dp.message_handler()
async def handle_button_click(message: types.Message):
    if message.text == "Новый запрос":
        await YourState.wait_bin_number.set()
        await message.answer(
            f"Введите первые 6 цифр номера банковской платёжной карты.\n"
            f"В случае отсутствия ответа, повторите запрос и введите первые 8 цифр номера банковской платёжной карты, "
            f"в виду принадлежности данной количества цифр к платёжной системе 'Белкарт'")
    else:
        await message.answer("Неизвестная команда")

# Функция для обработки ввода количества популярных новостей
@dp.message_handler(state=YourState.wait_bin_number)
async def process_count_pop_news(message: types.Message, state: FSMContext):
    try:
        count = int(message.text)
        if count > 0:
            if len(str(count)) < 10:
                result = get_bank(message.text)
                if result:
                    for i in result:
                        get_bin = i[1]
                        if i[2] != '':
                            get_type = i[2]
                        else:
                            get_type = "неизвестна"
                        if i[3] != '':
                            get_dop_type = i[3]
                        else:
                            get_dop_type = "нет"
                        get_bank_name = i[4]
                    await message.answer(f"Карта с bin номером {get_bin} эмитирована {get_bank_name}. \nПлатёжная система карты: {get_type}. Дополнительные сведения: {get_dop_type}")
                else:
                    await message.answer("Информация о пренадлежности отсутствует")
            else:
                await message.answer("Количество символов должно быть меньше 8")
        else:
                await message.answer("Следующий раз, введите число, больше нуля.")
    except ValueError:
        await message.answer("Неверный формат числа. Следующий раз, введите целое число.")

    await state.finish()


# Функция для вставки данных в таблицу
def insert_card(bin, type_card, dop_type_card, bank):
    cursor.execute('''
        INSERT OR REPLACE INTO cards (bin, type_card, dop_type_card, bank)
        VALUES (?, ?, ?, ?)
    ''', (bin, type_card, dop_type_card, bank))






if __name__ == '__main__':
    for card in resources.data:
        insert_card(*card)

    # Сохранение изменений и закрытие соединения
    conn.commit()
    conn.close()
    while True:
        try:
            executor.start_polling(dp, timeout=60, skip_updates=True)
        except Exception as e:
            print(f"Error occurred: {e}")
            print("Restarting the bot...")