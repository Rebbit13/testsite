import sqlite3

DATABASE_FILE = 'db.db'


class DataBase:
    """
    Class to connect to a database
    uses sqlite3
    """
    def __init__(self):
        self.connection = sqlite3.connect(DATABASE_FILE)
        self.cursor = self.connection.cursor()

    @staticmethod
    def _form_db_format(list_: list):
        """
        method to form list ['el', 'el', 'el']
        to a form for database requests (el, el, el)
        :param list_: a list to reformat
        :return: str injection in format (el, el, el)
        """
        result = f'({list_[0]},'
        if len(list_) > 2:
            for el in list_[1:-1]:
                result += f' {el},'
        if len(list_) > 1:
            result += f' {list_[-1]})'
        else:
            result += ' )'
        return result

    def _form_inject_format(self, dict_):
        """
        method to form injections in requests
        :param dict_: a dict of values to insert to a db
                      in format {column name: value to insert}
        :return: keys in str format (el, el, el), values in tuple,
                 proxies in str format (?, ?, ?)
        """
        values = []
        keys = list(dict_.keys())
        proxies = []
        for key in keys:
            values.append(dict_[key])
            proxies.append('?')
        values = tuple(values)
        proxies = self._form_db_format(proxies)
        keys = self._form_db_format(keys)
        return keys, values, proxies

    @staticmethod
    def _form_set(dict_):
        """
        method to form set condition injections in requests
        :param dict_: provided conditions in dict
        :return: condition - to inject in request,
                 values - to send as an argument for a cursor.execute()
        """
        condition = ""
        values = []
        keys = list(dict_.keys())
        if len(keys) > 1:
            for key in keys[:-1]:
                condition += f'{key} = ?, '
                values.append(dict_[key])
        condition += f'{keys[-1]} = ?'
        values.append(dict_[keys[-1]])
        values = tuple(values)
        return condition, values

    @staticmethod
    def _form_where(dict_):
        """
        method to form where condition injections in requests
        :param dict_: provided conditions in dict
        :return: condition - to inject in request,
                 values - to send as an argument for a cursor.execute()
        """
        condition = "where "
        values = []
        keys = list(dict_.keys())
        if len(keys) > 1:
            for key in keys[:-1]:
                condition += f'{key} = ? and '
                values.append(dict_[key])
        condition += f'{keys[-1]} = ?'
        values.append(dict_[keys[-1]])
        values = tuple(values)
        return condition, values

    def insert(self, table_name: str, values: dict):
        """
        insert request to a database
        :param table_name: name of the table in db to search in
        :param values: a dict of values to insert to a
                       db in format {column name: value to insert}
        :return: None
        """
        with self.connection:
            values_dict = self._form_inject_format(values)
            keys = values_dict[0]
            values = values_dict[1]
            proxies = values_dict[2]
            self.cursor.execute(f"insert into {table_name} {keys} values {proxies}", values)

    def select(self, table_name: str, search: list = None, conditions: dict = None):
        """
        select request to a database
        :param table_name: name of the table in db to search in
        :param search: list of column's names in table to return in result,
                       if not provided return all columns of the table
        :param conditions: dict of condition values to inject in request, if not provided
                           return all records of the table
        :return: tuple of search results
        """
        with self.connection:
            if search is not None:
                search = ', '.join(search)
            else:
                search = '*'
            if conditions is not None:
                conditions = self._form_where(conditions)
                condition = conditions[0]
                values = conditions[1]
                result = self.cursor.execute(f"select {search} from {table_name} {condition}",
                                             values).fetchall()
            else:
                result = self.cursor.execute(f"select {search} from {table_name}").fetchall()
            return result

    def delete(self, table_name: str, conditions: dict):
        """
        delete request to a database
        :param table_name: name of the table in db to search in
        :param conditions: dict of condition values to inject in request
        :return: None
        """
        with self.connection:
            conditions = self._form_where(conditions)
            condition = conditions[0]
            values = conditions[1]
            self.cursor.execute(f"delete from {table_name} {condition}", values)

    def update(self, table_name: str, values: dict, conditions: dict):
        """
        update request to a database
        :param table_name: name of the table in db to search in
        :param values: a dict of values to insert to a
                       db in format {column name: value to insert}
        :param conditions: dict of condition values to inject in request
        :return: None
        """
        with self.connection:
            values_dict = self._form_set(values)
            values_condition = values_dict[0]
            inject_values = values_dict[1]
            conditions = self._form_where(conditions)
            condition = conditions[0]
            condition_values = conditions[1]
            values = inject_values + condition_values
            self.cursor.execute(f"update {table_name} set {values_condition} {condition}", values)
