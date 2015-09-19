#!/usr/bin/python

import getopt
import os.path
import re
import sys

MAJOR = 0
MINOR = 1
REV = 0


# Custom exceptions we'll be raising
class IncludeError(Exception):
    pass


class BZElectron(object):
    def __init__(self):
        self.variables = {}
        self.groups = {}

    def get_variable(self, name):
        try:
            return self.variables[name]
        except:
            raise NameError('Variable {} was not previously initialized'.format(name))

    def set_variable(self, name, value):
        self.variables[name] = value

    def create_group(self, group_name):
        if not group_name in self.groups:
            self.groups[group_name] = []

        return group_name

    def handle_permission(self, group, perm):
        action = perm[:1]
        perm_name = perm[1:]

        add_perm = "+" + perm_name
        remove_perm = "-" + perm_name
        negate_perm = "!" + perm_name

        if action == "+":
            try:
                self.groups[group].remove(remove_perm)
            except ValueError:
                pass
        elif action == "-":
            try:
                self.groups[group].remove(add_perm)
            except ValueError:
                pass
        elif action == "!":
            try:
                self.groups[group].remove(remove_perm)
                self.groups[group].remove(add_perm)
            except ValueError:
                pass

        if negate_perm not in self.groups[group] and perm not in self.groups[group]:
            self.groups[group].append(perm)


class BZElectronParser(object):
    varname = "\$[a-zA-Z]+"
    groupname = "[A-Z_\-\.]+"
    comment = "\s*?#.*"

    var_name = re.compile("(" + varname + ")")
    comment_line = re.compile(comment)
    var_instantiation = re.compile("(" + varname + ")\s?=\s?\"(.+)\"")
    group_declaration = re.compile("(" + groupname + ")")

    def __init__(self, _electron):
        self.electron = _electron
        self.functions = {
            'include': self.func_include,
            'extend': self.func_extend
        }

    @staticmethod
    def _loadfile(_path):
        try:
            with open(_path) as f:
                return f.read().splitlines()
        except IOError:
            print "bzelectron: " + _path + ": No such file"
            sys.exit(2)

    def _evaluate_variables(self, _line):
        variables = re.findall(BZElectronParser.var_name, _line)

        for var in variables:
            value = self.electron.get_variable(var)
            _line = _line.replace(var, value)

        return _line

    def parse(self, _filepath):
        abspath = os.path.abspath(_filepath)
        fullpath = os.path.dirname(abspath)
        filename = os.path.basename(abspath)

        filecontents = self._loadfile(os.path.join(fullpath, filename))
        line_counter = 0
        last_group = ""

        for line in filecontents:
            line_counter += 1

            if line.isspace() or len(line) == 0:
                continue

            if BZElectronParser.comment_line.search(line) is not None:
                continue
            elif BZElectronParser.var_instantiation.match(line):
                vardata = re.search(BZElectronParser.var_instantiation, line)
                name = vardata.group(1)
                value = vardata.group(2)

                electron.set_variable(name, value)
                continue

            if BZElectronParser.var_name.search(line) is not None:
                try:
                    line = self._evaluate_variables(line)
                except NameError, e:
                    print str(e), "on line", line_counter, "of file:", _filepath
                    sys.exit(2)

            if BZElectronParser.group_declaration.match(line):
                last_group = self.electron.create_group(line)
                continue

            line = line.strip()

            if line[:1] == "+" or line[:1] == "-" or line[:1] == "!":
                self.electron.handle_permission(last_group, line)
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
                    self.functions[func_call](params)
                except IncludeError, e:
                    print str(e), "on line", line_counter, "of file:", _filepath
                    sys.exit(2)
                except KeyError:
                    print "Undefined function @" + func_call + " on line", line_counter, "of file:", _filepath
                    sys.exit(2)

    # Language functions
    def func_include(self, params):
        filepath = os.path.join(params[0]['full_path'], params[1])

        if os.path.isfile(filepath):
            self.parse(filepath)
        else:
            raise IncludeError("Included file '{}' not found".format(filepath))

    def func_extend(self, params):
        target_group = params[0]['last_group']
        extend_group = params[1]

        for perm in electron.groups[extend_group]:
            self.electron.handle_permission(target_group, perm)

if __name__ == '__main__':
    inputfile = ''
    outputfile = ''

    # Setup getopt
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hvi:o:", ["input=", "output="])
    except getopt.GetoptError:
        print 'bzelectron.py -i <inputfile> -o <outputfile>'
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print 'bzelectron.py -i <inputfile> -o <outputfile>'
            sys.exit()
        elif opt in ("-v", "--version"):
            print 'bzelectron {}.{}.{}'.format(MAJOR, MINOR, REV)
            sys.exit()
        elif opt in ("-i", "--input"):
            inputfile = arg
        elif opt in ("-o", "--output"):
            outputfile = arg

    # By default, set an output file if it hasn't been specified
    if not outputfile:
        basename = os.path.basename(inputfile)
        filename = os.path.splitext(basename)[0]
        outputfile = '{}.groupdb'.format(filename)

    # Parse the initial file
    electron = BZElectron()
    parser = BZElectronParser(electron)

    parser.parse(inputfile)

    # Output the gathered information
    try:
        os.remove(outputfile)
    except OSError:
        pass

    with open(outputfile, "a") as f:
        for group in electron.groups:
            f.write('{}: {}\n'.format(group, ' '.join(electron.groups[group])))
