#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2001-2007 Donald N. Allingham
# Copyright (C) 2008      Lukasz Rymarczyk
# Copyright (C) 2008      Raphael Ackermann
# Copyright (C) 2008-2011 Brian G. Matherly
# Copyright (C) 2010      Jakim Friant
# Copyright (C) 2011      Paul Franklin
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
#
# cli.plug.__init__
#
# $Id$


#-------------------------------------------------------------------------
#
# Python modules
#
#-------------------------------------------------------------------------
from gen.ggettext import gettext as _
import traceback
import os
import sys

import logging
log = logging.getLogger(".")

#-------------------------------------------------------------------------
#
# Gramps modules
#
#-------------------------------------------------------------------------
import Utils
from gen.plug import BasePluginManager
from gen.plug.docgen import (StyleSheet, StyleSheetList, PaperStyle,
                             PAPER_PORTRAIT, PAPER_LANDSCAPE, graphdoc)
from gen.plug.menu import (FamilyOption, PersonOption, NoteOption, 
                           MediaOption, PersonListOption, NumberOption, 
                           BooleanOption, DestinationOption, StringOption, 
                           TextOption, EnumeratedListOption, Option)
from gen.display.name import displayer as name_displayer
from Errors import ReportError
from gen.plug.report import (CATEGORY_TEXT, CATEGORY_DRAW, CATEGORY_BOOK,
                             CATEGORY_GRAPHVIZ, CATEGORY_CODE)
from gen.plug.report._paper import paper_sizes
import const
import DbState
from cli.grampscli import CLIManager
import cli.user

#------------------------------------------------------------------------
#
# Private Functions
#
#------------------------------------------------------------------------
def _convert_str_to_match_type(str_val, type_val):
    """
    Returns a value representing str_val that is the same type as type_val.
    """
    str_val = str_val.strip()
    ret_type = type(type_val)
    
    if ret_type in (str, unicode):
        if ( str_val.startswith("'") and str_val.endswith("'") ) or \
           ( str_val.startswith('"') and str_val.endswith('"') ):
            # Remove enclosing quotes
            return unicode(str_val[1:-1])
        else:
            return unicode(str_val)
        
    elif ret_type == int:
        if str_val.isdigit():
            return int(str_val)
        else:
            print "'%s' is not an integer number" % str_val
            return 0
        
    elif ret_type == float:
        try:
            return float(str_val)
        except ValueError:
            print "'%s' is not a decimal number" % str_val
            return 0.0
        
    elif ret_type == bool:
        if str_val == str(True):
            return True
        elif str_val == str(False):
            return False
        else:
            print "'%s' is not a boolean-- try 'True' or 'False'" % str_val
            return False
    
    elif ret_type == list:
        ret_val = []
        if not ( str_val.startswith("[") and str_val.endswith("]") ):
            print "'%s' is not a list-- try: [%s]" % (str_val, str_val)
            return ret_val
        
        entry = ""
        quote_type = None
        
        # Search through characters between the brackets
        for char in str_val[1:-1]:
            if (char == "'" or char == '"') and quote_type == None:
                # This character starts a string
                quote_type = char
            elif char == quote_type:
                # This character ends a string
                quote_type = None
            elif quote_type == None and char == ",":
                # This character ends an entry
                ret_val.append(entry.strip())
                entry = ""
                quote_type = None
            else:
                entry += char

        if entry != "":
            # Add the last entry
            ret_val.append(entry.strip())
            
        return ret_val

def _validate_options(options, dbase):
    """
    Validate all options by making sure that their values are consistent with
    the database.
    
    menu: The Menu class
    dbase: the database the options will be applied to
    """
    if not hasattr(options, "menu"):
        return
    menu = options.menu
    
    for name in menu.get_all_option_names():
        option = menu.get_option_by_name(name)

        if isinstance(option, PersonOption):
            pid = option.get_value()
            person = dbase.get_person_from_gramps_id(pid)
            if not person:
                person = dbase.get_default_person()
                if not person:
                    try:
                        phandle = dbase.iter_person_handles().next()
                    except StopIteration:
                        phandle = None
                    person = dbase.get_person_from_handle(phandle)
                    if not person:
                        print _("ERROR: Please specify a person").encode(sys.getfilesystemencoding())
            if person:
                option.set_value(person.get_gramps_id())
            
        elif isinstance(option, FamilyOption):
            fid = option.get_value()
            family = dbase.get_family_from_gramps_id(fid)
            if not family:
                person = dbase.get_default_person()
                family_list = []
                family_handle = None
                if person:
                    family_list = person.get_family_handle_list()
                if family_list:
                    family_handle = family_list[0]
                else:
                    try:
                        family_handle = dbase.iter_family_handles().next()
                    except StopIteration:
                        family_handle = None
                if family_handle:
                    family = dbase.get_family_from_handle(family_handle)
                    option.set_value(family.get_gramps_id())
                else:
                    print _("ERROR: Please specify a family").encode(sys.getfilesystemencoding())

#------------------------------------------------------------------------
#
# Command-line report
#
#------------------------------------------------------------------------
class CommandLineReport(object):
    """
    Provide a way to generate report from the command line.
    """

    def __init__(self, database, name, category, option_class, options_str_dict,
                 noopt=False):
        
        pmgr = BasePluginManager.get_instance()
        self.__textdoc_plugins = []
        self.__drawdoc_plugins = []
        self.__bookdoc_plugins = []
        for plugin in pmgr.get_docgen_plugins():
            if plugin.get_text_support() and plugin.get_extension():
                self.__textdoc_plugins.append(plugin)
            if plugin.get_draw_support() and plugin.get_extension():
                self.__drawdoc_plugins.append(plugin)
            if plugin.get_text_support() and \
               plugin.get_draw_support() and \
               plugin.get_extension():
                self.__bookdoc_plugins.append(plugin)
        
        self.database = database
        self.category = category
        self.format = None
        self.option_class = option_class(name, database)
        if category == CATEGORY_GRAPHVIZ:
            # Need to include GraphViz options
            self.__gvoptions = graphdoc.GVOptions()
            menu = self.option_class.menu
            self.__gvoptions.add_menu_options(menu)
            for name in menu.get_all_option_names():
                if name not in self.option_class.options_dict:
                    self.option_class.options_dict[name] = \
                      menu.get_option_by_name(name).get_value()
        self.option_class.load_previous_values()
        _validate_options(self.option_class, database)
        self.show = options_str_dict.pop('show', None)
        self.options_str_dict = options_str_dict
        self.init_standard_options(noopt)
        self.init_report_options()
        self.parse_options()
        self.show_options()

    def init_standard_options(self, noopt):
        """
        Initialize the options that are hard-coded into the report system.
        """
        self.options_dict = {
            'of'        : self.option_class.handler.module_name,
            'off'       : self.option_class.handler.get_format_name(),
            'style'     : \
                    self.option_class.handler.get_default_stylesheet_name(),
            'papers'    : self.option_class.handler.get_paper_name(),
            'papero'    : self.option_class.handler.get_orientation(),
            'paperml'   : self.option_class.handler.get_margins()[0],
            'papermr'   : self.option_class.handler.get_margins()[1],
            'papermt'   : self.option_class.handler.get_margins()[2],
            'papermb'   : self.option_class.handler.get_margins()[3],
            'css'       : self.option_class.handler.get_css_filename(),
            }

        self.options_help = {
            'of'        : ["=filename", "Output file name. MANDATORY", ""],
            'off'       : ["=format", "Output file format.", []],
            'style'     : ["=name", "Style name.", ""],
            'papers'    : ["=name", "Paper size name.", ""],
            'papero'    : ["=num", "Paper orientation number.", ""],
            'paperml'   : ["=num", "Left paper margin", "Size in cm"],
            'papermr'   : ["=num", "Right paper margin", "Size in cm"],
            'papermt'   : ["=num", "Top paper margin", "Size in cm"],
            'papermb'   : ["=num", "Bottom paper margin", "Size in cm"],
            'css'       : ["=css filename", "CSS filename to use, html format"
                            " only", ""],
            }

        if noopt:
            return

        self.options_help['of'][2] = os.path.join(const.USER_HOME, 
                                                  "whatever_name")

        if self.category == CATEGORY_TEXT:
            for plugin in self.__textdoc_plugins:
                self.options_help['off'][2].append( 
                    plugin.get_extension() + "\t" + plugin.get_description() )
        elif self.category == CATEGORY_DRAW:
            for plugin in self.__drawdoc_plugins:
                self.options_help['off'][2].append(  
                    plugin.get_extension() + "\t" + plugin.get_description() )
        elif self.category == CATEGORY_BOOK:
            for plugin in self.__bookdoc_plugins:
                self.options_help['off'][2].append(  
                    plugin.get_extension() + "\t" + plugin.get_description() )
        elif self.category == CATEGORY_GRAPHVIZ:
            for graph_format in graphdoc.FORMATS:
                self.options_help['off'][2].append(
                    graph_format["type"] + "\t" + graph_format["descr"] )
        else:
            self.options_help['off'][2] = "NA"

        self.options_help['papers'][2] = \
            [ paper.get_name() for paper in paper_sizes 
                        if paper.get_name() != 'Custom Size' ]

        self.options_help['papero'][2] = [
            "%d\tPortrait" % PAPER_PORTRAIT,
            "%d\tLandscape" % PAPER_LANDSCAPE ]

        self.options_help['css'][2] = os.path.join(const.USER_HOME,
                                                   "whatever_name.css")

        if self.category in (CATEGORY_TEXT, CATEGORY_DRAW):
            default_style = StyleSheet()
            self.option_class.make_default_style(default_style)

            # Read all style sheets available for this item
            style_file = self.option_class.handler.get_stylesheet_savefile()
            self.style_list = StyleSheetList(style_file, default_style)
            
            self.options_help['style'][2] = self.style_list.get_style_names()
            
    def init_report_options(self):
        """
        Initialize the options that are defined by each report.
        """

        if self.category == CATEGORY_BOOK: # a Book Report has no "menu"
            for key in self.option_class.options_dict:
                self.options_dict[key] = self.option_class.options_dict[key]
                self.options_help[key] = \
                    self.option_class.options_help[key][:3]
            # a Book Report can't have HTML output so "css" is meaningless
            self.options_dict.pop('css')

        if not hasattr(self.option_class, "menu"):
            return
        menu = self.option_class.menu
        for name in menu.get_all_option_names():
            option = menu.get_option_by_name(name)
            self.options_dict[name] = option.get_value()
            self.options_help[name] = [ "", option.get_help() ]
            
            if isinstance(option, PersonOption):
                id_list = []
                for person_handle in self.database.get_person_handles(True):
                    person = self.database.get_person_from_handle(person_handle)
                    id_list.append("%s\t%s" % (
                        person.get_gramps_id(),
                        name_displayer.display(person)))
                self.options_help[name].append(id_list)
            elif isinstance(option, FamilyOption):
                id_list = []
                for family in self.database.iter_families():
                    mname = ""
                    fname = ""
                    mhandle = family.get_mother_handle()
                    if mhandle:
                        mother = self.database.get_person_from_handle(mhandle)
                        if mother:
                            mname = name_displayer.display(mother)
                    fhandle = family.get_father_handle()
                    if fhandle:
                        father = self.database.get_person_from_handle(fhandle)
                        if father:
                            fname = name_displayer.display(father)
                    text = "%s:\t%s, %s" % \
                        (family.get_gramps_id(), fname, mname)
                    id_list.append(text)
                self.options_help[name].append(id_list)
            elif isinstance(option, NoteOption):
                id_list = []
                for nhandle in self.database.get_note_handles():
                    note = self.database.get_note_from_handle(nhandle)
                    id_list.append(note.get_gramps_id())
                self.options_help[name].append(id_list)
            elif isinstance(option, MediaOption):
                id_list = []
                for mhandle in self.database.get_media_object_handles():
                    mobject = self.database.get_object_from_handle(mhandle)
                    id_list.append(mobject.get_gramps_id())
                self.options_help[name].append(id_list)
            elif isinstance(option, PersonListOption):
                self.options_help[name].append("")
            elif isinstance(option, NumberOption):
                self.options_help[name].append("A number")
            elif isinstance(option, BooleanOption):
                self.options_help[name].append(["False", "True"])
            elif isinstance(option, DestinationOption):
                self.options_help[name].append("A file system path")
            elif isinstance(option, StringOption):
                self.options_help[name].append("Any text")
            elif isinstance(option, TextOption):
                self.options_help[name].append(
                    "A list of text values. Each entry in the list "
                    "represents one line of text." )
            elif isinstance(option, EnumeratedListOption):
                ilist = []
                for (value, description) in option.get_items():
                    ilist.append("%s\t%s" % (value, description))
                self.options_help[name].append(ilist)
            elif isinstance(option, Option):
                self.options_help[name].append(option.get_help())
            else:
                print (_("Unknown option: %s") % option).encode(sys.getfilesystemencoding())
                print (_("   Valid options are:"), ", ".join(
                                                     self.options_dict.keys())).encode(sys.getfilesystemencoding())
                print (_("   Use '%(donottranslate)s' to see description "
                         "and acceptable values") %
                       {'donottranslate' : "show=option"}).encode(sys.getfilesystemencoding())
                
    def parse_options(self):
        """
        Load the options that the user has entered.
        """
        if not hasattr(self.option_class, "menu"):
            menu = None
        else:
            menu = self.option_class.menu
            menu_opt_names = menu.get_all_option_names()
        for opt in self.options_str_dict:
            if opt in self.options_dict:
                self.options_dict[opt] = \
                    _convert_str_to_match_type(self.options_str_dict[opt], 
                                               self.options_dict[opt])

                self.option_class.handler.options_dict[opt] = \
                                                        self.options_dict[opt]
                                                        
                if menu and opt in menu_opt_names:
                    option = menu.get_option_by_name(opt)
                    option.set_value(self.options_dict[opt])
                
            else:
                print (_("Ignoring unknown option: %s") % opt).encode(sys.getfilesystemencoding())
                print (_("   Valid options are:") + ", ".join(
                                                     self.options_dict.keys())).encode(sys.getfilesystemencoding())
                print (_("   Use '%(donottranslate)s' to see description "
                         "and acceptable values") %
                       {'donottranslate' : "show=option"}).encode(sys.getfilesystemencoding())
        
        self.option_class.handler.output = self.options_dict['of']

        self.css_filename = None
        _chosen_format = None
        if self.category == CATEGORY_TEXT:
            for plugin in self.__textdoc_plugins:
                if plugin.get_extension() == self.options_dict['off']:
                    self.format = plugin.get_basedoc()
            self.css_filename = self.options_dict['css']
            if self.format is None:
                # Pick the first one as the default.
                self.format = self.__textdoc_plugins[0].get_basedoc()
                _chosen_format = self.__textdoc_plugins[0].get_extension()
        elif self.category == CATEGORY_DRAW:
            for plugin in self.__drawdoc_plugins:
                if plugin.get_extension() == self.options_dict['off']:
                    self.format = plugin.get_basedoc()
            if self.format is None:
                # Pick the first one as the default.
                self.format = self.__drawdoc_plugins[0].get_basedoc()
                _chosen_format = self.__drawdoc_plugins[0].get_extension()
        elif self.category == CATEGORY_BOOK:
            for plugin in self.__bookdoc_plugins:
                if plugin.get_extension() == self.options_dict['off']:
                    self.format = plugin.get_basedoc()
            if self.format is None:
                # Pick the first one as the default.
                self.format = self.__bookdoc_plugins[0].get_basedoc()
                _chosen_format = self.__bookdoc_plugins[0].get_extension()
        elif self.category == CATEGORY_GRAPHVIZ:
            for graph_format in graphdoc.FORMATS:
                if graph_format['type'] == self.options_dict['off']:
                    if not self.format: # choose the first one, not the last
                        self.format = graph_format["class"]
            if self.format is None:
                # Pick the first one as the default.
                self.format = graphdoc.FORMATS[0]["class"]
                _chosen_format = graphdoc.FORMATS[0]["type"]
        else:
            self.format = None
        if _chosen_format and self.options_str_dict.has_key('off'):
            print (_("Ignoring '%(notranslate1)s=%(notranslate2)s' "
                     "and using '%(notranslate1)s=%(notranslate3)s'.") %
                   {'notranslate1' : "off",
                    'notranslate2' : self.options_dict['off'],
                    'notranslate3' : _chosen_format}).encode(sys.getfilesystemencoding())
            print (_("Use '%(notranslate)s' to see valid values.") %
                   {'notranslate' : "show=off"}).encode(sys.getfilesystemencoding())

        self.paper = paper_sizes[0] # make sure one exists
        for paper in paper_sizes:
            if paper.get_name() == self.options_dict['papers']:
                self.paper = paper
        self.option_class.handler.set_paper(self.paper)

        self.orien = self.options_dict['papero']
        
        self.marginl = self.options_dict['paperml']
        self.marginr = self.options_dict['papermr']
        self.margint = self.options_dict['papermt']
        self.marginb = self.options_dict['papermb']

        if self.category in (CATEGORY_TEXT, CATEGORY_DRAW):
            default_style = StyleSheet()
            self.option_class.make_default_style(default_style)

            # Read all style sheets available for this item
            style_file = self.option_class.handler.get_stylesheet_savefile()
            self.style_list = StyleSheetList(style_file, default_style)

            # Get the selected stylesheet
            style_name = self.option_class.handler.get_default_stylesheet_name()
            self.selected_style = self.style_list.get_style_sheet(style_name)

    def show_options(self):
        """
        Print available options on the CLI.
        """
        if not self.show:
            return
        elif self.show == 'all':
            print _("   Available options:").encode(sys.getfilesystemencoding())
            for key in sorted(self.options_dict.keys()):
                if key in self.options_help:
                    opt = self.options_help[key]
                    # Make the output nicer to read, assume a tab has 8 spaces
                    tabs = '\t\t' if len(key) < 10 else '\t'
                    optmsg = "      %s%s%s (%s)" % (key, tabs, opt[1], opt[0])
                    print optmsg.encode(sys.getfilesystemencoding())
                else:
                    optmsg = " %s" % key
                    print optmsg.encode(sys.getfilesystemencoding())
            print (_("   Use '%(donottranslate)s' to see description "
                     "and acceptable values") %
                   {'donottranslate' : "show=option"}).encode(sys.getfilesystemencoding())
        elif self.show in self.options_help:
            opt = self.options_help[self.show]
            tabs = '\t\t' if len(self.show) < 10 else '\t'
            print '   %s%s%s (%s)' % (self.show, tabs, opt[1], opt[0])
            print _("   Available values are:").encode(sys.getfilesystemencoding())
            vals = opt[2]
            if isinstance(vals, (list, tuple)):
                for val in vals:
                    optmsg = "      %s" % val
                    print optmsg.encode(sys.getfilesystemencoding())
            else:
                optmsg = "      %s" % opt[2]
                print optmsg.encode(sys.getfilesystemencoding())

        else:
            #there was a show option given, but the option is invalid
            print (_("option '%(optionname)s' not valid. "
                     "Use '%(donottranslate)s' to see all valid options.") %
                   {'optionname' : self.show, 'donottranslate' : "show=all"}).encode(sys.getfilesystemencoding())

#------------------------------------------------------------------------
#
# Command-line report generic task
#
#------------------------------------------------------------------------
def cl_report(database, name, category, report_class, options_class, 
              options_str_dict):
    
    err_msg = _("Failed to write report. ").encode(sys.getfilesystemencoding())
    clr = CommandLineReport(database, name, category, options_class, 
                            options_str_dict)

    # Exit here if show option was given
    if clr.show:
        return

    # write report
    try:
        if category in [CATEGORY_TEXT, CATEGORY_DRAW, CATEGORY_BOOK]:
            clr.option_class.handler.doc = clr.format(
                        clr.selected_style,
                        PaperStyle(clr.paper,clr.orien,clr.marginl,
                                   clr.marginr,clr.margint,clr.marginb))
        elif category == CATEGORY_GRAPHVIZ:
            clr.option_class.handler.doc = clr.format(
                        clr.option_class,
                        PaperStyle(clr.paper,clr.orien,clr.marginl,
                                   clr.marginr,clr.margint,clr.marginb))
        if clr.css_filename is not None and \
           hasattr(clr.option_class.handler.doc, 'set_css_filename'):
            clr.option_class.handler.doc.set_css_filename(clr.css_filename)
        MyReport = report_class(database, clr.option_class, cli.user.User())
        MyReport.doc.init()
        MyReport.begin_report()
        MyReport.write_report()
        MyReport.end_report()
        return clr
    except ReportError, msg:
        (m1, m2) = msg.messages()
        print err_msg
        print m1
        if m2:
            print m2
    except:
        if len(log.handlers) > 0:
            log.error(err_msg, exc_info=True)
        else:
            print >> sys.stderr, err_msg
            ## Something seems to eat the exception above.
            ## Hack to re-get the exception:
            try:
                raise
            except:
                traceback.print_exc()

def run_report(db, name, **options_str_dict):
    """
    Given a database, run a given report.

    db is a Db database

    name is the name of a report

    options_str_dict is the same kind of options
    given at the command line. For example:
    
    >>> run_report(db, "ancestor_report", off="txt",
                   of="ancestor-007.txt", pid="I37")

    returns CommandLineReport (clr) if successfully runs the report,
    None otherwise.

    You can see:
       options and values used in  clr.option_class.options_dict
       filename in clr.option_class.get_output()
    """
    dbstate = DbState.DbState()
    climanager = CLIManager(dbstate, False) # don't load db
    climanager.do_reg_plugins(dbstate, None)
    pmgr = BasePluginManager.get_instance()
    cl_list = pmgr.get_reg_reports()
    clr = None
    for pdata in cl_list:
        if name == pdata.id:
            mod = pmgr.load_plugin(pdata)
            if not mod:
                #import of plugin failed
                return clr
            category = pdata.category
            report_class = getattr(mod, pdata.reportclass)
            options_class = getattr(mod, pdata.optionclass)
            if category in (CATEGORY_BOOK, CATEGORY_CODE):
                options_class(db, name, category, 
                              options_str_dict)
            else:
                clr = cl_report(db, name, category, 
                                report_class, options_class,
                                options_str_dict)
                return clr
    return clr
