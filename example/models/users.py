from sqlalchemy import Column, BigInteger, Integer, String, func
import bcrypt
from m2core.data_schemes.db_system_scheme import M2UserRoles, M2Roles, M2Error, BaseModel, CreatedMixin


class User(BaseModel, CreatedMixin):
    id = Column(BigInteger, primary_key=True)
    email = Column(String(100), nullable=False, unique=True)
    password = Column(String(255))
    name = Column(String(255), info={'custom_param_for_json_scheme_1': '11111', 'custom_param_for_json_scheme_2': True})
    gender = Column(Integer, nullable=False)

    @classmethod
    def authorize(cls, _email: str, _password: str) -> dict or None:
        """
        Authorize user and save his access token to Redis
        :param _email: user email
        :param _password: user password
        """
        user_obj = cls.q.filter(
            func.lower(cls.email) == _email.lower(),
            # cls.password == func.crypt(_password, cls.password)  <- this could be used for check in DB
        ).first()
        if not user_obj:
            return None

        # check authorization via python bcrypt, not postgres bcrypt
        if not bcrypt.checkpw(str.encode(_password), str.encode(user_obj.get('password'))):
            return None

        access_token = cls.sh.generate_token(user_obj.get('id'))
        access_token['user_info'] = user_obj.data('password')
        return access_token

    def add_role(self, _role_name: str):
        """
        Adds new role for user. User can have unlimited number of roles. If he already has this role - do nothing
        :param _role_name: role name
        """
        role = M2Roles.load_by_params(name=_role_name)
        if not role:
            raise M2Error('Trying to add non-existent role', True)

        M2UserRoles.load_or_create(user_id=self.get('id'), role_id=role.get('id'))

        roles = [role.get('role_id') for role in self.get_roles()]
        self.sh.dump_user_roles(self.get('id'), roles)

    def get_roles(self) -> list:
        """
        Returns all user roles list
        :return: list of roles
        """
        user_roles = M2UserRoles.all(user_id=self.get('id'))
        return [role for role in user_roles]

    @classmethod
    def resync_all(cls):
        """
        Resyncs all users permissions between DB and Redis
        """
        entities = User.all(
            order_by='id asc',
        )

        for entity in entities:
            roles = [role.get('id') for role in entity.get_roles()]
            entity.sh.dump_user_roles(entity.get('id'), roles)
