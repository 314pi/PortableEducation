#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2003-2007  Donald N. Allingham
# Copyright (C) 2007-2008  Brian G. Matherly
# Copyright (C) 2010       Jakim Friant
# Copyright (C) 2011       Paul Franklin
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

# Written by Alex Roitman, 
# largely based on the BaseDoc classes by Don Allingham

#-------------------------------------------------------------------------
#
# Standard Python modules
#
#-------------------------------------------------------------------------
from gen.ggettext import gettext as _

#------------------------------------------------------------------------
#
# Set up logging
#
#------------------------------------------------------------------------
import logging
log = logging.getLogger(".BookReport")
import os

#-------------------------------------------------------------------------
#
# SAX interface
#
#-------------------------------------------------------------------------
try:
    from xml.sax import make_parser, handler, SAXParseException
    from xml.sax.saxutils import escape
except:
    from _xmlplus.sax import make_parser, handler, SAXParseException
    from _xmlplus.sax.saxutils import escape

#-------------------------------------------------------------------------
#
# GTK/Gnome modules
#
#-------------------------------------------------------------------------
import gtk
import gobject

#-------------------------------------------------------------------------
#
# gramps modules
#
#-------------------------------------------------------------------------
import const
import Utils
import ListModel
import Errors
from gui.pluginmanager import GuiPluginManager
from gen.plug.docgen import StyleSheet, StyleSheetList, PaperStyle
from QuestionDialog import WarningDialog, ErrorDialog
from gen.plug.menu import PersonOption, FilterOption, FamilyOption
import ManagedWindow
from glade import Glade
import gui.utils
import gui.user
from gui.plug import make_gui_option
from types import ClassType

# Import from specific modules in ReportBase
from gen.plug.report import CATEGORY_BOOK, book_categories
from gui.plug.report._reportdialog import ReportDialog
from gui.plug.report._docreportdialog import DocReportDialog
from gen.plug.report._options import ReportOptions
from cli.plug import CommandLineReport
import cli.user

from gen.display.name import displayer as _nd

#------------------------------------------------------------------------
#
# Private Constants
#
#------------------------------------------------------------------------
_UNSUPPORTED = _("Unsupported")

#------------------------------------------------------------------------
#
# Private Functions
#
#------------------------------------------------------------------------
def _initialize_options(options, dbstate, uistate):
    """
    Validates all options by making sure that their values are consistent with
    the database.
    
    menu: The Menu class
    dbase: the database the options will be applied to
    """
    if not hasattr(options, "menu"):
        return
    dbase = dbstate.get_database()
    menu = options.menu
    
    for name in menu.get_all_option_names():
        option = menu.get_option_by_name(name)
        value = option.get_value()

        if isinstance(option, PersonOption):
            if not dbase.get_person_from_gramps_id(value):
                person_handle = uistate.get_active('Person')
                person = dbase.get_person_from_handle(person_handle)
                option.set_value(person.get_gramps_id())
        
        elif isinstance(option, FamilyOption):
            if not dbase.get_family_from_gramps_id(value):
                person_handle = uistate.get_active('Person')
                person = dbase.get_person_from_handle(person_handle)
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
                    print "No family specified for ", name

def _get_subject(options, dbase):
    """
    Attempts to determine the subject of a set of options. The subject would
    likely be a person (using a PersonOption) or a filter (using a 
    FilterOption)
    
    options: The ReportOptions class
    dbase: the database for which it corresponds
    """
    if not hasattr(options, "menu"):
        return ""
    menu = options.menu
    
    option_names = menu.get_all_option_names()
    if not option_names:
        return _("Entire Database")

    for name in option_names:
        option = menu.get_option_by_name(name)
        
        if isinstance(option, FilterOption):
            return option.get_filter().get_name()
        
        elif isinstance(option, PersonOption):
            gid = option.get_value()
            person = dbase.get_person_from_gramps_id(gid)
            return _nd.display(person)
        
        elif isinstance(option, FamilyOption):
            family = dbase.get_family_from_gramps_id(option.get_value())
            if not family:
                return ""
            family_id = family.get_gramps_id()
            fhandle = family.get_father_handle()
            mhandle = family.get_mother_handle()
            
            if fhandle:
                father = dbase.get_person_from_handle(fhandle)
                father_name = _nd.display(father)
            else:
                father_name = _("unknown father")
                
            if mhandle:
                mother = dbase.get_person_from_handle(mhandle)
                mother_name = _nd.display(mother)
            else:
                mother_name = _("unknown mother")
                
            name = _("%(father)s and %(mother)s (%(id)s)") % {
                                                'father' : father_name, 
                                                'mother' : mother_name, 
                                                'id' : family_id }
            return name
        
    return ""

#------------------------------------------------------------------------
#
# Book Item class
#
#------------------------------------------------------------------------
class BookItem(object):
    """
    Interface into the book item -- a smallest element of the book.
    """

    def __init__(self, dbase, name):
        """
        Create a new empty BookItem.
        
        name:   the book item is retrieved 
                from the book item registry using name for lookup
        """
        self.dbase = dbase
        self.style_name = "default"
        pmgr = GuiPluginManager.get_instance()

        for pdata in pmgr.get_reg_bookitems():
            if pdata.id == name:
                self.translated_name = pdata.name
                if not pdata.supported:
                    self.category = _UNSUPPORTED
                else:
                    self.category = book_categories[pdata.category]
                mod = pmgr.load_plugin(pdata)
                self.write_item = eval('mod.' + pdata.reportclass)
                self.name = pdata.id
                oclass = eval('mod.' + pdata.optionclass)
                self.option_class = oclass(self.name, self.dbase)
                self.option_class.load_previous_values()

    def get_name(self):
        """
        Return the name of the item.
        """
        return self.name

    def get_translated_name(self):
        """
        Return the translated name of the item.
        """
        return self.translated_name

    def get_category(self):
        """
        Return the category of the item.
        """
        return self.category

    def get_write_item(self):
        """
        Return the report-writing function of the item.
        """
        return self.write_item

    def set_style_name(self, style_name):
        """
        Set the style name for the item.
        
        style_name: name of the style to set.
        """
        self.style_name = style_name

    def get_style_name(self):
        """
        Return the style name of the item.
        """
        return self.style_name

#------------------------------------------------------------------------
#
# Book class
#
#------------------------------------------------------------------------
class Book(object):
    """
    Interface into the user-defined book -- a collection of book items.
    """

    def __init__(self, obj=None):
        """
        Create a new empty Book.

        obj:    if not None, creates the Book from the values in
                obj, instead of creating an empty Book.
        """

        self.name = ""
        self.dbname = ""
        if obj:
            self.item_list = obj.item_list
        else:
            self.item_list = []
        
    def set_name(self, name):
        """
        Set the name of the book.
        
        name:   the name to set.
        """
        self.name = name

    def get_name(self):
        """
        Return the name of the book.
        """
        return self.name

    def get_dbname(self):
        """
        Return the name of the database file used for the book.
        """
        return self.dbname

    def set_dbname(self, name):
        """
        Set the name of the database file used for the book.

        name:   a filename to set.
        """
        self.dbname = name

    def clear(self):
        """
        Clears the contents of the book.
        """
        self.item_list = []

    def append_item(self, item):
        """
        Add an item to the book.
        
        item:   an item to append.
        """
        self.item_list.append(item)

    def insert_item(self, index, item):
        """
        Inserts an item into the given position in the book.
        
        index:  a position index. 
        item:   an item to append.
        """
        self.item_list.insert(index, item)

    def pop_item(self, index):
        """
        Pop an item from given position in the book.
        
        index:  a position index. 
        """
        return self.item_list.pop(index)

    def get_item(self, index):
        """
        Return an item at a given position in the book.
        
        index:  a position index. 
        """
        return self.item_list[index]

    def set_item(self, index, item):
        """
        Set an item at a given position in the book.
        
        index:  a position index. 
        item:   an item to set.
        """
        self.item_list[index] = item

    def get_item_list(self):
        """
        Return list of items in the current book.
        """
        return self.item_list

#------------------------------------------------------------------------
#
# BookList class
#
#------------------------------------------------------------------------
class BookList(object):
    """
    Interface into the user-defined list of books.  

    BookList is loaded from a specified XML file if it exists.
    """

    def __init__(self, filename, dbase):
        """
        Create a new BookList from the books that may be defined in the 
        specified file.

        file:   XML file that contains book items definitions
        """
        self.dbase = dbase
        self.bookmap = {}
        self.file = os.path.join(const.HOME_DIR, filename)
        self.parse()
    
    def delete_book(self, name):
        """
        Remove a book from the list. Since each book must have a
        unique name, the name is used to delete the book.

        name:   name of the book to delete
        """
        del self.bookmap[name]

    def get_book_map(self):
        """
        Return the map of names to books.
        """
        return self.bookmap

    def get_book(self, name):
        """
        Return the Book associated with the name

        name:   name associated with the desired Book.
        """
        return self.bookmap[name]

    def get_book_names(self):
        "Return a list of all the book names in the BookList, sorted"
        return sorted(self.bookmap.keys())

    def set_book(self, name, book):
        """
        Add or replaces a Book in the BookList. 

        name:   name associated with the Book to add or replace.
        book:   definition of the Book
        """
        self.bookmap[name] = book

    def save(self):
        """
        Saves the current BookList to the associated file.
        """
        f = open(self.file, "w")
        f.write("<?xml version=\"1.0\" encoding=\"utf-8\"?>\n")
        f.write('<booklist>\n')
        for name in sorted(self.bookmap): # enable a diff of archived copies
            book = self.get_book(name)
            dbname = book.get_dbname()
            f.write('<book name="%s" database="%s">\n' % (name, dbname) )
            for item in book.get_item_list():
                f.write('  <item name="%s" trans_name="%s">\n' % 
                            (item.get_name(),item.get_translated_name() ) )
                options = item.option_class.handler.options_dict
                for option_name, option_value in options.iteritems():
                    if isinstance(option_value, (list, tuple)):
                        f.write('  <option name="%s" value="" '
                                'length="%d">\n' % (
                                    escape(option_name),
                                    len(options[option_name]) ) )
                        for list_index in range(len(option_value)):
                            option_type = Utils.type_name(
                                option_value[list_index]
                            )
                            value = escape(unicode(option_value[list_index]))
                            value = value.replace('"', '&quot;')
                            f.write('    <listitem number="%d" type="%s" '
                                    'value="%s"/>\n' % (
                                    list_index,
                                    option_type,
                                    value ) )
                        f.write('  </option>\n')
                    else:
                        option_type = Utils.type_name(option_value)
                        value = escape(unicode(option_value))
                        value = value.replace('"', '&quot;')
                        f.write('  <option name="%s" type="%s" '
                                'value="%s"/>\n' % (
                                escape(option_name),
                                option_type,
                                value) )

                f.write('    <style name="%s"/>\n' % item.get_style_name() )
                f.write('  </item>\n')
            f.write('</book>\n')

        f.write('</booklist>\n')
        f.close()
        
    def parse(self):
        """
        Loads the BookList from the associated file, if it exists.
        """
        try:
            p = make_parser()
            p.setContentHandler(BookParser(self, self.dbase))
            the_file = open(self.file)
            p.parse(the_file)
            the_file.close()
        except (IOError, OSError, ValueError, SAXParseException, KeyError,
               AttributeError):
            pass


#-------------------------------------------------------------------------
#
# BookParser
#
#-------------------------------------------------------------------------
class BookParser(handler.ContentHandler):
    """
    SAX parsing class for the Books XML file.
    """
    
    def __init__(self, booklist, dbase):
        """
        Create a BookParser class that populates the passed booklist.

        booklist:   BookList to be loaded from the file.
        """
        handler.ContentHandler.__init__(self)
        self.dbase = dbase
        self.booklist = booklist
        self.b = None
        self.i = None
        self.o = None
        self.an_o_name = None
        self.an_o_value = None
        self.s = None
        self.bname = None
        self.iname = None
        
    def startElement(self, tag, attrs):
        """
        Overridden class that handles the start of a XML element
        """
        if tag == "book":
            self.b = Book()
            self.bname = attrs['name']
            self.b.set_name(self.bname)
            self.dbname = attrs['database']
            self.b.set_dbname(self.dbname)
        elif tag == "item":
            self.i = BookItem(self.dbase, attrs['name'])
            self.o = {}
        elif tag == "option":
            self.an_o_name = attrs['name']
            if attrs.has_key('length'):
                self.an_o_value = []
            else:
                converter = Utils.get_type_converter_by_name(attrs['type'])
                self.an_o_value = converter(attrs['value'])
        elif tag == "listitem":
            converter = Utils.get_type_converter_by_name(attrs['type'])
            self.an_o_value.append(converter(attrs['value']))
        elif tag == "style":
            self.s = attrs['name']
        else:
            pass

    def endElement(self, tag):
        "Overridden class that handles the end of a XML element"
        if tag == "option":
            self.o[self.an_o_name] = self.an_o_value
        elif tag == "item":
            self.i.option_class.handler.options_dict.update(self.o)
            self.i.set_style_name(self.s)
            self.b.append_item(self.i)
        elif tag == "book":
            self.booklist.set_book(self.bname, self.b)

#------------------------------------------------------------------------
#
# BookList Display class
#
#------------------------------------------------------------------------
class BookListDisplay(object):
    """
    Interface into a dialog with the list of available books. 

    Allows the user to select and/or delete a book from the list.
    """

    def __init__(self, booklist, nodelete=0, dosave=0):
        """
        Create a BookListDisplay object that displays the books in BookList.

        booklist:   books that are displayed
        nodelete:   if not 0 then the Delete button is hidden
        dosave:     if 1 then the book list is saved on hitting OK
        """
        
        self.booklist = booklist
        self.dosave = dosave
        self.xml = Glade()
        self.top = self.xml.toplevel
        self.unsaved_changes = False

        ManagedWindow.set_titles(self.top,
            self.xml.get_object('title'),_('Available Books'))

        if nodelete:
            delete_button = self.xml.get_object("delete_button")
            delete_button.hide()
        self.xml.connect_signals({
            "on_booklist_cancel_clicked" : self.on_booklist_cancel_clicked,
            "on_booklist_ok_clicked"     : self.on_booklist_ok_clicked,
            "on_booklist_delete_clicked" : self.on_booklist_delete_clicked,
            "on_book_ok_clicked"         : self.do_nothing,
            "destroy_passed_object"      : self.do_nothing,
            "on_setup_clicked"           : self.do_nothing,
            "on_down_clicked"            : self.do_nothing,
            "on_up_clicked"              : self.do_nothing,
            "on_remove_clicked"          : self.do_nothing,
            "on_add_clicked"             : self.do_nothing,
            "on_edit_clicked"            : self.do_nothing,
            "on_open_clicked"            : self.do_nothing,
            "on_save_clicked"            : self.do_nothing,
            "on_clear_clicked"           : self.do_nothing
            })

        title_label = self.xml.get_object('title')
        title_label.set_text(Utils.title(_('Book List')))
        title_label.set_use_markup(True)
        
        self.blist = ListModel.ListModel(self.xml.get_object("list"),
                                        [('Name',-1,10)],)
        self.redraw()
        self.selection = None
        self.top.run()

    def redraw(self):
        """Redraws the list of currently available books"""
        
        self.blist.model.clear()
        names = self.booklist.get_book_names()
        if not len(names):
            return
        for name in names:
            the_iter = self.blist.add([name])
        if the_iter:
            self.blist.selection.select_iter(the_iter)

    def on_booklist_ok_clicked(self, obj):
        """Return selected book. Saves the current list into xml file."""
        store, the_iter = self.blist.get_selected()
        if the_iter:
            data = self.blist.get_data(the_iter, [0])
            self.selection = self.booklist.get_book(unicode(data[0]))
        if self.dosave:
            self.booklist.save()

    def on_booklist_delete_clicked(self, obj):
        """
        Deletes selected book from the list.
        
        This change is not final. OK button has to be clicked to save the list.
        """
        store, the_iter = self.blist.get_selected()
        if not the_iter:
            return
        data = self.blist.get_data(the_iter, [0])
        self.booklist.delete_book(unicode(data[0]))
        self.blist.remove(the_iter)
        self.unsaved_changes = True
        self.top.run()

    def on_booklist_cancel_clicked(self, obj):
        if self.unsaved_changes:
            from QuestionDialog import QuestionDialog2
            q = QuestionDialog2(
                _('Discard Unsaved Changes'),
                _('You have made changes which have not been saved.'),
                _('Proceed'),
                _('Cancel'))
            if q.run():
                return                
            else:
                self.top.run()
    
    def do_nothing(self, object):
        pass

#------------------------------------------------------------------------
#
# 
#
#------------------------------------------------------------------------
class BookOptions(ReportOptions):

    """
    Defines options and provides handling interface.
    """

    def __init__(self, name, dbase):
        ReportOptions.__init__(self, name, dbase)

        # Options specific for this report
        self.options_dict = {
            'bookname'    : '',
        }
        self.options_help = {
            'bookname'    : ("=name",_("Name of the book. MANDATORY"),
                            BookList('books.xml',dbase).get_book_names(),
                            False),
        }

#-------------------------------------------------------------------------
#
# Book creation dialog 
#
#-------------------------------------------------------------------------
class BookReportSelector(ManagedWindow.ManagedWindow):
    """
    Interface into a dialog setting up the book. 

    Allows the user to add/remove/reorder/setup items for the current book
    and to clear/load/save/edit whole books.
    """

    def __init__(self, dbstate, uistate):
        self.db = dbstate.db
        self.dbstate = dbstate
        self.uistate = uistate
        self.title = _('Book Report')
        self.file = "books.xml"

        ManagedWindow.ManagedWindow.__init__(self, uistate, [], self.__class__)

        self.xml = Glade(toplevel="top")
        window = self.xml.toplevel
        
        title_label = self.xml.get_object('title')
        self.set_window(window, title_label, self.title)
        window.show()
        self.xml.connect_signals({
            "on_add_clicked"        : self.on_add_clicked,
            "on_remove_clicked"     : self.on_remove_clicked,
            "on_up_clicked"         : self.on_up_clicked,
            "on_down_clicked"       : self.on_down_clicked,
            "on_setup_clicked"      : self.on_setup_clicked,
            "on_clear_clicked"      : self.on_clear_clicked,
            "on_save_clicked"       : self.on_save_clicked,
            "on_open_clicked"       : self.on_open_clicked,
            "on_edit_clicked"       : self.on_edit_clicked,
            "on_book_ok_clicked"    : self.on_book_ok_clicked,
            "destroy_passed_object" : self.close,

        # Insert dummy handlers for second top level in the glade file
            "on_booklist_ok_clicked"    : lambda _:None,
            "on_booklist_delete_clicked": lambda _:None,
            "on_booklist_cancel_clicked": lambda _:None,
            "on_booklist_ok_clicked"    : lambda _:None,
            "on_booklist_ok_clicked"    : lambda _:None,
            })

        self.avail_tree = self.xml.get_object("avail_tree")
        self.book_tree = self.xml.get_object("book_tree")
        self.avail_tree.connect('button-press-event', self.avail_button_press)
        self.book_tree.connect('button-press-event', self.book_button_press)

        self.name_entry = self.xml.get_object("name_entry")
        self.name_entry.set_text(_('New Book'))

        avail_label = self.xml.get_object('avail_label')
        avail_label.set_text("<b>%s</b>" % _("_Available items"))
        avail_label.set_use_markup(True)
        avail_label.set_use_underline(True)
        book_label = self.xml.get_object('book_label')
        book_label.set_text("<b>%s</b>" % _("Current _book"))
        book_label.set_use_underline(True)
        book_label.set_use_markup(True)

        avail_titles = [ (_('Name'), 0, 230),
                      (_('Type'), 1, 80 ),
                      (  '' ,    -1, 0  ) ]
        
        book_titles = [ (_('Item name'), -1, 230),
                      (_('Type'),      -1, 80 ),
                      (  '',           -1, 0  ),
                      (_('Subject'),   -1, 50 ) ]
        
        self.avail_nr_cols = len(avail_titles)
        self.book_nr_cols = len(book_titles)

        self.avail_model = ListModel.ListModel(self.avail_tree, avail_titles)
        self.book_model = ListModel.ListModel(self.book_tree, book_titles)
        self.draw_avail_list()

        self.book = Book()

    def build_menu_names(self, obj):
        return (_("Book selection list"), self.title)

    def draw_avail_list(self):
        """
        Draw the list with the selections available for the book.
        
        The selections are read from the book item registry.
        """
        pmgr = GuiPluginManager.get_instance()
        regbi = pmgr.get_reg_bookitems()
        if not regbi:
            return

        available_reports = []
        for pdata in regbi:
            category = _UNSUPPORTED
            if pdata.supported and pdata.category in book_categories:
                category = book_categories[pdata.category]
            available_reports.append([ pdata.name, category, pdata.id ])
        for data in sorted(available_reports):
            new_iter = self.avail_model.add(data)

        self.avail_model.connect_model()

        if new_iter:
            self.avail_model.selection.select_iter(new_iter)
            path = self.avail_model.model.get_path(new_iter)
            col = self.avail_tree.get_column(0)
            self.avail_tree.scroll_to_cell(path, col, 1, 1, 0.0)

    def open_book(self, book):
        """
        Open the book: set the current set of selections to this book's items.
        
        book:   the book object to load.
        """
        if book.get_dbname() == self.db.get_save_path():
            same_db = 1
        else:
            same_db = 0
            WarningDialog(_('Different database'), _(
                'This book was created with the references to database '
                '%s.\n\n This makes references to the central person '
                'saved in the book invalid.\n\n' 
                'Therefore, the central person for each item is being set ' 
                'to the active person of the currently opened database.' )
                % book.get_dbname() )
            
        self.book.clear()
        self.book_model.clear()
        for saved_item in book.get_item_list():
            name = saved_item.get_name()
            item = BookItem(self.db, name)
            item.option_class = saved_item.option_class

            # The option values were loaded magically by the book parser.
            # But they still need to be applied to the menu options.
            opt_dict = item.option_class.handler.options_dict
            menu = item.option_class.menu
            for optname in opt_dict:
                menu_option = menu.get_option_by_name(optname)
                if menu_option:
                    menu_option.set_value(opt_dict[optname])
            
            _initialize_options(item.option_class, self.dbstate, self.uistate)
            item.set_style_name(saved_item.get_style_name())
            self.book.append_item(item)
            
            data = [ item.get_translated_name(),
                     item.get_category(), item.get_name() ]
            
            data[2] = _get_subject(item.option_class, self.db)
            self.book_model.add(data)

    def on_add_clicked(self, obj):
        """
        Add an item to the current selections. 
        
        Use the selected available item to get the item's name in the registry.
        """
        store, the_iter = self.avail_model.get_selected()
        if not the_iter:
            return
        data = self.avail_model.get_data(the_iter, range(self.avail_nr_cols))
        item = BookItem(self.db, data[2])
        _initialize_options(item.option_class, self.dbstate, self.uistate)
        data[2] = _get_subject(item.option_class, self.db)
        self.book_model.add(data)
        self.book.append_item(item)

    def on_remove_clicked(self, obj):
        """
        Remove the item from the current list of selections.
        """
        store, the_iter = self.book_model.get_selected()
        if not the_iter:
            return
        row = self.book_model.get_selected_row()
        self.book.pop_item(row)
        self.book_model.remove(the_iter)

    def on_clear_clicked(self, obj):
        """
        Clear the whole current book.
        """
        self.book_model.clear()
        self.book.clear()

    def on_up_clicked(self, obj):
        """
        Move the currently selected item one row up in the selection list.
        """
        row = self.book_model.get_selected_row()
        if not row or row == -1:
            return
        store, the_iter = self.book_model.get_selected()
        data = self.book_model.get_data(the_iter, range(self.book_nr_cols))
        self.book_model.remove(the_iter)
        self.book_model.insert(row-1, data, None, 1)
        item = self.book.pop_item(row)
        self.book.insert_item(row-1, item)

    def on_down_clicked(self, obj):
        """
        Move the currently selected item one row down in the selection list.
        """
        row = self.book_model.get_selected_row()
        if row + 1 >= self.book_model.count or row == -1:
            return
        store, the_iter = self.book_model.get_selected()
        data = self.book_model.get_data(the_iter, range(self.book_nr_cols))
        self.book_model.remove(the_iter)
        self.book_model.insert(row+1, data, None, 1)
        item = self.book.pop_item(row)
        self.book.insert_item(row+1, item)

    def on_setup_clicked(self, obj):
        """
        Configure currently selected item.
        """
        store, the_iter = self.book_model.get_selected()
        if not the_iter:
            WarningDialog(_('No selected book item'),
                          _('Please select a book item to configure.')
                         )
            return
        data = self.book_model.get_data(the_iter, range(self.book_nr_cols))
        row = self.book_model.get_selected_row()
        item = self.book.get_item(row)
        option_class = item.option_class
        option_class.handler.set_default_stylesheet_name(item.get_style_name())
        item.is_from_saved_book = bool(self.book.get_name())
        item_dialog = BookItemDialog(self.dbstate, self.uistate,
                                     item, self.track)

        while True:
            response = item_dialog.window.run()
            if response == gtk.RESPONSE_OK:
                # dialog will be closed by connect, now continue work while
                # rest of dialog is unresponsive, release when finished
                style = option_class.handler.get_default_stylesheet_name()
                item.set_style_name(style)
                subject = _get_subject(option_class, self.db)
                self.book_model.model.set_value(the_iter, 2, subject)
                self.book.set_item(row, item)
                item_dialog.close()
                break
            elif response == gtk.RESPONSE_CANCEL:
                item_dialog.close()
                break
            elif response == gtk.RESPONSE_DELETE_EVENT:
                #just stop, in ManagedWindow, delete-event is already coupled to
                #correct action.
                break

    def book_button_press(self, obj, event):
        """
        Double-click on the current book selection is the same as setup.
        Right click evokes the context menu. 
        """
        if event.type == gtk.gdk._2BUTTON_PRESS and event.button == 1:
            self.on_setup_clicked(obj)
        elif gui.utils.is_right_click(event):
            self.build_book_context_menu(event)

    def avail_button_press(self, obj, event):
        """
        Double-click on the available selection is the same as add.
        Right click evokes the context menu. 
        """
        if event.type == gtk.gdk._2BUTTON_PRESS and event.button == 1:
            self.on_add_clicked(obj)
        elif gui.utils.is_right_click(event):
            self.build_avail_context_menu(event)

    def build_book_context_menu(self, event):
        """Builds the menu with item-centered and book-centered options."""
        
        store, the_iter = self.book_model.get_selected()
        if the_iter:
            sensitivity = 1 
        else:
            sensitivity = 0 
        entries = [
            (gtk.STOCK_GO_UP, self.on_up_clicked, sensitivity),
            (gtk.STOCK_GO_DOWN, self.on_down_clicked, sensitivity),
            (_("Setup"), self.on_setup_clicked, sensitivity),
            (gtk.STOCK_REMOVE, self.on_remove_clicked, sensitivity),
            (None,None,0),
            (gtk.STOCK_CLEAR, self.on_clear_clicked, 1),
            (gtk.STOCK_SAVE, self.on_save_clicked, 1),
            (gtk.STOCK_OPEN, self.on_open_clicked, 1),
            (_("Edit"), self.on_edit_clicked,1 ),
        ]

        menu = gtk.Menu()
        menu.set_title(_('Book Menu'))
        for stock_id, callback, sensitivity in entries:
            item = gtk.ImageMenuItem(stock_id)
            if callback:
                item.connect("activate", callback)
            item.set_sensitive(sensitivity)
            item.show()
            menu.append(item)
        menu.popup(None, None, None, event.button, event.time)

    def build_avail_context_menu(self, event):
        """Builds the menu with the single Add option."""
        
        store, the_iter = self.avail_model.get_selected()
        if the_iter:
            sensitivity = 1 
        else:
            sensitivity = 0 
        entries = [
            (gtk.STOCK_ADD, self.on_add_clicked, sensitivity),
        ]

        menu = gtk.Menu()
        menu.set_title(_('Available Items Menu'))
        for stock_id, callback, sensitivity in entries:
            item = gtk.ImageMenuItem(stock_id)
            if callback:
                item.connect("activate", callback)
            item.set_sensitive(sensitivity)
            item.show()
            menu.append(item)
        menu.popup(None, None, None, event.button, event.time)

    def on_book_ok_clicked(self, obj): 
        """
        Run final BookReportDialog with the current book. 
        """
        if self.book.item_list:
            BookReportDialog(self.dbstate, self.uistate,
                             self.book, BookOptions)
        else:
            WarningDialog(_('No items'), _('This book has no items.'))
            return
        self.close()

    def on_save_clicked(self, obj):
        """
        Save the current book in the xml booklist file. 
        """
        self.book_list = BookList(self.file, self.db)
        name = unicode(self.name_entry.get_text())
        if not name:
            WarningDialog(_('No book name'), _(
                'You are about to save away a book with no name.\n\n'
                'Please give it a name before saving it away.')
                )
            return
        if name in self.book_list.get_book_names():
            from QuestionDialog import QuestionDialog2
            q = QuestionDialog2(
                _('Book name already exists'),
                _('You are about to save away a '
                  'book with a name which already exists.'
                ),
                _('Proceed'),
                _('Cancel'))
            if q.run():
                self.book.set_name(name)
            else:
                return
        else:
            self.book.set_name(name)
        self.book.set_dbname(self.db.get_save_path())
        self.book_list.set_book(name, self.book)
        self.book_list.save()

    def on_open_clicked(self, obj):
        """
        Run the BookListDisplay dialog to present the choice of books to open. 
        """
        self.book_list = BookList(self.file, self.db)
        booklistdisplay = BookListDisplay(self.book_list, 1, 0)
        booklistdisplay.top.destroy()
        book = booklistdisplay.selection
        if book:
            self.open_book(book)
            self.name_entry.set_text(book.get_name())
            self.book.set_name(book.get_name())

    def on_edit_clicked(self, obj):
        """
        Run the BookListDisplay dialog to present the choice of books to delete. 
        """
        self.book_list = BookList(self.file, self.db)
        booklistdisplay = BookListDisplay(self.book_list, 0, 1)
        booklistdisplay.top.destroy()

#------------------------------------------------------------------------
#
# Book Item Options dialog
#
#------------------------------------------------------------------------
class BookItemDialog(ReportDialog):

    """
    This class overrides the interface methods common for different reports
    in a way specific for this report. This is a book item dialog.
    """

    def __init__(self, dbstate, uistate, item, track=[]):
        self.category = CATEGORY_BOOK
        self.database = dbstate.db
        self.item = item
        name = item.get_name()
        translated_name = item.get_translated_name()
        self.option_class = item.option_class
        self.is_from_saved_book = item.is_from_saved_book
        ReportDialog.__init__(self, dbstate, uistate,
                              self.option_class, name, translated_name, track)

    def on_ok_clicked(self, obj):
        """The user is satisfied with the dialog choices. Parse all options
        and close the window."""

        # Preparation
        self.parse_style_frame()
        self.parse_user_options()
        self.item.set_style_name(self.style_menu.get_value()[0])
        self.options.handler.save_options()
        
    def setup_target_frame(self):
        """Target frame is not used."""
        pass
    
    def parse_target_frame(self):
        """Target frame is not used."""
        return 1

    def init_options(self, option_class):
        try:
            if (issubclass(option_class, object) or     # New-style class
                isinstance(option_class, ClassType)):   # Old-style class
                self.options = option_class(self.raw_name, self.db)
        except TypeError:
            self.options = option_class
        if not self.is_from_saved_book:
            self.options.load_previous_values()

    def add_user_options(self):
        """
        Generic method to add user options to the gui.
        """
        if not hasattr(self.options, "menu"):
            return
        menu = self.options.menu
        options_dict = self.options.options_dict
        for category in menu.get_categories():
            for name in menu.get_option_names(category):
                option = menu.get_option(category, name)
                
                # override option default with xml-saved value:
                if name in options_dict:
                    option.set_value(options_dict[name])
                    
                widget, label = make_gui_option(option, self.dbstate,
                                                self.uistate, self.track,
                                                self.is_from_saved_book)
                if widget is not None:
                    if label:
                        self.add_frame_option(category,
                                              option.get_label(), 
                                              widget)
                    else:
                        self.add_frame_option(category, "", widget)
    
#-------------------------------------------------------------------------
#
# _BookFormatComboBox
#
#-------------------------------------------------------------------------
class _BookFormatComboBox(gtk.ComboBox):

    def __init__(self, active):

        gtk.ComboBox.__init__(self)
        
        pmgr = GuiPluginManager.get_instance()
        self.__bookdoc_plugins = []
        for plugin in pmgr.get_docgen_plugins():
            if plugin.get_text_support() and plugin.get_draw_support():
                self.__bookdoc_plugins.append(plugin)
        
        self.store = gtk.ListStore(gobject.TYPE_STRING)
        self.set_model(self.store)
        cell = gtk.CellRendererText()
        self.pack_start(cell, True)
        self.add_attribute(cell, 'text', 0)

        index = 0
        active_index = 0
        for plugin in self.__bookdoc_plugins:
            name = plugin.get_name()
            self.store.append(row=[name])
            if plugin.get_extension() == active:
                active_index = index
            index += 1
        self.set_active(active_index)

    def get_active_plugin(self):
        """
        Get the plugin represented by the currently active selection.
        """
        return self.__bookdoc_plugins[self.get_active()]

#------------------------------------------------------------------------
#
# The final dialog - paper, format, target, etc. 
#
#------------------------------------------------------------------------
class BookReportDialog(DocReportDialog):
    """
    A usual Report.Dialog subclass. 
    
    Create a dialog selecting target, format, and paper/HTML options.
    """

    def __init__(self, dbstate, uistate, book, options):
        self.format_menu = None
        self.options = options
        self.is_from_saved_book = False
        self.page_html_added = False
        self.book = book
        DocReportDialog.__init__(self, dbstate, uistate, options,
                                  'book', _("Book Report"))
        self.options.options_dict['bookname'] = self.book.name
        self.database = dbstate.db

        response = self.window.run()
        if response == gtk.RESPONSE_OK:
            try:
                self.make_report()
            except (IOError,OSError),msg:
                ErrorDialog(str(msg))
        self.close()

    def setup_style_frame(self): pass
    def setup_other_frames(self): pass
    def parse_style_frame(self): pass

    def get_title(self):
        return _("Book Report")

    def get_header(self, name):
        return _("Gramps Book")

    def make_doc_menu(self, active=None):
        """Build a menu of document types that are appropriate for
        this text report.  This menu will be generated based upon
        whether the document requires table support, etc."""
        self.format_menu = _BookFormatComboBox( active )

    def make_document(self):
        """Create a document of the type requested by the user."""
        user = gui.user.User()
        self.rptlist = []
        selected_style = StyleSheet()

        pstyle = self.paper_frame.get_paper_style()
        self.doc = self.format(None, pstyle)

        for item in self.book.get_item_list():
            item.option_class.set_document(self.doc)
            report_class = item.get_write_item()
            obj = write_book_item(self.database, report_class, 
                                  item.option_class, user)
            self.rptlist.append(obj)
            append_styles(selected_style, item)

        self.doc.set_style_sheet(selected_style)
        self.doc.open(self.target_path)

    def make_report(self):
        """The actual book report. Start it out, then go through the item list 
        and call each item's write_book_item method."""

        self.doc.init()
        newpage = 0
        for rpt in self.rptlist:
            if newpage:
                self.doc.page_break()
            newpage = 1
            if rpt:
                rpt.begin_report()
                rpt.write_report()
        self.doc.close()
        
        if self.open_with_app.get_active():
            gui.utils.open_file_with_default_application(self.target_path)

    def init_options(self, option_class):
        try:
            if (issubclass(option_class, object) or     # New-style class
                isinstance(option_class, ClassType)):   # Old-style class
                self.options = option_class(self.raw_name, self.db)
        except TypeError:
            self.options = option_class
        if not self.is_from_saved_book:
            self.options.load_previous_values()

#------------------------------------------------------------------------
#
# Function to write books from command line
#
#------------------------------------------------------------------------
def cl_report(database, name, category, options_str_dict):

    clr = CommandLineReport(database, name, category,
                            BookOptions, options_str_dict)

    # Exit here if show option was given
    if clr.show:
        return
    
    if 'bookname' not in clr.options_dict or not clr.options_dict['bookname']:
        print _("Please specify a book name")
        return

    book_list = BookList('books.xml', database)
    book_name = clr.options_dict['bookname']
    if book_name:
        if book_name not in book_list.get_book_names():
            print _("No such book '%s'") % book_name
            return
        book = book_list.get_book(book_name)
    else:
        print _("Please specify a book name")
        return

    # write report
    doc = clr.format(None,
                     PaperStyle(clr.paper, clr.orien, clr.marginl,
                                clr.marginr, clr.margint, clr.marginb))
    user = cli.user.User()
    rptlist = []
    selected_style = StyleSheet()
    for item in book.get_item_list():

        # The option values were loaded magically by the book parser.
        # But they still need to be applied to the menu options.
        opt_dict = item.option_class.options_dict
        menu = item.option_class.menu
        for optname in opt_dict:
            menu_option = menu.get_option_by_name(optname)
            if menu_option:
                menu_option.set_value(opt_dict[optname])

        item.option_class.set_document(doc)
        report_class = item.get_write_item()
        obj = write_book_item(database,
                              report_class, item.option_class, user)
        if obj:
            append_styles(selected_style, item)
            rptlist.append(obj)

    doc.set_style_sheet(selected_style)
    doc.open(clr.option_class.get_output())
    doc.init()
    newpage = 0
    for rpt in rptlist:
        if newpage:
            doc.page_break()
        newpage = 1
        rpt.begin_report()
        rpt.write_report()
    doc.close()

def append_styles(selected_style, item):
    """
    Append the styles for a book item to the stylesheet.
    """
    # Set up default style
    default_style = StyleSheet()
    make_default_style = item.option_class.make_default_style
    make_default_style(default_style)

    # Read all style sheets available for this item
    style_file = item.option_class.handler.get_stylesheet_savefile()
    style_list = StyleSheetList(style_file, default_style)

    # Get the selected stylesheet
    style_name = item.get_style_name()
    style_sheet = style_list.get_style_sheet(style_name)

    for this_style_name in style_sheet.get_paragraph_style_names():
        selected_style.add_paragraph_style(
            this_style_name,style_sheet.get_paragraph_style(this_style_name))

    for this_style_name in style_sheet.get_draw_style_names():
        selected_style.add_draw_style(
            this_style_name,style_sheet.get_draw_style(this_style_name))

    for this_style_name in style_sheet.get_table_style_names():
        selected_style.add_table_style(
            this_style_name,style_sheet.get_table_style(this_style_name))

    for this_style_name in style_sheet.get_cell_style_names():
        selected_style.add_cell_style(
            this_style_name,style_sheet.get_cell_style(this_style_name))

    return selected_style

#------------------------------------------------------------------------
#
# Generic task function for book report
#
#------------------------------------------------------------------------
def write_book_item(database, report_class, options, user):
    """Write the report using options set.
    All user dialog has already been handled and the output file opened."""
    try:
        return report_class(database, options, user)
    except Errors.ReportError, msg:
        (m1, m2) = msg.messages()
        ErrorDialog(m1, m2)
    except Errors.FilterError, msg:
        (m1, m2) = msg.messages()
        ErrorDialog(m1, m2)
    except:
        log.error("Failed to write book item.", exc_info=True)
    return None
