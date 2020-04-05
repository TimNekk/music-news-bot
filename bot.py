import telebot
from telebot import types
import networking as nw
import pickle
import os

bot = telebot.TeleBot('1220887328:AAFjQdnTuwIRi7qg00PI9up6JOUDhjBqgwk')  # Установка токена бота


# ---------------------------------------------------------------
# Обработчики сообщение
# ---------------------------------------------------------------


@bot.message_handler(commands=['new'])
def start_message(message):
    bot.send_chat_action(message.chat.id, "upload_photo")
    users = get_users()

    # Если новый пользователь
    if message.chat.id not in users:
        print('Новый пользователь')

        # Создание пользователся
        user = create_user()
        users[message.chat.id] = user
        save_users(users)

    text = 'За каким артистом вы хотите следить?'
    msg = bot.send_message(message.chat.id, text)

    bot.register_next_step_handler(msg, send_artist)


# ---------------------------------------------------------------
# Обработчик Callback
# ---------------------------------------------------------------


@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    # Список артистов
    if call.data == 'show_artists_list':
        bot.delete_message(call.message.chat.id, call.message.message_id)  # Удаление предыдущего сообщения
        send_artists_list(call.message)

    # Выбор артиста из списка
    elif call.data[:-1] == 'add_artist':
        add_artist(call.message, int(call.data[-1]))

    elif call.data == 'back_page':
        send_artists_list(call.message, k=-1, edit=True)
    elif call.data == 'next_page':
        send_artists_list(call.message, edit=True)


# ---------------------------------------------------------------
# Функции
# ---------------------------------------------------------------


def add_artist(message, i):
    # Получить пользователя
    users = get_users()
    user = users[message.chat.id]

    if user['current_page'] == -1:
        user['current_page'] = 0
    artist = user['list'][user['current_page']][i]

    user['artists'].append(artist)

    text = f'Теперь вы следите за исполнителем *{artist["name"]}*'

    user['current_page'] = -1
    user['list'] = []
    save_users(users)

    bot.delete_message(message.chat.id, message.message_id)  # Удаление предыдущего сообщения

    bot.send_message(message.chat.id, text, parse_mode='Markdown')


def send_artist(message):
    artist_name = message.text
    artists = nw.get_artists(artist_name)
    print(artists)
    if artists == [[]]:
        print(1)
        text = 'Исполнителей с таким названием не найдено'
        bot.send_message(message.chat.id, text)
        return

    # Получить пользователя
    users = get_users()
    user = users[message.chat.id]
    user['list'] = artists
    save_users(users)

    bot.send_photo(message.chat.id, artists[0][0]['img'], caption=f'*{artists[0][0]["name"]}*', parse_mode='Markdown',
                   reply_markup=artist_keyboard())


def send_artists_list(message, k=1, edit=False):
    # Получить пользователя
    users = get_users()
    user = users[message.chat.id]
    old_page = user['current_page']
    user['current_page'] += 1 * k
    save_users(users)

    if user['current_page'] < 0:
        user['current_page'] = old_page
        save_users(users)
        return
    try:
        artists = user['list'][user['current_page']]
    except IndexError:
        user['current_page'] = old_page
        save_users(users)
        return

    text = f'Результаты *{(user["current_page"] + 1) * 10 - 9}*-*{(user["current_page"] + 1) * 10}* из *{sum(list(map(lambda x: len(x), user["list"])))}*\n\n'
    for i, artist in enumerate(artists, 1):
        text += f'{i}. {artist["name"]}\n'

    if edit:
        bot.edit_message_text(text, message.chat.id, message.message_id, reply_markup=artists_list_keyboard(len(artists)), parse_mode='Markdown')

    else:
        bot.send_message(message.chat.id, text, reply_markup=artists_list_keyboard(len(artists)), parse_mode='Markdown')


# ---------------------------------------------------------------
# Клавиатуры
# ---------------------------------------------------------------


def artist_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    b1 = types.InlineKeyboardButton('✅', callback_data='add_artist0')
    b2 = types.InlineKeyboardButton('❌', callback_data='show_artists_list')
    keyboard.add(b1, b2)
    return keyboard


def artists_list_keyboard(count):
    bs = []
    for i in range(count):
        b = types.InlineKeyboardButton(f'{i + 1}', callback_data=f'add_artist{i}')
        bs.append(b)

    keyboard = types.InlineKeyboardMarkup()
    if count == 1:
        keyboard.row(bs[0])
    if count == 2:
        keyboard.row(bs[0], bs[1])
    if count == 3:
        keyboard.row(bs[0], bs[1], bs[2])
    if count == 4:
        keyboard.row(bs[0], bs[1], bs[2], bs[3])
    if count == 5:
        keyboard.row(bs[0], bs[1], bs[2], bs[3], bs[4])
    if count == 6:
        keyboard.row(bs[0], bs[1], bs[2], bs[3], bs[4])
        keyboard.row(bs[5])
    if count == 7:
        keyboard.row(bs[0], bs[1], bs[2], bs[3], bs[4])
        keyboard.row(bs[5], bs[6])
    if count == 8:
        keyboard.row(bs[0], bs[1], bs[2], bs[3], bs[4])
        keyboard.row(bs[5], bs[6], bs[7])
    if count == 9:
        keyboard.row(bs[0], bs[1], bs[2], bs[3], bs[4])
        keyboard.row(bs[5], bs[6], bs[7], bs[8])
    if count == 10:
        keyboard.row(bs[0], bs[1], bs[2], bs[3], bs[4])
        keyboard.row(bs[5], bs[6], bs[7], bs[8], bs[9])

    btn_back = types.InlineKeyboardButton('⬅️', callback_data='back_page')
    btn_next = types.InlineKeyboardButton('➡️', callback_data='next_page')
    btn_cross = types.InlineKeyboardButton('❌', callback_data='close')
    keyboard.add(btn_back, btn_cross, btn_next)

    return keyboard


# ---------------------------------------------------------------
# Работа с users.txt
# ---------------------------------------------------------------


def create_user():
    user = {'artists': [], 'list': [], 'current_page': -1}
    return user


def delete_user(message):
    users = get_users()
    users.pop(message.chat.id)
    save_users(users)


def save_users(users):
    with open('users.txt', 'wb') as file:
        pickle.dump(users, file)


def get_users():
    with open('users.txt', 'rb') as file:
        users = pickle.load(file)
        return users


def reset_users_file():
    with open('users.txt', 'wb') as file:
        pickle.dump({}, file)
    print('users.txt reset')


if __name__ == '__main__':
    try:
        # Существует ли users.txt
        if os.path.getsize('users.txt') == 0:
            reset_users_file()
    except FileNotFoundError:
        reset_users_file()

    reset_users_file()

    bot.skip_pending = True
    print('Bot started successfully')
    bot.polling(none_stop=True, interval=2)
