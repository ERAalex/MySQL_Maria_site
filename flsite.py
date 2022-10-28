import mail
from flask import Flask, render_template, url_for, request, flash, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message

import email_validator
import psycopg2
import psycopg2.extras
import urllib.request
import os

from werkzeug.utils import secure_filename

from flask_security import SQLAlchemyUserDatastore
from flask_security import Security
from flask_security import UserMixin, RoleMixin
from flask_security import login_required

from db_articles import art_all_information, art_add_article, art_get_article



app = Flask(__name__)


app.config['SECRET_KEY'] = 'assdfweff3f24fvvmfl2330bfv2313kmfwemfweDDSDM243mdDAD56gg'
if 'SECURITY_PASSWORD_SALT' not in app.config:
    app.config['SECURITY_PASSWORD_SALT'] = app.config['SECRET_KEY']



# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://alex:nazca007@db_postgres:5432/maria'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://alex:nazca007@localhost:5432/maria'


# Создать объект подключения к базе данных
db = SQLAlchemy(app)


DB_HOST = "localhost"
DB_NAME = "maria"
DB_USER = "alex"
DB_PASS = "nazca007"

# conn = psycopg2.connect(dbname="maria", user="alex", password="nazca007", host="db_postgres")
conn = psycopg2.connect(dbname="maria", user="alex", password="nazca007", host="localhost")

UPLOAD_FOLDER = 'static/images/gallery/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS





# Важный момент, с 30 мая гугл заблокировал простой доступ. Теперь пароль нужен не от почты, а особенный,
# созданный для приложений в блоке Безопасность аккаунта Гугл
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'erapyth@gmail.com'
app.config['MAIL_PASSWORD'] = 'cdckiucrsowjuoxd'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)






# Создание схемы User  - FLASK SEQURITY



roles_users = db.Table('roles_users',
                       db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
                       db.Column('role_id', db.Integer, db.ForeignKey('role.id'))
                       )


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean)
    roles = db.relationship('Role', secondary=roles_users, backref=db.backref('users', lazy='dynamic'))


class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(100), unique=True)
    description = db.Column(db.String(255))


user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)










###### БЛОК ПО ДОБАВЛЕНИЮ сразу 2 КАРТИНОК И ПУТЕЙ К НИМ В БАЗУ ДАННЫХ ######


@app.route('/upload_image')
@login_required
def home():
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    s = "SELECT * FROM img_kat"
    cur.execute(s)  # Execute the SQL
    list_img = cur.fetchall()

    return render_template('b_image_change.html', list_img=list_img)



@app.route('/upload_image', methods=['GET', 'POST'])
@login_required
def upload_image():
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    if request.method == 'POST':
        if 'file1' not in request.files or 'file2' not in request.files:
            return 'there is no file in form!'
        file1 = request.files['file1']
        file2 = request.files['file2']
        path = os.path.join(app.config['UPLOAD_FOLDER'], file1.filename)
        path2 = os.path.join(app.config['UPLOAD_FOLDER'], file2.filename)

        file1.save(path)
        file2.save(path2)

        flash('Картинки успешно загружены. E.R.Alex')
        # сохраняем названия файлов для их поиска плюс сразу прописываем в имя файла весь путь, для href html
        filename = 'static/images/gallery/' + secure_filename(file1.filename)
        filename_big = 'static/images/gallery/' + secure_filename(file2.filename)

        position = request.form['position']
        name = request.form['name']
        text = request.form['text']

        cur.execute("INSERT INTO img_kat (position, name, text, file_name, file_name_big) VALUES (%s,%s,%s,%s,%s)", (position, name, text, filename, filename_big))
        conn.commit()
        return redirect(url_for('home'))


@app.route('/delete/<string:id>', methods=['POST', 'GET'])
@login_required
def delete_img(id):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # ищем как зовут файл в базе данных,имя нужно, чтобы потом удалить его в системе сайта. Т.е. ищем file_name
    cur.execute('SELECT * FROM img_kat WHERE id = %s', (id,))
    dat_del = cur.fetchall()
    # у нас в базе 6 колонок и предпоследний итем это имя маленьк файла, послед итем это название большого.
    # dat_del[0] это коллекция - например внутри нее [4, 'adsad', 'asdsad', 'asdasd', 'ZaresURSS.jpg', 'Espad.jpg']
    # путем перебора достаем имена 2 файлов и ставим в переменную
    small_name_del = ''
    big_name_del = ''
    count = 0
    for x in dat_del[0]:
        count += 1
        if count == 5:
            small_name_del = x
            print(small_name_del)
        if count == 6:
            big_name_del = x
            print(big_name_del)


    cur.execute('DELETE FROM img_kat WHERE id = {0}'.format(id))
    conn.commit()

    # удаляем не только из базы данные, но и сами 2 картинки с сайта (чтобы не было мусора)
    # картинка может быть двойная и в первом проходе удалим ее и чтобы не было ошибок запакуем в try c FileNotFoundErr
    try:
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], small_name_del))
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], big_name_del))
    except FileNotFoundError:
        pass

    flash('Image link Removed Successfully')
    return redirect(url_for('home'))



##

@app.route('/edit/<id>', methods=['POST', 'GET'])
@login_required
def get_image(id):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute('SELECT * FROM img_kat WHERE id = %s', (id,))
    data = cur.fetchall()
    cur.close()
    print(data[0])
    return render_template('b_img_edit.html', article_show=data[0])


@app.route('/update/<id>', methods=['POST'])
@login_required
def update_image(id):
    if request.method == 'POST':
        position = request.form['position']
        name = request.form['name']
        text = request.form['text']
        small_img = request.form['small_img']
        big_img = request.form['big_img']

        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("""
            UPDATE img_kat
            SET position = %s,
                name = %s,
                text = %s,
                file_name = %s,
                file_name_big = %s
            WHERE id = %s
        """, (position, name, text, small_img, big_img, id))
        flash('Image Information Updated Successfully, E.R.Alex')
        conn.commit()
        return redirect(url_for('home'))


###### ###### ###### ###### ###### ###### ###### ###### ######





###### БЛОК ПО ИЗМЕНЕНИЮ В ШАБЛОНЕ - art_change - В БАЗЕ ДАННЫХ ######

@app.route('/art_change')
@login_required
def art_change():
    result = art_all_information()
    return render_template('b_art_change.html', list_users=result)


@app.route('/add_articles', methods=['POST'])
@login_required
def add_article():
    art_add_article()
    return redirect(url_for('art_change'))


@app.route('/edit_art/<id>', methods=['POST', 'GET'])
@login_required
def get_article(id):
    result = art_get_article(id)
    return render_template('b_edit.html', article_show=result)


@app.route('/update_edit/<id>', methods=['POST'])
@login_required
def update_article(id):
    if request.method == 'POST':
        position = request.form['position']
        name = request.form['name']
        text = request.form['text']

        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("""
            UPDATE art3
            SET position = %s,
                name = %s,
                text = %s
            WHERE id = %s
        """, (position, name, text, id))
        flash('Article Updated Successfully, EspinosaAlex')
        conn.commit()
        return redirect(url_for('art_change'))


@app.route('/delete_art/<string:id>', methods=['POST', 'GET'])
@login_required
def delete_article(id):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute('DELETE FROM art3 WHERE id = {0}'.format(id))
    conn.commit()
    flash('Student Removed Successfully')
    return redirect(url_for('art_change'))


###### БЛОК ПО ИЗМЕНЕНИЮ В БАЗЕ ДАННЫХ ######








menu = [
    {"name": "Установка", "url": "install flask"},
    {"name": "Приложение", "url": "app"},
    {"name": "Обратная связь", "url": "contact"},
    ]





@app.route("/", methods=['POST', 'GET'])
def index():

    # блок отправки письма
    if request.method == 'POST':

        name = request.form['name']
        email = request.form['email']
        message = request.form['message']

        msg = Message(name, sender=email, recipients=['moonanamiss@gmail.com'])
        # в body ставим текст из формы
        msg.body = email + " " + message
        mail.send(msg)
        flash('Email Sanded Successfully')

        return redirect(url_for('index'))



    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    ban1 = "SELECT * FROM img_kat WHERE position = 'banner1'"
    cur.execute(ban1)  # Execute the SQL
    list_ban1 = cur.fetchall()

    ban2 = "SELECT * FROM img_kat WHERE position = 'banner2'"
    cur.execute(ban2)  # Execute the SQL
    list_ban2 = cur.fetchall()

    ban3 = "SELECT * FROM img_kat WHERE position = 'banner3'"
    cur.execute(ban3)  # Execute the SQL
    list_ban3 = cur.fetchall()

    ban4 = "SELECT * FROM img_kat WHERE position = 'banner4'"
    cur.execute(ban4)  # Execute the SQL
    list_ban4 = cur.fetchall()

    # делаем запрос, что нам надо, какие данные достать.
    art1 = "SELECT * FROM art3 WHERE position = 'position1'"
    # через курсор отправляем запрос на получение данных
    cur.execute(art1)  # Execute the SQL
    # сохраняем все данные в переменную
    list_art1 = cur.fetchall()


    art2 = "SELECT * FROM art3 WHERE position = 'position2'"
    cur.execute(art2)  # Execute the SQL
    list_art2 = cur.fetchall()

    art3 = "SELECT * FROM art3 WHERE position = 'position3'"
    cur.execute(art3)  # Execute the SQL
    list_art3 = cur.fetchall()

    art4 = "SELECT * FROM art3 WHERE position = 'position4'"
    cur.execute(art4)  # Execute the SQL
    list_art4 = cur.fetchall()

    art5 = "SELECT * FROM art3 WHERE position = 'position5'"
    cur.execute(art5)  # Execute the SQL
    list_art5 = cur.fetchall()

    img1 = "SELECT * FROM img_kat WHERE position = 'position1'"
    cur.execute(img1)  # Execute the SQL
    list_img1 = cur.fetchall()

    img2 = "SELECT * FROM img_kat WHERE position = 'position2'"
    cur.execute(img2)  # Execute the SQL
    list_img2 = cur.fetchall()

    img3 = "SELECT * FROM img_kat WHERE position = 'position3'"
    cur.execute(img3)  # Execute the SQL
    list_img3 = cur.fetchall()

    img4 = "SELECT * FROM img_kat WHERE position = 'position4'"
    cur.execute(img4)  # Execute the SQL
    list_img4 = cur.fetchall()

    img5 = "SELECT * FROM img_kat WHERE position = 'position5'"
    cur.execute(img5)  # Execute the SQL
    list_img5 = cur.fetchall()


    return render_template('index.html', title='- Все про Flask',
                           list_ban1=list_ban1,
                           list_ban2=list_ban2,
                           list_ban3=list_ban3,
                           list_ban4=list_ban4,

                           list_art1=list_art1,
                           list_art2=list_art2,
                           list_art3=list_art3,
                           list_art4=list_art4,
                           list_art5=list_art5,

                           list_img1=list_img1,
                           list_img2=list_img2,
                           list_img3=list_img3,
                           list_img4=list_img4,
                           list_img5=list_img5,
                           )







@app.route("/about")
def about():
    print(url_for('about'))
    return render_template('about.html', title='О нас', menu=menu_names)


@app.route("/about_me")
def about_me():
    print(url_for('about_me'))

    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    ban1 = "SELECT * FROM img_kat WHERE position = 'banner1'"
    cur.execute(ban1)  # Execute the SQL
    list_ban1 = cur.fetchall()


    art1 = "SELECT * FROM art3 WHERE position = 'position1'"
    cur.execute(art1)
    list_art1 = cur.fetchall()

    img1 = "SELECT * FROM img_kat WHERE position = 'position1'"
    cur.execute(img1)  # Execute the SQL
    list_img1 = cur.fetchall()

    img2 = "SELECT * FROM img_kat WHERE position = 'position2'"
    cur.execute(img2)  # Execute the SQL
    list_img2 = cur.fetchall()

    img3 = "SELECT * FROM img_kat WHERE position = 'position3'"
    cur.execute(img3)  # Execute the SQL
    list_img3 = cur.fetchall()

    img4 = "SELECT * FROM img_kat WHERE position = 'position4'"
    cur.execute(img4)  # Execute the SQL
    list_img4 = cur.fetchall()

    img5 = "SELECT * FROM img_kat WHERE position = 'position5'"
    cur.execute(img5)  # Execute the SQL
    list_img5 = cur.fetchall()



    return render_template('s_aboutme.html', title='Обо мне', list_art1=list_art1,
                           list_ban1=list_ban1,

                           list_img1=list_img1,
                           list_img2=list_img2,
                           list_img3=list_img3,
                           list_img4=list_img4,
                           list_img5=list_img5,
                           )







@app.route("/contact", methods=["POST", "GET"])
def contact():
    if request.method == 'POST':
        print(request.form['username'])

        if len(request.form['username']) > 3:
            flash('Сообщение отправлено')
        else:
            flash('Ошибка в создании сообщения')

    return render_template('contact.html', title='Контакты')


if __name__ == "__main__":
    app.run(debug=False, host='0.0.0.0')