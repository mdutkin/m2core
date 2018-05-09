# holds mapping between human key prefixes and real Redis prefixes
minute = 60
hour = 60 * minute
day = 24 * hour
week = 7 * day
month = 31 * day

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
    #           |                 |         key TTL in Redis (sec), None - never expire
    #           V                 V                     V
    # mapping between token (key) and user id (value)
    'ACCESS_TOKENS_BY_HASH': {'prefix': 'at:%s', 'ttl': None},
    # mapping of user id and his roles
    'USER_ROLES': {'prefix': 'ur:%s', 'ttl': -1},
    # mapping between role id and its permissions
    'ROLE_PERMISSIONS': {'prefix': 'rp:%s', 'ttl': -1},
}
