from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash
from flask_login import UserMixin
from flask_login import LoginManager

admin_type = "ADMIN"
user_type = "USER"

class LoginHandler(LoginManager):
    def __init__(self, server, neo_interface, login_graph_name):
        super().__init__(server)
        self.init_app(server)
        self.driver = neo_interface
        self.name = [login_graph_name]
        self.admin = self.get_admin()

    def add_admin(self, username, password):
        password = generate_password_hash(password)
        self.admin = User(username, password, self, is_admin=True)
        self._add_user(self.admin)
        return self.admin

    def add_user(self, username, password):
        password = generate_password_hash(password)
        user = User(username, password, self)
        self._add_user(user)
        return user
    
    def remove_user(self,username):
        self.driver.remove_node(key=username,type=user_type,
                                properties={"graph_name":self.name})
        self.driver.submit(log=False)

    def get_admin(self):
        res = self._node_query(admin_type)
        if res == []:
            return None
        return self._node_to_user(res[0])

    def get_user(self, username, password):
        if username == self.admin.username and self.admin.check_password(password):
            return User(username, password, self, is_admin=True)
        user = User(username, password, self)
        if self.is_user(user):
            return user
        return None

    def does_exist(self, username):
        if username == self.admin.username:
            return True
        for user in self.get_users():
            existing_user = user
            if username == existing_user.username:
                return True
        return False

    def get_users(self):
        return [self._node_to_user(u) for u in self._node_query(user_type)]

    def is_user(self, user):
        for eu in self.get_users():
            existing_user = eu
            if existing_user == user:
                return True
        return False

    def _node_to_user(self, node):
        nlabs = eval(node.get_key())
        if admin_type in nlabs:
            u_type = True
            nlabs.remove(admin_type)
        else:
            u_type = False
            nlabs.remove(user_type)
        return User(nlabs[0], node["password"], self, is_admin=u_type)

    def _add_user(self, user):
        u_type = admin_type if user.is_admin else user_type
        self.driver.add_node(user.username, u_type,
                             password=user.password, graph_name=self.name)
        self.driver.submit(log=False)

    def _node_query(self, u_type=None):
        return self.driver.node_query(u_type, graph_name=self.name)


class User(UserMixin):
    def __init__(self, username, password, manager, is_admin=False):
        self.username = username
        self.password = password
        self.is_admin = is_admin
        self._manager = manager

    def __eq__(self, other):
        if not isinstance(other, User):
            return False
        if other.username == self.username and self.check_password(other.password):
            return True
        return False

    def get_id(self):
        return self.username

    def set_password(self, password):
        self.password = password

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def is_authenticated(self):
        if self.is_admin:
            return True
        if self._manager.is_user(self):
            return True
        return False
