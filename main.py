"""
This handles the user actions; at the end, there is an argparse call.
"""
import sys
import time
import argparse
from datetime import datetime


from config import PARENT_FOLDER
from app import Sub, format_timer
from app import blacklist_match as blacklist
from data import ConnectionToDatabase as Database


USER_CHOICE = """
    ______             __                        __
   /      \           /  |                      /  |
  /$$$$$$  | __    __ $$ |____          _______ $$ |  ______    ______   _______    ______    ______
  $$ \__$$/ /  |  /  |$$      \        /       |$$ | /      \  /      \ /       \  /      \  /      \\
  $$      \ $$ |  $$ |$$$$$$$  |      /$$$$$$$/ $$ |/$$$$$$  | $$$$$$  |$$$$$$$  |/$$$$$$  |/$$$$$$  |
   $$$$$$  |$$ |  $$ |$$ |  $$ |      $$ |      $$ |$$    $$ | /    $$ |$$ |  $$ |$$    $$ |$$ |  $$/
  /  \__$$ |$$ \__$$ |$$ |__$$ |      $$ \_____ $$ |$$$$$$$$/ /$$$$$$$ |$$ |  $$ |$$$$$$$$/ $$ |
  $$    $$/ $$    $$/ $$    $$/       $$       |$$ |$$       |$$    $$ |$$ |  $$ |$$       |$$ |
   $$$$$$/   $$$$$$/  $$$$$$$/         $$$$$$$/ $$/  $$$$$$$/  $$$$$$$/ $$/   $$/  $$$$$$$/ $$/


1. Normal scan
2. Full scan (ignores database entries and scans the whole thing)
3. Show blacklist
4. Statistics


0. Exit

Choose a number: 
"""


class Menu:

    def __init__(self):
        self.parent = PARENT_FOLDER

    def choices(self):
        """Present available choices to choose from"""

        run = Sub(self.parent, False)  # False value is normal scan
        run.create_sub_table()
        user_input = input(USER_CHOICE)

        while user_input != '0':

            if user_input == '1':
                t0 = time.time()
                run.start_scan()

                total = (time.time() - t0)
                format_timer(total)

            elif user_input == '2':
                t0 = time.time()

                run = Sub(self.parent, True)  # Full scan
                run.start_scan()

                total = (time.time() - t0)
                format_timer(total)

            elif user_input == '3':
                # Make the sorting case insensitive
                ordered_blacklist = sorted(blacklist, key=str.lower)

                for line in ordered_blacklist:
                    print(line)

                user_input_2 = input("\n1. Back to menu \n0. Exit ")
                if user_input_2 == '1':
                    Menu().choices()

                elif user_input_2 == '0':
                    sys.exit()

                else:
                    print("Command not recognized, please try again... ")

            elif user_input == '4':
                Database().get_statistics()

                user_input_2 = input("\n1. Back to menu \n0. Exit ")
                if user_input_2 == '1':
                    Menu().choices()

                elif user_input_2 == '0':
                    sys.exit()

                else:
                    print("Command not recognized, please try again... ")

            else:
                print("Command not recognized, please try again... ")
            user_input = input(USER_CHOICE)

    def automatic_mode(self):
        """
        This allows to do a normal scan without being prompted for choices,
        so it can be called by other programs such as Sub-Zero.
        """

        run = Sub(self.parent, False)
        run.start_scan()


# This allows an automatic mode when --auto argument is passed.
parser = argparse.ArgumentParser(prog='Sub Cleaner')
parser.add_argument('--auto', action='store_true', help='Automatic mode')
args = parser.parse_args()

if not args.auto:
    Menu().choices()
else:
    opened_log = open('./log.txt', 'a')

    try:
        Menu().automatic_mode()
        opened_log.write(f'\nFinished at {str(datetime.now())}')
        opened_log.close()
        print("Finished!")
    except Exception as error:
        opened_log.write(f"\nError: {error} ----------- Hour: {str(datetime.now())}")
        opened_log.close()
