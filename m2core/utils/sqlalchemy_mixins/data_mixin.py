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
        """Get primary key properties for a SQLAlchemy cls.
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
        """Return a `list` of relationship names or the given model
        """
        return [c.key for c in cls.__mapper__.iterate_properties
                if isinstance(c, RelationshipProperty)]

    @classproperty
    def settable_relations(cls):
        """Return a `list` of relationship names or the given model
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
        Внутренний метод обработки параметров, переданных в запрос load_all, load_all_with_paginate
        :param initial_query экземпляр sqlalchemy Query, к которой мы дальше добавим все .filter()
        :return:
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
        self.set(**_params)
        return self.save()

    def set(self, **_params):
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
        Универсальный геттер атрибутов из самой sqlalchemy-модели
        :param item:
        :return:
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
        Возвращает объект по значению переданного PK
        """
        try:
            return cls.q.get(_pk)
        except SQLAlchemyError:
            cls.s.rollback()
            raise

    @classmethod
    def load_by_params(cls, **_params):
        """
        Возвращает объект по значению переданных пар столбец->значение
        """
        try:
            return cls._prepare_parametrized_queue(**_params).first()
        except SQLAlchemyError:
            cls.s.rollback()
            raise

    @classmethod
    def load_or_create(cls, **_params):
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
        Универсальный метод для создания нового экземпляра модели для последующего присвоения некоторых атрибутов
        и добавления этого экземпляра в БД
        :return:
        """
        cls_inst = cls()
        cls_inst = cls_inst.set(**_params)
        cls_inst.save()
        return cls_inst

    def save(self):
        """
        Сохраняем изменения в БД (если есть поле `updated` - изменяет его значение на текущее время)
        """
        try:
            # если есть поле updated - сохраняем его с now()
            if 'updated' in self.columns and self.get('updated') is not None:
                self.set(updated=text('now()'))
            self.s.add(self)
            self.s.commit()
            return self
        except SQLAlchemyError:
            self.s.rollback()
            raise

    def delete(self):
        """Removes the model from the current entity session and mark for deletion.
        """
        try:
            self.s.delete(self)
            self.s.commit()
        except SQLAlchemyError:
            self.s.rollback()
            raise

    def data(self, *_except_fields):
        """
        Получить экземлпяр модели. Удобно для использования, например, в хэндлерах, когда мы хотим в json запихнуть
        всю модель целиком, не исколючая никаких ее атрибутов. А дальше, в self.write_json() сработает
        AlchemyJSONEncoder, у которого неплохо получается приводить типы данных к типам JSON'а по всем стандартам.
        В _except_fields можно указать название полей таблицы, которые не должны попасть в итоговую выборку. Например,
        это может быть `password`
        можно также дропать поля из итоговой выборки с учетом вложенности, пример:
            data('photo_id', '>id', '>author_id')
        дропнет в следующей выборке:
            {
                "email": null,
                "total_articles": 3,
                "created": "2017-06-29T16:18:37.389449+00:00",
                "iz_nick": "Алексей Самойлов",
                "creator_id": null,
                "note": "Был автоматически импортирован (увидели тут: http://iz.ru/news/641888)",
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
                "name": "Алексей Самойлов",
                "fathername": null,
                "gender": null,
                "birthday": null,
                "photo_id": null,
                "surname": null,
                "phone": null
            }
        photo_id, socials>id, socials>author_id
        """

        def model_to_dict(obj, ignore_fields=list(), visited_children=set(), back_relationships=set()):
            serialized_data = {c.key: getattr(obj, c.key) for c in obj.__table__.columns}
            relationships = class_mapper(obj.__class__).relationships
            visitable_relationships = [(name, rel) for name, rel in relationships.items() if
                                       name not in back_relationships and name not in _except_fields]

            # обработаем field. если есть `>` в начале имени поля - значит в текущей функции его не трогаем,
            # убираем `>` и передаем дальше в рекурсию
            ignore_in_cur_iteration = list()
            ignore_in_next_iteration = list()
            for field in ignore_fields:
                try:
                    pos = field.index('>')
                except ValueError:
                    pos = len(field)

                if pos == 0:
                    ignore_in_next_iteration.append(field[1:])
                else:
                    ignore_in_cur_iteration.append(field[:pos])

            for name, relation in visitable_relationships:
                if relation.backref:
                    if type(relation.backref) == str:
                        back_relationships.add(relation.backref)
                    elif type(relation.backref) == tuple:
                        back_relationships.add(relation.backref[0])
                relationship_children = getattr(obj, name)
                if relationship_children is not None:
                    if relation.uselist:
                        children = []
                        for child in [c for c in relationship_children if c not in visited_children]:
                            visited_children.add(child)
                            children.append(model_to_dict(child,
                                                          ignore_in_next_iteration,
                                                          visited_children,
                                                          back_relationships))
                        serialized_data[name] = children
                    else:
                        serialized_data[name] = model_to_dict(relationship_children,
                                                              ignore_in_next_iteration,
                                                              visited_children,
                                                              back_relationships)
            for field in ignore_in_cur_iteration:
                if field in serialized_data.keys():
                    serialized_data.pop(field)
            return serialized_data

        try:
            return model_to_dict(self, list(_except_fields))
        except SQLAlchemyError:
            self.s.rollback()
            raise

    @classmethod
    def count(cls, **_params):
        """
        Считает кол-во строк в выборке с параметрами средствами sql
        :param _params: пара поле_таблицы => значение, пример:
                        pub_date=(between, '2016-06-22 08:30:00', '2017-06-27 08:30:00'),
                        author_id=('>=', -13),
                        iz_id=777777,
        :return: число строк, скалярное значение
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
        Просто возвращает все объекты из БД, ничего не записывая в self._data с возможной фильтрацией по параметрам и
        пагинацией
        :param page: номер страницы, начиная с 1
        :param per_page: сколько выводить на странице
        :param _params: пара поле_таблицы => значение, пример:
                        pub_date=(between, '2016-06-22 08:30:00', '2017-06-27 08:30:00'),
                        author_id=('>=', -13),
                        iz_id=777777,
        :return: генератор с модельками результата
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
        Вовзращает json-схему всех таблиц в базе. Если передан флаг only_self=True то возвращает схему только по
        конкретной таблице (которую берет из класса cls)
        :param only_self:
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
