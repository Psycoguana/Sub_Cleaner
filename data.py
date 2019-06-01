"""
These functions handle every kind of connection to the database,
such as getting it's name, it's values and even some statistics.
"""

import datetime
import sqlite3

from config import DATABASE_LOCATION, DATABASE_NAME


class ConnectionToDatabase:
    def __init__(self):
        self.database = "".join((DATABASE_LOCATION, DATABASE_NAME))

    def get_name(self):
        """Return the database name"""
        return self.database

    def create(self):
        """Create database if it doesn't exists already."""
        connection = sqlite3.connect(self.database)
        cursor = connection.cursor()

        cursor.execute(
            'CREATE TABLE IF NOT EXISTS subs(name text primary key, ad_found integer, last_mod_date integer)')

        connection.commit()
        connection.close()

    def get_values(self):
        """Get and return every value inside the database"""
        connection = sqlite3.connect(self.database)
        cursor = connection.cursor()

        cursor.execute('SELECT * FROM subs')

        sub_list = [[{'name': row[0], 'ad_found': row[1], 'last_mod_date': row[2]} for row in cursor.fetchall()]]

        connection.commit()
        connection.close()
        return sub_list

    def get_statistics(self):
        """
        Count how many values are inside the database (scanned subs)
        and how many of them had ads
        """

        connection = sqlite3.connect(self.database)
        cursor = connection.cursor()

        # Get number of total subtitles and ads
        cursor.execute('SELECT COUNT(*) FROM subs;')
        subs_number = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(ad_found) FROM subs WHERE ad_found = 1;')
        ads_number = cursor.fetchone()[0]

        connection.close()

        print(f"Scanned subs: {subs_number}" + '\n')
        print(f"Cleaned subs: {ads_number}" + '\n')

    def update_database(self, cleaned_files, is_dirty):
        """
        If there are any new cleaned files (subs with ads),
        update the ad_found column in the database with a 1.
        """

        current_time = datetime.datetime.now()

        if cleaned_files:
            to_update = set(cleaned_files)  # Remove duplicated strings.

            connection_update = sqlite3.connect(self.database)
            cursor = connection_update.cursor()

            try:
                for sub_name in to_update:
                    if is_dirty:
                        cursor.execute('UPDATE subs SET ad_found = 1, last_mod_date = ? WHERE name = ?',
                                       (current_time, sub_name,))
                        print(f"Updated {sub_name} into the db")
                    elif not is_dirty:
                        cursor.execute('UPDATE subs SET last_mod_date = ? WHERE name = ?',
                                       (str(current_time), sub_name,))

            except TypeError as error:
                print(error)

            connection_update.commit()
            connection_update.close()
