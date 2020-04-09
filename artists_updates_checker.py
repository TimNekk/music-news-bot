# - *- coding: utf- 8 - *-
import requests
from bs4 import BeautifulSoup as BS
import pickle


def check_artists_updates():
    artists = get_artists()  # Получить артистов
    albums = []

    for artist_name in artists:
        artist = artists[artist_name]

        # Если нет кол-ва альбомов
        if artist['albums'] == 0:
            artist['albums'] = len(get_albums_urls(artist['url']))  # Установить текущее кол-во альбомов
            save_artists(artists)
            continue

        current_albums = get_albums_urls(artist['url'])  # Текущее кол-во альбомов
        if artist['albums'] < len(current_albums) or True:
            albums_to_check = len(current_albums) - artist['albums']

            for album_index in range(albums_to_check):
                album_url = current_albums[album_index]
                album = get_album_info(album_url)
                album['users'] = artist['users']
                album['url'] = album_url
                albums.append(album)

    return albums


def get_album_info(album_url):
    album = {}

    r = requests.get(album_url)
    soup = BS(r.content, 'html.parser')

    album['mode'] = soup.select('.stamp__entity')[0].text
    album['name'] = soup.select('h1')[0].text
    album['artist'] = soup.select('a.d-link')[0].text
    album['img'] = 'http:' + soup.select('.entity-cover__image')[0]['src'][:-7] + '1000x1000'
    album['songs'] = []

    songs_divs = soup.select('.d-track')
    for song_div in songs_divs:
        try:
            song = song_div.select('.d-track_inline-meta .d-track__title, .d-track_inline-meta .d-track__version')[0].text
            album['songs'].append(song)
        except Exception as e:
            print(f'{e}\n\n{album}')
            continue

    return album


def get_albums_urls(artist_url):
    r = requests.get(artist_url + '/albums')
    soup = BS(r.content, 'html.parser')
    sopu_albums = soup.select('.album')
    albums = []
    for album in sopu_albums:
        url = 'https://music.yandex.ru' + album.select('.d-link')[0]['href']
        albums.append(url)

    return albums


# ---------------------------------------------------------------
# Работа с artists.txt
# ---------------------------------------------------------------


def create_artist():
    artist = {'users': [], 'albums': 0}
    return artist


def delete_artist(artist):
    artists = get_artists()
    artists.pop(artist['name'])
    save_artists(artists)


def save_artists(artists):
    with open('artists.txt', 'wb') as file:
        pickle.dump(artists, file)


def get_artists():
    with open('artists.txt', 'rb') as file:
        artists = pickle.load(file)
        return artists


def reset_artists_file():
    with open('artists.txt', 'wb') as file:
        pickle.dump({}, file)
    print('artists.txt reset')
