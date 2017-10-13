from m2core.utils.data_helper import DataHelper


class SessionHelper:
    """
    This helper class is used to interact with Redis to get and store user access tokens, permissions and roles
    """
    def __init__(self, redis_connector, redis_scheme):
        self._current_user = None
        self._current_role_id = None
        self._current_token = None
        self._redis = redis_connector
        self._redis_scheme = redis_scheme
        self.__inited = False

    def get_user_id(self) -> None or int:
        """
        Returns user id from Redis (if found)
        :return: 
        """
        self._check_inited()

        return self._current_user

    def get_token(self) -> str:
        """
        Returns access token from Redis
        :return: 
        """
        self._check_inited()

        return self._current_token

    def generate_token(self, user_id: int) -> dict:
        """
        Generates token per specified user, stores it in Redis and returns generated token with expiration info
        :param user_id: 
        :return: 
        """
        # generate token
        token = '%s_%s' % (DataHelper.random_hex_str(8), DataHelper.random_hex_str(32))
        # store in Redis in access tokens table, and also store it in user's access tokens table
        self._redis.set(
            self._redis_scheme['ACCESS_TOKENS_BY_HASH']['prefix'] % token,
            user_id,
            ex=self._redis_scheme['ACCESS_TOKENS_BY_HASH']['ttl'],
        )
        self._redis.set(
            self._redis_scheme['ACCESS_TOKENS_BY_USER_ID']['prefix'] % (user_id, DataHelper.random_char(6).lower()),
            token,
            ex=self._redis_scheme['ACCESS_TOKENS_BY_USER_ID']['ttl'],
        )

        self._current_token = token
        self._current_user = user_id
        self.__inited = True

        return {
            'access_token': token,
            'expire': self._redis_scheme['ACCESS_TOKENS_BY_HASH']['ttl']
        }

    def update_token(self) -> dict:
        """
        Updates token - delete old one, generates new and stores it in Redis
        :return: 
        """
        self._check_inited()

        old_token = self._current_token
        # generate new
        token = '%s_%s' % (DataHelper.random_hex_str(8), DataHelper.random_hex_str(32))
        # store in Redis in access tokens table, and also store it in user's access tokens table
        self._redis.set(
            self._redis_scheme['ACCESS_TOKENS_BY_HASH']['prefix'] % token,
            self.get_user_id(),
            ex=self._redis_scheme['ACCESS_TOKENS_BY_HASH']['ttl'],
        )
        self._redis.set(
            self._redis_scheme['ACCESS_TOKENS_BY_USER_ID']['prefix'] % (self.get_user_id(),
                                                                        DataHelper.random_char(6).lower()),
            token,
            ex=self._redis_scheme['ACCESS_TOKENS_BY_USER_ID']['ttl'],
        )

        self.__delete_token(old_token)

        return {
            'access_token': token,
            'expire': self._redis.ttl(self._redis_scheme['ACCESS_TOKENS_BY_HASH']['prefix'] % token),
            'user_id': self.get_user_id()
        }

    def logout(self):
        """
        Logouts user by it's access token (other access tokens are still valid)
        """
        self._check_inited()

        self.__delete_token(self._current_token)

    def __delete_token(self, token: str):
        """
        Deletes access token from 2 Redis tables
        :param token: access token to delete
        """
        self._check_inited()

        # delete old token from tokens table
        self._redis.delete(self._redis_scheme['ACCESS_TOKENS_BY_HASH']['prefix'] % token)
        # and also delete it from user's tokens table
        for key in self._redis.keys(self._redis_scheme['ACCESS_TOKENS_BY_USER_ID_PREFIX_ONLY']['prefix'] %
                                    self._current_user):
            redis_val = self._redis.get(key)
            if redis_val == token:
                self._redis.delete(key)
                break

    def dump_role_permissions(self, role_id, permissions):
        """
        Stores (rewrites) role permissions in Redis
        """
        # get existing permissions
        existing_permissions = self._redis.smembers(self._redis_scheme['ROLE_PERMISSIONS']['prefix'] % role_id)
        for permission in permissions:
            if permission not in existing_permissions:
                self._redis.sadd(self._redis_scheme['ROLE_PERMISSIONS']['prefix'] % role_id, permission)

        for permission in existing_permissions:
            if permission not in permissions:
                self._redis.srem(self._redis_scheme['ROLE_PERMISSIONS']['prefix'] % role_id, permission)

    def dump_user_roles(self, user_id: int, role_ids: list):
        """
        Stores (rewrites) user roles list in Redis
        """
        # delete all existing roles
        self._redis.delete(self._redis_scheme['USER_ROLES']['prefix'] % user_id)
        # and add new ones
        if len(role_ids):
            self._redis.sadd(self._redis_scheme['USER_ROLES']['prefix'] % user_id, *role_ids)

    def get_user_permissions(self):
        """
        Returns all user permissions based on it's roles
        """
        self._check_inited()

        # get user role ids
        redis_val = self._redis.smembers(
            self._redis_scheme['USER_ROLES']['prefix'] % self._current_user
        )
        group_ids = [int(role_id) for role_id in redis_val]
        all_permissions = set()
        for group_id in group_ids:
            # get permissions per each role by role id
            permissions = self._redis.smembers(
                self._redis_scheme['ROLE_PERMISSIONS']['prefix'] % group_id
            )
            for permission in permissions:
                all_permissions.add(permission)
        return all_permissions

    def _check_inited(self):
        """
        Check if instance was inited with user's data or not
        :return: 
        """
        if not self.__inited:
            raise Exception('Session is not inited')

    def init_user(self, _access_token: str):
        """
        Init current instance with user access token. This is the place were data per user is requested from Redis
        :param _access_token: 
        :return: 
        """
        # TODO: update EXP if token is valid or think of re-requesting new AT ?
        redis_val = self._redis.get(
            self._redis_scheme['ACCESS_TOKENS_BY_HASH']['prefix'] % _access_token
        )

        self._current_user = int(redis_val) if redis_val else None
        self._current_token = _access_token
        self.__inited = True
