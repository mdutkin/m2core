from sqlalchemy.orm import state
from tornado import escape

from sqlalchemy.ext.declarative import DeclarativeMeta
import json


# TODO: Rewrite all queries into simple way! Queries has to be cached on the server side!
# TODO: VERY IMPORTANT!!!! move all `difficult` db operations from this funcs to DB funcs
class AlchemyJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        def dump_sqlalchemy_obj(sqlalchemy_obj):
            fields = {}
            for field in [x for x in dir(sqlalchemy_obj)
                          if not x.startswith('_')  # sqlalch builtin attr
                and not x.startswith('rel_')  # for my attr, which are references to other tbls
                and x != 'metadata']:
                data = sqlalchemy_obj.__getattribute__(field)
                try:
                    # this will fail on non-encodable values, like other classes
                    # also deals with every type which has an `isoformat` attr, like
                    # datetime.datetime
                    if hasattr(data, 'isoformat'):
                        fields[field] = data.isoformat()
                    # # no need of this if we are not taking `rel_*` attrs
                    # elif isinstance(data.__class__, DeclarativeMeta): # an SQLAlchemy class
                    # fields[field] = dump_sqlalchemy_obj(data)
                    else:
                        fields[field] = dump_sqlalchemy_obj(data) if isinstance(data.__class__,
                                                                                DeclarativeMeta) else data
                except TypeError:
                    fields[field] = None
            # a json-encodable dict
            return fields

        if isinstance(obj, state.InstanceState):
            return None
        if isinstance(obj.__class__, DeclarativeMeta):  # an SQLAlchemy class
            return dump_sqlalchemy_obj(obj)
        if isinstance(obj, bytes):
            return escape.to_unicode(obj)
        if hasattr(obj, 'isoformat'):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)
