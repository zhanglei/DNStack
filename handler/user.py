#!/usr/bin/python
# -*- coding:utf-8 -*-
# Powered By KK Studio

from BaseHandler import BaseHandler
from tornado.web import authenticated as Auth
from model.models import User, or_, and_

class LoginHandler(BaseHandler):

    def get(self):
        if not self.session.isGuest:
            return self.redirect('/') # 已登录则跳转到首页
        next = self.get_argument("next", "/")
        self.render('user/login.html', next=next)

    def post(self):
        username = self.get_argument("username", None)
        password = self.get_argument("password", None)
        remember = self.get_argument("remember", "no")
        if not username or not password:
            return self.jsonReturn({'code':-1,'msg':u'参数错误'})
        profile = self.db.query(User).filter(or_(User.username==username,User.email==username),and_(User.status=='1')).first()
        if profile:
            password_hash = self.md5(password+profile.password_key)
            if password_hash != profile.password:
                return self.jsonReturn({'code':-2,'msg':u'用户名或密码错误'})
            session_data = {
                'uid': profile.id,
                'username': profile.username,
                'email': profile.email,
                'nickname': profile.nickname,
                'login_time': profile.login_time,
                'login_ip': profile.login_ip,
                'login_location': profile.login_location,
            }
            self.create_session(session_data, remember)
            # 记录登录信息
            headers = self.request.headers
            login_ua = headers.get('User-Agent')
            login_ip = self.request.remote_ip
            login_data = {
                "login_count": int(profile.login_count) + 1,
                "login_time": self.time,
                "login_ua": login_ua,
                "login_ip": login_ip
                # "login_location": login_location
            }
            self.db.query(User).filter_by(id=profile.id).update(login_data)
            self.db.commit()
            # 跳转登录前的URL
            next_url = self.get_argument("next", "/")
            return self.jsonReturn({'code': 0, 'msg': u'Login Successful', 'next':next_url})
        else:
            return self.jsonReturn({'code': -2, 'msg': u'用户名或密码错误'})


    def create_session(self,data,remember):
        sid = self.session.gen_session_id()
        self.session.data = data
        self.session.isGuest = False
        #self.session.save() # Why don't save? See self._on_finish !!
        if remember == "yes":
            expires_days = 15  # Remember Session 15 days
        else:
            expires_days = None
        self.set_secure_cookie(self.cookie_name, sid, expires_days)


# Sign Out
class LogoutHandler(BaseHandler):
    def get(self):
        self.session.remove()
        self.clear_cookie(self.cookie_name)
        self.redirect(self.get_login_url())


# Profile
class ProfileHandler(BaseHandler):
    @Auth
    def get(self):
        uid = self.session.get('uid')
        profile = self.db.query(User).filter_by(id=uid).first()
        self.nav_active['/settings'] = 'active'
        self.render('user/profile.html',profile=profile)

    @Auth
    def post(self):
        uid = self.session.get('uid')
        email = self.get_argument("email") or None
        phone = self.get_argument("phone") or None
        nickname = self.get_argument("nickname") or None
        dept = self.get_argument("dept") or None
        if not email:
            return self.jsonReturn({'code': -1, 'msg': u'Email不能为空'})
        if not nickname:
            return self.jsonReturn({'code': -1, 'msg': u'姓名不能为空'})
        chk = self.db.query(User).filter(User.email==email,User.id!=uid).first()
        if chk:
            return self.jsonReturn({'code': -2, 'msg': u'Email重复'})
        self.db.query(User).filter_by(id=uid).update({'email':email, 'phone':phone, 'nickname':nickname, 'dept':dept, 'update_time': self.time})
        self.db.commit()
        self.session.set('email',email)
        self.session.set('nickname',nickname)
        return self.jsonReturn({'code': 0, 'msg': 'Success'})


# Password
class PasswdHandler(BaseHandler):
    @Auth
    def get(self):
        self.nav_active['/settings'] = 'active'
        self.render('user/passwd.html')

    @Auth
    def post(self):
        password_old = self.get_argument("password_old") or None
        password = self.get_argument("password") or None # New Password
        if not password_old or not password:
            return self.jsonReturn({'code': -1, 'msg': u'密码不能为空'})
        uid = self.session.get('uid')
        profile = self.db.query(User).filter_by(id=uid).first()
        password_old_hash = self.md5(password_old + profile.password_key)
        if password_old_hash != profile.password:
            return self.jsonReturn({'code': -2, 'msg': u'原始密码错误'})
        password_key = self.random_str(12) # 使用新的PasswordKey
        password_hash = self.md5(password + password_key)
        self.db.query(User).filter_by(id=uid).update({'password': password_hash, 'password_key': password_key,'update_time': self.time})
        self.db.commit()
        return self.jsonReturn({'code': 0, 'msg': 'Success'})
