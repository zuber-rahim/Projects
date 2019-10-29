from datetime import date


class Operator(object):
    """ Stores details on an operator. """

    def __init__(self, id=None, first_name=None, last_name=None, date_of_birth=None, drone_license=None, rescue_endorsement=False, number_of_operations=0, drone=None):
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.date_of_birth = date_of_birth
        self.drone_license = drone_license
        self.rescue_endorsement = rescue_endorsement
        self.number_of_operations = number_of_operations
        self.drone = drone


class OperatorAction(object):
    """ A pending action on the OperatorStore. """

    def __init__(self, operator, commit_action):
        self.operator = operator
        self.messages = []
        self._commit_action = commit_action
        self._committed = False

    def add_message(self, message):
        """ Adds a message to the action. """
        self.messages.append(message)

    def is_valid(self):
        """ Returns True if the action is valid, False otherwise. """
        return len(self.messages) == 0

    def commit(self):
        """ Commits (performs) this action. """
        if self._committed:
            raise Exception("Action has already been committed")

        self._commit_action(self.operator)
        self._committed = True


class OperatorStore(object):
    """ Stores the operators. """

    def __init__(self, conn=None):
        self._operators = {}
        self._last_id = 0
        self._conn = conn

    def add(self, operator):
        """ Starts adding a new operator to the store. """
        '''action = OperatorAction(operator, self._add)
        check_age = True
        if operator.first_name is None:
            action.add_message("First name is required")
        if operator.date_of_birth is None:
            action.add_message("Date of birth is required")
            check_age = False
        if operator.drone_license is None:
            action.add_message("Drone license is required")
        if check_age and operator.drone_license == 2:
            today = date.today()
            age = today.year - operator.date_of_birth.year - \
                ((today.month, today.day) < (
                    operator.date_of_birth.month, operator.date_of_birth.day))
            if age < 20:
                action.add_message(
                    "Operator should be at least twenty to hold a class 2 license")
        if operator.rescue_endorsement and operator.operations < 5:
            action.add_message(
                "To hold a rescue drone endorsement, the operator must have been involved in ï¬�ve prior rescue operations")
        return action'''
        self.save(operator)

    def _add(self, operator):
        """ Adds a new operator to the store. """
        if operator.id in self._operators:
            raise Exception('Operator already exists in store')
        else:
            self._last_id += 1
            operator.id = self._last_id
            self._operators[operator.id] = operator

    def remove(self, operator):
        """ Removes a operator from the store. """
        if not operator.id in self._operators:
            raise Exception('Operator does not exist in store')
        else:
            del self._operators[operator.id]

    def get(self, id):
        """ Retrieves a operator from the store by its ID or name. """
        if isinstance(id, str):
            for op in self._operators:
                if (op.first_name + ' ' + op.family_name) == id:
                    return op
            return None
        else:
            if not id in self._operators:
                return None
            else:
                return self._operators[id]

    def list_all(self):
        """ Lists all the _operators in the system. """
        for _operator in self._operators:
            yield _operator

    def save(self, operator):
        """ Saves the store to the database. """
        cursor = self._conn.cursor()
        query = 'INSERT INTO OperatorStore (first_name, last_name, drone_license, rescue_endorsement, number_of_operations) VALUES (%s, %s, %s, %s, %s)'
        cursor.execute(query, (operator.first_name, operator.last_name, operator.drone_license, operator.rescue_endorsement, operator.number_of_operations))
        self._conn.commit()
        cursor.close() 
        
    def update(self, operator):
        """ Saves the store to the database. """
        cursor = self._conn.cursor()
        query = 'UPDATE OperatorStore SET drone_license = %s, rescue_endorsement = %s, number_of_operations = %s WHERE first_name = %s AND last_name = %s'
        cursor.execute(query, (operator.drone_license, operator.rescue_endorsement, operator.number_of_operations, operator.first_name, operator.last_name))
        self._conn.commit()
        cursor.close()   
