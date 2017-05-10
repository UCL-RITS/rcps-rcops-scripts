#!/usr/bin/env python

import argparse
import mysql.connector
from mysql.connector import errorcode

###############################################################
# -u, --user <username>
# -n, --name <givenname>
# -s, --surname <surname> (optional)
# -e, --email <institutional email address> 
# -k, --key <"ssh_key"> (quotes necessary)
#
# -p, --project <project>       initial project the user belongs to
# -c, --contact <poc_id>        short ID of the Point of Contact who approved user

parser = argparse.ArgumentParser(description="manage user data in the Thomas database")
parser.parse_args()
parser.add_argument("-u", "--user", metavar="username", help="UCL username of user")
parser.add_argument("-n", "--name", metavar="given name", help="Given name of user")
parser.add_argument("-s", "--surname", metavar="surname", help="Surname of user (optional)")
parser.add_argument("-e", "--email", metavar="email address", help="Institutional email address of user")
parser.add_argument("-k", "--key", metavar='"ssh key"', help="User's public ssh key (quotes necessary)")

parser.add_argument("-p", "--project", metavar="project ID", help="Initial project the user belongs to")
parser.add_argument("-c", "--contact", metavar="poc_id", help="Short ID of the user's Point of Contact")

args = parser.parse_args()
# make a dictionary from args
args_dict = vars(args)

# sanity check input
# usernames must be 7 characters
if (len(args.user) != 7):
    print("Invalid username, must be 7 characters: %s"), args.user
# look at sshpubkeys package for ssh validation eventually


# connect to MySQL database with write access.
# (.thomas.cnf has readonly connection details as the default option group)

try:
    conn = mysql.connector.connect(option_files='~/.thomas.cnf', option_groups='thomas_update' database='thomas')
    cursor = conn.cursor()

    # add user
    # the values will be taken from the dictionary given to cursor.execute()
    add_user = ("""INSERT INTO users SET username=%(user)s, givenname=%(name)s,"""
               """email=%(email)s, ssh_key=%(key)s, creation_date=now()""")
    user_values = (args.user, args.name, args.email, args.key)
    # surname is optional so may not be inserted
    if (args.surname != None):
        add_user += ", surname=%(surname)s"

    # add information to projectusers
    add_projectuser = ("""INSERT INTO projectusers SET username=%(user)s,"""
                       """project=%(project)s, poc_id=%(contact)s, creation_date=now()""")

    # takes a query string and a dictionary or tuple
    cursor.execute(add_user, args_dict)
    cursor.execute(add_projectuser, args_dict)
    # commit the change to the database
    conn.commit()

except mysql.connector.Error as err:
  if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
    print("Access denied: Something is wrong with your user name or password")
  elif err.errno == errorcode.ER_BAD_DB_ERROR:
    print("Database does not exist")
  else:
    print(err)
else:
  cursor.close()
  conn.close()

