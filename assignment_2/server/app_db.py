import json
import sqlite3
import requests

from flask import Flask, g
from flask_cors import CORS
from bs4 import BeautifulSoup as soup

app = Flask(__name__)
CORS(app)

DATABASE = 'my_database.sqlite'


def get_db():
    db_conn = getattr(g, '_database', None)
    if db_conn is None:
        db_conn = g._database = sqlite3.connect(DATABASE)
    return db_conn


def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.executescript(
            """CREATE TABLE IF NOT EXISTS TVShows
               (id integer primary key, 
               show text not null,
               episode text not null, 
               subtitles text,
               site text not null)"""
        )

        cursor.execute("SELECT * FROM TVShows")
        res = cursor.fetchall()
        if len(res) != 0:
            return

        parse_fanserials()


@app.route('/get_all')
def get_all():
    db_cursor = get_db().cursor()
    db_cursor.row_factory = sqlite3.Row
    db_cursor.execute("SELECT * From TVShows")
    result = db_cursor.fetchall()
    json_result = json.dumps([dict(row) for row in result])
    return json_result


"""
@app.route('/')
def init_site():
    parse_fanserials()
    # more sites
    return redirect('/get_all')
"""


def add_to_db(data, site):
    db = get_db()
    cursor = db.cursor()

    for row in data:
        query = f"INSERT INTO TVShows (show, episode, subtitles, site) VALUES (?, ?, ?, ?)"
        print(row["show"], row["episode"], row["subtitles"], site)
        cursor.execute(query, (row["show"], row["episode"], row["subtitles"], site,))
        db.commit()


def parse_fanserials():
    url = 'http://fanserials.auction/'
    page = requests.get(url)
    sp = soup(page.text, "html.parser")

    data = []
    containers = sp.findAll("div", {"class": "item-serial with-shadow"})
    for container in containers:
        name_raw = container.findAll("div", {"class": "field-title"})
        name = name_raw[0].text

        description_raw = container.findAll("div", {"class": "field-description"})
        episode = description_raw[0].text

        fields = container.findAll("div", {"class": "serial-translate"})
        subtitles_raw = fields[0].div.findAll("span")
        subs = ""
        for sub in subtitles_raw:
            # subs += sub.text + f": {url}" + sub.find("a").get("href")[1:] + "\n"
            subs += f'<a href=\"{url}' + sub.find("a").get("href")[1:] + "\">" + sub.text + "</a><br>"

        row = {
            'show': name,
            'episode': episode,
            'subtitles': subs
        }
        data.append(row)

    add_to_db(data, 'Fanserials')


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


if __name__ == '__main__':
    init_db()
    app.run()
