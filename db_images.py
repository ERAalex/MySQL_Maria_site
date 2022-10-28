import psycopg2
import psycopg2.extras
from flask import request, flash
import os
from werkzeug.utils import secure_filename


conn = psycopg2.connect(dbname="maria", user="alex", password="nazca007", host="localhost")


def img_home():
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    s = "SELECT * FROM img_kat"
    cur.execute(s)
    list_img = cur.fetchall()
    return list_img


def img_upload_image(file1, file2):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    # сохраняем названия файлов для их поиска плюс сразу прописываем в имя файла весь путь, для href html
    filename = 'static/images/gallery/' + secure_filename(file1.filename)
    filename_big = 'static/images/gallery/' + secure_filename(file2.filename)

    position = request.form['position']
    name = request.form['name']
    text = request.form['text']

    cur.execute("INSERT INTO img_kat (position, name, text, file_name, file_name_big) VALUES (%s,%s,%s,%s,%s)",
                (position, name, text, filename, filename_big))
    conn.commit()
    return flash('Картинки успешно загружены. E.R.Alex')










