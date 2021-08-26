from flask import Blueprint, request, render_template, url_for, flash, session, g, jsonify
from bcrypt import checkpw, hashpw, gensalt
from werkzeug.utils import redirect, secure_filename
from models import Book, User, UserRoles, AddStock
from app import db

from datetime import datetime

bp = Blueprint('admin', __name__, url_prefix='/admin')


@bp.before_app_request
def load_administrator():
    user_id = session.get('user_id')
    if user_id is None:
        g.administrator = None
    else:
        g.administrator = UserRoles.query.get(user_id)


@bp.route('/login', methods=['GET'])
def login_try():
    return render_template('admin/admin_login.html')


@bp.route('/login', methods=['POST'])
def admin_login():
    user_id = request.form['user_id']
    user_password = request.form['user_password']

    user_data = User.query.filter_by(user_id=user_id).first()
    if user_data is not None:
        is_administrator = UserRoles.query.filter_by(user_id=user_id).first()
        if is_administrator:
            # validators 실행
            if len(user_password) < 8:
                flash('비밀번호는 8자리 이상 입력하세요.')
                return redirect(url_for('admin.login'))

            elif not checkpw(user_password.encode('utf-8'), user_data.user_password):
                flash('비밀번호가 일치하지 않습니다.')
                return redirect(url_for('admin.login'))

            else:
                session.clear()
                session['user_id'] = user_id
                flash(
                    f'{user_data.user_name}({is_administrator.role_title})님 안녕하세요!')
                return redirect(url_for('admin.dashboard'))
    else:
        flash('아이디를 다시 확인해 주세요.')
        return redirect(url_for('admin.login_try'))


@bp.route('/logout', methods=['POST'])
def logout():
    db.session.clear()

    flash('로그아웃 되었습니다.')
    return redirect(url_for('admin.login_try'))


@bp.route('/dashboard', methods=['GET'])
def dashboard():
    user_id = session['user_id']
    is_authorized = UserRoles.query.filter_by(user_id=user_id).first()
    if is_authorized:

        # search가 있을 경우
        search = request.args.get('search')
        if search is not None:
            search = "%{}%".format(search)
            added_list = AddStock.query.join(Book).filter(
                AddStock.user_id == user_id, Book.book_name.like(search)).order_by(AddStock.added_at.desc())
        else:
            added_list = AddStock.query.filter(
                AddStock.user_id == user_id).order_by(AddStock.added_at.desc())

        page = request.args.get('page', type=int, default=1)
        added_list = added_list.paginate(page, per_page=8)

        return render_template('admin/admin_dashboard.html', added_list=added_list)
    else:
        return redirect(url_for('admin.login_try'))


@bp.route('/add-data', methods=['GET'])
def add_data_try():
    return render_template('admin/admin_add_book.html')


@bp.route('/add-data', methods=['POST'])
def add_data():
    book_name = request.form['book_name']
    publisher = request.form['publisher']
    author = request.form['author']
    publicated_at = request.form['publicated_at']
    pages = request.form['pages']
    isbn = request.form['isbn']
    description = request.form['description']
    link = request.form['link']
    f = request.files['img_url']
    stock = request.form['stock']
    rating = 0

    data = [book_name, publisher, author, publicated_at,
            pages, isbn, description, link, f, stock]
    if not all(data):
        flash('입력하지 않은 내용이 있습니다.')
        return redirect(url_for('admin.add_data_try'))

    else:
        publicated_at = datetime.strptime(
            publicated_at, '%Y-%m-%d')

        f.save("static/images/" + secure_filename(f.filename))
        img_url = "images/" + secure_filename(f.filename)

        book = Book.query.filter_by(book_name=book_name).first()

        if not book:
            user_id = session['user_id']
            new_book = Book(book_name=book_name, publisher=publisher,
                            author=author, publicated_at=publicated_at, pages=pages, isbn=isbn, description=description, link=link, img_url=img_url, stock=stock, rating=rating)

            add_stock = AddStock(user_id=user_id, book_name=book_name)

            db.session.add(new_book)
            db.session.add(add_stock)
            db.session.commit()

            return redirect(url_for('admin.dashboard'))
        else:
            flash('이미 등록된 책입니다.')
            return redirect(url_for('admin.add_data_try'))