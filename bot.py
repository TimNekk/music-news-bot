# - *- coding: utf- 8 - *-
import telebot
from telebot import types
import networking as nw
import pickle
import os
import artists_updates_checker as checker
from threading import Thread
from time import sleep
from colorama import Fore
import datetime

bot = telebot.TeleBot('1220887328:AAFjQdnTuwIRi7qg00PI9up6JOUDhjBqgwk')  # Установка токена бота
admins = [551019360]


def log(message, text):
    dt = datetime.datetime.strftime(datetime.datetime.now(), '[%d/%m/%y | %R]')
    print(f'{Fore.YELLOW}{dt} {Fore.BLUE}{message.chat.id}: {Fore.RESET}{text}')

# ---------------------------------------------------------------
# Обработчики сообщение
# ---------------------------------------------------------------


@bot.message_handler(commands=['start'])
def start_command(message):
    log(message, '/start')
    # Если новый пользователь
    users = get_users()
    if message.chat.id not in users:
        log(message, 'Новый пользователь')
        # Создание пользователся
        user = create_user()
        users[message.chat.id] = user
        save_users(users)

    text = 'Привет! Я музыкальный бот 😁\n'
    text += 'Я буду оповещать тебя о новинках твоих любимых исполнителей!\n\n'
    text += '/new - добавить нового артиста\n'
    text += '/list - артисты за которыми ты следишь\n'

    if message.chat.id in admins:
        text += '/users - список пользователей\n'
        text += '/reset - сброс файлов'

    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=['new'])
def new_command(message):
    log(message, '/new')
    # Если новый пользователь
    users = get_users()
    if message.chat.id not in users:
        log(message, 'Новый пользователь')
        # Создание пользователся
        user = create_user()
        users[message.chat.id] = user
        save_users(users)

    text = 'За каким артистом вы хотите следить?'
    msg = bot.send_message(message.chat.id, text)

    bot.register_next_step_handler(msg, send_artist)


@bot.message_handler(commands=['list'])
def list_command(message):
    log(message, '/list')
    # Если новый пользователь
    users = get_users()
    if message.chat.id not in users:
        log(message, 'Новый пользователь')
        # Создание пользователся
        user = create_user()
        users[message.chat.id] = user
        save_users(users)

    artists = users[message.chat.id]['artists']
    if artists:
        text = 'Список артистов за которыми вы сделите:\n\n'

        for i, artist in enumerate(artists, 1):
            text += f'{i}. {artist["name"]}\n'

        bot.send_message(message.chat.id, text, reply_markup=edit_artists_keyboard())
    else:
        text = 'Чтобы добавить артиста введите /new'

        bot.send_message(message.chat.id, text)


@bot.message_handler(commands=['users'])
def artists_command(message):
    log(message, '/users')
    # Если новый пользователь
    users = get_users()
    if message.chat.id not in users:
        log(message, 'Новый пользователь')
        # Создание пользователся
        user = create_user()
        users[message.chat.id] = user
        save_users(users)

    if message.chat.id in admins:
        users = get_users()

        text = f'Total users: {len(users)}\n\n'
        for user in users:
            user_data = users[user]
            text += f'chat_id: {user}\n'
            text += f'artists: {user_data["artists"]}\n'

        with open('info.txt', 'w') as file:
            file.write(text)
        with open('info.txt', 'r') as file:
            bot.send_document(message.chat.id, file)
        os.remove('info.txt')


@bot.message_handler(commands=['reset'])
def artists_command(message):
    log(message, '/reset')
    # Если новый пользователь
    users = get_users()
    if message.chat.id not in users:
        log(message, 'Новый пользователь')
        # Создание пользователся
        user = create_user()
        users[message.chat.id] = user
        save_users(users)

    if message.chat.id in admins:
        reset_users_file()
        checker.reset_artists_file()

        bot.send_message(message.chat.id, 'Файлы *users.txt* и *artists.txt* сброшены', parse_mode='Markdown')


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

    # След и пред страницы
    elif call.data == 'back_page':
        send_artists_list(call.message, k=-1, edit=True)
    elif call.data == 'next_page':
        send_artists_list(call.message, edit=True)

    elif call.data == 'edit_artists':
        edit_artists(call.message)


# ---------------------------------------------------------------
# Функции
# ---------------------------------------------------------------


def edit_artists(message):
    text = 'Отправте номер артиста, которого вы хотите *удалить*:\n\n'

    users = get_users()
    artists = users[message.chat.id]['artists']
    for i, artist in enumerate(artists, 1):
        text += f'{i}. {artist["name"]}\n'

    text += '\nОтправате *0* для отмены!'

    msg = bot.edit_message_text(text, message.chat.id, message.message_id, parse_mode='Markdown')

    bot.register_next_step_handler(msg, delete_artist)


def delete_artist(message):
    # Получить пользователя
    users = get_users()
    user = users[message.chat.id]

    answer = message.text
    if answer == '0':
        for i in range(2):
            bot.delete_message(message.chat.id, message.message_id - i)
        list_command(message)
        return

    try:
        artist_index = int(answer)
        if 1 <= artist_index <= len(user['artists']):
            # Удаление 2 предыдущих сообщений
            for i in range(2):
                bot.delete_message(message.chat.id, message.message_id - i)

            log(message, f"{user['artists'][artist_index - 1]['name']} удален")

            # Отправка сообщения
            text = f"Вы больше не следите за артистом *{user['artists'][artist_index - 1]['name']}*"
            bot.send_message(message.chat.id, text, parse_mode='Markdown')

            # Получение артиста из artists.txt
            saved_artists = checker.get_artists()  # Получить артистов
            saved_artist = saved_artists[user['artists'][artist_index - 1]['name']]
            saved_artist['users'].remove(message.chat.id)

            # Остались ли у артиста пользовтели
            if not saved_artist['users']:
                checker.delete_artist(user['artists'][artist_index - 1])

            # Удаление артиста у пользовтеля
            user['artists'].pop(artist_index - 1)
            save_users(users)

            return
    except ValueError:
        pass
    text = f'Нужно ввести число от *1* до *{len(user["artists"])}*'

    bot.send_message(message.chat.id, text, parse_mode='Markdown')


def add_artist(message, i):
    # Получить пользователя
    users = get_users()
    user = users[message.chat.id]

    if user['current_page'] == -1:  # Обнуление страницы
        user['current_page'] = 0
    artist = user['list'][user['current_page']][i]

    # Артист уже добавлен
    if artist in user['artists']:
        text = f'Вы уже следите за исполнителем *{artist["name"]}*'

        bot.delete_message(message.chat.id, message.message_id)  # Удаление предыдущего сообщения

        bot.send_message(message.chat.id, text, parse_mode='Markdown')

        return

    user['artists'].append(artist)  # Добавление ариста пользователю

    # Сброс даннхых списка и сраницы
    user['current_page'] = -1
    user['list'] = []
    save_users(users)

    saved_artists = checker.get_artists()  # Получить артистов
    # Если ли артист в artists.txt
    if artist['name'] not in saved_artists:
        saved_artist = checker.create_artist()
        saved_artist['url'] = artist['url']
    else:
        saved_artist = saved_artists[artist['name']]

    # Добавлен ли позльзователь к этому артисту
    if message.chat.id not in saved_artist['users']:
        saved_artist['users'].append(message.chat.id)
        saved_artists[artist['name']] = saved_artist

        checker.save_artists(saved_artists)

    bot.delete_message(message.chat.id, message.message_id)  # Удаление предыдущего сообщения

    log(message, artist["name"])

    # Отправка сообщения
    text = f'Теперь вы следите за исполнителем *{artist["name"]}*'
    bot.send_message(message.chat.id, text, parse_mode='Markdown')


def send_artist(message):
    # Обход ввода команды
    if message.text[0] == '/':
        return

    artist_name = message.text
    artists = nw.get_artists(artist_name)
    if artists == [[]]:
        text = 'Исполнителей с таким названием не найдено'
        bot.send_message(message.chat.id, text)
        return

    # Получить пользователя
    users = get_users()
    user = users[message.chat.id]
    user['list'] = artists
    user['current_page'] = -1
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


def edit_artists_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    b1 = types.InlineKeyboardButton('Редактировать ✏️', callback_data='edit_artists')
    keyboard.add(b1)
    return keyboard


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


def yandex_music_keyboard(url):
    keyboard = types.InlineKeyboardMarkup()
    b1 = types.InlineKeyboardButton('Яндекс Музыка', url=url)
    keyboard.add(b1)
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


# ---------------------------------------------------------------
# Artists updates checker
# ---------------------------------------------------------------


def start_checker_thread():
    Thread(target=artists_updates_checker).start()


def artists_updates_checker():
    while True:
        sleep(300)
        albums = checker.check_artists_updates()
        if albums:
            for album in albums:
                text = f"Новый {album['mode']} от *{album['artist']}*"

                if album['mode'] == 'Альбом':
                    text += f"\n*{album['name']}*\n\n"

                for i, song in enumerate(album['songs'], 1):
                    text += f"{i}. {song}\n"

                print(text)

                for user in album['users']:
                    bot.send_photo(user, album['img'], text, reply_markup=yandex_music_keyboard(album['url']), parse_mode='Markdown')


if __name__ == '__main__':
    # Существует ли users.txt
    try:
        if os.path.getsize('users.txt') == 0:
            reset_users_file()
    except FileNotFoundError:
        reset_users_file()

    # Существует ли artists.txt
    try:
        if os.path.getsize('artists.txt') == 0:
            checker.reset_artists_file()
    except FileNotFoundError:
        checker.reset_artists_file()

    bot.skip_pending = True
    print('Bot started successfully')
    start_checker_thread()
    bot.polling(none_stop=True, interval=2)

