# holds mapping between human key prefixes and real Redis prefixes
minute = 60
hour = 60 * minute
day = 24 * hour

redis_scheme = {
    #
    # human-readable table name
    #           |
    #           |         prefix for key in Redis +
    #           |             key placeholder
    #           |                 |
    #           |                 |
    #           |                 |
    #           |                 |
    #           |                 |
    #           |                 |
    #           |                 |
    #           |                 |
    #           |                 |         key TTL in Redis (sec)
    #           V                 V                     V
    # mapping between token (key) and user id (value)
    'ACCESS_TOKENS_BY_HASH': {'prefix': 'at:%s', 'ttl': 3 * day},
    # mapping of user id and their tokens. we add unique symbols to key and after that we can find all user tokens
    # by requesting keys by mask `{user_id}_*`
    'ACCESS_TOKENS_BY_USER_ID': {'prefix': 'uat:%s_%s', 'ttl': 3 * day},
    # used to search all user tokens made via previous key (ACCESS_TOKENS_BY_USER_ID)
    'ACCESS_TOKENS_BY_USER_ID_PREFIX_ONLY': {'prefix': 'uat:%s*', 'ttl': 3 * day},
    # mapping of user id and his roles
    'USER_ROLES': {'prefix': 'ur:%s', 'ttl': -1},
    # mapping between role id and its permissions
    'ROLE_PERMISSIONS': {'prefix': 'rp:%s', 'ttl': -1},
}
