"""
Every call that comes from main.py is handled here; some of these functions
will be calling data.py if they need anything from the database.
"""

import fnmatch
import os
from datetime import datetime as dt
from sqlite3 import DatabaseError
from typing import List, Any

from config import BLACKLIST
from data import *

lst: List[Any] = []

DATABASE = ConnectionToDatabase()
DATABASE_NAME = DATABASE.get_name()
new_subs = {}
sub_dict = {}
sub_info = []


class Sub:

    def __init__(self, parent, scan_type):
        self.parent = parent
        self.encoding = 'UTF-8'
        self.scan_type = scan_type
        self.cleaned_files = []

    def start_scan(self):
        """
        Call this function and all the necessary functions
        get called aswell.
        """

        self.create_sub_table()
        self.get_sub_info()

        # Insert new subs into db,
        # then check scan type and call remove_junk accordingly.
        self.normal_or_full()

        # If subs with ads were found, update the ad_found column with a 1.
        DATABASE.update_database(self.cleaned_files, True)

        self.count_scanned_files()

    def create_sub_table(self):
        """Creates database if not found in parent directory"""

        dir_files = os.listdir(self.parent)
        if DATABASE_NAME in dir_files:
            pass
        else:
            DATABASE.create()

    @staticmethod
    def get_database_names():
        """Get every value in the database"""

        return DATABASE.get_values()

    def get_sub_info(self):
        """Get every .srt file name and absolute path under parent folder"""

        for file in os.listdir(self.parent):
            if file.endswith('.srt'):
                file_abspath = os.path.abspath(os.path.join(self.parent, file))
                file_last_mod = os.path.getmtime(file_abspath)  # Get Unix timestamp
                file_last_mod = dt.fromtimestamp(file_last_mod)  # Convert it to datetime

                global sub_info
                # TODO: Please change this horror.
                #  Remove_junk takes a dict, so we need to pass a dict (hopefully) created from the sub_info list.
                sub_info.append([file, file_abspath, file_last_mod])
                sub_dict.update({file: file_abspath})

            else:
                current_path = "".join((self.parent, "/", file))
                if os.path.isdir(current_path):
                    try:
                        subfolder = Sub(current_path, self.scan_type)
                        subfolder.get_sub_info()

                    except OSError:
                        pass
        self.is_in_database(sub_info)

    @staticmethod
    def is_in_database(sub_info):
        """Get every new sub which will be inserted to the db by insert_to_db"""

        # TODO: move this function to data.py

        connection = sqlite3.connect(DATABASE_NAME)
        # Change default transaction value, highly improves database writing speed.
        connection.isolation_level = None
        cursor = connection.cursor()

        try:
            for sub in sub_info:
                sub_name = sub[0]
                sub_path = sub[1]
                file_last_mod_date = sub[2]

                cursor.execute('SELECT count(*) FROM subs WHERE name = ?', (sub_name,))
                is_in_database = cursor.fetchone()[0]

                if is_in_database == 1:  # In database
                    # Select a row if the actual file has been modified since the last scan.
                    cursor.execute('SELECT name FROM subs WHERE name = ? AND last_mod_date < ?',
                                   (sub_name, file_last_mod_date,))

                    if cursor.fetchone():
                        new_subs.update({sub_name: sub_path})

                elif is_in_database == 0:  # Not in database
                    new_subs.update({sub_name: sub_path})

        except DatabaseError as error:
            print(error)
            connection.rollback()

        connection.commit()
        connection.close()

    def normal_or_full(self):
        """
        Decide whether it should pass every sub
        to remove_junk or just new ones
        """

        self.insert_to_database(new_subs)

        if self.scan_type:  # Full Scan
            self.remove_junk(self.encoding, sub_dict)

        else:  # Normal scan
            self.remove_junk(self.encoding, new_subs)

    @staticmethod
    def insert_to_database(to_insert):
        """
        Insert every new subtitle name into database.
        Default value for ad_found column will be 0
        """

        current_time = datetime.datetime.now()

        connection = sqlite3.connect(DATABASE_NAME)
        cursor = connection.cursor()

        to_insert_set = set(to_insert)  # Remove duplicated strings.

        for name in to_insert_set:
            cursor.execute('INSERT OR IGNORE INTO subs VALUES (?, ?, ?)',
                (name, 0, current_time,))

        connection.commit()
        connection.close()

    def remove_junk(self, encoding, sub_paths):
        """Remove unwanted lines from sub files"""

        update_dates = []

        for sub_name, sub_path in sub_paths.items():
            opened_sub = open(os.path.join(self.parent, sub_path), 'r',
                encoding=encoding)
            try:
                for line in opened_sub:

                    # Looks for matching lines inside file.
                    # This is case-INSENSITIVE. It also allows wildcards.
                    for match in BLACKLIST:
                        if fnmatch.fnmatch(line.lower(), match.lower()):
                            self.cleaned_files.append(sub_name)
                            print(f'Cleaning {sub_name}')
                            print(line)

                            line = line.replace(line, '')
                    global lst
                    lst.append(line)

                self.write_new_sub(encoding, sub_path)

                if opened_sub not in self.cleaned_files:
                    update_dates.append(sub_name)

            # If file can't be opened in UTF-8, use ISO-8859-1 instead.
            except UnicodeDecodeError:
                self.remove_junk('ISO-8859-1', {sub_name: sub_path})
            except OSError:
                pass

            finally:
                opened_sub.close()
        DATABASE.update_database(update_dates, False)

    def write_new_sub(self, encoding, sub_path):
        """ Opens file in write mode and replaces
        the text with the new clean text."""

        opened_sub = open(os.path.join(self.parent, sub_path), 'w', encoding=encoding)
        global lst
        for line in lst:
            opened_sub.write(line)

            # If lst in not cleared here, it will copy the contents of every
            # previous file when writing the current one.
            lst = []
        opened_sub.close()

    def count_scanned_files(self):
        """Count new scanned files, and cleaned files."""

        # TODO: This doesn't work, it will always say 1 sub was scanned

        global new_subs

        if new_subs == {}:
            print("\nNo new subs found")

        elif new_subs == 1:
            print(f"\nI scanned {str(len(new_subs))} subtitle.")
            print(new_subs)

        else:
            print("\nI scanned " + str(len(new_subs)) + f" subtitles:")
            i = 1
            for scanned_sub in new_subs.keys():
                print(f"#{i} {scanned_sub}")
                i += 1

            if not len(self.cleaned_files):
                print("\nNone of them had recognized ads.")

            else:
                containedAds = set(self.cleaned_files)
                print(f"\n{str(len(containedAds))} of them had ads.")

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
