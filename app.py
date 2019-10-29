import mysql.connector
import tkinter as tk
import tkinter.ttk as ttk

from drones import Drone, DroneStore
from operators import Operator, OperatorStore



class Application(object):
    """ Main application view - displays the menu. """

    def __init__(self, conn):
        # Initialise the stores
        self.drones = DroneStore(conn)
        self.operators = OperatorStore(conn)

        # Initialise the GUI window
        self.root = tk.Tk()
        self.root.title('Drone Allocation and Localisation')
        frame = tk.Frame(self.root)
        frame.pack(padx=10, pady=10)

        # Add in the buttons
        drone_button = tk.Button(
            frame, text="View Drones", command=self.view_drones, width=40, padx=5, pady=5)
        drone_button.pack(side=tk.TOP)
        operator_button = tk.Button(
            frame, text="View Operators", command=self.view_operators, width=40, padx=5, pady=5)
        operator_button.pack(side=tk.TOP)
        exit_button = tk.Button(frame, text="Exit System",
                                command=quit, width=40, padx=5, pady=5)
        exit_button.pack(side=tk.TOP)

    def main_loop(self):
        """ Main execution loop - start Tkinter. """
        self.root.mainloop()

    def view_operators(self):
        """ Display the operators. """
        # Instantiate the operators window
        # Display the window and wait
        wnd = OperatorListWindow(self)
        self.root.wait_window(wnd.root)

    def view_drones(self):
        """ Display the drones. """
        wnd = DroneListWindow(self)
        self.root.wait_window(wnd.root)


class ListWindow(object):
    """ Base list window. """

    def __init__(self, parent, title):
        # Add a variable to hold the stores
        self.drones = parent.drones
        self.operators = parent.operators

        # Initialise the new top-level window (modal dialog)
        self._parent = parent.root
        self.root = tk.Toplevel(parent.root)
        self.root.title(title)
        self.root.transient(parent.root)
        self.root.grab_set()

        # Initialise the top level frame
        self.frame = tk.Frame(self.root)
        self.frame.pack(side=tk.TOP, fill=tk.BOTH,
                        expand=tk.Y, padx=10, pady=10)

    def add_list(self, columns, edit_action):
        # Add the list
        self.tree = ttk.Treeview(self.frame, columns=columns, show='headings')
        for col in columns:
            self.tree.heading(col, text=col.title())
        ysb = ttk.Scrollbar(self.frame, orient=tk.VERTICAL,
                            command=self.tree.yview)
        xsb = ttk.Scrollbar(self.frame, orient=tk.HORIZONTAL,
                            command=self.tree.xview)
        self.tree['yscroll'] = ysb.set
        self.tree['xscroll'] = xsb.set
        self.tree.bind("<Double-1>", edit_action)

        # Add tree and scrollbars to frame
        self.tree.grid(in_=self.frame, row=0, column=0, sticky=tk.NSEW)
        ysb.grid(in_=self.frame, row=0, column=1, sticky=tk.NS)
        xsb.grid(in_=self.frame, row=1, column=0, sticky=tk.EW)

        # Set frame resize priorities
        self.frame.rowconfigure(0, weight=1)
        self.frame.columnconfigure(0, weight=1)

    def close(self):
        """ Closes the list window. """
        self.root.destroy()
        
class OperatorListWindow(ListWindow):
    """ Window to display a list of drones. """

    def __init__(self, parent):
        super(OperatorListWindow, self).__init__(parent, 'Operators')

        # Add the list and fill it with data
        columns = ('Name', 'Class', 'Rescue', 'Operations', 'Drone')
        self.add_list(columns, self.edit_operator)
        self.populate_data()

        # Add the command buttons
        add_button = tk.Button(self.frame, text="Add Operator",
                               command=self.add_operator, width=20, padx=5, pady=5)
        add_button.grid(in_=self.frame, row=2, column=0, sticky=tk.E)
        exit_button = tk.Button(self.frame, text="Close",
                                command=self.close, width=20, padx=5, pady=5)
        exit_button.grid(in_=self.frame, row=3, column=0, sticky=tk.E)

    def populate_data(self):
        """ Populates the data in the view. """
        #print('TODO: Load data')
        # The following is a dummy record - need to remove and replace with data from the store
        #self.tree.insert('', 'end', values=(1, 'Test', 1, 'No', '<None>'))
        #self.tree.delete(self.tree.get_children())
        if self.tree.get_children():
            for i in self.tree.get_children():
                self.tree.delete(i)
        cursor = conn.cursor()
        query1 =  "SELECT CONCAT(OperatorStore.first_name,' ',OperatorStore.last_name), case when OperatorStore.drone_license = 1 then 'One' when OperatorStore.drone_license = 2 then 'Two' when OperatorStore.drone_license = NULL then '<None>' end as drone_license, \
                    case when rescue_endorsement = 1 then 'Yes' else 'No' end as Rescue, number_of_operations, case when OperatorStore.droneID is Null then '<None>' else CONCAT(DroneStore.ID,' :  ' ,DroneStore.name) end as Name FROM OperatorStore LEFT OUTER JOIN DroneStore on OperatorStore.droneID = DroneStore.ID"
        cursor.execute(query1)
        self.data = cursor.fetchall()
        count = 0
        for i in self.data:
            self.tree.insert('', count, values=(i[0], i[1], i[2], i[3], i[4]))
            count += 1
        cursor.close()

    def add_operator(self):
        """ Starts a new drone and displays it in the list. """
        # Start a new drone instance
 
        operator = Operator()
        # Display the drone
        self.view_operator(operator, self._save_new_operator)
        

    def _save_new_operator(self, operator):
        self.operators.add(operator)
        self.populate_data()

    def edit_operator(self, event):
        # Retrieve the identifer of the drone
        item = self.tree.item(self.tree.focus())
        
        operator = Operator()
        name = item['values'][0].split()
        operator.first_name = name[0]
        operator.last_name = name[1]
        operator.drone_license = item['values'][1]
        operator.rescue_endorsement = item['values'][2]
        operator.number_of_operations = item['values'][3]
        #,item['values'][1], item['values'][2], item['values'][3]
        
        # Display the drone
        self.view_operator(operator, self._update_operator)

    def _update_operator(self, operator):
        """ Saves the new details of the drone. """
        self.operators.update(operator)
        self.populate_data()

    def view_operator(self, operator, save_action):
        """ Displays the drone editor. """
        wnd = OperatorEditorWindow(self, operator, save_action)
        self.root.wait_window(wnd.root)


class DroneListWindow(ListWindow):
    """ Window to display a list of drones. """

    def __init__(self, parent):
        super(DroneListWindow, self).__init__(parent, 'Drones')

        # Add the list and fill it with data
        columns = ('id', 'Name', 'Class', 'Rescue', 'Operator')
        self.add_list(columns, self.edit_drone)
        self.populate_data()

        # Add the command buttons
        add_button = tk.Button(self.frame, text="Add Drone",
                               command=self.add_drone, width=20, padx=5, pady=5)
        add_button.grid(in_=self.frame, row=2, column=0, sticky=tk.E)
        exit_button = tk.Button(self.frame, text="Close",
                                command=self.close, width=20, padx=5, pady=5)
        exit_button.grid(in_=self.frame, row=3, column=0, sticky=tk.E)

    def populate_data(self):
        """ Populates the data in the view. """
        #print('TODO: Load data')
        # The following is a dummy record - need to remove and replace with data from the store
        #self.tree.insert('', 'end', values=(1, 'Test', 1, 'No', '<None>'))
        #self.tree.delete(self.tree.get_children())
        if self.tree.get_children():
            for i in self.tree.get_children():
                self.tree.delete(i)
        cursor = conn.cursor()
        query1 =  "SELECT DroneStore.ID, name as Name, class_type as Class, case when rescue = 1 then 'Yes' else 'No' end as Rescue,\
                        CONCAT(OperatorStore.first_name,' ', OperatorStore.last_name) as Operator FROM DroneStore LEFT JOIN OperatorStore ON DroneStore.OperatorID = OperatorStore.ID ORDER BY DroneStore.ID ASC"
        cursor.execute(query1)
        self.data = cursor.fetchall()
        count = 0
        for i in self.data:
            self.tree.insert('', count, values=(i[0], i[1], i[2], i[3], i[4]))
            count += 1
        cursor.close()

    def add_drone(self):
        """ Starts a new drone and displays it in the list. """
        # Start a new drone instance
        #print('TODO: Start a new drone')
        #drone = Drone(id, name, class_type, rescue, operator)
        drone = Drone(None)
        # Display the drone
        self.view_drone(drone, self._save_new_drone)
        

    def _save_new_drone(self, drone):
        """ Saves the drone in the store and updates the list. """
        self.drones.add(drone)
        self.populate_data()

    def edit_drone(self, event):
        """ Retrieves the drone and shows it in the editor. """
        # Retrieve the identifer of the drone
        item = self.tree.item(self.tree.focus())
        item_id = item['values'][0]
        drone = Drone()
        # Load the drone from the store
        #print('TODO: Load drone with ID %04d' % (item_id))
        #drone = Drone(item['values'][0],item['values'][1], item['values'][2], item['values'][3])
        drone.id = item['values'][0]
        #print(drone.id)
        drone.name = item['values'][1]
        #print(drone.name)
        drone.class_type = item['values'][2]
        #print(drone.class_type)
        drone.rescue = item['values'][3]
        #print(drone.rescue)
        drone.operatorID = item['values'][4]
        # Display the drone
        self.view_drone(drone, self._update_drone)
        #print(drone.operatorID)

    def _update_drone(self, drone):
        """ Saves the new details of the drone. """
        self.drones.update(drone)
        self.populate_data()

    def view_drone(self, drone, save_action):
        """ Displays the drone editor. """
        wnd = DroneEditorWindow(self, drone, save_action)
        self.root.wait_window(wnd.root)


class EditorWindow(object):
    """ Base editor window. """

    def __init__(self, parent, title, save_action):
        # Initialise the new top-level window (modal dialog)
        self._parent = parent.root
        self.root = tk.Toplevel(parent.root)
        self.root.title(title)
        self.root.transient(parent.root)
        self.root.grab_set()

        # Initialise the top level frame
        self.frame = tk.Frame(self.root)
        self.frame.pack(side=tk.TOP, fill=tk.BOTH,
                        expand=tk.Y, padx=10, pady=10)

        ###### The following segment has been overridden in the DroneEditorWindow and OperatorEditorWindow ######
        '''# Add the editor widgets
        last_row = self.add_editor_widgets()

        # Add the command buttons
        add_button = tk.Button(self.frame, text="Save",
                               command=save_action, width=20, padx=5, pady=5)
        add_button.grid(in_=self.frame, row=last_row + 1, column=1, sticky=tk.E)
        exit_button = tk.Button(self.frame, text="Close",
                                command=self.close, width=20, padx=5, pady=5)
        exit_button.grid(in_=self.frame, row=last_row + 2, column=1, sticky=tk.E)'''
        ##########################################################################################################

    def add_editor_widgets(self):
        """ Adds the editor widgets to the frame - this needs to be overriden in inherited classes. 
        This function should return the row number of the last row added - EditorWindow uses this
        to correctly display the buttons. """
        return -1

    def close(self):
        """ Closes the editor window. """
        self.root.destroy()

class OperatorEditorWindow(EditorWindow):
    """ Editor window for drones. """

    def __init__(self, parent, operator, save_action):
        # TODO: Add either the drone name or <new> in the window title, depending on whether this is a new
        # drone or not
        if operator.first_name == None:
            super(OperatorEditorWindow, self).__init__(parent, 'Operator: <new>', self.save_operator)
        else:
            super(OperatorEditorWindow, self).__init__(parent, 'Operator: '+ operator.first_name + ' '+ operator.last_name, self.save_operator)
            
            
        self.drones = parent.drones
        self.operators = parent.operators
        
        self._firstname = None
        self._lastname = None
        self._class = None 
        self._rescue = None
        self._ops = None
        
        self._forUpdate = False
        self._operator = operator
        self._save_action = save_action
        
        last_row = self.add_editor_widgets()
        
        add_button = tk.Button(self.frame, text="Save", command=self.load_operator_details, width=20, padx=5, pady=5)
        add_button.grid(in_=self.frame, row=last_row + 1, column=1, sticky=tk.E)
        exit_button = tk.Button(self.frame, text="Close",
                                command=self.close, width=20, padx=5, pady=5)
        exit_button.grid(in_=self.frame, row=last_row + 2, column=1, sticky=tk.E)
              
        # TODO: Load drone details
    def load_operator_details(self):    
        
        self._operator.first_name = self._firstname.get()
        self._operator.last_name = self._lastname.get()
        classType = self._class.get()
        if classType == 'One':
            self._operator.drone_license = 1
        elif classType == 'Two':
            self._operator.drone_license = 2
        else:
            self._operator.drone_license = None
        
        self._operator.number_of_operations = self._ops.get()
        
        if int(self._operator.number_of_operations) >= 5:
            self._operator.rescue_endorsement = True
        else:
            self._operator.rescue_endorsement = False
        
        '''rescue_endorsement = self._rescue.get()
        if rescue_endorsement == "Yes":
            self._operator.rescue_endorsement = True
        else:
            self._operator.rescue_endorsement = False'''
        
        
        
        
        
        if self._forUpdate == False:
            #print(str(self._forUpdate) +"1")
            self._save_action(self._operator)
        else:
            #print(str(self._forUpdate)+"2")
            self.save_operator()

    def add_editor_widgets(self):
        """ Adds the widgets for editing a drone. """
        #print('TODO: Create widgets and populate them with data')
        tk.Label(self.frame, text = "First Name :").grid(row=0, column=0, sticky="W", pady=10)
        self._firstname = tk.Entry(self.frame, width=40)
        self._firstname.grid(row=0, column=1, sticky="W")
        
        tk.Label(self.frame, text = "Family Name :").grid(row=1, column=0, sticky="W", pady=10)
        self._lastname = tk.Entry(self.frame, width=40)
        self._lastname.grid(row=1, column=1, sticky="W")
        
        tk.Label(self.frame, text = "Drone License :").grid(row=3, column=0, sticky='W', pady=10)
        self._class = ttk.Combobox(self.frame, width = 10)
        self._class['values'] = ('One', 'Two', 'None')
        self._class.current(2)
        self._class.grid(row=3,column=1, sticky="E")

        tk.Label(self.frame, text = "Rescue Endorsement :").grid(row=4, column=0, sticky='W', pady=10)
        self._rescue = ttk.Combobox(self.frame, width = 10)
        self._rescue['values'] = ('Yes', 'No')
        self._rescue.grid(row=4,column=1, sticky="E")
        
        tk.Label(self.frame, text = "Rescue Operations :").grid(row=5, column=0, sticky='W', pady=10)
        self._ops = ttk.Spinbox(self.frame, from_=0, to=100, width = 10)
        self._ops .grid(row=5,column=1, sticky="E")
        
        if self._operator.first_name != None:
            self._firstname.insert(tk.INSERT, self._operator.first_name)
            self._forUpdate = True
        
        if self._operator.last_name != None:
            self._lastname.insert(tk.INSERT, self._operator.last_name)
            
        if self._operator.drone_license == 'One':
            self._class.current(0)
        elif self._operator.drone_license == 'Two':
            self._class.current(1)
        else:
            self._class.current(2)
            
        if self._operator.rescue_endorsement == 'Yes':
            self._rescue.current(0)
        else:
            self._rescue.current(1)
            
        if self._operator.number_of_operations != None:
            self._ops.insert(tk.INSERT, self._operator.number_of_operations)
       
        return 6

    def save_operator(self):
        """ Updates the drone details and calls the save action. """
        print('TODO: Update the drone from the widgets')
        self.operators.update(self._operator)
        #self._update_drone(self._drone)
        self._save_action(self._operator)

class DroneEditorWindow(EditorWindow):
    """ Editor window for drones. """

    def __init__(self, parent, drone, save_action):
        # TODO: Add either the drone name or <new> in the window title, depending on whether this is a new
        # drone or not
        if drone.name == None:
            super(DroneEditorWindow, self).__init__(parent, 'Drone: <new>', self.save_drone)
        else:
            super(DroneEditorWindow, self).__init__(parent, 'Drone: '+ drone.name, self.save_drone)
            
            
        self.drones = parent.drones
        self.operators = parent.operators
        
        self._name = None
        self._class = None 
        self._rescue = None
        
        self._forUpdate = False
        self._id = drone.id
        self._drone = drone
        self._save_action = save_action
        
        last_row = self.add_editor_widgets()
        
        add_button = tk.Button(self.frame, text="Save",
                               command=self.load_drone_details, width=20, padx=5, pady=5)
        add_button.grid(in_=self.frame, row=last_row + 1, column=1, sticky=tk.E)
        exit_button = tk.Button(self.frame, text="Close",
                                command=self.close, width=20, padx=5, pady=5)
        exit_button.grid(in_=self.frame, row=last_row + 2, column=1, sticky=tk.E)
              
        # TODO: Load drone details
    def load_drone_details(self):    
        
        self._drone.id = self._id
        self._drone.name = self._name.get()
        classType = self._class.get()
        if classType == 'One':
            self._drone.class_type = 1
        elif classType == 'Two':
            self._drone.class_type = 2
        else:
            self._drone.class_type = 3
        
        rescue = self._rescue.get()
        if rescue == "Yes":
            self._drone.rescue = True
        else:
            self._drone.rescue = False
        
        if self._forUpdate == False:
            #print(str(self._forUpdate) +"1")
            self._save_action(self._drone)
        else:
            #print(str(self._forUpdate)+"2")
            self.save_drone()

    def add_editor_widgets(self):
        """ Adds the widgets for editing a drone. """
        #print('TODO: Create widgets and populate them with data')
        tk.Label(self.frame, text = "Name :").grid(row=0, column=0, sticky="W", pady=10)
        self._name = tk.Entry(self.frame, width=40)
        self._name.grid(row=0, column=1, sticky="W")
        
        tk.Label(self.frame, text = "Drone Class :").grid(row=1, column=0, sticky='W', pady=10)
        self._class = ttk.Combobox(self.frame, width = 10)
        self._class['values'] = ('One', 'Two', 'Three')
        self._class.grid(row=1,column=1, sticky="W")

        tk.Label(self.frame, text = "Rescue :").grid(row=2, column=0, sticky='W', pady=10)
        self._rescue = ttk.Combobox(self.frame, width = 10)
        self._rescue['values'] = ('Yes', 'No')
        self._rescue.grid(row=2,column=1, sticky="W")
        
        if self._drone.name != None:
            self._name.insert(tk.INSERT, self._drone.name)
            self._forUpdate = True
            
        if self._drone.class_type == 1:
            self._class.current(0)
        elif self._drone.class_type == 2:
            self._class.current(1)
        else:
            self._class.current(2)
            
        if self._drone.rescue == 'Yes':
            self._rescue.current(0)
        else:
            self._rescue.current(1)
       
        return 3

    def save_drone(self):
        """ Updates the drone details and calls the save action. """
        print('TODO: Update the drone from the widgets')
        self.drones.update(self._drone)
        #self._update_drone(self._drone)
        self._save_action(self._drone)
        

if __name__ == '__main__':
    conn = mysql.connector.connect(user='zrah502',
                                       password='6fa4ba59',
                                       host='studdb-mysql.fos.auckland.ac.nz',
                                       database='stu_zrah502_COMPSCI_280_C_S2_2019',
                                       charset='utf8') 
    app = Application(conn)
    app.main_loop()
    conn.close()
