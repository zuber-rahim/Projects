from operators import Operator


class Drone(object):
    """ Stores details on a drone. """

    def __init__(self, id=None, name=None, class_type=1, rescue=False, operator=None):
        self.id = id
        self.name = name
        self.class_type = class_type
        self.rescue = rescue
        self.operator = operator


class DroneAction(object):
    """ A pending action on the DroneStore. """

    def __init__(self, drone, operator, commit_action):
        self.drone = drone
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

        self._commit_action(self.drone, self.operator)
        self._committed = True


class DroneStore(object):
    """ DroneStore stores all the drones for DALSys. """

    def __init__(self, conn=None):
        self._conn = conn

    def add(self, drone):
        """ Adds a new drone to the store. """
        self.save(drone)

    def remove(self, id):
        """ Removes a drone from the store. """
        cursor = self._conn.cursor()

        # check if drone exists
        drone = self.get(id)

        # remove the reference to this drone from the operator
        query = 'SELECT ID FROM OperatorStore WHERE droneID = %s'
        cursor.execute(query, (id,))
        record = cursor.fetchone()
        if record is not None:
            query = 'UPDATE OperatorStore SET droneID = %s WHERE ID = %s'
            cursor.execute(query, (None, record[0]))

        query = 'DELETE FROM DroneStore WHERE ID = %s'
        cursor.execute(query, (id,))

        cursor.close()

    def get(self, id):
        """ Retrieves a drone from the store by its ID. """
        cursor = self._conn.cursor()
        query = 'SELECT * FROM DroneStore WHERE ID = %s'
        cursor.execute(query, (id,))
        record = cursor.fetchone()

        if cursor.rowcount == 0 or record is None:
            raise Exception('Unknown drone')
        else:
            record = list(record)
            return Drone(*record)
        cursor.close()

    def list_all(self, class_type='all', rescue='all'):
        """ Lists all the drones in the system. """

        # fetch all the records from the database
        cursor = self._conn.cursor()
        if class_type == 'all' and rescue == 'all':
            query = 'SELECT * FROM DroneStore ORDER BY name'
        elif class_type == 1 and rescue == 'all':
            query = 'SELECT * FROM DroneStore WHERE class_type = 1 ORDER BY name'
        elif class_type == 2 and rescue == 'all':
            query = 'SELECT * FROM DroneStore WHERE class_type = 2 ORDER BY name'
        elif class_type == 1 and rescue == 1:
            query = 'SELECT * FROM DroneStore WHERE class_type = 1 AND rescue = 1 ORDER BY name'
        elif class_type == 2 and rescue == 1:
            query = 'SELECT * FROM DroneStore WHERE class_type = 2 AND rescue = 1 ORDER BY name'
        elif class_type == 'all' and rescue == 1:
            query = 'SELECT * FROM DroneStore WHERE rescue = 1 ORDER BY name'

        cursor.execute(query)
        records = cursor.fetchall()
        cursor.close()

        # check if the records are empty
        if records == []:
            raise Exception('There are no drones for this criteria')

        # store all the records in drones
        drones = {}
        for record in records:
            record = list(record)
            drone = Drone(*record)
            drones[drone.id] = drone

        for drone in drones:
            yield drones[drone]

    def allocate(self, drone, operator):
        """ Starts the allocation of a drone to an operator. """

        # check if the drone exists
        drone = self.get(drone)  # raises exception if does not exits

        cursor = self._conn.cursor()
        first_name = operator[0]
        family_name = operator[1]
        query = 'SELECT * FROM OperatorStore WHERE Firstname = %s AND Lastname = %s'
        cursor.execute(query, (first_name, family_name))
        record = cursor.fetchone()

        # check if the operator exists
        if cursor.rowcount == 0 or record is None:
            print('Validation errors: ')
            choice = input(
                'Operator does not exist, do you want to add operator [Y/ n]? ').strip().lower()
            if choice == 'y' or choice == '':
                # make an operator with current values
                operator = Operator(None, first_name, family_name)

                # update the OperatorStore table in the database
                query = 'INSERT INTO OperatorStore (Firstname, Lastname, DateOfBirth, DroneLicence, rescueEndorsement, rescueOperations, droneID) VALUES (%s, %s, %s, %s, %s, %s, %s)'
                cursor.execute(query, (operator.first_name, operator.family_name, operator.date_of_birth,
                                       operator.drone_license, operator.rescue_endorsement, operator.operations, operator.drone))

                # fetch the last id added and set it to the id of the operator
                query = 'SELECT ID FROM OperatorStore ORDER BY ID DESC LIMIT 1'
                cursor.execute(query)
                id = cursor.fetchone()[0]
                operator.id = id
                print(f'Operator {first_name} {family_name} added')
            else:
                raise Exception('Allocation cancelled')
        else:
            record = list(record)
            operator = Operator(*record)

        action = DroneAction(drone, operator, self._allocate)

        if operator.drone is not None:
            action.add_message("Operator can only control one drone")
        if drone.operator is not None:
            query = 'SELECT Firstname, Lastname FROM OperatorStore WHERE droneID = %s'
            cursor.execute(query, (drone.id,))
            first_name, last_name = cursor.fetchone()
            action.add_message(
                f"Drone already allocated to {first_name} {last_name}")
        if operator.drone_license != drone.class_type:
            action.add_message(
                "Operator does not have correct drone license")
        if drone.rescue and not operator.rescue_endorsement:
            action.add_message("Operator does not have rescue endorsement")

        if action.messages == []:
            self._allocate(drone, operator)
        else:
            print('Validation errors:')
            while action.messages != []:
                print(f'- {action.messages[0]}')
                choice = input(
                    'Do you want to continue [Y/n]? ').strip().lower()
                if choice == 'y' or choice == '':
                    action.messages.pop(0)
                else:
                    raise Exception('Allocation cancelled')

        self._allocate(drone, operator)

        cursor.close()

    def _allocate(self, drone, operator):
        """ Performs the actual allocation of the operator to the drone. """
        if drone.operator is not None:
            # If the operator had a drone previously, we need to clean it so it does not
            # hold an incorrect reference
            cursor = self._conn.cursor()
            query = 'UPDATE OperatorStore SET droneID = %s WHERE ID = %s'
            cursor.execute(query, (None, drone.operator))
            cursor.close()
        if operator.drone is not None:
            # If the drone had a operator previously, we need to clean it so it does not
            # hold an incorrect reference
            cursor = self._conn.cursor()
            query = 'UPDATE DroneStore SET operatorID = %s WHERE ID = %s'
            cursor.execute(query, (None, operator.drone))
            cursor.close()

        operator.drone = drone.id
        drone.operator = operator.id
        self.update(drone, operator=operator)

    def save(self, drone):
        """ Saves the drone to the database. """     
        cursor = self._conn.cursor()
        query = 'INSERT INTO DroneStore (name, class_type, rescue, operatorID) VALUES (%s, %s, %s, %s)'
        cursor.execute(query, (drone.name, drone.class_type,
                               drone.rescue, drone.operator))
        self._conn.commit()
        cursor.close()

    def update(self, drone, operator=None, query=None):
        #print("its working")
        cursor = self._conn.cursor()
        sql = "UPDATE DroneStore SET name = %s, class_type = %s, rescue = %s WHERE ID = %s"
        values = (drone.name, drone.class_type, drone.rescue, drone.id)
        cursor.execute(sql, values)
        self._conn.commit()
        cursor.close()
