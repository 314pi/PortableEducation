# -*- coding: utf-8 -*-
#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2006  Donald N. Allingham, A. Roitman
# Copyright (C) 2007-2009  B. Malengier
# Copyright (C) 2008       Lukasz Rymarczyk
# Copyright (C) 2008       Raphael Ackermann
# Copyright (C) 2008       Brian G. Matherly
# Copyright (C) 2012       Doug Blank
# Copyright (C) 2012-2013  Paul Franklin
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

# $Id$

"""
Module responsible for handling the command line arguments for GRAMPS.
"""

#-------------------------------------------------------------------------
#
# Standard python modules
#
#-------------------------------------------------------------------------
import sys
import getopt
from gen.ggettext import gettext as _
import logging

#-------------------------------------------------------------------------
#
# gramps modules
#
#-------------------------------------------------------------------------
import const
import config
import Utils

# Note: Make sure to edit const.py.in POPT_TABLE too!
_HELP = _("""
Usage: gramps.py [OPTION...]
  --load-modules=MODULE1,MODULE2,...     Dynamic modules to load

Help options
  -?, --help                             Show this help message
  --usage                                Display brief usage message

Application options
  -O, --open=FAMILY_TREE                 Open family tree
  -C, --create=FAMILY_TREE               Create on open if new family tree
  -i, --import=FILENAME                  Import file
  -e, --export=FILENAME                  Export file
  -f, --format=FORMAT                    Specify family tree format
  -a, --action=ACTION                    Specify action
  -p, --options=OPTIONS_STRING           Specify options
  -d, --debug=LOGGER_NAME                Enable debug logs
  -l                                     List Family Trees
  -L                                     List Family Trees in Detail
  -t                                     List Family Trees, tab delimited
  -u, --force-unlock                     Force unlock of family tree
  -s, --show                             Show config settings
  -c, --config=[config.setting[:value]]  Set config setting(s) and start Gramps
  -v, --version                          Show versions
""")

_USAGE = _("""
Example of usage of Gramps command line interface

1. To import four databases (whose formats can be determined from their names)
and then check the resulting database for errors, one may type:
gramps -i file1.ged -i file2.gpkg -i ~/db3.gramps -i file4.wft -a tool -p name=check. 

2. To explicitly specify the formats in the above example, append filenames with appropriate -f options:
gramps -i file1.ged -f gedcom -i file2.gpkg -f gramps-pkg -i ~/db3.gramps -f gramps-xml -i file4.wft -f wft -a tool -p name=check. 

3. To record the database resulting from all imports, supply -e flag
(use -f if the filename does not allow Gramps to guess the format):
gramps -i file1.ged -i file2.gpkg -e ~/new-package -f gramps-pkg

4. To save any error messages of the above example into files outfile and errfile, run:
gramps -i file1.ged -i file2.dpkg -e ~/new-package -f gramps-pkg >outfile 2>errfile

5. To import three databases and start interactive Gramps session with the result:
gramps -i file1.ged -i file2.gpkg -i ~/db3.gramps

6. To open a database and, based on that data, generate timeline report in PDF format
putting the output into the my_timeline.pdf file:
gramps -O 'Family Tree 1' -a report -p name=timeline,off=pdf,of=my_timeline.pdf

7. To generate a summary of a database:
gramps -O 'Family Tree 1' -a report -p name=summary

8. Listing report options
Use the name=timeline,show=all to find out about all available options for the timeline report.
To find out details of a particular option, use show=option_name , e.g. name=timeline,show=off string.
To learn about available report names, use name=show string.

9. To convert a family tree on the fly to a .gramps xml file:
gramps -O 'Family Tree 1' -e output.gramps -f gramps-xml

10. To generate a web site into an other locale (in german):
LANGUAGE=de_DE; LANG=de_DE.UTF-8 gramps -O 'Family Tree 1' -a report -p name=navwebpage,target=/../de

11. Finally, to start normal interactive session type:
gramps

Note: These examples are for bash shell.
Syntax may be different for other shells and for Windows.
""")

#-------------------------------------------------------------------------
# ArgParser
#-------------------------------------------------------------------------
class ArgParser(object):
    """
    This class is responsible for parsing the command line arguments (if any)
    given to gramps, and determining if a GUI or a CLI session must be started.
    The valid arguments are:

    Possible: 
        1/ FAMTREE : Just the family tree (name or database dir)
        2/ -O, --open=FAMTREE, Open of a family tree
        3/ -i, --import=FILE, Import a family tree of any format understood 
                 by an importer, optionally provide -f to indicate format
        4/ -e, --export=FILE, export a family tree in required format,
                 optionally provide -f to indicate format
        5/ -f, --format=FORMAT : format after a -i or -e option
        6/ -a, --action: An action (possible: 'report', 'tool')
        7/ -p, --options=OPTIONS_STRING : specify options
        8/ -u, --force-unlock: A locked database can be unlocked by giving
                 this argument when opening it
    
    If the filename (no flags) is specified, the interactive session is 
    launched using data from filename. 
    In this mode (filename, no flags), the rest of the arguments is ignored.
    This is a mode suitable by default for GUI launchers, mime type handlers,
    and the like
    
    If no filename or -i option is given, a new interactive session (empty
    database) is launched, since no data is given anyway.
    
    If -O or -i option is given, but no -e or -a options are given, an
    interactive session is launched with the FILE (specified with -i). 
    
    If both input (-O or -i) and processing (-e or -a) options are given,
    interactive session will not be launched. 
    """

    def __init__(self, args):
        """
        Pass the command line arguments on creation.
        """
        self.args = args

        self.open_gui = None
        self.open = None
        self.exports = []
        self.actions = []
        self.imports = []
        self.imp_db_path = None
        self.list = False
        self.list_more = False
        self.list_table = False
        self.help = False
        self.usage = False
        self.force_unlock = False
        self.create = None
        self.runqml = False

        self.errors = []
        self.parse_args()

    #-------------------------------------------------------------------------
    # Argument parser: sorts out given arguments
    #-------------------------------------------------------------------------
    def parse_args(self):
        """
        Fill in lists with open, exports, imports, and actions options.

        Any errors are added to self.errors
        
        Possible: 
        1/ Just the family tree (name or database dir)
        2/ -O, --open:   Open of a family tree
        3/ -i, --import: Import a family tree of any format understood by
                 an importer, optionally provide -f to indicate format
        4/ -e, --export: export a family tree in required format, optionally
                 provide -f to indicate format
        5/ -f, --format=FORMAT : format after a -i or -e option
        6/ -a, --action: An action (possible: 'report', 'tool')
        7/ -p, --options=OPTIONS_STRING : specify options
        8/ -u, --force-unlock: A locked database can be unlocked by giving
                 this argument when opening it
        9/ -s  --show : Show config settings
        10/ -c --config=config.setting:value : Set config.setting and start
                 Gramps without :value, the actual config.setting is shown
                            
        """
        try:
            # Convert arguments to unicode, otherwise getopt will not work
            # if a non latin character is used as an option (by mistake).
            # getopt will try to treat the first char in an utf-8 sequence. Example:
            # -Ärik is '-\xc3\x84rik' and getopt will respond :
            # option -\xc3 not recognized
            for arg in range(len(self.args) - 1):
                self.args[arg+1] = Utils.get_unicode_path_from_env_var(self.args[arg + 1])
            options, leftargs = getopt.getopt(self.args[1:],
                                             const.SHORTOPTS, const.LONGOPTS)
        except getopt.GetoptError, msg:
            # Extract the arguments in the list.
            # The % operator replaces the list elements with repr() of the list elemements
            # which is OK for latin characters, but not for non latin characters in list elements
            cliargs = "[ "
            for arg in range(len(self.args) - 1):
                cliargs += self.args[arg + 1] + " "
            cliargs += "]"
            # Must first do str() of the msg object.
            msg = unicode(str(msg))
            self.errors += [(_('Error parsing the arguments'), 
                        msg + '\n' +
                        _("Error parsing the arguments: %s \n" 
                        "Type gramps --help for an overview of commands, or "
                        "read the manual pages.") % cliargs)]
            return

        if leftargs:
            # if there were an argument without option,
            # use it as a file to open and return
            self.open_gui = leftargs[0]
            print >> sys.stderr, "Trying to open: %s ..." % leftargs[0]
            #see if force open is on
            for opt_ix in range(len(options)):
                option, value = options[opt_ix]
                if option in ('-u', '--force-unlock'):
                    self.force_unlock = True
                    break
            return

        # Go over all given option and place them into appropriate lists
        cleandbg = []
        need_to_quit = False
        for opt_ix in range(len(options)):
            option, value = options[opt_ix]
            if option in ( '-O', '--open'):
                self.open = value
            elif option in ( '-C', '--create'):
                self.create = value
            elif option in ( '-i', '--import'):
                family_tree_format = None
                if opt_ix < len(options) - 1 \
                   and options[opt_ix + 1][0] in ( '-f', '--format'): 
                    family_tree_format = options[opt_ix + 1][1]
                self.imports.append((value, family_tree_format))
            elif option in ( '-e', '--export' ):
                family_tree_format = None
                if opt_ix < len(options) - 1 \
                   and options[opt_ix + 1][0] in ( '-f', '--format'): 
                    family_tree_format = options[opt_ix + 1][1]
                self.exports.append((value, family_tree_format))
            elif option in ( '-a', '--action' ):
                action = value
                if action not in ( 'report', 'tool' ):
                    print >> sys.stderr, "Unknown action: %s. Ignoring." % action
                    continue
                options_str = ""
                if opt_ix < len(options)-1 \
                            and options[opt_ix+1][0] in ( '-p', '--options' ): 
                    options_str = options[opt_ix+1][1]
                self.actions.append((action, options_str))
            elif option in ('-d', '--debug'):
                print >> sys.stderr, 'setup debugging', value
                logger = logging.getLogger(value)
                logger.setLevel(logging.DEBUG)
                cleandbg += [opt_ix]
            elif option in ('-l'):
                self.list = True
            elif option in ('-L'):
                self.list_more = True
            elif option in ('-t'):
                self.list_table = True
            elif option in ('-s','--show'):
                print "Gramps config settings from %s:" % \
                       config.config.filename.encode(sys.getfilesystemencoding())
                for section in config.config.data:
                    for setting in config.config.data[section]:
                        print "%s.%s=%s" % (
                            section, setting, 
                            repr(config.config.data[section][setting]))
                    print
                sys.exit(0)
            elif option in ('-c', '--config'):
                setting_name = value
                set_value = False
                if setting_name:
                    if ":" in setting_name:
                        setting_name, new_value = setting_name.split(":", 1)
                        set_value = True
                    if config.has_default(setting_name):
                        setting_value = config.get(setting_name)
                        print >> sys.stderr, "Current Gramps config setting: " \
                                   "%s:%s" % (setting_name, repr(setting_value))
                        if set_value:
                            # does a user want the default config value?
                            if new_value in ("DEFAULT", _("DEFAULT")):
                                new_value = config.get_default(setting_name)
                            else:
                                converter = Utils.get_type_converter(setting_value)
                                new_value = converter(new_value)
                            config.set(setting_name, new_value)
                            # translators: indent "New" to match "Current"
                            print >> sys.stderr, "    New Gramps config " \
                                            "setting: %s:%s" % (
                                                setting_name,
                                                repr(config.get(setting_name))
                                                )
                        else:
                            need_to_quit = True
                    else:
                        print >> sys.stderr, "Gramps: no such config setting:" \
                                             " '%s'" % setting_name
                        need_to_quit = True
                cleandbg += [opt_ix]
            elif option in ('-h', '-?', '--help'):
                self.help = True
            elif option in ('-u', '--force-unlock'):
                self.force_unlock = True
            elif option in ('--usage'):
                self.usage = True
            elif option in ('--qml'):
                self.runqml = True
        
        #clean options list
        cleandbg.reverse()
        for ind in cleandbg:
            del options[ind]
        
        if len(options) > 0 and self.open is None and self.imports == [] \
                and not (self.list or self.list_more or self.list_table or
                         self.help or self.runqml):
            # Extract and convert to unicode the arguments in the list.
            # The % operator replaces the list elements with repr() of
            # the list elements, which is OK for latin characters
            # but not for non-latin characters in list elements
            cliargs = "[ "
            for arg in range(len(self.args) - 1):
                cliargs += Utils.get_unicode_path_from_env_var(self.args[arg + 1]) + " "
            cliargs += "]"
            self.errors += [(_('Error parsing the arguments'),
                             _("Error parsing the arguments: %s \n"
                               "To use in the command-line mode, supply at "
                               "least one input file to process.") % cliargs)]
        if need_to_quit:
            sys.exit(0)

    #-------------------------------------------------------------------------
    # Determine the need for GUI
    #-------------------------------------------------------------------------
    def need_gui(self):
        """
        Determine whether we need a GUI session for the given tasks.
        """
        if self.errors: 
            #errors in argument parsing ==> give cli error, no gui needed
            return False
        
        if self.list or self.list_more or self.list_table or self.help:
            return False

        if self.open_gui:
            # No-option argument, definitely GUI
            return True

        # If we have data to work with:
        if (self.open or self.imports):
            if (self.exports or self.actions):
                # have both data and what to do with it => no GUI
                return False
            elif self.create:
                if self.open: # create an empty DB, open a GUI to fill it
                    return True
                else: # create a DB, then do the import, with no GUI
                    self.open = self.create
                    return False
            else:
                # data given, but no action/export => GUI
                return True
        
        # No data, can only do GUI here
        return True
    
    def print_help(self):
        """
        If the user gives the --help or -h option, print the output to terminal.
        """
        if self.help:
            # Convert Help messages to file system encoding before printing
            print _HELP.encode(sys.getfilesystemencoding())
            sys.exit(0)
            
    def print_usage(self):
        """
        If the user gives the --usage print the output to terminal.
        """
        if self.usage:
            # Convert Help messages to file system encoding before printing
            print _USAGE.encode(sys.getfilesystemencoding())
            sys.exit(0)
