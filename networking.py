# - *- coding: utf- 8 - *-
import requests
from bs4 import BeautifulSoup as BS

urls = {'search': 'https://music.yandex.ru/search'}


def get_artists(artist_name):
    params = {'text': artist_name, 'type': 'artists'}
    r = requests.get(urls['search'], params=params)

    soup = BS(r.content, 'html.parser')
    soup_artists = soup.select('.artist__content')

    artists = []
    page = []
    for artist in soup_artists:
        if len(page) < 10:
            artist = {'name': get_artist_name(artist), 'url': get_artist_url(artist), 'img': get_artist_url(artist)}
            page.append(artist)
        else:
            artists.append(page)
            page = []
    artists.append(page)
    return artists


def get_artist_img_url(artist):
    img_url = 'http:' + artist.select('.artist-pics__pic')[0]['src']
    return img_url


def get_artist_name(artist):
    name = artist.select('.d-link')[0].text
    return name


def get_artist_url(artist):
    url = 'https://music.yandex.ru' + artist.select('.d-link')[0]['href']
    return url


if __name__ == '__main__':
    artists = get_artists('моргенштерн')
    for artist in artists:
        print(get_artist_url(artist))