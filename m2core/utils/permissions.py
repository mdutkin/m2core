class HandlerPermissions:
    def __init__(self):
        self.handler_settings = dict()
        self.all_permissions = set()

    def add_handler_rules(self, handler: str, rules: dict()):
        """
        Adds methods permissions, listed in `rules`, to `handler`
        :param handler: handler route
        :param rules: dict() with permissions per each method, i.e.: 
                    {
                        'get': ['perm1', 'perm2'],
                        'post': None,
                        'put': ['perm1', 'perm4'],
                        'delete': ['perm1', 'perm5'],
                    }
                    if there is None in permissions (like for `post` in this example - 
                    it disables this method)
        """
        self.handler_settings[handler] = rules
        for k, v in rules.items():
            if v:
                self.add_permission(*v)

    def add_handler_method_rules(self, human_route: str, method: str, rules: list()):
        """
        Adds method permissions to the corresponding method
        :param human_route: handler route
        :param method: handler method
        :param rules: permissions list. if None - METHOD NOT ALLOWED is being raised
        """
        if self.handler_settings.get(human_route):
            self.handler_settings[human_route].update({method: rules})
        else:
            self.handler_settings[human_route] = {method: rules}
        if rules:
            self.add_permission(*rules)

    def add_permission(self, *permissions: str):
        """
        Adds permissions to global permissions list
        :param permissions: enumerate all permissions you want to add as *args   
        """
        for permission in permissions:
            self.all_permissions.add(permission)

    def get_all_permissions(self) -> list:
        """
        Returns list of all permissions
        """
        return list(self.all_permissions)

    def get_all_permitted_handlers(self, user_permissions: list) -> dict:
        """
        Returns dict() of all available routes and their method depending on user permissions  
        :param user_permissions: list of user permissions
        """
        permitted_handlers = dict()
        for handler in self.handler_settings.keys():
            for method in self.handler_settings[handler].keys():
                method_permissions = self.handler_settings[handler][method]
                if method_permissions is not None and not (set(method_permissions)-set(user_permissions)):
                    if not permitted_handlers.get(handler, False):
                        permitted_handlers[handler] = list()
                    permitted_handlers[handler].append(method)
        return permitted_handlers

    def get_all_handler_settings(self) -> dict:
        """
        Returns dict() of all routes with their method permissions
        """
        return self.handler_settings

    def get_handler_method_permissions(self, human_route: str, method: str) -> list or None:
        """
        Returns permissions for specified route for specified method
        :param human_route: handler route
        :param method: handler method
        """
        method_permissions = list()
        if self.handler_settings.get(human_route, None) is not None:
            real_method_permissions = self.handler_settings[human_route].get(method, None)
            if real_method_permissions is not None:
                method_permissions = self.handler_settings[human_route][method]
            else:
                method_permissions = None
        else:
            method_permissions = None
        return method_permissions
