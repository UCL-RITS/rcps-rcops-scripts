#!/usr/bin/env python

import os.path
import argparse
import mysql.connector
from mysql.connector import errorcode
import validate

###############################################################
# Subcommands:
# user, project, projectuser, poc, institute
#
# --debug			show SQL query submitted without committing the change

# custom Action class, must override __call__
class ValidateUser(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        # raises a ValueError if the value is incorrect
        validate.user(values)
        setattr(namespace, self.dest, values)
# end class ValidateUser

def getargs():
    parser = argparse.ArgumentParser(description="Add data to the Thomas database. Use [positional argument -h] for more help.")
    # store which subparser was used in args.subcommand
    subparsers = parser.add_subparsers(dest="subcommand")

    # the arguments for subcommand 'user'
    userparser = subparsers.add_parser("user", help="Adding a new user with their initial project")
    userparser.add_argument("-u", "--user", dest="username", help="UCL username of user", required=True, action=ValidateUser)
    userparser.add_argument("-n", "--name", dest="given_name", help="Given name of user", required=True)
    userparser.add_argument("-s", "--surname", dest="surname", help="Surname of user (optional)")
    userparser.add_argument("-e", "--email", dest="email_address", help="Institutional email address of user", required=True)
    userparser.add_argument("-k", "--key", dest='"ssh_key"', help="User's public ssh key (quotes necessary)", required=True)
    userparser.add_argument("-p", "--project", dest="project_ID", help="Initial project the user belongs to", required=True)
    userparser.add_argument("-c", "--contact", dest="poc_id", help="Short ID of the user's Point of Contact", required=True)
    userparser.add_argument("--debug", help="Show SQL query submitted without committing the change", action='store_true')

    # the arguments for subcommand 'project'
    projectparser = subparsers.add_parser("project", help="Adding a new project")
    projectparser.add_argument("-p", "--project", dest="project_ID", help="A new unique project ID", required=True)
    projectparser.add_argument("-i", "--institute", dest="inst_ID", help="Institute ID this project belongs to", required=True)
    projectparser.add_argument("--debug", help="Show SQL query submitted without committing the change", action='store_true')

    # the arguments for subcommand 'projectuser'
    projectuserparser = subparsers.add_parser("projectuser", help="Adding a new user-project-contact relationship")
    projectuserparser.add_argument("-u", "--user", dest="username", help="An existing UCL username", required=True, action=ValidateUser)
    projectuserparser.add_argument("-p", "--project", dest="project_ID", help="An existing project ID", required=True)
    projectuserparser.add_argument("-c", "--contact", dest="poc_id", help="An existing Point of Contact ID", required=True)
    projectuserparser.add_argument("--debug", help="Show SQL query submitted without committing the change", action='store_true')

    # the arguments for subcommand 'poc'
    pocparser = subparsers.add_parser("poc", help="Adding a new Point of Contact")
    pocparser.add_argument("-p", "--poc_id", dest="poc_id", help="Unique PoC ID, in form N(ame)N(ame)_instituteID", required=True)
    pocparser.add_argument("-n", "--name", dest="given_name", help="Given name of PoC", required=True)
    pocparser.add_argument("-s", "--surname", dest="surname", help="Surname of PoC (optional)")
    pocparser.add_argument("-e", "--email", dest="email_address", help="Email address of PoC", required=True)
    pocparser.add_argument("-i", "--institute", dest="inst_ID", help="Institute ID of PoC", required=True)
    pocparser.add_argument("-u", "--user", dest="username", help="The PoC's UCL username (optional)", action=ValidateUser)
    pocparser.add_argument("--debug", help="Show SQL query submitted without committing the change", action='store_true')

    # the arguments for subcommand 'institute'
    instituteparser = subparsers.add_parser("institute", help="Adding a new institute/consortium")
    instituteparser.add_argument("-i", "--id", dest="inst_ID", help="Unique institute ID, eg QMUL, Imperial, Soton", required=True)
    instituteparser.add_argument("-n", "--name", dest="institute", help="Full name of institute/consortium", required=True)
    instituteparser.add_argument("--debug", help="Show SQL query submitted without committing the change", action='store_true')

    # return the arguments
    # contains only the attributes for the main parser and the subparser that was used
    return parser.parse_args()
# end getargs

# query to run for 'user' subcommand
# the values are inserted by cursor.execute from args.dict
def run_user(surname):
    query = ("""INSERT INTO users SET username=%(username)s, givenname=%(given_name)s, """
             """email=%(email_address)s, ssh_key=%("ssh_key")s, creation_date=now()""")
    if (surname != None):
        query += ", surname=%(surname)s"
    return query

# query to run for 'user' and 'projectuser' subcommands
def run_projectuser():
    query = ("""INSERT INTO projectusers SET username=%(username)s, """
             """project=%(project_ID)s, poc_id=%(poc_id)s, creation_date=now()""")
    return query

# query to run for 'project' subcommand
def run_project():
    query = ("""INSERT INTO projects SET project=%(project_ID)s,  """
             """institute_id=%(inst_ID)s, creation_date=now()""")
    return query

# query to run for 'poc' subcommand
def run_poc(surname, username):
    query = ("""INSERT INTO pointofcontact SET poc_id=%(poc_id)s, """
             """poc_givenname=%(given_name)s, poc_email=%(email_address)s,  """
             """institute=%(inst_ID)s, creation_date=now()""")
    if (surname != None):
        query += ", poc_surname=%(surname)s"
    if (username != None):
        query += ", username=%(username)s"
    return query

# query to run for 'institute' subcommand
def run_institute():
    query = ("""INSERT INTO institutes SET inst_id=%(inst_ID)s, name=%(institute)s, """
             """creation_date=now()""") 
    return query

if __name__ == "__main__":

    # get all the parsed args
    try:
        args = getargs()
        # make a dictionary from args to make string substitutions doable by key name
        args_dict = vars(args)
    except ValueError as err:
        print(err)
        exit(1)

    # look at sshpubkeys package for ssh validation eventually

    # connect to MySQL database with write access.
    # (.thomas.cnf has readonly connection details as the default option group)

    try:
        conn = mysql.connector.connect(option_files=os.path.expanduser('~/.thomas.cnf'), option_groups='thomas_update', database='thomas')
        cursor = conn.cursor()

        print(">>>> Queries being sent:")

        # cursor.execute takes a querystring and a dictionary or tuple
        if (args.subcommand == "user"):
            cursor.execute(run_user(args.surname), args_dict)
            print(cursor.statement)
        # this is run in both cases
        if (args.subcommand == "user" or args.subcommand == "projectuser"):
            cursor.execute(run_projectuser(), args_dict)
            print(cursor.statement)
        elif (args.subcommand == "project"):
            cursor.execute(run_project(), args_dict)
            print(cursor.statement)
        elif (args.subcommand == "poc"):
            cursor.execute(run_poc(args.surname, args.username), args_dict)
            print(cursor.statement)
        elif (args.subcommand == "institute"):
            cursor.execute(run_institute(), args_dict)
            print(cursor.statement)

        # commit the change to the database unless we are debugging
        if (not args.debug):
            print("Committing database change")
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

# end main