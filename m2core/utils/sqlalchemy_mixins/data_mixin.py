from .session_mixin import SessionMixin
from .decorators import classproperty
from sqlalchemy import func, asc, desc, text
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import RelationshipProperty, class_mapper
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.engine import reflection
from m2core.utils.error import M2Error
import operator
import copy


class DataMixin(SessionMixin):
    __abstract__ = True

    @classproperty
    def columns(cls):
        return inspect(cls).columns.keys()

    @classproperty
    def primary_keys_full(cls):
        """
        Get primary key properties for a SQLAlchemy cls.
        Taken from marshmallow_sqlalchemy
        """
        mapper = cls.__mapper__
        return [
            mapper.get_property_by_column(column)
            for column in mapper.primary_key
        ]

    @classproperty
    def primary_keys(cls):
        return [pk.key for pk in cls.primary_keys_full]

    @classproperty
    def relations(cls):
        """
        Return a `list` of relationship names or the given model
        """
        return [c.key for c in cls.__mapper__.iterate_properties
                if isinstance(c, RelationshipProperty)]

    @classproperty
    def settable_relations(cls):
        """
        Return a `list` of relationship names or the given model
        """
        return [r for r in cls.relations
                if getattr(cls, r).property.viewonly is False]

    @classproperty
    def hybrid_properties(cls):
        items = inspect(cls).all_orm_descriptors
        return [item.__name__ for item in items
                if type(item) == hybrid_property]

    @classproperty
    def hybrid_methods_full(cls):
        items = inspect(cls).all_orm_descriptors
        return {item.func.__name__: item
                for item in items if type(item) == hybrid_method}

    @classproperty
    def hybrid_methods(cls):
        return list(cls.hybrid_methods_full.keys())

    @classmethod
    def _prepare_parametrized_queue(cls, initial_query=None, **_params):
        """
        Private method for preparing query in method `all`, `load_by_params`, `count`
        :param initial_query sqlalchemy Query instance, which will be used for `.filter()`
        """
        ops = {
            '>': operator.gt,
            '<': operator.lt,
            '>=': operator.ge,
            '<=': operator.le,
            '=': operator.eq
        }

        if not initial_query:
            query = cls.q
        else:
            query = initial_query

        order_by = None
        if 'order_by' in _params.keys():
            order_by = _params.pop('order_by')

        for _field in _params.keys():
            param = _params[_field]
            if type(param) == tuple:
                if len(param):
                    first_param = param[0]
                    if callable(first_param):
                        query = query.filter(first_param(getattr(cls, _field), *param[1:]))
                    elif type(first_param) == str and first_param in ops.keys():
                        op = ops[first_param]
                        query = query.filter(op(getattr(cls, _field), param[1]))
            else:
                query = query.filter(getattr(cls, _field) == _params[_field])

        if order_by:
            order_by_params = order_by.split(' ')
            order_function = globals()[order_by_params[1]]
            query = query.order_by(order_function(getattr(cls, order_by_params[0]), ))
        return query

    @classproperty
    def settable_attributes(cls):
        return cls.columns + cls.hybrid_properties + cls.settable_relations

    def set_and_save(self, **_params):
        """
        Updates instance and permanently saves changes to DB
        :param _params: data to save
        """
        self.set(**_params)
        return self.save()

    def set(self, **_params):
        """
        Sets fields in instance without saving
        :param _params: data to save
        """
        try:
            for name in _params.keys():
                if name in self.settable_attributes:
                    setattr(self, name, _params[name])
                else:
                    raise M2Error('Error while trying to set non-existent property `%s`' % name)
            return self
        except SQLAlchemyError:
            self.s.rollback()
            raise

    def get(self, item):
        """
        Universal getter of attributes from sqlaclhemy model instance
        :param item: key
        :return: value
        """
        try:
            data = copy.deepcopy(getattr(self, item))
        except AttributeError:
            raise M2Error('Error while trying to get non-existent property `%s`' % item, False)
        except SQLAlchemyError:
            self.s.rollback()
            raise
        return data

    @classmethod
    def load_by_pk(cls, _pk):
        """
        Loads model by primary key
        """
        try:
            return cls.q.get(_pk)
        except SQLAlchemyError:
            cls.s.rollback()
            raise

    @classmethod
    def load_by_params(cls, **_params):
        """
        Loads model with filtering by params
        """
        try:
            return cls._prepare_parametrized_queue(**_params).first()
        except SQLAlchemyError:
            cls.s.rollback()
            raise

    @classmethod
    def load_or_create(cls, **_params):
        """
        Loads existing model or creates new with specified params
        :param _params:
        """
        result = cls.load_by_params(**_params)
        try:
            if not result:
                result = cls.create(**_params)
            return result
        except SQLAlchemyError:
            cls.s.rollback()
            raise

    @classmethod
    def create(cls, **_params):
        """
        Universal method for creation new empty model for further attribute settings and saving it to DB
        """
        cls_inst = cls()
        cls_inst = cls_inst.set(**_params)
        cls_inst.save()
        return cls_inst

    def save(self):
        """
        Saves changes to DB. If there is `updated` field in model - sets it's value to current time
        """
        try:
            # set `updated` field with current datetime
            if 'updated' in self.columns and self.get('updated') is not None:
                self.set(updated=text('now()'))
            self.s.add(self)
            self.s.commit()
            return self
        except SQLAlchemyError:
            self.s.rollback()
            raise

    def delete(self):
        """
        Removes the model from the current entity session and mark for deletion.
        """
        try:
            self.s.delete(self)
            self.s.commit()
        except SQLAlchemyError:
            self.s.rollback()
            raise

    def data(self, *_except_fields, **kwargs):
        """
        Dumps model to JSON. Also dumps all it's relations.
        Useful in handlers, where we want to return model in JSON to client.
        In `_except_fields` you can specify fields, which you don't want to see in an output JSON (i.e. `password`).
        You can also drop fields from nested models, i.e:
            data('photo_id', 'socials>id', 'socials>author_id')
        in the data:
            {
                "email": null,
                "total_articles": 3,
                "created": "2017-06-29T16:18:37.389449+00:00",
                "nick": "nick name",
                "creator_id": null,
                "note": "Some notes about user",
                "updated": "2017-06-29T16:18:37.389449+00:00",
                "id": 421,
                "socials": [
                    {
                        "author_id": 421,
                        "id": 1,
                        "link": "link1"
                    },
                    {
                        "author_id": 421,
                        "id": 2,
                        "link": "link2"
                    },
                    {
                        "author_id": 421,
                        "id": 3,
                        "link": "link3"
                    }
                ],
                "name": "User",
                "gender": null,
                "birthday": null,
                "photo_id": null,
                "surname": null,
                "phone": null
            }
        will drop:
            photo_id, socials>id, socials>author_id

        :param kwargs:
                `max_level` - maximum recursion level, 2 by default
        """

        _max_level = kwargs.get('max_level', 2)

        def model_to_dict(obj, ignore_fields=list(), back_relationships=set(), max_level=2,
                          current_level=0):
            current_level += 1
            ignore_in_cur_iteration = list()
            for field in ignore_fields:
                final_exclusion = len(field) == 1
                if final_exclusion:
                    ignore_in_cur_iteration.append(field[0])

            serialized_data = dict()
            for c in obj.__table__.columns:
                if c.key not in ignore_in_cur_iteration:
                    serialized_data[c.key] = getattr(obj, c.key)
            relationships = class_mapper(obj.__class__).relationships
            visitable_relationships = [(name, rel) for name, rel in relationships.items() if
                                       name not in back_relationships and name not in _except_fields]

            for name, relation in visitable_relationships:
                ignore_in_next_iteration = list()

                if name in ignore_in_cur_iteration:
                    continue

                for i in ignore_fields:
                    if len(i) > 1 and name == i[0]:
                        ignore_in_next_iteration.append(i[1:])

                if relation.backref:
                    if type(relation.backref) == str:
                        back_relationships.add(relation.backref)
                    elif type(relation.backref) == tuple:
                        back_relationships.add(relation.backref[0])
                relationship_children = getattr(obj, name)
                if relationship_children is not None:
                    if relation.uselist and current_level != max_level:
                        children = []
                        for child in [c for c in relationship_children]:
                            if current_level < max_level:
                                children.append(model_to_dict(child,
                                                              ignore_in_next_iteration,
                                                              back_relationships,
                                                              max_level,
                                                              current_level))
                        serialized_data[name] = children
                    else:
                        if current_level < max_level:
                            serialized_data[name] = model_to_dict(relationship_children,
                                                                  ignore_in_next_iteration,
                                                                  back_relationships,
                                                                  max_level,
                                                                  current_level)
            return serialized_data

        try:
            normalized_except_fields = []
            for f in _except_fields:
                normalized_except_fields.append(f.split('>'))
            return model_to_dict(self, ignore_fields=normalized_except_fields, max_level=_max_level)
        except SQLAlchemyError:
            self.s.rollback()
            raise

    @classmethod
    def count(cls, **_params):
        """
        Counts all rows in query with specified params via SQL
        :param _params: table_field => value, i.e.:
                        pub_date=(between, '2016-06-22 08:30:00', '2017-06-27 08:30:00'),
                        author_id=('>=', -13),
                        user_id=777777,
        :return: rows count, scalar value
        """
        try:
            query = cls.s.query(func.count())
            query = cls._prepare_parametrized_queue(query, **_params)
            return query.scalar()
        except SQLAlchemyError:
            cls.s.rollback()
            raise

    @classmethod
    def all(cls, page: int=0, per_page: int=0, **_params):
        """
        Simply returns all objects from DB, without initializing self._data and possible filtering by params and
        pagination
        :param page: page number, starts with 1
        :param per_page: page size
        :param _params: table_field => value, i.e.:
                        pub_date=(between, '2016-06-22 08:30:00', '2017-06-27 08:30:00'),
                        author_id=('>=', -13),
                        user_id=777777,
        :return: generator with rows from query result
        """
        try:
            query = cls._prepare_parametrized_queue(**_params)
            if page != 0 and per_page != 0:
                query = query.limit(per_page)
                query = query.offset((page - 1) * per_page)

            return query.all()
        except SQLAlchemyError:
            cls.s.rollback()
            raise

    @classmethod
    def schema(cls, only_self: bool=False):
        """
        Returns JSON-scheme of all tables from current DB. If you pass `only_self=True`, it returns only scheme for
        current table of model, which is taken from `cls`
        :param only_self: get JSON schema only for current cls
        :return:
        """
        try:
            md_tbls = cls.metadata.tables
            insp = reflection.Inspector.from_engine(cls.s.bind.engine)
            tbls = dict()
            for tbl in insp.get_table_names():
                if not only_self or (only_self and tbl == cls.__tablename__):
                    cols = dict()
                    for col in insp.get_columns(tbl):
                        info = dict(col)
                        col_info = md_tbls[tbl].c[col['name']]
                        info['type'] = {
                            'compiled': col['type'].compile(),
                            'native': col['type'].python_type.__name__
                        }
                        info['type']['length'] = col['type'].length if hasattr(col['type'], 'length') else None
                        if info['autoincrement']:
                            info['default'] = 'autoincrement'
                        info.update(col_info.info)
                        info['placeholder'] = '%s_%s' % (tbl, col['name'])
                        cols[col['name']] = info
                    tbls[tbl] = cols

            return tbls
        except SQLAlchemyError:
            cls.s.rollback()
            raise
