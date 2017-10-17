# M2Core web framework

### Status
[![Build Status](https://travis-ci.org/mdutkin/m2core.svg?branch=master)](https://travis-ci.org/mdutkin/m2core.svg?branch=master)

M2Core is a framework build over Tornado web server. It helps you to build an effective REST API in a few minutes.
We use a mix of Tornado, SQLAlchemy and Redis. M2Core has lots of helpers to do you ordinary tasks while building handlers
for your REST API. Real benefits are achieved when you are making REST services in connection with PostgreSQL. Redis is used
in order to cache access tokens, roles and role permissions, so each authorization check is made without PostgreSQL participation.


### The list of main features:

* **rights management (completely cached in Redis)**

* **handy BaseModel mixin**

* **a bunch of decorators for permissions check, try-catch block and etc.**

* **automatic documentation in JSON per each method of each handler retrieved from docstrings**

* **DB schema in JSON with custom fields (we use it somehow in our React form generators)**

* **helper class for unit testing of REST API**



## Installation

install package in normal way via pip:

```bash
pip install m2core
```

required packages will install automatically



## Usage

M2Core uses `tornado.options` / `tornado.define` to set up configuration. Here is a list of settings with default values:

**Server options**

| Option name        | Description                                                                    | Type        | Default value                    |
|--------------------|--------------------------------------------------------------------------------|:-----------:|----------------------------------|
|debug               | Tornado debug mode                                                             | bool        | False                            |
|config_name         | Config name                                                                    | str         | config.py                        |
|admin_role_name     | Admin group name                                                               | str         | admins                           |
|default_role_name   | Default user group with login permissions                                      | str         | users                            |
|default_permission  | Default permission                                                             | str         | authorized                       |
|xsrf_cookie         | Enable or disable XSRF-cookie protection                                       | str or bool | False                            |
|cookie_secret       | Tornado cookie secret                                                          | str         | gfqeg4t023ty724ythweirhgiuwehrtp |
|server_port         | Tornado TCP server bind port                                                   | int         | 8888                             |
|locale              | Server locale for dates, times, currency and etc                               | str         | ru_RU.UTF-8                      |
|json_indent         | Number of `space` characters, which are used in json responses after new lines | int         | 2                                |
|thread_pool_size    | Pool size for background executor                                              | int         | 10                               |
|gen_salt            | Argument for gen_salt func in bcrypt module                                    | int         | 12                               |


**DB options**

| Option name    | Description                            | Type | Default value |
|----------------|----------------------------------------|:----:|---------------|
|debug_orm       | SQLAlchemy debug mode                  | bool | False         |
|pg_host         | Database host                          | str  | 127.0.0.1     |
|pg_port         | Database port                          | int  | 5432          |
|pg_port         | Database port                          | int  | 5432          |
|pg_db           | Database name                          | str  | m2core        |
|pg_user         | Database user                          | str  | postgres      |
|pg_password     | Database password                      | str  | password      |
|pg_pool_size    | Pool size for executor                 | int  | 40            |
|pg_pool_recycle | Pool recycle time in sec, -1 - disable | int  | -1            |


**Redis options**

| Option name | Description                  | Type | Default value |
|-------------|------------------------------|:----:|---------------|
|redis_host   | Redis host                   | str  | 127.0.0.1     |
|redis_port   | Redis port                   | int  | 6379          |
|redis_db     | Redis database number (0-15) | int  | 0             |


You can place your settings in root folder and name it `config.py`, or place it wherever you want and pass relative path to this config file via
`--config_name=my/cool/path/to/config.py` argument. You can read more about tornado.options [here](http://www.tornadoweb.org/en/stable/options.html).
By the way, **M2Core** also supports command-line parsing.

Here is an [Example REST API sources](https://github.com/mdutkin/m2core/tree/master/example). In this example I tried to show most important **M2Core** features.
All modules are documented, you can read description of each function in sources.

Rights management in **M2Core** is quite simple. You implement your handlers with inheritance from `BaseHandler`, then do something like:

```python
from handlers import AdminUsersHandler


m2core = M2Core()
human_route = r'/users/:{id:int}'
m2core.add_endpoint(human_route, AdminUsersHandler)
# or like that
m2core.add_endpoint_permissions(human_route, {
    'get': [options.default_permission, 'get_user_info'],
    'post': None,
    'put': [options.default_permission, 'update_user_info'],
    'delete': [options.default_permission, 'delete_user'],
})
```

This will set certain bunch of permissions per each method of each route you want. You may use the same handler again with different route with other permissions.
For further information read docs of `m2core.add_endpoint_permissions`.

I should say a few words about url mask. It supports it's own rules and later generates url for Tornado. Url masks can be like:

| Url mask                                          | Params | Rule description                                                                               |
|---------------------------------------------------|:------:|------------------------------------------------------------------------------------------------|
|/users/:{id}                                       | :id    | attribute, any type                                                                            |
|/users/:{id:int}                                   | :id    | int attribute, any length                                                                      |
|/users/:{id:int(2)}                                | :id    | int attribute, length is 2 numbers                                                             |
|/users/:{id:float}                                 | :id    | float attribute                                                                                |
|/users/:{id:float(3)}                              | :id    | float attribute, length is 3 numbers including `,`                                             |
|/users/:{id:float(2,5)}                            | :id    | float attribute, length is between 2 and 5 numbers including `,`                               |
|/users/:{id:string}                                | :id    | string, any length, without `/` symbol                                                         |
|/users/:{id:string(2)}                             | :id    | string,  length is 2 symbols, without `/` symbol                                               |
|/users/:{id:bool}                                  | :id    | bool flag, accepts only `0` or `1`                                                             |
|/users/:{id:int(0,\[0-100\])}                      | :id    | int, any length (0), but value must be between `0` and `100`                                   |
|/users/:{id:float(0,\[0-100\])}                    | :id    | float, any length (0), but value must be between `0` and `100`                                 |
|/users/:{id:string(0,\[string1;string2;string3\])} | :id    | string, any length (0), but value must be in list of values: ('string1', 'string2', 'string3') |