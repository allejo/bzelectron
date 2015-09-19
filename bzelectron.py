#!/usr/bin/python

import getopt
import os.path
import re
import sys


# Global variables we'll abuse and reuse
inputfile = ''
outputfile = ''
variables = {}
groups = {}


# Regex definitions
varname = "\$[a-zA-Z]+"
groupname = "[A-Z_\-\.]+"
comment = "\s*?#.*"

var_name = re.compile("(" + varname + ")")
comment_line = re.compile(comment)
var_instantiation = re.compile("(" + varname + ")\s?=\s?\"(.+)\"")
group_declaration = re.compile("(" + groupname + ")")


# Custom exceptions we'll be raising
class IncludeError(Exception):
    pass


# Functions
def loadfile(path):
    try:
        with open(path) as f:
            return f.read().splitlines()
    except IOError:
        print "bzgrpc: " + path + ": No such file"
        sys.exit(2)

def set_variable(name, value):
    global variables

    variables[name] = value

def get_variable(name):
    try:
        return variables[name]
    except:
        raise NameError('Variable {} was not previously initialized'.format(name))

def evaluate_variables(line):
    variables = re.findall(var_name, line)

    for var in variables:
        value = get_variable(var)
        line = line.replace(var, value)

    return line

def create_group_if_not_exist(group_name):
    global groups

    if not group_name in groups:
        groups[group_name] = []

    return group_name

def handle_permission(group, perm):
    global groups

    action = perm[:1]
    perm_name = perm[1:]

    add_perm = "+" + perm_name
    remove_perm = "-" + perm_name
    negate_perm = "!" + perm_name

    if action == "+":
        try:
            groups[group].remove(remove_perm)
        except:
            pass
    elif action == "-":
        try:
            groups[group].remove(add_perm)
        except:
            pass
    elif action == "!":
        try:
            groups[group].remove(remove_perm)
            groups[group].remove(add_perm)
        except:
            pass

    if negate_perm not in groups[group] and perm not in groups[group]:
        groups[group].append(perm)

def parse(filepath):
    abspath = os.path.abspath(filepath)
    fullpath = os.path.dirname(abspath)
    filename = os.path.basename(abspath)

    filecontents = loadfile(os.path.join(fullpath, filename))
    line_counter = 0
    last_group = ""

    for line in filecontents:
        line_counter = line_counter + 1

        if line.isspace() or len(line) == 0:
            continue

        if comment_line.search(line) is not None:
            continue
        elif var_instantiation.match(line):
            vardata = re.search(var_instantiation, line)
            name = vardata.group(1)
            value = vardata.group(2)

            set_variable(name, value)
            continue

        if var_name.search(line) is not None:
            try:
                line = evaluate_variables(line)
            except NameError, e:
                print str(e), "on line", line_counter, "of file:", filepath
                sys.exit(2)

        if group_declaration.match(line):
            last_group = create_group_if_not_exist(line)
            continue

        line = line.strip()

        if line[:1] == "+" or line[:1] == "-" or line[:1] == "!":
            handle_permission(last_group, line)
        elif line[:1] == "@":
            tokens = line.split(" ")
            func_call = tokens[0][1:]

            if len(tokens) >= 1:
                params = tokens[1:]
            else:
                params = None

            # Index 0 is going to have useful variables that is passed to language functions
            params.insert(0, {
                'last_group': last_group,
                'full_path': fullpath
            })

            try:
                functions[func_call](params)
            except IncludeError, e:
                print str(e), "on line", line_counter, "of file:", filepath
                sys.exit(2)
            except KeyError:
                print "Undefined function @" + func_call + " on line", line_counter, "of file:", filepath
                sys.exit(2)


# Language functions
def func_include(file_path):
    file_path = os.path.join(file_path[0]['full_path'], file_path[1])

    if os.path.isfile(file_path):
        parse(file_path)
    else:
        raise IncludeError("Included file '{}' not found".format(file_path))

def func_extend(params):
    global groups

    target_group = params[0]['last_group']
    extend_group = params[1]

    for perm in groups[extend_group]:
        handle_permission(target_group, perm)

functions = {
    'include': func_include,
    'extend': func_extend
}


# Setup getopt
try:
    opts, args = getopt.getopt(sys.argv[1:], "hi:o:", ["input=", "output="])
except getopt.GetoptError:
    print 'bzgdbc.py -i <inputfile> -o <outputfile>'
    sys.exit(2)

for opt, arg in opts:
    if opt == '-h':
        print 'bzgdbc.py -i <inputfile> -o <outputfile>'
        sys.exit()
    elif opt in ("-i", "--input"):
        inputfile = arg
    elif opt in ("-o", "--output"):
        outputfile = arg


# Parse the initial file
parse(inputfile)


# Output the gathered information
if os.path.isfile(outputfile):
    os.remove(outputfile)

with open(outputfile, "a") as f:
    for group in groups:
        f.write('{}: {}\n'.format(group, ' '.join(groups[group])))
