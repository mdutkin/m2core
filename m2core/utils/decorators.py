import functools
from tornado.web import HTTPError
from m2core.bases.base_handler import http_statuses
import jwt


def no_cache(func):
    """
    Decorator made to modify http-response to make it no_cache
    """
    def disable_caching(request_handler, *args, **kwargs):
        request_handler.set_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        request_handler.set_header('Pragma', 'no-cache')
        request_handler.set_header('Expires', 0)
        return func(request_handler, *args, **kwargs)

    return disable_caching


def authenticated_json(method):
    """Decorate methods with this to require that the user be logged in.

    If the user is not logged in, they will be redirected to the configured
    `login url <RequestHandler.get_login_url>`.

    If you configure a login url with a query parameter, Tornado will
    assume you know what you're doing and use it as-is.  If not, it
    will add a `next` parameter so the login page knows where to send
    you once you're logged in.
    """
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        if not self.current_user:
            raise HTTPError(http_statuses['WRONG_CREDENTIALS']['code'],
                            http_statuses['WRONG_CREDENTIALS']['msg'])
        return method(self, *args, **kwargs)

    return wrapper


def action_name(name):
    """
    Работает на функциях хэндлера
    :param name: 
    :return: 
    """
    def test(func_to_decorate):
        def new_func(*original_args, **original_kwargs):
            # Do whatever else you want here
            original_args[0].decorated_val = name
            return func_to_decorate(*original_args, **original_kwargs)
        return new_func
    return test


# TODO: We are not using JWT authorization, but maybe someday... )
secret_key = "my_secret_key"
options = {
    'verify_signature': True,
    'verify_exp': True,
    'verify_nbf': False,
    'verify_iat': True,
    'verify_aud': False
}


def authenticated_jwt(method):
    """Decorate methods with this to require that the user be logged in.

    If the user is not logged in, they will be redirected to the configured
    `login url <RequestHandler.get_login_url>`.

    If you configure a login url with a query parameter, Tornado will
    assume you know what you're doing and use it as-is.  If not, it
    will add a `next` parameter so the login page knows where to send
    you once you're logged in.
    """
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        def require_auth(handler, kwargs):

            auth = handler.request.headers.get('Authorization')
            if auth:
                try:
                    jwt.decode(
                        auth,
                        secret_key,
                        options=options
                    )

                except Exception:
                    raise HTTPError(http_statuses['WRONG_CREDENTIALS']['code'],
                                    http_statuses['WRONG_CREDENTIALS']['msg'])
            else:
                handler._transforms = []
                handler.write("Missing authorization")
                handler.finish()

            return True

        require_auth(self, kwargs)
        return method(self, *args, **kwargs)

    return wrapper


def jwtauth(handler_class):
    """
    Handle Tornado JWT Auth
    :param handler_class: 
    :return: 
    """
    def wrap_execute(handler_execute):
        def require_auth(handler, kwargs):

            auth = handler.request.headers.get('Authorization')
            if auth:
                parts = auth.split()

                if parts[0].lower() != 'bearer':
                    handler._transforms = []
                    handler.set_status(401)
                    handler.write("invalid header authorization")
                    handler.finish()
                elif len(parts) == 1:
                    handler._transforms = []
                    handler.set_status(401)
                    handler.write("invalid header authorization")
                    handler.finish()
                elif len(parts) > 2:
                    handler._transforms = []
                    handler.set_status(401)
                    handler.write("invalid header authorization")
                    handler.finish()

                token = parts[1]
                try:
                    jwt.decode(
                        token,
                        secret_key,
                        options=options
                    )

                except Exception as e:
                    handler._transforms = []
                    handler.set_status(401)
                    handler.write(e.message)
                    handler.finish()
            else:
                handler._transforms = []
                handler.write("Missing authorization")
                handler.finish()

            return True

        def _execute(self, transforms, *args, **kwargs):

            try:
                require_auth(self, kwargs)
            except Exception:
                return False

            return handler_execute(self, transforms, *args, **kwargs)

        return _execute

    handler_class._execute = wrap_execute(handler_class._execute)
    return handler_class
