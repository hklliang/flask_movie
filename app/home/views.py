from . import home
from flask import render_template, redirect, url_for, flash, session, request
from functools import wraps
from app.home.forms import RegisterForm, LoginForm, UserdetailForm, PwdForm
from app.models import User, Userlog,Preview
from werkzeug.security import generate_password_hash
import uuid, os, datetime, stat
from werkzeug.utils import secure_filename
from app import db, app

if not os.path.exists(app.config['FC_DIR']):
    os.makedirs(app.config['FC_DIR'])
    os.chmod(app.config['FC_DIR'], stat.S_IRWXU)


def change_filename(filename):
    fileinfo = os.path.splitext(filename)
    filename = datetime.datetime.now().strftime('%Y%m%d%H%M%S') + str(uuid.uuid4().hex) + fileinfo[-1]

    return filename


# 登录装饰器
def user_login_req(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('home.login', next=request.url))  # 记录要进入的地址参数
        return f(*args, **kwargs)

    return decorated_function


@home.route("/")
def index():
    return render_template("home/index.html")


@home.route('/login/', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    data = form.data

    if form.validate_on_submit():

        user = User.query.filter_by(name=data['name']).first()

        if not user:
            flash('账号不存在', 'err')
            return render_template("home/login.html", form=form)  # 直接将form返回去

        if not user.check_pwd(data['pwd']):  # passwordfield不能赋值，可以用stringfield加上type='password'
            flash('密码错误', 'err')
            return render_template("home/login.html", form=form)

        session['user'] = user.name
        session['user_id'] = user.id
        userlog = Userlog(
            user_id=user.id,
            ip=request.remote_addr
        )
        db.session.add(userlog)
        db.session.commit()
        return redirect(url_for('home.user'))
    return render_template("home/login.html", form=form)


@home.route('/regist/', methods=['GET', 'POST'])
def regist():
    form = RegisterForm()

    if form.validate_on_submit():
        data = form.data
        user = User(
            name=data['name'],
            email=data['email'],
            phone=data['phone'],
            pwd=generate_password_hash(data['pwd']),
            uuid=uuid.uuid4().hex
        )
        db.session.add(user)
        db.session.commit()

        flash('注册成功', 'ok')

    return render_template('home/regist.html', form=form)


@home.route('/logout/')
def logout():
    session.pop('user', None)
    session.pop('user_id', None)
    return redirect(url_for('home.login'))


@home.route('/user/', methods=['GET', 'POST'])
@user_login_req
def user():
    form = UserdetailForm()

    user = User.query.get_or_404(int(session['user_id']))  # get通过主键获取

    if request.method == 'GET':
        form.name.data = user.name
        form.email.data = user.email
        form.phone.data = user.phone
        form.info.data = user.info
    form.face.validators = []

    if form.validate_on_submit():
        data = form.data
        face = form.face.data.filename  # 要在form标签加上enctype="multipart/form-data"

        # 要先判断是否有上传文件
        name_count = User.query.filter(User.name == data['name'], User.id != session['user_id']).count()
        if name_count >= 1:
            flash('该昵称已经存在！', 'err')
            return render_template('home/user.html', form=form, user=user)

        email_count = User.query.filter(User.email == data['email'], User.id != session['user_id']).count()
        if email_count >= 1:
            flash('该邮箱已经存在！', 'err')
            return render_template('home/user.html', form=form, user=user)

        phone_count = User.query.filter(User.name == data['name'], User.id != session['user_id']).count()
        if phone_count >= 1:
            flash('该电话已经存在！', 'err')
            return render_template('home/user.html', form=form, user=user)

        if face:
            file_face = secure_filename(face)
            user.face = change_filename(file_face)
            form.face.data.save(app.config['FC_DIR'] + user.face)
        user.name = data['name']
        user.emali = data['email']
        user.phone = data['phone']
        user.info = data['info']
        db.session.add(user)
        db.session.commit()

        flash('修改成功！', 'ok')
    return render_template('home/user.html', form=form, user=user)


@home.route('/pwd/', methods=['GET', 'POST'])
@user_login_req
def pwd():
    form = PwdForm()
    if form.validate_on_submit():
        data = form.data
        print(session['user'])
        user = User.query.filter_by(id=int(session['user_id'])).first()  # 有可能字符串和数字不相等
        print(user)
        from werkzeug.security import generate_password_hash
        user.pwd = generate_password_hash(data['new_pwd'])  # 可以通过form去检查那么error在输入框下面，如果在
        db.session.commit()
        flash('修改密码成功', 'ok')
        # return redirect(url_for('user.logout'))
    return render_template('home/pwd.html', form=form)


@home.route('/comments/')
@user_login_req
def comments():
    return render_template('home/comments.html')


@home.route('/loginlog/<int:page>/', methods=['GET'])
@user_login_req
def loginlog(page=None):
    if page is None:
        page = 1
    page_data = Userlog.query.filter_by(id=int(session['user_id'])).order_by(
        Userlog.addtime.desc()
    ).paginate(page=page, per_page=10, error_out=False)
    if page == 1 or page_data.items:
        return render_template('home/loginlog.html', page_data=page_data)
    elif not page_data.items:
        return redirect(url_for('home.loginlog', page=1))


@home.route('/moviecol/')
@user_login_req
def moviecol():
    return render_template('home/moviecol.html')


@home.route('/animation/')
def animation():
    data=Preview.query.all()
    return render_template('home/animation.html',data=data)


@home.route('/search/')
def search():
    return render_template('home/search.html')


@home.route('/play/')
def play():
    return render_template('home/play.html')
