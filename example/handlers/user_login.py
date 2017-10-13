from m2core.bases.base_handler import BaseHandler, http_statuses
from m2core.m2core import M2Core
from tornado import gen
from json.decoder import JSONDecodeError
from sqlalchemy import exc
from tornado.escape import json_decode
from voluptuous import Required, Schema, All, Length, Email, In
from example.models import User

exceptions_list = [
    (JSONDecodeError, http_statuses['WRONG_REQUEST']),
    (exc.SQLAlchemyError, http_statuses['WRONG_PARAM']),
    (TypeError, {'code': 500, 'msg': 'Some error occurred on server side'})
]


class UsersLoginHandler(BaseHandler):
    """User authorization"""
    @gen.coroutine
    @M2Core.tryex(*exceptions_list)
    def post(self):
        """Authorizes user by email+pass, gets token, expire and user info in return
        input_json = {
            'email': 'max@dutkin.ru',
            'password': 'un3ncrypt3d_p@$$'
        }"""
        # data validation scheme
        validate = Schema({
            Required('email'): All(Email(msg='`email` did not pass validation')),
            Required('password'): All(Length(min=6, max=32, msg='`password` length is not enough')),
        })

        data = json_decode(self.request.body)
        validate(data)

        access_token = User.authorize(
            data['email'],
            data['password']
        )

        if access_token:
            self.write_json(
                code=http_statuses['OK']['code'],
                msg=http_statuses['OK']['msg'],
                data=access_token
            )
        else:
            self.write_json(
                code=http_statuses['WRONG_CREDENTIALS']['code'],
                msg=http_statuses['WRONG_CREDENTIALS']['msg'],
            )
