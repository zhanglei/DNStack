#!/usr/bin/python
# -*- coding:utf-8 -*-
# Powered By KK Studio

from BaseHandler import BaseHandler
from tornado.web import authenticated as Auth
from model.models import Options

class StateHandler(BaseHandler):

    @Auth
    def get(self):
        self.nav_active['/system/state'] = 'active'
        self.render('system/state.html')


class SettingsHandler(BaseHandler):

    @Auth
    def get(self):
        self.nav_active['/settings'] = 'active'
        _data = self.db.query(Options).all()
        data = {}
        for i in _data:
            data[i.name] = {'id':i.id,'name':i.name,'value':i.value,'default':i.default_value}
        self.render('system/settings.html',data=data)


    @Auth
    def post(self):
        data = dict(
            primary_ns=self.get_argument('primary_ns') or None,
            second_ns = self.get_argument('second_ns') or None,
            resp_person = self.get_argument('resp_person') or None,
            rndc_host = self.get_argument('rndc_host') or None,
            rndc_port = self.get_argument('rndc_port') or None,
            rndc_algo = self.get_argument('rndc_algo') or None,
            rndc_secret = self.get_argument('rndc_secret') or None
        )
        for name in data:
            self.db.query(Options).filter_by(name=name).update({'value':data[name],'update_time': self.time})
        self.db.commit()
        return self.jsonReturn({'code': 0, 'msg': 'Success'})


