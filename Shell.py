import time, csv, sys
import random, os
import subprocess, pygame
CommandTracker = 0
run = True
Program_list = ("Math_progams, " + "temp1, " + "temp2, " + "temp3")
chose = True
Permission = 0

def Filewriter(File, Data, fieldnames):
    try:
        # Check if file exists to decide whether to write the header
        file_exists = os.path.isfile(File)

        # Open in append mode with newline='' to prevent extra blank lines
        with open(File, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            # Write header only if the file is newly created
            if not file_exists:
                writer.writeheader(fieldnames)
                
            writer.writerow(Data)
            print("Successfully added data")
    except Exception as e:
        # Better error handling: print the actual error for debugging
        print(f"Error writing to {File}, Error code: {e}") 

print('\033c')

import cmd

class MyInteractiveShell(cmd.Cmd):
    intro = 'Welcome to My Interactive Shell. Type help or ? to list commands. Please Login/Sign Up To Continue.'
    prompt = ' '
    _Login_commands = ['']
    
    def __init__(self, UserName="Guest", Password2=None, Password1=None, logged_in=False):
        super().__init__()
        self.username1 = UserName
        self.Password2 = Password2
        self.Password1 = Password1
        self.logged_in = logged_in
        # Keep track of launched Main Menu process so we don't launch it twice
        self.game_process = None
        # Do not auto-start Main Menu here — starting it here causes recursion
        # when `Shell` is imported by `Main Menu.py`. If you want auto-start
        # behavior, launch Main Menu from the `if __name__ == '__main__'` block below.

    def do_login(self, line):
        """
        Login with a username and password.
        Usage: Login <username> <password>
        """
        args = line.split()

        if len(args) != 2:
            print("*** Invalid number of arguments")
            print("Usage: Login <username> <password>")
            print("Then will be varified for 2ed Password")
            return

        username = args[0]
        password = args[1]
        
        data = []
        with open('User.txt', 'r', newline='') as User:
            reader = csv.DictReader(User)
            for row in reader:
                data.append(row)

                if username == row['Username'] and password == row['Password']:
                    password2 = input(f"Please varifi it's you by entering your second Password: ")
                    if password2 == row['Password2']:
                        self.logged_in = True
                        self.Password2 = password2
                        self.Password1 = password
                        self.username1 = username
                        self._Login_commands = ['']
                        print("Success! Logged in to this account.")
                        self.onecmd('clear')
                        self.onecmd('help')
                        return
                    else:
                        CommandTracker =+ 1
                        print(f"You are not the owner of this account.")

                else:
                    print("Error: Invalid username or password.")
                    return

    def do_userinfo(self, arg):
        """
        This is used to see your info like username and logged in state
        to use this command do: userinfo  <username/password/operator or op>
        """

        if self:
            with open('User.txt', mode='r', newline='') as file:
                # Use DictReader to access columns by name
                delimiter = ','
                reader = csv.DictReader(file, delimiter=delimiter)
        
                for row in reader:
                    Username_value = row.get('Username')
                    Password2_value = row.get('Password2')
                    Password1_value = row.get('Password')
                    Operator_value = row.get('Operator')
                    try:
                        if arg == "username":
                            print(f"Username: {Username_value}")
                            return
                        if arg == "password":
                            print(f"Password: {Password1_value}")
                            return
                        if not arg:
                            print("Invalid: number of arguments")
                            return
                        if arg == 'operator' or arg == 'op' and self.logged_in:
                            print(f"Operator value: {Operator_value}")
                            return
                        else:
                            print("You have to be logged in to use: userinfo <op/operator>")
                            return
                    except Exception as e:
                        print(f"Error: {e}")

    def do_close(self, arg):
        'Exit the shell: Close'
        if self:          
            print("Closing PROGRAM IN 2 Seconds")
            time.sleep(2)
            print("\033c")
            return True
    
    def do_programs(self, arg):
        'Program list: Programs'
        if self:
            time.sleep(1)
            print(Program_list)
    
    def do_signup(self, line):
        """
        To sign up for the shell: SignUp <username> <password>  <2password>
        """
        args = line.split()
        if len(args) != 3:
            print("*** Invalid number of arguments")
            print("Usage: SignUp <username> <password> <2password>")
            # Note: in a cmd/shell environment, returning here stops the function.
            return 

        username = args[0]
        password = args[1]
        password2 = args[2]
        
        # Basic validation that passwords match *before* checking the file
        if not password != password2:
            print("*** Error: Passwords do not match.")
            return

        File = 'User.txt'
        fieldnames = ['Username', 'Password', 'Password2', 'Operator']
        file_exists = os.path.exists(File)
        
        # 1. Check if the user/details already exists 
        if file_exists:
            try:
                with open(File, 'r', newline='') as User:
                    reader = csv.DictReader(User)
                    for row in reader:
                        # Check all criteria across all existing rows
                        if (row.get('Username') == username or 
                            row.get('Password') == password or  # Check if the new password is an existing password
                            row.get('Password2') == password or # Check if the new password is an existing secondary password
                            row.get('Password') == password2 or # Redundant but comprehensive check
                            row.get('Password2') == password2): # Redundant but comprehensive check
                            
                            print(f"*** Error: An account using that username ('{username}') or associated passwords already exists.")
                            return # Exit the function immediately if a match is found

            except Exception as e:
                # Handle potential errors during reading, like a corrupt file
                print(f"Error reading file during existence check: {e}")
                return

        # 2. If no existing match was found, proceed to registration
        try:
            status = False # Assuming 'Operator' status is a boolean/string representation of False
            user_data = {'Username': username, 'Password': password, 'Password2': password2, 'Operator': status}
            Filewriter(File, user_data, fieldnames)
            print("Account successfully created!")
            
        except Exception as e:
            # Handle potential errors during the writing phase
            print(f"An error occurred during account creation: {e}")
            return False
    
    def do_clear(self, arg):
        'Use this to Clear the console while running: Clear'
        if self:
            print('\033c')
            print(self.intro)

    def do_newtab(self, line):
        """Create a new GUI tab from the shell.
        Usage: newtab <tab_id> <label>
        Example: newtab logs "Logs Panel"""
        args = line.split()
        if len(args) < 2:
            print('Usage: newtab <tab_id> <label>')
            return
        tab_id = args[0]
        label = ' '.join(args[1:])
        # Request the GUI to add a tab; content defaults to tab_id
        request_tab(tab_id, label, tab_id)

    def emptyline(self):
        pass # This overrides the default behavior and does nothing
    
    def onecmd(self, line):
        """Handle case-insensitivity by converting input to lowercase."""
        # Convert the command part of the line to lowercase
        cmd, arg, line = self.parseline(line)
        if cmd:
            line = cmd.lower() + (' ' + arg if arg else '')
        
        # Call the original onecmd with the lowercased command
        return super().onecmd(line)

    # --- Override print_topics to filter hidden commands ---
    def print_topics(self, header, topics, cmdlen=15, maxtab=80):
        # Filter out hidden commands from the topics list
        filtered_topics = [topic for topic in topics if topic not in self._Login_commands]
        
        # Only call super().print_topics if there are topics to display
        if filtered_topics:
            super().print_topics(header, filtered_topics, cmdlen, maxtab)


# Callback that can be set by the GUI (Main Menu) so shell commands can request
# the GUI create new tabs/panels. Main Menu should set `create_tab_callback`.
create_tab_callback = None

def request_tab(tab_id: str, label: str, content):
    """Ask the GUI to create a new tab. Safe no-op if GUI not attached."""
    global create_tab_callback
    if callable(create_tab_callback):
        try:
            create_tab_callback(tab_id, label, content)
        except Exception as e:
            print(f"Failed to request tab: {e}")
    else:
        print("GUI callback not set. Can't create tab.")


if __name__ == '__main__':
    # Auto-start Main Menu once when running this file directly
    try:
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'Main Menu.py'))
        if os.path.exists(script_path):
            subprocess.Popen([sys.executable, script_path])
            print('Auto-started Main Menu.')
    except Exception as e:
        print(f'Failed to auto-start Main Menu: {e}')

    app = MyInteractiveShell(UserName="Guest", Password1=None, Password2=None, logged_in=False)
    app.cmdloop()