from . import admin
from flask import render_template, redirect, url_for, flash, session, request
from app.admin.fomrs import LoginForm, TagForm, MovieForm, PreviewForm
from app.models import Admin, Tag, Movie, Preview,User
from functools import wraps
from app import db, app
from werkzeug.utils import secure_filename
import os, uuid, datetime, stat

if not os.path.exists(app.config['UP_DIR']):
    os.makedirs(app.config['UP_DIR'])
    os.chmod(app.config['UP_DIR'], stat.S_IRWXU)


def admin_login_req(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin' not in session:
            return redirect(url_for('admin.login', next=request.url))  # 记录要进入的地址参数
        return f(*args, **kwargs)

    return decorated_function


# 引用的是__init__.py里面的admin
# flash信息闪现

def change_filename(filename):
    fileinfo = os.path.splitext(filename)
    filename = datetime.datetime.now().strftime('%Y%m%d%H%M%S') + str(uuid.uuid4().hex) + fileinfo[-1]

    return filename


@admin.route("/")
@admin_login_req
def index():
    return render_template('admin/index.html')


@admin.route("/login/", methods=['GET', 'POST'])
def login():
    if 'admin' in session:
        return redirect(url_for('admin.index'))

    form = LoginForm()
    if form.validate_on_submit():
        data = form.data
        admin = Admin.query.filter_by(name=data['account']).first()
        if not admin.check_pwd(data['pwd']):
            flash('密码错误！')
            # return redirect(url_for('admin.login'))
            return render_template('admin/login.html', form=form)
        session['admin'] = data['account']
        return redirect(request.args.get('next') or url_for('admin.index'))  # 是否有要进入的参数
    return render_template('admin/login.html', form=form)


@admin.route("/logout/")
@admin_login_req
def logout():
    session.pop('admin')
    return redirect(url_for('admin.login'))


@admin.route("/pwd/")
@admin_login_req
def pwd():
    return render_template('admin/pwd.html')


@admin.route("/tag/add/", methods=['GET', 'POST'])
@admin_login_req
def tag_add():
    form = TagForm()
    if form.validate_on_submit():
        data = form.data
        tag = Tag.query.filter_by(name=data['name']).count()

        if tag >= 1:
            flash('名称已经存在！', 'err')
            return render_template('admin/tag_add.html', form=form)
        tag = Tag(
            name=data['name']
        )
        db.session.add(tag)
        db.session.commit()
        flash('添加标签成功！', 'ok')

    return render_template('admin/tag_add.html', form=form)  # 因为在html中引用了form


@admin.route("/tag/edit/<int:id>/<int:page>/", methods=['GET', 'POST'])
@admin_login_req
def tag_edit(id, page=None):
    form = TagForm()  # 点了提交才有数据传过来了，get请求是没有数据
    tag = Tag.query.get_or_404(id)
    if form.validate_on_submit():
        data = form.data
        # filter_by只能用=，而不能用!=，没有filter灵活
        tag_count = Tag.query.filter(Tag.name == data['name'], Tag.id != id).count()
        tag.name = data['name']
        if tag_count >= 1:
            flash('名称已经存在！', 'err')
            return render_template('admin/tag_edit.html', form=form, tag=tag)

        # 更新不用写额外的session操作
        db.session.commit()
        flash('修改标签成功！', 'ok')
        return redirect(url_for('admin.tag_list', page=page or 1))

    return render_template('admin/tag_edit.html', form=form, tag=tag)


# 标签删除
@admin.route("/tag/del/<int:id>/<int:page>/", methods=['GET'])
@admin_login_req
def tag_del(id=None, page=None):
    tag = Tag.query.filter_by(id=id).first_or_404()
    db.session.delete(tag)
    db.session.commit()

    flash('删除标签成功！', 'ok')

    return redirect(url_for('admin.tag_list', page=page or 1))


@admin.route("/tag/list/<int:page>/", methods=['GET'])
@admin_login_req
def tag_list(page=None):
    if page is None:
        page = 1
    page_data = Tag.query.order_by(
        Tag.addtime.desc()
    ).paginate(page=page, per_page=10)
    if page == 1:
        return render_template('admin/tag_list.html', page_data=page_data)
    elif not page_data.items:
        return redirect(url_for('admin.tag_list', page=1))


@admin.route("/movie/add/", methods=['GET', 'POST'])
@admin_login_req
def movie_add():
    form = MovieForm()
    if form.validate_on_submit():
        data = form.data
        movie_count = Movie.query.filter_by(title=data['title']).count()
        if movie_count >= 1:
            flash('该电影已经存在！', 'err')
            return render_template('admin/movie_add.html', form=form)

        file_url = secure_filename(form.url.data.filename)
        file_logo = secure_filename(form.logo.data.filename)

        url = change_filename(file_url)
        logo = change_filename(file_logo)
        form.url.data.save(app.config['UP_DIR'] + url)
        form.logo.data.save(app.config['UP_DIR'] + logo)
        movie = Movie(
            title=data['title'],
            url=url,
            info=data['info'],
            logo=logo,
            star=int(data['star']),
            playnum=0,
            commentnum=0,
            tag_id=int(data['tag_id']),
            area=data['area'],
            release_time=data['release_time'],
            length=data['length']
        )
        db.session.add(movie)
        db.session.commit()

        flash('添加电影成功！', 'ok')
        return redirect(url_for('admin.movie_add'))
    return render_template('admin/movie_add.html', form=form)


@admin.route("/movie/list/<int:page>/", methods=['GET'])
@admin_login_req
def movie_list(page=None):
    if page is None:
        page = 1
    page_data = Movie.query.join(Tag).filter(
        Tag.id == Movie.tag_id
    ).order_by(
        Movie.addtime.desc()
    ).paginate(page=page, per_page=10)
    if page == 1:
        return render_template('admin/movie_list.html', page_data=page_data)
    elif not page_data.items:
        return redirect(url_for('admin.movie_list', page=1))


@admin.route("/movie/list/<int:id>/<int:page>", methods=['GET'])
@admin_login_req
def movie_del(id=None, page=None):
    movie = Movie.query.get_or_404(int(id))
    db.session.delete(movie)
    db.session.commit()
    flash('删除电影成功！', 'ok')
    return redirect(url_for('admin.movie_list', page=page or 1))


@admin.route("/movie/edit/<int:id>/<int:page>/", methods=['GET', 'POST'])
@admin_login_req
def movie_edit(id, page=None):
    form = MovieForm()  # 没有点提交时，没有任何数据
    movie = Movie.query.get_or_404(int(id))  # 只能通过id在数据库里查

    if request.method == 'GET':  # input可以用form.title(value=movie.title)，但是类似于textarea或者select等标签是不可以的
        form.info.data = movie.info#但是如果是在src里的地址，只能通过movie.logo
        form.tag_id.data = movie.tag_id
        form.star.data = movie.star

    form.logo.validators = []  # 去掉封面和电影的校验，否则会提示上传数据
    form.url.validators = []  #
    if form.validate_on_submit():  # 校验通过时
        data = form.data
        movie_count = Movie.query.filter(Movie.title == data['title'], Movie.id != id).count()
        if movie_count > 1:
            flash('该电影已经存在！', 'err')
            return render_template('admin/movie_edit.html', form=form, movie=movie)

        url = form.url.data.filename
        logo = form.logo.data.filename

        # 要先判断是否有上传文件
        if url:
            file_url = secure_filename(url)
            movie.url = change_filename(file_url)
            form.url.data.save(app.config['UP_DIR'] + movie.url)

        if logo:
            file_logo = secure_filename(logo)
            movie.logo = change_filename(file_logo)
            form.logo.data.save(app.config['UP_DIR'] + movie.logo)

        movie.star = data['star']
        movie.tag_id = data['tag_id']
        movie.info = data['info']
        movie.title = data['title']
        movie.area = data['area']
        movie.length = data['length']
        movie.release_time = data['release_time']

        # db.session.add(movie)#加不加都可以
        db.session.commit()

        flash('修改电影成功！', 'ok')
        return redirect(url_for('admin.movie_list', page=page or 1))
    return render_template('admin/movie_edit.html', form=form, movie=movie)


@admin.route("/preview/add/", methods=['GET', 'POST'])
@admin_login_req
def preview_add():
    form = PreviewForm()
    if form.validate_on_submit():
        data = form.data
        preview_count = Preview.query.filter_by(title=data['title']).count()
        if preview_count >= 1:
            flash('预告已经存在！', 'err')
            return render_template('admin/preview_add.html', form=form)

        file_logo = secure_filename(form.logo.data.filename)
        logo = change_filename(file_logo)
        form.logo.data.save(app.config['UP_DIR'] + logo)

        preview = Preview(
            title=data['title'],
            logo=logo
        )
        db.session.add(preview)
        db.session.commit()
        flash('添加预告成功！', 'ok')
        return redirect(url_for('admin.preview_add'))

    return render_template('admin/preview_add.html', form=form)


@admin.route("/preview/list/<int:id>/<int:page>", methods=['GET'])
@admin_login_req
def preview_del(id=None, page=None):
    preview = Preview.query.get_or_404(int(id))
    db.session.delete(preview)
    db.session.commit()
    flash('删除预告成功！', 'ok')
    return redirect(url_for('admin.preview_list', page=page or 1))


@admin.route("/preview/list/<int:page>", methods=['GET'])
@admin_login_req
def preview_list(page=None):
    if page is None:
        page = 1
    page_data = Preview.query.order_by(
        Preview.addtime.desc()
    ).paginate(page=page, per_page=2, error_out=False)
    # 没有数据的时候返回第一页
    if page == 1:
        return render_template('admin/preview_list.html', page_data=page_data)
    elif not page_data.items:
        return redirect(url_for('admin.preview_list', page=1))


@admin.route("/preview/edit/<int:id>/<int:page>/", methods=['GET', 'POST'])  # 编辑完要返回到列表相应页
@admin_login_req
def preview_edit(id, page=None):
    form = PreviewForm()  # 点了提交才有数据传过来了，get请求是没有数据

    preview = Preview.query.get_or_404(int(id))

    if request.method == "GET":
        form.title.data = preview.title#令html标签有值

    form.logo.validators = []
    if form.validate_on_submit():  # 两个form一个是get带过来的，一个是sumbit带过来的
        data = form.data
        # filter_by只能用=，而不能用!=，没有filter灵活
        preview_count = Preview.query.filter(Preview.title == data['title'], Preview.id != id).count()

        if preview_count >= 1:
            flash('预告已经存在！', 'err')
            return render_template('admin/preview_edit.html', form=form,preview=preview)

        logo = form.logo.data.filename
        if logo:
            file_logo = secure_filename(logo)
            preview.logo = change_filename(file_logo)
            form.logo.data.save(app.config['UP_DIR'] + preview.logo)
        preview.title = data['title']#data数据库数据字典
        # 更新不用写额外的session操作
        db.session.commit()
        flash('修改预告成功！', 'ok')
        return redirect(url_for('admin.preview_list', page=page))

    return render_template('admin/preview_edit.html', form=form,preview=preview)#为了显示图片，form主要用于标签构造和标签名



@admin.route("/user/list/<int:page>", methods=['GET'])
@admin_login_req
def user_list(page=None):
    if page is None:
        page = 1
    page_data = User.query.order_by(
        User.addtime.desc()
    ).paginate(page=page, per_page=10, error_out=False)

    # 没有数据的时候返回第一页
    if page == 1:
        return render_template('admin/user_list.html', page_data=page_data)
    elif not page_data.items:
        return redirect(url_for('admin.user_list', page=1))


@admin.route("/user/list/<int:id>/<int:page>", methods=['GET'])
@admin_login_req
def user_del(id=None, page=None):
    user = User.query.get_or_404(int(id))
    db.session.delete(user)
    db.session.commit()
    flash('删除用户成功！', 'ok')
    return redirect(url_for('admin.user_list', page=page))

@admin.route("/user/view/<int:id>/",methods=['GET'])
@admin_login_req
def user_view(id=None):
    user=User.query.get_or_404(int(id))

    return render_template('admin/user_view.html',user=user)


@admin.route("/comment/list/")
@admin_login_req
def comment_list():
    return render_template('admin/comment_list.html')


@admin.route("/moviecol/list/")
@admin_login_req
def moviecol_list():
    return render_template('admin/moviecol_list.html')


@admin.route("/oplog/list/")
@admin_login_req
def oplog_list():
    return render_template('admin/oplog_list.html')


@admin.route("/adminloginlog/list/")
@admin_login_req
def adminloginlog_list():
    return render_template('admin/adminloginlog_list.html')


@admin.route("/userloginlog/list/")
@admin_login_req
def userloginlog_list():
    return render_template('admin/userloginlog_list.html')


@admin.route("/auth/add/")
@admin_login_req
def auth_add():
    return render_template('admin/auth_add.html')


@admin.route("/auth/list/")
@admin_login_req
def auth_list():
    return render_template('admin/auth_list.html')


@admin.route("/role/add/")
@admin_login_req
def role_add():
    return render_template('admin/role_add.html')


@admin.route("/role/list/")
def role_list():
    return render_template('admin/role_list.html')


@admin.route("/admin/add/")
@admin_login_req
def admin_add():
    return render_template('admin/admin_add.html')


@admin.route("/admin/list/")
@admin_login_req
def admin_list():
    return render_template('admin/admin_list.html')
