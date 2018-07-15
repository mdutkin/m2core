__author__ = 'Maxim Dutkin (max@dutkin.ru)'


class classproperty(property):
    def __get__(self, obj, objtype=None):
        return super(classproperty, self).__get__(objtype)

    def __set__(self, obj, value):
        super(classproperty, self).__set__(type(obj), value)

    def __delete__(self, obj):
        super(classproperty, self).__delete__(type(obj))


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
