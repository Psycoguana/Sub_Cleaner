"""
Every call that comes from main.py is handled here; some of these functions
will be calling data.py if they need anything from the database.
"""

import os
import fnmatch
from typing import List, Any
from sqlite3 import DatabaseError

from data import *

blacklist_match = ['[###]',
                   'a Card Shark AMERICASCARDROOM*',
                   'Advertise your product or brand here',
                   'Apóyanos y conviértete en miembro VIP Para',
                   '*Addic7ed*',
                   '*argenteam*',
                   '*corrected by*',
                   'Entre a AmericasCardroom. com Hoy',
                   'Everyone is intimidated by a shark. Become',
                   '*Juegue Poker en Línea por Dinero Real*',
                   '*OpenSubtitles*',
                   '*Resync for*',
                   'Ripped By *',
                   'Sigue "Community" en',
                   'Subtitles by *',
                   'Subtítulos por *',
                   'Support us and become VIP member',
                   '*Subs*Team*',
                   '*subscene*',
                   '*Subtitulado por*',
                   '*subtitulamos*',
                   '*Sync * Corrected*',
                   'Sync & corrections by *',
                   '*Sync by *',
                   '*tvsubtitles*',
                   'Una traducción de *',
                   'Tacho8',
                   'www. com',
                   'www. es'
                   ]

lst: List[Any] = []

Database = ConnectionToDatabase()
database_name = Database.get_name()
new_subs = {}
sub_dict = {}


class Sub:

    def __init__(self, parent, scan_type):
        self.parent = parent
        self.encoding = 'UTF-8'
        self.scan_type = scan_type
        self.database = ConnectionToDatabase()
        self.cleaned_files = []

    def start_scan(self):
        """
        I thinks this could be called a wrapper? Call this function and all the necessary functions
        get called aswell.
        """

        self.create_sub_table()
        self.get_sub_paths()
        self.is_in_database()

        # Insert new subs into db, then check scan type and call remove_junk accordingly.
        self.normal_or_full()

        # If subs with ads were found, update the ad_found column with a 1.
        Database.update_database(self.cleaned_files)

        self.count_scanned_files()

    def create_sub_table(self):
        """Creates database if not found in parent directory"""

        dir_files = os.listdir(self.parent)
        if database_name in dir_files:
            pass
        else:
            Database.create()

    @staticmethod
    def get_database_names():
        """Get every value in the database"""

        Database.get_values()

    def get_sub_paths(self):
        """Get every .srt file name and absolute path under parent folder"""

        for file in os.listdir(self.parent):
            if file.endswith('.srt'):
                file_abspath = os.path.abspath(os.path.join(self.parent, file))
                sub_dict.update({file: file_abspath})

            else:
                current_path = "".join((self.parent, "/", file))
                if os.path.isdir(current_path):
                    try:
                        subfolder = Sub(current_path, self.scan_type)
                        subfolder.get_sub_paths()

                    except OSError:
                        pass

    def is_in_database(self):
        """Get every new sub which will be inserted to the db by insert_to_db"""

        connection = sqlite3.connect(self.database.get_name())
        # Change default transaction value, highly improves database writing speed.
        connection.isolation_level = None
        cursor = connection.cursor()

        try:
            for name, path in sub_dict.items():
                cursor.execute('SELECT count(*) FROM subs WHERE name = ?', (name,))
                is_in_database = cursor.fetchone()[0]

                if is_in_database == 1:  # In database
                    pass

                elif is_in_database == 0:  # Not in database
                    new_subs.update({name: path})
        except DatabaseError as error:
            print(error)
            connection.rollback()

        connection.commit()
        connection.close()

    def normal_or_full(self):
        """Decide whether it should pass every sub to remove_junk or just new ones"""

        self.insert_to_database(new_subs)

        if self.scan_type:  # Full Scan
            self.remove_junk(self.encoding, sub_dict)

        else:  # Normal scan
            self.remove_junk(self.encoding, new_subs)

    def insert_to_database(self, to_insert):
        """
        Insert every new subtitle name into database.
        Default value for ad_found column will be 0
        """

        connection = sqlite3.connect(self.database.get_name())
        cursor = connection.cursor()

        to_insert_set = set(to_insert)  # Remove duplicated strings.

        for name in to_insert_set:
            cursor.execute('INSERT OR IGNORE INTO subs VALUES (?, ?)', (name, 0))

        connection.commit()
        connection.close()

    def remove_junk(self, encoding, sub_paths):
        """Remove unwanted lines from sub files"""
        sub_path_lst = []
        if sub_paths is dict:
            for name, sub_path in sub_paths.items():
                sub_path.append(sub_path_lst)
        elif sub_paths is list:
            sub_paths.append(sub_path_lst)

        for sub_path in sub_path_lst:
            opened_sub = open(os.path.join(self.parent, sub_path), 'r', encoding=encoding)
            try:
                for line in opened_sub:

                    # Looks for matching lines inside file.
                    # This is case-INSENSITIVE. It also allows wildcards.
                    for match in blacklist_match:
                        if fnmatch.fnmatch(line, match):
                            print(f'Cleaning {name}')
                            print(line)

                            self.cleaned_files.append(name)
                            line = line.replace(line, '')
                    global lst
                    lst.append(line)

            # If file can't be opened in UTF-8, use ISO-8859-1 instead.
            except UnicodeDecodeError:
                self.remove_junk('ISO-8859-1', sub_path)

            # Opens each and every file in write mode
            # and replaces the text with the new clean text.
            try:
                opened_sub = open(os.path.join(self.parent, sub_path), 'w', encoding=self.encoding)
                for line in lst:
                    opened_sub.write(line)

                    # If lst in not cleared here, it will copy the contents of every previous
                    # file when writing the current one.
                    lst = []
            except OSError:
                pass

            opened_sub.close()

    def count_scanned_files(self):
        """Count new scanned files, and cleaned files."""

        global new_subs

        if new_subs == {}:
            print("\nNo new subs found")

        else:
            print("\nI scanned " + str(len(new_subs)) + " new subtitles.")

            if not len(self.cleaned_files):
                print("None of them had recognized ads. ")

            else:
                print(str(len(self.cleaned_files)) + " of them had ads. ")

        new_subs = {}
        self.cleaned_files = []


def format_timer(total_time):
    """Correctly format the amount of time it took the script to run."""

    if total_time < 60:
        total_time = '{:3.2f} seconds'.format(total_time)
    elif total_time == 1:
        total_time = '{:3.2f} minute'.format(total_time / 60)
    else:
        total_time = '{:3.2f} minutes'.format(total_time / 60)

    print("Completed in " + total_time)
