import bcrypt
from m2core.bases.base_handler import BaseHandler, http_statuses
from m2core.m2core import M2Core
from m2core.utils.error import M2Error
from example.models import User
from tornado import gen
from tornado.options import options
from json.decoder import JSONDecodeError
from tornado.escape import json_decode
from sqlalchemy import exc, func
from voluptuous import Required, Optional, Schema, All, Length, Email, In
import bcrypt


exceptions_list = [
    (JSONDecodeError, http_statuses['WRONG_REQUEST']),
    (exc.SQLAlchemyError, http_statuses['WRONG_PARAM']),
    (TypeError, {'code': 500, 'msg': 'Some error occurred on server side'})
]


class AdminUsersHandler(BaseHandler):
    """Manages users on the admin level. All methods here requires authorization"""
    @gen.coroutine
    @M2Core.tryex(*exceptions_list)
    @M2Core.user_can
    def get(self, *args, **kwargs):
        """Get concrete user info by id or return info of your own"""
        self.validate_url_params(kwargs)

        if 'id' in kwargs.keys():
            # for admin handler - return info about every user with `id`
            user = User.load_by_pk(kwargs['id'])
            if not user:
                raise M2Error('User [%s] with access token [%s] could not be found in DB' %
                              (kwargs['id'], kwargs['access_token']))
        else:
            # id not specified - means request has come from non-admin handler and we simply return self info
            user = User.load_by_pk(self.current_user['id'])
            if not user:
                raise M2Error('User [%s] with access token [%s] could not be found in DB' %
                              (self.current_user['id'], self.current_user['access_token']))
        self.write_json(data=user.data('password'))

    @gen.coroutine
    @M2Core.tryex(*exceptions_list)
    @M2Core.user_can
    def post(self, *args, **kwargs):
        """Creates new user, input JSON has to be like:
        input_json = {
            'name': 'Max',
            'login': 'admin1',
            'password': 'un3ncrypt3d_p@$$',
            'email': 'max@dutkin.ru',
            'gender': 0
        }"""
        # incoming data check scheme
        validate = Schema({
            Required('name'): All(Length(min=2, max=32, msg='`name` length is not enough')),
            Required('password'): All(Length(min=6, max=32, msg='`password` length is not enough')),
            Required('email'): All(Email(msg='`email` did not pass validation')),
            Required('gender'): All(In([0, 1], msg='`gender` have to be defined correctly'))
        })

        data = json_decode(self.request.body)
        validate(data)

        password = data.pop('password')
        # data['password'] = func.crypt(password, func.gen_salt('bf', options.gen_salt))
        bytes_hash = bcrypt.hashpw(str.encode(password), bcrypt.gensalt(rounds=options.gen_salt))
        data['password'] = bytes_hash.decode()
        user = User.create(**data)

        # add default role
        user.add_role(options.default_role_name)

        self.write_json(
            code=http_statuses['CREATED']['code'],
            msg=http_statuses['CREATED']['msg'],
            data={
                'id': user.get('id')
            }
        )

    @gen.coroutine
    @M2Core.tryex(*exceptions_list)
    @M2Core.user_can
    def put(self, *args, **kwargs):
        """Modifies user in the system
        input_json = {
            'name': 'Max',
            'login': 'admin1',
            'password': 'un3ncrypt3d_p@$$',
            'email': 'max@dutkin.ru',
            'gender': 0
        }"""
        self.validate_url_params(kwargs)

        # incoming data check scheme
        validate = Schema({
            Optional('name'): All(Length(min=2, max=32, msg='`name` length is not enough')),
            Optional('password'): All(Length(min=6, max=32, msg='`password` length is not enough')),
            Optional('email'): All(Email(msg='`email` did not pass validation')),
            Optional('gender'): All(In([0, 1], msg='`gender` have to be defined correctly'))
        })

        data = json_decode(self.request.body)
        validate(data)

        if data.get('email'):
            raise M2Error('You are not allowed to change `login`', True)

        if 'id' in kwargs.keys():
            # edit info by user id
            user = User.load_by_pk(kwargs['id'])
            if not user:
                raise M2Error('User [%s] with access token [%s] could not be found in DB' %
                              (kwargs['id'], kwargs['access_token']))
        else:
            # edit self info
            user = User.load_by_pk(self.current_user['id'])
            if not user:
                raise M2Error('User [%s] with access token [%s] could not be found in DB' %
                              (self.current_user['id'], self.current_user['access_token']))

        if 'password' in data.keys():
            password = data.pop('password')
            bytes_hash = bcrypt.hashpw(str.encode(password), bcrypt.gensalt(rounds=options.gen_salt))
            data['password'] = bytes_hash.decode()
        user.set_and_save(**data)

        self.write_json(
            code=http_statuses['CREATED']['code'],
            msg=http_statuses['CREATED']['msg']
        )

    @gen.coroutine
    @M2Core.tryex(*exceptions_list)
    @M2Core.user_can
    def delete(self, *args, **kwargs):
        """Deletes user from DB"""
        self.validate_url_params(kwargs)

        if 'id' in kwargs.keys():
            # delete user by id
            user = User.load_by_pk(kwargs['id'])
            if not user:
                raise M2Error('User [%s] with access token [%s] could not be found in DB' %
                              (kwargs['id'], kwargs['access_token']))
        else:
            # delete self account
            user = User.load_by_pk(self.current_user['id'])
            if not user:
                raise M2Error('User [%s] with access token [%s] could not be found in DB' %
                              (self.current_user['id'], self.current_user['access_token']))

        user.delete()

        self.write_json(
            code=http_statuses['OK']['code'],
            msg=http_statuses['OK']['msg']
        )
