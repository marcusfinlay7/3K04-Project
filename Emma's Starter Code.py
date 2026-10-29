# Automated Dispensing Cabinet

# This code currently is able to:
# - verify a user's ID and assign their role (very basic right now, would change it to lists of valid IDs later)
# - can assign which functions can be done in specific modes, and who has access to those functions
# - has methods for dispensing and replenishing medication, and also updating inventory
# - has a simple handling fault method
# - kind of has an event logging system? will probably need to work on that and having things stored in one whole log
# - has tons of test cases for user input (quantity of medication, menu options, medication names, etc.)

# Things that still need to be done:
# - add max inventory limits
# - add method that can 'send' log to monitoring system
# - add that technicians can view logs? (or is this just done through monitoring system?)
# - make a list of potential faults (if we want to have specific ones) and every time the program runs, it chooses True/False at random (to simulate faults happening randomly)
# - give user the option to 'quit' program at any point (can break while loops at any time)
# - want to assign specific faults to the mistakes made? (ex. incorrect ID can be authentication error which would be logged)
# - 3x failed authentication (per session) before fault mode
# - lock/open cabinet?

# Login IDs:
# 12345 - nurse
# 23456 - pharmacist
# 34567 - technician 
# -anything else will be invalid


import random

# This class checks the user's ID, identifies their role, and returns the verified user
class AccessControl:
    def __init__(self):
        self.verified_users = {
            "12345": "Nurse",
            "23456": "Pharmacist",
            "34567": "Technician"
        }

    def authenticate(self, user_id):
        if user_id in self.verified_users:
            return self.verified_users[user_id] #return role of verified role

        return None #invalid ID

class ModeManager:
    def __init__(self):
        self.mode = "Normal" #cabinet starts in normal mode (unless fault is implemented)

    def set_mode(self, new_mode):
        self.mode = new_mode

    def allows(self, role, action): #checks whether a role can perform an action in the current operating mode
        if self.mode == "Normal":
            return role == "Nurse" and action == "Dispense"

        elif self.mode == "Replenishing":
            return role == "Pharmacist" and action == "Replenish"

        elif self.mode == "Fault":
            return role == "Technician" and action == "handle_fault"

        return False

class InventoryManager:
    def __init__(self):
        self.inventory = {
            "Ibuprofen": 20,
            "Antibiotics": 25,
            "Antibacterials": 15
        }

    def display_inventory(self):
        print("\n--- Medication Inventory ---")

        for medication, quantity in self.inventory.items():
            print(f"{medication}: {quantity} units")

    def dispense(self, medication, quantity): #check if medication exists
        if medication not in self.inventory:
            print("Medication not found.")
            return False

        if quantity <= 0: #checks that quantity requested is greater than 0
            print("Input a valid quantity")
            return False

        if self.inventory[medication] < quantity: #checks that enough medication is available
            print("\nInsufficient Medication in Stock")
            return False

        self.inventory[medication] -= quantity #reduce inventory after valid request

        print(f"\nDispensing Request Processed: {quantity} unit(s) of {medication}.")
        print(f"Updated Inventory: {medication}: {self.inventory[medication]} units")

        return True

    def replenish(self, medication, quantity):
        if medication not in self.inventory:
            print("Medication not found.")
            return False

        if quantity <= 0:
            print("Quantity must be greater than zero.")
            return False

        self.inventory[medication] += quantity

        print(f"\nReplenishment Processed: {quantity} unit(s) of {medication} added")
        print(f"Updated Inventory: {self.inventory[medication]} units")

        return True


class EventLogger:
    def __init__(self):
        self.events = []

    def record(self, message):
        self.events.append(message)
        print(f"[EVENT LOG] {message}") #take this out?

    def display_events(self):
        print("\n--- Event Log ---")

        if len(self.events) == 0:
            print("No events recorded.")
        else:
            for event in self.events:
                print(event)


class FaultHandler:
    def __init__(self, mode_manager, event_logger):
        self.mode_manager = mode_manager
        self.event_logger = event_logger

        self.active_fault = None #None = no active fault

    def report_fault(self, description):
        self.active_fault = description
        self.event_logger.record(f"Fault detected: {description}")

        self.mode_manager.set_mode("Fault")

        print("WARNING: A cabinet fault has been detected.")
        print("Dispensing and replenishing are unavailable")
        print("Please contact a technician.")

    def handle_fault(self, role):
        if not self.mode_manager.allows(role, "handle_fault"): #only a technician can handle a fault
            print("Fault Handling is unavailable")
            return

        if self.active_fault is None:
            print("No active faults.")
            return

        #print(f"\nActive Fault: {self.active_fault}")

        choice = input("Resolve fault (Y/N): ")

        if choice.upper() == "Y": #simulate fault resolution
            resolved_fault = self.active_fault
            self.active_fault = None

            self.event_logger.record(
                f"Technician resolved {resolved_fault} fault"
            )

            self.mode_manager.set_mode("Normal")
            print("Fault resolved. Cabinet now in Normal mode")

        elif choice.upper() == "N":
            print("Fault still acvtive.")

        else:
            print("Invalid option.")

class ADCController:
    def __init__(self):
        self.mode_manager = ModeManager()
        self.inventory_manager = InventoryManager()
        self.event_logger = EventLogger()
        self.fault_handler = FaultHandler(
            self.mode_manager,
            self.event_logger
        )

    def show_menu(self, role): #display menu based on verified role and mode. Mode is checked every time menu is displayed
        mode = self.mode_manager.mode
        print("\n" + "="*28)
        print("AUTOMATED DISPENSING CABINET")
        print(f"Role: {role.upper()}")
        print(f"Mode: {mode.upper()}")

        if mode == "Fault":
            print("WARNING: Cabinet fault detected.")
            print("Dispensing and replenishing are unavailable.")

        if role == "Nurse" and mode == "Normal": #Nurse Menu
            print("1. Dispense Medication")
            print("2. Log out")


        elif role == "Pharmacist" and mode == "Replenishing":
            print("1. Replenish Medication")
            print("2. Log out")

        elif role == "Technician" and mode == "Fault":
            print("1. Handle Fault")
            print("2. Log out")
            #print("3. View Event Log") #--> need to implement in main

        else:
            print("Role not authorized")


    def dispense_medication(self, role):
        if not self.mode_manager.allows(role, "Dispense"):
            print("Dispensing is unavailable in this mode.")
            self.event_logger.record(f"Dispensing denied for role: {role}")

            return

        self.inventory_manager.display_inventory()

        while True: 
            medication = input("\nEnter the medication: ").strip().title()
            
            if medication in self.inventory_manager.inventory:
                break

            print("Invalid medication name. Please re-enter.")
        
        while True:
            try:
                quantity = int(input("\nEnter quantity to dispense: "))

                if quantity <=0:
                    print("Enter a valid number.")
                    continue

                available = self.inventory_manager.inventory[medication]

                if quantity > available:
                    print(f"Insufficient stock. Only {available} units available.")
                    print("\nPlease enter a smaller quantity.")
                    continue

                break

            except ValueError:
                print("Invalid quantity. Please enter number.")

        success = self.inventory_manager.dispense(medication, quantity)
        if success:
            self.event_logger.record(f"Nurse dispensed {quantity} unti(s) of {medication}")
        else:
            self.event_logger.record(f"Dispensing request unsuccessful for {medication}")


    def replenish_medication(self, role):
        if not self.mode_manager.allows(role, "Replenish"):
            print("Replenishment is unavailable in this mode.")
            self.event_logger.record(f"Unauthorized replenshing attempt")
            return

        self.inventory_manager.display_inventory()

        while True:
            medication = input("\nEnter the medication: ").strip().title()
            if medication in self.inventory_manager.inventory:
                break

            print("Invalid medication name. Please re-enter.")

        while True:
            try: 
                quantity = int(input("\nEnter quantity to add: "))

                if quantity <= 0:
                    print("Enter a valid number")
                    continue

                break

            except ValueError:
                print("Enter a valid number.")

        success = self.inventory_manager.replenish(medication, quantity)
        if success:
            self.event_logger.record(f"Pharmacist replenished {quantity} unit(s) of {medication}")
        else:
            self.event_logger.record(f"Replenishment unsuccessful for {medication}")

    def run_session(self, role):
        if role == "Pharmacist" and self.mode_manager.mode == "Normal": #when a pharmacist signs in, enter Replenishing mode
            self.mode_manager.set_mode("Replenishing")

        # if self.mode_manager.mode == "Fault":
        #     print("\nWARNING: Cabinet fault detected.")
        #     print("Please contact a technicican.")

        while True: #continue displaying menu until user logs out
            mode = self.mode_manager.mode

            authorized = ((role == "Nurse" and mode == "Normal") or (role == "Pharmacist" and mode == "Replenishing") or (role == "Technician" and mode == "Fault"))

            if not authorized:
                print(f"\nRole not authorized in {mode} mode")

                while True:
                    choice = input("Log out (Y): ").strip().upper()

                    if choice == "Y":
                        self.event_logger.record(f"{role} logged out")
                        print("\nLogging out")
                        return

                    else:
                        print("Invalid option. Please log out.")

                continue

            self.show_menu(role)
            choice = int(input("\nChoose an Option: "))

            if role == "Nurse" and self.mode_manager.mode == "Normal":
                if choice == 1:
                    self.dispense_medication(role)
                elif choice == 2:
                    self.event_logger.record(f"{role} logged out")
                    print("\nLogging out")
                    return
                else:
                    print("Invalid option. Please try again")

            elif role == "Pharmacist" and self.mode_manager.mode == "Replenishing":
                if choice == 1:
                    self.replenish_medication(role)
                elif choice == 2:
                    self.event_logger.record(f"{role} logged out")
                    if self.mode_manager.mode == "Replenishing":
                        self.mode_manager.set_mode("Normal")
                    print("\nLoggint out")
                    return
                else:
                    print("Invalid option. Please try again")


            elif role == "Technician" and self.mode_manager.mode == "Fault":
                if choice == 1:
                    self.fault_handler.handle_fault(role)
                elif choice == 2:
                    self.event_logger.record(f"{role} logged out")
                    print("\nLogging out")
                    return
                else: 
                    print("Invalid option. Please try again")

def main():
    access_control = AccessControl()
    controller = ADCController()

    SIMULATE_FAULT_AT_START = True #change this to random.choice[True, False]

    if SIMULATE_FAULT_AT_START:
        controller.fault_handler.report_fault("Simulated cabinet mechanism fault")

    print("\nHospital ADC.")

    while True: #keep returning to login until program is exited
        print("\n--- Login ---")
        print("Enter your user ID.")
        print("Type 'Q' to exit.")

        user_id = input("User ID: ").strip()

        if user_id.upper() == "Q":
            print("\nExiting")
            break

        role = access_control.authenticate(user_id)

        if role is None:
            print("Invalid ID. Access Denied")
            controller.event_logger.record("Invalid Login Attempt")
            continue

        print(f"\nLogin Successful. Role: {role.upper()}")
        controller.event_logger.record(f"{role} logged in")

        controller.run_session(role)

if __name__ == "__main__":
    main()


# THINGS TO IMPLEMENT
# no max inventory limits
# remove event log messages?
# add function/class to view event logs + 'send' to MS
#add that technician can view event logs? (would need to allow technician to function even when not in Fault mode)

#print mode when user not authorized
#make fault mode a list and every time the program runs it chooses true/false at random
#give option for user to quit dispense/replenish at any point (ex. they change their mind).

# if i have test cases for valid quantities in the dispensing/replenishing functions in ADC methods, do I need it again in the inventory manager class?