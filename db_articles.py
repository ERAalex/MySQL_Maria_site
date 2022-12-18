import psycopg2
import psycopg2.extras
from flask import request, flash

# conn = psycopg2.connect(dbname="maria", user="alex", password="nazca007", host="localhost")
conn = psycopg2.connect(dbname="maria", user="alex", password="nazca007", host="db_postgres")


###### БЛОК ПО ИЗМЕНЕНИЮ В БАЗЕ ДАННЫХ СТАТЕЙ ТЕКСТОВ ######


def art_all_information():
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    s = "SELECT * FROM art3"
    cur.execute(s)  # Execute the SQL
    list_users = cur.fetchall()
    return list_users


def art_add_article():
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if request.method == 'POST':
        position = request.form['position']
        name = request.form['name']
        text = request.form['text']
        cur.execute("INSERT INTO art3 (position, name, text) VALUES (%s,%s,%s)", (position, name, text))
        conn.commit()
        return flash('Article Added successfully, EspinosaAlex')


def art_get_article(id):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute('SELECT * FROM art3 WHERE id = %s', (id,))
    data = cur.fetchall()
    cur.close()
    total = data[0]
    return total


def art_update_article(id):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if request.method == 'POST':
        position = request.form['position']
        name = request.form['name']
        text = request.form['text']

        cur.execute("""
            UPDATE art3
            SET position = %s,
                name = %s,
                text = %s
            WHERE id = %s
        """, (position, name, text, id))
        conn.commit()
        return flash('Article Updated Successfully, EspinosaAlex')


def art_delete_article(id):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute('DELETE FROM art3 WHERE id = {0}'.format(id))
    conn.commit()
    return flash('Student Removed Successfully')




###### БЛОК ПО ИЗМЕНЕНИЮ В БАЗЕ ДАННЫХ ФОТОГРАФИЙ ######














