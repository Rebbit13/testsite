import hashlib
import random
import string
import time
from datetime import datetime


from pydantic import BaseModel
from db_connection import DataBase


def generate_token():
    """
    generate session token
    :return: rand string
    """
    letters_and_digits = string.ascii_letters + string.digits
    rand_string = ''.join(random.sample(letters_and_digits, 32))
    return rand_string


class Session(BaseModel):
    """
    class to create and check current session
    """
    id: int
    _table: str = 'session'
    token: str
    last_activity: str = None
    customer: int = None
    authorized: bool = False
    admin: int = None

    @staticmethod
    def create():
        """
        method to create new session
        :return: the entity of Session class
        """
        token = generate_token()
        last_activity = time.strftime("%Y-%m-%d, %H:%M:%S", time.localtime())
        DataBase().insert('session', {'token': token,
                                      'last_activity': last_activity})
        session_id = DataBase().select('session',
                                       ['id'],
                                       {'token': token,
                                        'last_activity': last_activity})[0][0]
        session = Session(id=session_id,
                          token=token,
                          last_activity=last_activity)
        return session

    @staticmethod
    def find(search_data: dict):
        """
        find session by search data
        :param search_data
        :return: the entity of Session class
        """
        result = DataBase().select('session', conditions=search_data)[0]
        session = Session(id=result[0],
                          token=result[1],
                          last_activity=result[2],
                          customer=result[3],
                          authorized=bool(result[4]))
        return session

    def _fill_attrs(self):
        """
        refresh session attrs
        :return: None (refresh last_activity, customer, authorized)
        """
        search = DataBase().select(self._table,
                                   conditions={'id': self.id,
                                               'token': self.token})[0]
        self.last_activity = search[2]
        self.customer = search[3]
        self.authorized = bool(search[4])
        self.admin = search[5]

    def _check_time_delta(self):
        """
        measure time delta between time now and last activity of the token
        :return: time delta in minutes
        """
        time_format = "%Y-%m-%d, %H:%M:%S"
        last_activity = datetime.strptime(self.last_activity, time_format)
        time_now = time.strftime(time_format, time.localtime())
        time_now = datetime.strptime(time_now, time_format)
        delta = time_now - last_activity
        return int(delta.seconds / 60)

    def check_session_live(self):
        """
        method to check if token valid and lives
        :return: bool
        """
        try:
            self._fill_attrs()
        except IndexError:
            return False
        delta = self._check_time_delta()
        if delta < 10:
            return True
        else:
            return False

    def auth(self, customer_id: int):
        """
        links session to a customer if authorize
        :param customer_id: id of the customer to link to the session
        :return: None
        """
        DataBase().update(self._table,
                          values={'customer': customer_id, 'authorized': True},
                          conditions={'id': self.id})

    def auth_admin(self, admin: int):
        """
        links session to a admin if authorize
        :param admin: id of the admin to link to the session
        :return: None
        """
        DataBase().update(self._table,
                          values={'admin': admin, 'authorized': True},
                          conditions={'id': self.id})


class Admin(BaseModel):
    """
    class to represent admin
    can add directly to db only
    """
    id: int = None
    _table: str = "admin"
    login: str
    password: str

    def check_password(self):
        """
        method to check password
        incrypt input password and check if it equal to the db one
        :return: bool
        """
        enc = hashlib.md5()
        enc.update(self.password.encode('utf-8'))
        self.password = enc.hexdigest()
        db = DataBase().select(self._table, ['id', 'password'], {'login': self.login})[0]
        admin_id = db[0]
        password_db = db[1]
        if self.password == password_db:
            self.id = admin_id
            self.password = '***'
            return True
        else:
            return False


class Banner(BaseModel):
    """
    class banner - some promotional items in frontend
    """
    id: int = None
    _table: str = "banner"
    alias: str
    title: str = None
    text: str = None
    pic: str = None

    @staticmethod
    def find(search_data: dict):
        """
        find banner by search data
        :param search_data:
        :return: the entity of Banner class
        """
        result = DataBase().select('banner', conditions=search_data)[0]
        banner = Banner(id=result[0],
                        alias=result[1],
                        title=result[2],
                        text=result[3],
                        pic=result[4])
        return banner

    def _fill_attrs(self):
        """
        refresh banner attrs
        :return: None (refresh attrs)
        """
        result = DataBase().select(self._table, conditions={'alias': self.alias})[0]
        self.id = result[0]
        self.title = result[2]
        self.text = result[3]
        self.pic = result[4]

    def add(self):
        """
        the method to add banner to a database
        change self.id to one, that added in the db
        :return: None (change self.id to one, added in the db)
        """
        DataBase().insert(self._table, dict(self))
        search = self.find({'alias': self.alias})
        self.alias = search.alias

    def update(self, values: dict):
        """
        update values in db
        :param values: values to update in db
        :return: None (refresh banner attrs after adding)
        """
        DataBase().update(self._table, values, conditions={'alias': self.alias})
        search = self.find({'alias': self.alias})
        self.id = search.id
        self.title = search.title
        self.text = search.text
        self.pic = search.pic


class Customer(BaseModel):
    """
    the class to validate, add, check, update customers data
    """
    id: int = None
    _table: str = "customer"
    telephone: int
    password: str
    name: str = None
    email: str = None
    personal_discount: str = 0

    @staticmethod
    def find(search_data: dict):
        """
        find first customer by search data
        :param search_data:
        :return: the entity of Customer class
        """
        result = DataBase().select('customer', conditions=search_data)[0]
        customer = Customer(id=result[0],
                            telephone=result[1],
                            password='***',
                            name=result[3],
                            email=result[4],
                            personal_discount=result[5])
        return customer

    def _fill_attrs(self):
        """
        refresh customer attrs
        :return: None (refresh data)
        """
        result = DataBase().select(self._table, conditions={'telephone': self.telephone})[0]
        self.id = result[0]
        self.password = '***'
        self.name = result[3]
        self.email = result[4]
        self.personal_discount = result[5]

    def add(self):
        """
        the method to add customer to a database
        incript self password
        change self.id to one, that added in the db
        :return: None (change self.id to one, added in the db)
        """
        enc = hashlib.md5()
        enc.update(self.password.encode('utf-8'))
        self.password = enc.hexdigest()
        DataBase().insert(self._table, dict(self))
        search = self.find({'telephone': self.telephone})
        self.id = search.id
        self.password = '***'

    def update(self, values: dict):
        """
        update values in db
        :param values: values to update in db
        :return: None (refresh customer attrs after adding)
        """

        DataBase().update(self._table, values, conditions={'id': self.id})
        search = self.find({'id': self.id})
        self.telephone = search.telephone
        self.password = search.password
        self.name = search.name
        self.email = search.email
        self.personal_discount = search.personal_discount

    def check_password(self, password):
        """
        method to check password
        incrypt input password and check if it equal to the db one
        :param password: input password to check
        :return: Bool
        """
        try:
            check = DataBase().select(self._table, ['password'], {'telephone': self.telephone})[0][0]
        except IndexError:
            return False
        enc = hashlib.md5(password.encode('utf-8'))
        password = enc.hexdigest()
        if check == password:
            self._fill_attrs()
            return True
        else:
            return False


class Product(BaseModel):
    """
    class for  products to sell
    """
    id: int = None
    _table: str = "product"
    name: str = None
    type: str = None
    price: int = None
    discount_check: bool = None
    pic: str = None

    def find_many(self, search_data: dict = None):
        """
        find products by condition
        :param search_data: dict of conditions to search
        :return: list of products
        """
        result = DataBase().select(self._table, conditions=search_data)
        list_ = []
        for product in result:
            product = Product(id=product[0],
                              name=product[1],
                              type=product[2],
                              price=product[3],
                              discount_check=bool(product[4]),
                              pic=product[5])
            list_.append(product)
        return list_

    def _fill_attrs(self):
        """
        refresh product attrs
        :return: None (refresh data)
        """
        result = DataBase().select(self._table, conditions={'id': self.id})[0]
        self.name = result[1]
        self.type = result[2]
        self.price = result[3]
        self.discount_check = result[4]
        self.pic = result[5]

    def add(self):
        """
        add product to a database from exemplar of the class
        :return: None (change self.id)
        """
        DataBase().insert(self._table, dict(self))
        search = self.find_many({'name': self.name, 'type': self.type})[0]
        self.id = search.id
        self._fill_attrs()

