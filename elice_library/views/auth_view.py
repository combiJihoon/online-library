from flask import Blueprint, render_template, request, url_for, flash, session
from werkzeug.utils import redirect
from forms import LoginForm, RegistrationForm
from bcrypt import checkpw, hashpw, gensalt
from models import *

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm(request.form)
    user_id = login_form.user_id.data
    user_password = login_form.user_password.data
    if request.method == 'POST' and login_form.validate():
        user_data = User.query.filter(user_id=user_id).first()
        if not user_data:
            flash('아이디를 다시 확인해 주세요.')
            return redirect(url_for('auth.login'))
        elif not checkpw(user_password.encode('utf-8'), user_data.user_password):
            flash('비밀번호가 일치하지 않습니다.')
            return redirect(url_for('auth.login'))
        else:
            session.clear()
            session['user_id'] = user_id
            flash(f'{user_data.user_name}님 안녕하세요!')
            return redirect(url_for('main.home'))
    else:
        return render_template('login.html')


@bp.route('/signup', methods=['GET', 'POST'])
def signup():
    registration_form = RegistrationForm(request.form)
    user_id = registration_form.user_id
    user_password = registration_form.user_password
    user_name = registration_form.user_name
    if request.method == 'POST' and registration_form.validate():
        user_data = User.query.filter_by(user_id=user_id).first()
        if not user_data:
            hashed_password = hashpw(user_password.encode('utf-8'), gensalt())

            new_user = User(user_id=user_id,
                            user_password=hashed_password, user_name=user_name)
            db.session.add(new_user)
            db.session.commit()
        else:
            flash('이미 존재하는 아이디입니다. 다시 입력해 주세요.')
            return redirect(url_for('main.signup'))
    else:
        return render_template('signup.html')
