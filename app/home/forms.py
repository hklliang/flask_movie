# coding:utf8
from flask_wtf import FlaskForm
from app.models import User
from wtforms import StringField, PasswordField, SubmitField, FileField, TextAreaField
from wtforms.validators import DataRequired,EqualTo,Email,Regexp,ValidationError



class RegisterForm(FlaskForm):
    name = StringField(
        label='昵称',
        validators=[
            DataRequired('请输入昵称')
        ],
        description='昵称',
        render_kw={
            "class": "form-control",
            "placeholder": '请输入昵称！',
            # 'required': 'required'
        }
    )
    pwd = PasswordField(
        label="密码",
        validators=[
            DataRequired('请输入密码')
        ],
        description='密码',
        render_kw={
            "class": "form-control",
            "placeholder": '请输入密码！',
            # 'required': 'required'#请填写此字段
        }
    )
    repwd = PasswordField(
        label="确认密码",
        validators=[
            DataRequired('请输入确认密码'),
            EqualTo('pwd', message='两次密码不一致')
        ],
        description='确认密码',
        render_kw={
            "class": "form-control",
            "placeholder": '请输入确认密码！',
        }
    )
    email = StringField(
        label='邮箱',
        validators=[
            DataRequired('请输入邮箱'),
            Email('邮箱格式不正确')
        ],
        description='邮箱',
        render_kw={
            "class": "form-control",
            "placeholder": '请输入邮箱！',
            # 'required': 'required'
        }
    )
    phone = StringField(
        label='手机',
        validators=[
            DataRequired('请输入邮箱'),
            Regexp('1[3458]\d{9}', message='手机格式不正确')
        ],
        description='手机',
        render_kw={
            "class": "form-control",
            "placeholder": '请输入手机！',
            # 'required': 'required'
        }
    )

    submit = SubmitField(
        label="注册",
        render_kw={
            "class": "btn btn-primary btn-block btn-flat",
        }
    )

    def validate_name(self, field):
        name = field.data
        user = User.query.filter_by(name=name).count()
        if user >= 1:
            raise ValueError('昵称已经存在')

    def validate_email(self, field):
        email = field.data
        user = User.query.filter_by(email=email).count()
        if user >= 1:
            raise ValueError('邮件已经存在')

    def validate_phone(self, field):
        phone = field.data
        user = User.query.filter_by(phone=phone).count()
        if user >= 1:
            raise ValueError('手机已经存在')


class LoginForm(FlaskForm):
    name = StringField(
        label='账号',
        validators=[
            DataRequired('请输入账号')
        ],
        description='账号',
        render_kw={
            "class": "form-control",
            "placeholder": '请输入账号！',
            # 'required': 'required'
        }
    )
    pwd = StringField(
        label="密码",
        validators=[
            DataRequired('请输入密码')
        ],
        description='密码',
        render_kw={
            "class": "form-control",
            "placeholder": '请输入密码！',
            'type':'password'
            # 'required': 'required'#请填写此字段
        }
    )

    submit = SubmitField(
        label="登录",
        render_kw={
            "class": "btn btn-primary btn-block btn-flat",
        }

    )

class UserdetailForm(FlaskForm):
    name = StringField(
        label='昵称',
        validators=[
            DataRequired('请输入昵称')
        ],
        description='昵称',
        render_kw={
            "class": "form-control ",
            "placeholder": '请输入昵称！',
            # 'required': 'required'
        }
    )
    phone = StringField(
        label='手机',
        validators=[
            DataRequired('请输入邮箱'),
            Regexp('1[3458]\d{9}', message='手机格式不正确')
        ],
        description='手机',
        render_kw={
            "class": "form-control",
            "placeholder": '请输入手机！',
            # 'required': 'required'
        }
    )

    email = StringField(
        label='邮箱',
        validators=[
            DataRequired('请输入邮箱'),
            Email('邮箱格式不正确')
        ],
        description='邮箱',
        render_kw={
            "class": "form-control",
            "placeholder": '请输入邮箱！',
            # 'required': 'required'
        }
    )
    face=FileField(
        label='头像',
        validators=[
            DataRequired('请上传头像')
        ],
        description='头像',

    )
    info = TextAreaField(
        label="简介",
        validators=[
            DataRequired('请输入简介！')
        ],
        description='简介',
        render_kw=dict(
            class_="form-control",
            row=10
    )
    )
    submit = SubmitField(
        label='保存修改',
        render_kw={
            "class": "btn btn-success",
        }

    )

class PwdForm(FlaskForm):
    old_pwd = PasswordField(
        label="旧密码",
        validators=[
            DataRequired('请输入旧密码')
        ],
        description='旧密码',
        render_kw={
            "class": "form-control",
            "placeholder": '请输入旧密码！',
        }
    )
    new_pwd = PasswordField(
        label="新密码",
        validators=[
            DataRequired('请输入新密码')
        ],
        description='新密码',
        render_kw={
            "class": "form-control",
            "placeholder": '请输入新密码！',
        }
    )
    submit = SubmitField(
        label="修改密码",
        render_kw={
            "class": "btn btn-success",
        }
    )
    def validate_old_pwd(self, field):
        from flask import session
        pwd = field.data
        user_id = session['user_id']
        admin = User.query.filter_by(
            id=user_id
        ).first()
        if not admin.check_pwd(pwd):
            raise ValidationError('旧密码错误')