#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2007  Donald N. Allingham
# Copyright (C) 2008       Raphael Ackermann
# Copyright (C) 2010       Benny Malengier
# Copyright (C) 2010       Nick Hall
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

#-------------------------------------------------------------------------
#
# Standard python modules
#
#-------------------------------------------------------------------------
import random
from gen.ggettext import gettext as _
import os
from xml.sax.saxutils import escape

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
import config
import const
import DateHandler
from gen.display.name import displayer as _nd
from gen.display.name import NameDisplayError
import Utils
import gen.lib
from gen.lib import Name, Surname, NameOriginType
import ManagedWindow
from gui.widgets import MarkupLabel, BasicLabel
from QuestionDialog import ErrorDialog, QuestionDialog2, OkDialog
from glade import Glade
from gen.plug.utils import available_updates
from gui.plug import PluginWindows
from Errors import WindowActiveError
from Spell import HAVE_GTKSPELL

#-------------------------------------------------------------------------
#
# Constants 
#
#-------------------------------------------------------------------------

_surname_styles = [
    _("Father's surname"), 
    _("None"), 
    _("Combination of mother's and father's surname"), 
    _("Icelandic style"), 
    ]

# column numbers for the 'name format' model
COL_NUM  = 0
COL_NAME = 1
COL_FMT  = 2
COL_EXPL = 3

#-------------------------------------------------------------------------
#
#
#
#-------------------------------------------------------------------------
class DisplayNameEditor(ManagedWindow.ManagedWindow):
    def __init__(self, uistate, dbstate, track, dialog):
        # Assumes that there are two methods: dialog.name_changed_check(), 
        # and dialog._build_custom_name_ui() 
        ManagedWindow.ManagedWindow.__init__(self, uistate, [], DisplayNameEditor)
        self.dialog = dialog
        self.dbstate = dbstate
        self.set_window(
            gtk.Dialog(_('Display Name Editor'), 
                       flags=gtk.DIALOG_NO_SEPARATOR, 
                       buttons=(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE)), 
            None, _('Display Name Editor'), None)
        table = self.dialog._build_custom_name_ui()
        label = gtk.Label(_("""The following keywords are replaced with the appropriate name parts:
<tt>  
  <b>Given</b>      - given name (first name) <b>Surname</b>      - surnames (with prefix and connectors)
  <b>Title</b>      - title (Dr., Mrs.)       <b>Suffix</b>       - suffix (Jr., Sr.)
  <b>Call</b>       - call name               <b>Nickname</b>     - nick name
  <b>Initials</b>   - first letters of Given  <b>Common</b>       - nick name, otherwise first of Given
  <b>Primary, Primary[pre] or [sur] or [con]</b>- full primary surname, prefix, surname only, connector   
  <b>Patronymic, or [pre] or [sur] or [con]</b> - full pa/matronymic surname, prefix, surname only, connector 
  <b>Familynick</b> - family nick name        <b>Prefix</b>       - all prefixes (von, de)  
  <b>Rest</b>       - non primary surnames    <b>Notpatronymic</b>- all surnames, except pa/matronymic &amp; primary
  <b>Rawsurnames</b>- surnames (no prefixes and connectors)

</tt>
UPPERCASE keyword forces uppercase. Extra parentheses, commas are removed. Other text appears literally.

<b>Example</b>: 'Dr. Edwin Jose von der Smith and Weston Wilson Sr ("Ed") - Underhills'
     <i>Edwin Jose</i> is given name, <i>von der</i> is the prefix, <i>Smith</i> and <i>Weston</i> surnames, 
     <i>and</i> a connector, <i>Wilson</i> patronymic surname, <i>Dr.</i> title, <i>Sr</i> suffix, <i>Ed</i> nick name, 
     <i>Underhills</i> family nick name, <i>Jose</i> callname.
"""))
        label.set_use_markup(True)
        self.window.vbox.pack_start(label, expand=False)        
        self.window.vbox.pack_start(table)
        self.window.set_default_size(600, 550)
        self.window.connect('response', self.close)
        self.show()
    def close(self, *obj):
        self.dialog.name_changed_check()
        ManagedWindow.ManagedWindow.close(self, *obj)
        
    def build_menu_names(self, obj):
        return (_(" Name Editor"), _("Preferences"))


#-------------------------------------------------------------------------
#
# ConfigureDialog
#
#-------------------------------------------------------------------------

class ConfigureDialog(ManagedWindow.ManagedWindow):
    """
    Base class for configuration dialogs. They provide a Notebook, to which 
    pages are added with configuration options, and a Cancel and Save button.
    On save, a config file on which the dialog works, is saved to disk, and
    a callback called.
    """
    def __init__(self, uistate, dbstate, configure_page_funcs, configobj,
                 configmanager,
                 dialogtitle=_("Preferences"), on_close=None):
        """
        Set up a configuration dialog
        :param uistate: a DisplayState instance
        :param dbstate: a DbState instance
        :param configure_page_funcs: a list of function that return a tuple
            (str, gtk.Widget). The string is used as label for the 
            configuration page, and the widget as the content of the 
            configuration page
        :param configobj: the unique object that is configured, it must be 
            identifiable (id(configobj)). If the configure dialog of the 
            configobj is already open, a Errors.WindowActiveError will be
            raised. Grab this exception in the calling method
        :param configmanager: a configmanager object. Several convenience
            methods are present in ConfigureDialog to set up widgets that 
            write changes directly via this configmanager.
        :param dialogtitle: the title of the configuration dialog
        :param on_close: callback that is called on close
        """
        self.dbstate = dbstate
        self.__config = configmanager
        ManagedWindow.ManagedWindow.__init__(self, uistate, [], configobj)
        self.set_window(
            gtk.Dialog(dialogtitle, flags=gtk.DIALOG_NO_SEPARATOR, 
                       buttons=(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE)), 
                       None, dialogtitle, None)
        self.panel = gtk.Notebook()
        self.panel.set_scrollable(True)
        self.window.vbox.add(self.panel)
        self.__on_close = on_close
        self.window.connect('response', self.done)
        
        self.__setup_pages(configure_page_funcs)
        
        self.window.show_all()
        self.show()
    
    def __setup_pages(self, configure_page_funcs):
        """
        This method builds the notebookpages in the panel
        """
        if callable(configure_page_funcs):
            pages = configure_page_funcs()
        else:
            pages = configure_page_funcs
        for func in pages:
            labeltitle, widget = func(self)
            self.panel.append_page(widget, MarkupLabel(labeltitle))

    def done(self, obj, value):
        if self.__on_close:
            self.__on_close()
        self.close()

    def update_int_entry(self, obj, constant):
        """
        :param obj: an object with get_text method that should contain an
            integer
        :param constant: the config setting to which the integer value must be 
            saved
        """
        try:
            self.__config.set(constant, int(obj.get_text()))
        except:
            print "WARNING: ignoring invalid value for '%s'" % constant

    def update_entry(self, obj, constant):
        """
        :param obj: an object with get_text method 
        :param constant: the config setting to which the text value must be 
            saved
        """
        self.__config.set(constant, unicode(obj.get_text()))

    def update_markup_entry(self, obj, constant):
        """
        :param obj: an object with get_text method 
        :param constant: the config setting to which the text value must be 
            saved
        """
        try:
            obj.get_text() % 'test_markup'
        except TypeError:
            print("WARNING: ignoring invalid value for '%s'" % constant)
            ErrorDialog(_("Invalid or incomplete format definition."), 
            obj.get_text())
            obj.set_text('<b>%s</b>')
        except ValueError:
            print("WARNING: ignoring invalid value for '%s'" % constant)
            ErrorDialog(_("Invalid or incomplete format definition."),
            obj.get_text())
            obj.set_text('<b>%s</b>')
        
        self.__config.set(constant, unicode(obj.get_text()))

    def update_color(self, obj, constant, color_hex_label):
        color = obj.get_color()
        hexval = "#%02x%02x%02x" % (color.red/256, 
                                    color.green/256, 
                                    color.blue/256)
        color_hex_label.set_text(hexval)
        self.__config.set(constant, hexval)

    def update_checkbox(self, obj, constant, config=None):
        if not config:
            config = self.__config
        config.set(constant, obj.get_active())

    def update_radiobox(self, obj, constant):
        self.__config.set(constant, obj.get_active())

    def update_combo(self, obj, constant):
        """
        :param obj: the ComboBox object
        :param constant: the config setting to which the value must be saved
        """
        self.__config.set(constant, obj.get_active())

    def update_slider(self, obj, constant):
        """
        :param obj: the HScale object
        :param constant: the config setting to which the value must be saved
        """
        self.__config.set(constant, int(obj.get_value()))

    def add_checkbox(self, table, label, index, constant, start=1, stop=9,
                     config=None, extra_callback=None):
        if not config:
            config = self.__config
        checkbox = gtk.CheckButton(label)
        checkbox.set_active(config.get(constant))
        checkbox.connect('toggled', self.update_checkbox, constant, config)
        if extra_callback:
            checkbox.connect('toggled', extra_callback)
        table.attach(checkbox, start, stop, index, index+1, yoptions=0)
        return checkbox

    def add_radiobox(self, table, label, index, constant, group, column,
                     config=None):
        if not config:
            config = self.__config
        radiobox = gtk.RadioButton(group,label)
        if config.get(constant) == True:
            radiobox.set_active(True)
        radiobox.connect('toggled', self.update_radiobox, constant)
        table.attach(radiobox, column, column+1, index, index+1, yoptions=0)
        return radiobox

    def add_text(self, table, label, index, config=None):
        if not config:
            config = self.__config
        text = gtk.Label()
        text.set_line_wrap(True)
        text.set_alignment(0.,0.)
        text.set_text(label)
        table.attach(text, 1, 9, index, index+1, yoptions=0)

    def add_path_box(self, table, label, index, entry, path, callback_label, 
                     callback_sel, config=None):
        """ Add an entry to give in path and a select button to open a 
            dialog. 
            Changing entry calls callback_label
            Clicking open button call callback_sel
        """
        if not config:
            config = self.__config
        lwidget = BasicLabel("%s: " %label)
        hbox = gtk.HBox()
        if path:
            entry.set_text(path)
        entry.connect('changed', callback_label)
        btn = gtk.Button()
        btn.connect('clicked', callback_sel)
        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_OPEN, gtk.ICON_SIZE_BUTTON)
        image.show()
        btn.add(image)
        hbox.pack_start(entry, expand=True, fill=True)
        hbox.pack_start(btn, expand=False, fill=False)
        table.attach(lwidget, 1, 2, index, index+1, yoptions=0, 
                     xoptions=gtk.FILL)
        table.attach(hbox, 2, 3, index, index+1, yoptions=0)

    def add_entry(self, table, label, index, constant, callback=None,
                  config=None, col_attach=0):
        if not config:
            config = self.__config
        if not callback:
            callback = self.update_entry
        lwidget = BasicLabel("%s: " % label)
        entry = gtk.Entry()
        entry.set_text(config.get(constant))
        entry.connect('changed', callback, constant)
        table.attach(lwidget, col_attach, col_attach+1, index, index+1, yoptions=0, 
                     xoptions=gtk.FILL)
        table.attach(entry, col_attach+1, col_attach+2, index, index+1, yoptions=0)

    def add_pos_int_entry(self, table, label, index, constant, callback=None,
                          config=None, col_attach=1, helptext=''):
        """ entry field for positive integers
        """
        if not config:
            config = self.__config
        lwidget = BasicLabel("%s: " % label)
        entry = gtk.Entry()
        entry.set_text(str(config.get(constant)))
        entry.set_tooltip_markup(helptext)
        if callback:
            entry.connect('changed', callback, constant)
        table.attach(lwidget, col_attach, col_attach+1, index, index+1,
                     yoptions=0, xoptions=gtk.FILL)
        table.attach(entry, col_attach+1, col_attach+2, index, index+1, 
                     yoptions=0)

    def add_color(self, table, label, index, constant, config=None):
        if not config:
            config = self.__config
        lwidget = BasicLabel("%s: " % label)
        hexval = config.get(constant)
        color = gtk.gdk.color_parse(hexval)
        entry = gtk.ColorButton(color=color)
        color_hex_label = BasicLabel(hexval)
        entry.connect('color-set', self.update_color, constant, color_hex_label)
        table.attach(lwidget, 0, 1, index, index+1, yoptions=0, 
                     xoptions=gtk.FILL)
        table.attach(entry, 1, 2, index, index+1, yoptions=0, xoptions=0)
        table.attach(color_hex_label, 2, 3, index, index+1, yoptions=0)
        return entry

    def add_combo(self, table, label, index, constant, opts, callback=None,
                  config=None):
        """
        A drop-down list allowing selection from a number of fixed options.
        :param opts: A list of options.  Each option is a tuple containing an
        integer code and a textual description.
        """
        if not config:
            config = self.__config
        if not callback:
            callback = self.update_combo
        lwidget = BasicLabel("%s: " % label)
        store = gtk.ListStore(int, str)
        for item in opts:
            store.append(item)
        combo = gtk.ComboBox(store)
        cell = gtk.CellRendererText()
        combo.pack_start(cell, True)
        combo.add_attribute(cell, 'text', 1)  
        combo.set_active(config.get(constant))
        combo.connect('changed', callback, constant)
        table.attach(lwidget, 1, 2, index, index+1, yoptions=0, 
                     xoptions=gtk.FILL)
        table.attach(combo, 2, 3, index, index+1, yoptions=0)
        return combo

    def add_slider(self, table, label, index, constant, range, callback=None,
                   config=None):
        """
        A slider allowing the selection of an integer within a specified range.
        :param range: A tuple containing the minimum and maximum allowed values.
        """
        if not config:
            config = self.__config
        if not callback:
            callback = self.update_slider
        lwidget = BasicLabel("%s: " % label)
        adj = gtk.Adjustment(config.get(constant), range[0], range[1], 1, 0, 0)
        slider = gtk.HScale(adj)
        slider.set_update_policy(gtk.UPDATE_DISCONTINUOUS)
        slider.set_digits(0)
        slider.set_value_pos(gtk.POS_BOTTOM)
        slider.connect('value-changed', callback, constant)
        table.attach(lwidget, 1, 2, index, index+1, yoptions=0, 
                     xoptions=gtk.FILL)
        table.attach(slider, 2, 3, index, index+1, yoptions=0)
        return slider

#-------------------------------------------------------------------------
#
# GrampsPreferences
#
#-------------------------------------------------------------------------
class GrampsPreferences(ConfigureDialog):

    def __init__(self, uistate, dbstate):
        page_funcs = (
            self.add_behavior_panel,
            self.add_famtree_panel,
            self.add_formats_panel,
            self.add_text_panel,
            self.add_prefix_panel,
            self.add_date_panel,
            self.add_advanced_panel,
            self.add_researcher_panel,
            )
        ConfigureDialog.__init__(self, uistate, dbstate, page_funcs, 
                                 GrampsPreferences, config,
                                 on_close=Utils.update_constants)

    def add_researcher_panel(self, configdialog):
        table = gtk.Table(3, 8)
        table.set_border_width(12)
        table.set_col_spacings(6)
        table.set_row_spacings(6)
        self.add_entry(table, _('Name'), 0, 'researcher.researcher-name')
        self.add_entry(table, _('Address'), 1, 'researcher.researcher-addr')
        self.add_entry(table, _('Locality'), 2, 'researcher.researcher-locality')
        self.add_entry(table, _('City'), 3, 'researcher.researcher-city')
        self.add_entry(table, _('State/County'), 4, 'researcher.researcher-state')
        self.add_entry(table, _('Country'), 5, 'researcher.researcher-country')
        self.add_entry(table, _('ZIP/Postal Code'), 6, 'researcher.researcher-postal')
        self.add_entry(table, _('Phone'), 7, 'researcher.researcher-phone')
        self.add_entry(table, _('Email'), 8, 'researcher.researcher-email')
        return _('Researcher'), table

    def add_prefix_panel(self, configdialog):
        """
        Add the ID prefix tab to the preferences.
        """
        table = gtk.Table(3, 8)
        table.set_border_width(12)
        table.set_col_spacings(6)
        table.set_row_spacings(6)
        self.add_entry(table, _('Person'), 0, 'preferences.iprefix', 
                       self.update_idformat_entry)
        self.add_entry(table, _('Family'), 1, 'preferences.fprefix',
                       self.update_idformat_entry)
        self.add_entry(table, _('Place'), 2, 'preferences.pprefix',
                       self.update_idformat_entry)
        self.add_entry(table, _('Source'), 3, 'preferences.sprefix',
                       self.update_idformat_entry)
        self.add_entry(table, _('Citation'), 4, 'preferences.cprefix',
                       self.update_idformat_entry)
        self.add_entry(table, _('Media Object'), 5, 'preferences.oprefix',
                       self.update_idformat_entry)
        self.add_entry(table, _('Event'), 6, 'preferences.eprefix',
                       self.update_idformat_entry)
        self.add_entry(table, _('Repository'), 7, 'preferences.rprefix',
                       self.update_idformat_entry)
        self.add_entry(table, _('Note'), 8, 'preferences.nprefix',
                       self.update_idformat_entry)
        return _('ID Formats'), table

    def add_advanced_panel(self, configdialog):
        table = gtk.Table(4, 8)
        table.set_border_width(12)
        table.set_col_spacings(6)
        table.set_row_spacings(6)
        self.add_checkbox(
            table, _('Suppress warning when adding parents to a child.'), 
            0, 'preferences.family-warn')
        
        self.add_checkbox(
            table, _('Suppress warning when cancelling with changed data.'), 
            1, 'interface.dont-ask')
        
        self.add_checkbox(
            table, _('Suppress warning about missing researcher when'
                     ' exporting to GEDCOM.'), 
            2, 'behavior.owner-warn')

        self.add_checkbox(
            table, _('Show plugin status dialog on plugin load error.'), 
            3, 'behavior.pop-plugin-status')
        
        return _('Warnings'), table

    def _build_name_format_model(self, active):
        """
        Create a common model for ComboBox and TreeView
        """
        name_format_model = gtk.ListStore(gobject.TYPE_INT, 
                                          gobject.TYPE_STRING, 
                                          gobject.TYPE_STRING, 
                                          gobject.TYPE_STRING)
        index = 0
        the_index = 0
        for num, name, fmt_str, act in _nd.get_name_format():
            translation = fmt_str
            for key in Utils.get_keywords():
                if key in translation:
                    translation = translation.replace(key, Utils.get_translation_from_keyword(key))
            self.examplename.set_display_as(num)
            name_format_model.append(
                row=[num, translation, fmt_str, _nd.display_name(self.examplename)])
            if num == active: the_index = index
            index += 1
        return name_format_model, the_index

    def __new_name(self, obj):
        lyst = ["%s, %s %s (%s)" % (_("Surname"), _("Given"), _("Suffix"), 
                                    _("Common")),
                "%s, %s %s (%s)" % (_("Surname"), _("Given"), _("Suffix"), 
                                    _("Nickname")),
                "%s, %s %s (%s)" % (_("Surname"), _("Name|Common"), _("Suffix"), 
                                    _("Nickname")),
                "%s, %s %s" % (_("Surname"), _("Name|Common"), _("Suffix")),
                "%s, %s %s (%s)" % (_("SURNAME"), _("Given"), _("Suffix"), 
                                    _("Call")),
                "%s, %s (%s)" % (_("Surname"), _("Given"), _("Name|Common")),
                "%s, %s (%s)" % (_("Surname"), _("Name|Common"), _("Nickname")),
                "%s %s" % (_("Given"), _("Surname")),
                "%s %s, %s" % (_("Given"), _("Surname"), _("Suffix")),
                "%s %s %s" % (_("Given"), _("NotPatronymic"), _("Patronymic")),
                "%s, %s %s (%s)" % (_("SURNAME"), _("Given"), _("Suffix"), 
                                    _("Common")),
                "%s, %s (%s)" % (_("SURNAME"), _("Given"), _("Name|Common")),
                "%s, %s (%s)" % (_("SURNAME"), _("Given"), _("Nickname")),
                "%s %s" % (_("Given"), _("SURNAME")),
                "%s %s, %s" % (_("Given"), _("SURNAME"), _("Suffix")),
                "%s /%s/" % (_("Given"), _("SURNAME")),
                "%s %s, %s" % (_("Given"), _("Rawsurnames"), _("Suffix")),
                ]
        #repeat above list, but not translated.
        fmtlyst = ["%s, %s %s (%s)" % (("Surname"), ("Given"), ("Suffix"), 
                                    ("Common")),
                "%s, %s %s (%s)" % (("Surname"), ("Given"), ("Suffix"), 
                                    ("Nickname")),
                "%s, %s %s (%s)" % (("Surname"), ("Name|Common"), ("Suffix"), 
                                    ("Nickname")),
                "%s, %s %s" % (("Surname"), ("Name|Common"), ("Suffix")),
                "%s, %s %s (%s)" % (("SURNAME"), ("Given"), ("Suffix"), 
                                    ("Call")),
                "%s, %s (%s)" % (("Surname"), ("Given"), ("Name|Common")),
                "%s, %s (%s)" % (("Surname"), ("Name|Common"), ("Nickname")),
                "%s %s" % (("Given"), ("Surname")),
                "%s %s, %s" % (("Given"), ("Surname"), ("Suffix")),
                "%s %s %s" % (("Given"), ("NotPatronymic"), ("Patronymic")),
                "%s, %s %s (%s)" % (("SURNAME"), ("Given"), ("Suffix"), 
                                    ("Common")),
                "%s, %s (%s)" % (("SURNAME"), ("Given"), ("Name|Common")),
                "%s, %s (%s)" % (("SURNAME"), ("Given"), ("Nickname")),
                "%s %s" % (("Given"), ("SURNAME")),
                "%s %s, %s" % (("Given"), ("SURNAME"), ("Suffix")),
                "%s /%s/" % (("Given"), ("SURNAME")),
                "%s %s, %s" % (("Given"), ("Rawsurnames"), ("Suffix")),
                   ]
        rand = int(random.random() * len(lyst))
        f = lyst[rand]
        fmt = fmtlyst[rand]
        i = _nd.add_name_format(f, fmt)
        node = self.fmt_model.append(row=[i, f, fmt, 
                                   _nd.format_str(self.examplename, fmt)])
        path = self.fmt_model.get_path(node)
        self.format_list.set_cursor(path, 
                                    focus_column=self.name_column, 
                                    start_editing=True)
        self.edit_button.set_sensitive(False)
        self.remove_button.set_sensitive(False)
        self.insert_button.set_sensitive(False)

    def __edit_name(self, obj):
        store, node = self.format_list.get_selection().get_selected()
        path = self.fmt_model.get_path(node)
        self.edit_button.set_sensitive(False)
        self.remove_button.set_sensitive(False)
        self.insert_button.set_sensitive(False)
        self.format_list.set_cursor(path, 
                                    focus_column=self.name_column, 
                                    start_editing=True)

    def __check_for_name(self, name, oldnode):
        """
        Check to see if there is another name the same as name
        in the format list. Don't compare with self (oldnode).
        """
        model = self.fmt_obox.get_model()
        iter = model.get_iter_first()
        while iter is not None:
            othernum = model.get_value(iter, COL_NUM)
            oldnum = model.get_value(oldnode, COL_NUM)
            if othernum == oldnum: 
                pass# skip comparison with self
            else:
                othername = model.get_value(iter, COL_NAME)
                if othername == name:
                    return True
            iter = model.iter_next(iter)
        return False

    def __start_name_editing(self, dummy_renderer, dummy_editable, dummy_path):
        """
        Method called at the start of editing a name format.
        """
        self.format_list.set_tooltip_text(_("Enter to save, Esc to cancel "
                                            "editing"))

    def __cancel_change(self, dummy_renderer):
        """
        Break off the editing of a name format.
        """
        self.format_list.set_tooltip_text('')
        num = self.selected_fmt[COL_NUM]
        if any(fmt[COL_NUM] == num for fmt in self.dbstate.db.name_formats):
            return
        else: # editing a new format not yet in db, cleanup is needed
            self.fmt_model.remove(self.iter)
            _nd.del_name_format(num)
            self.insert_button.set_sensitive(True)

    def __change_name(self, text, path, new_text):
        """
        Called when a name format changed and needs to be stored in the db.
        """
        self.format_list.set_tooltip_text('')
        if len(new_text) > 0 and text != new_text:
            # build a pattern from translated pattern:
            pattern = new_text
            if (len(new_text) > 2 and 
                new_text[0] == '"' and 
                new_text[-1] == '"'):
                pass
            else:
                for key in Utils.get_translations():
                    if key in pattern:
                        pattern = pattern.replace(key, Utils.get_keyword_from_translation(key))
            # now build up a proper translation:
            translation = pattern
            if (len(new_text) > 2 and 
                new_text[0] == '"' and 
                new_text[-1] == '"'):
                pass
            else:
                for key in Utils.get_keywords():
                    if key in translation:
                        translation = translation.replace(key, Utils.get_translation_from_keyword(key))
            num, name, fmt = self.selected_fmt[COL_NUM:COL_EXPL]
            node = self.fmt_model.get_iter(path)
            oldname = self.fmt_model.get_value(node, COL_NAME)
            # check to see if this pattern already exists
            if self.__check_for_name(translation, node):
                ErrorDialog(_("This format exists already."), 
                                           translation)
                self.edit_button.emit('clicked')
                return
            # else, change the name
            self.edit_button.set_sensitive(True)
            self.remove_button.set_sensitive(True)
            self.insert_button.set_sensitive(True)
            exmpl = _nd.format_str(self.examplename, pattern)
            self.fmt_model.set(self.iter, COL_NAME, translation, 
                               COL_FMT, pattern, 
                               COL_EXPL, exmpl)
            self.selected_fmt = (num, translation, pattern, exmpl)
            _nd.edit_name_format(num, translation, pattern)
            self.dbstate.db.name_formats = _nd.get_name_format(only_custom=True, 
                                                               only_active=False)

    def __format_change(self, obj):
        try:
            t = (_nd.format_str(self.name, escape(obj.get_text())))
            self.valid = True
        except NameDisplayError:
            t = _("Invalid or incomplete format definition.")
            self.valid = False
        self.fmt_model.set(self.iter, COL_EXPL, t)

    def _build_custom_name_ui(self):
        """
        UI to manage the custom name formats
        """

        table = gtk.Table(2, 3)
        table.set_border_width(6)
        table.set_col_spacings(6)
        table.set_row_spacings(6)

        # make a treeview for listing all the name formats
        format_tree = gtk.TreeView(self.fmt_model)
        name_renderer = gtk.CellRendererText()
        name_column = gtk.TreeViewColumn(_('Format'), 
                                         name_renderer, 
                                         text=COL_NAME)
        name_renderer.set_property('editable', False)
        name_renderer.connect('editing-started', self.__start_name_editing)
        name_renderer.connect('edited', self.__change_name)
        name_renderer.connect('editing-canceled', self.__cancel_change)
        self.name_renderer = name_renderer
        format_tree.append_column(name_column)
        example_renderer = gtk.CellRendererText()
        example_column = gtk.TreeViewColumn(_('Example'), 
                                            example_renderer, 
                                            text=COL_EXPL)
        format_tree.append_column(example_column)
        format_tree.get_selection().connect('changed', 
                                            self.cb_format_tree_select)
        format_tree.set_rules_hint(True)

        # ... and put it into a scrolled win
        format_sw = gtk.ScrolledWindow()
        format_sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        format_sw.add(format_tree)
        format_sw.set_shadow_type(gtk.SHADOW_IN)
        table.attach(format_sw, 0, 3, 0, 1, yoptions=gtk.FILL|gtk.EXPAND)

        # to hold the values of the selected row of the tree and the iter
        self.selected_fmt = ()
        self.iter = None

        self.insert_button = gtk.Button(stock=gtk.STOCK_ADD)
        self.insert_button.connect('clicked', self.__new_name)

        self.edit_button = gtk.Button(stock=gtk.STOCK_EDIT)
        self.edit_button.connect('clicked', self.__edit_name)
        self.edit_button.set_sensitive(False)

        self.remove_button = gtk.Button(stock=gtk.STOCK_REMOVE)
        self.remove_button.connect('clicked', self.cb_del_fmt_str)
        self.remove_button.set_sensitive(False)
        
        table.attach(self.insert_button, 0, 1, 1, 2, yoptions=0)
        table.attach(self.remove_button, 1, 2, 1, 2, yoptions=0)
        table.attach(self.edit_button,   2, 3, 1, 2, yoptions=0)
        self.format_list = format_tree
        self.name_column = name_column
        return table

    def name_changed_check(self):
        """
        Method to check for a name change. Called by Name Edit Dialog.
        """
        obj = self.fmt_obox
        the_list = obj.get_model()
        the_iter = obj.get_active_iter()
        format = the_list.get_value(the_iter, COL_FMT)
        if format != self.old_format:
            # Yes a change; call the callback
            self.cb_name_changed(obj)

    def cb_name_changed(self, obj):
        """
        Preset name format ComboBox callback
        """
        the_list = obj.get_model()
        the_iter = obj.get_active_iter()
        new_idx = the_list.get_value(the_iter, COL_NUM)
        config.set('preferences.name-format', new_idx)
        _nd.set_default_format(new_idx)
        self.uistate.emit('nameformat-changed')

    def cb_pa_sur_changed(self,*args):
        """
        checkbox patronymic as surname changed, propagate to namedisplayer
        """
        _nd.change_pa_sur()
        self.uistate.emit('nameformat-changed')

    def cb_format_tree_select(self, tree_selection):
        """
        Name format editor TreeView callback
        
        Remember the values of the selected row (self.selected_fmt, self.iter)
        and set the Remove and Edit button sensitivity
        
        """
        model, self.iter = tree_selection.get_selected()
        if self.iter is None:
            tree_selection.select_path(0)
            model, self.iter = tree_selection.get_selected()
        self.selected_fmt = model.get(self.iter, 0, 1, 2)
        idx = self.selected_fmt[COL_NUM] < 0
        self.remove_button.set_sensitive(idx)
        self.edit_button.set_sensitive(idx)
        self.name_renderer.set_property('editable', idx)

    def cb_del_fmt_str(self, obj):
        """
        Name format editor Remove button callback
        """
        num = self.selected_fmt[COL_NUM]

        if _nd.get_default_format() == num:
            self.fmt_obox.set_active(0)

        self.fmt_model.remove(self.iter)
        _nd.set_format_inactive(num)
        self.dbstate.db.name_formats = _nd.get_name_format(only_custom=True, 
                                                           only_active=False)

    def add_formats_panel(self, configdialog):
        row = 0
        table = gtk.Table(4, 4)
        table.set_border_width(12)
        table.set_col_spacings(6)
        table.set_row_spacings(6)

        # Display name:
        self.examplename = Name()
        examplesurname = Surname()
        examplesurnamesecond = Surname()
        examplesurnamepat = Surname()
        self.examplename.set_title('Dr.')
        self.examplename.set_first_name('Edwin Jose')
        examplesurname.set_prefix('von der')
        examplesurname.set_surname('Smith')
        examplesurname.set_connector('and')
        self.examplename.add_surname(examplesurname)
        examplesurnamesecond.set_surname('Weston')
        self.examplename.add_surname(examplesurnamesecond)
        examplesurnamepat.set_surname('Wilson')
        examplesurnamepat.set_origintype(
                                    NameOriginType(NameOriginType.PATRONYMIC))
        self.examplename.add_surname(examplesurnamepat)
        self.examplename.set_primary_surname(0)
        self.examplename.set_suffix('Sr')
        self.examplename.set_call_name('Jose')
        self.examplename.set_nick_name('Ed')
        self.examplename.set_family_nick_name('Underhills')
        # get the model for the combo and the treeview
        active = _nd.get_default_format()
        self.fmt_model, active = self._build_name_format_model(active)
        # set up the combo to choose the preset format
        self.fmt_obox = gtk.ComboBox()
        cell = gtk.CellRendererText()
        self.fmt_obox.pack_start(cell, True)
        self.fmt_obox.add_attribute(cell, 'text', 1)
        self.fmt_obox.set_model(self.fmt_model)
        # set the default value as active in the combo
        self.fmt_obox.set_active(active)
        self.fmt_obox.connect('changed', self.cb_name_changed)
        # label for the combo
        lwidget = BasicLabel("%s: " % _('Name format'))
        lwidget.set_use_underline(True)
        lwidget.set_mnemonic_widget(self.fmt_obox)
        hbox = gtk.HBox()
        btn = gtk.Button("%s..." % _('Edit') )
        btn.connect('clicked', self.cb_name_dialog)
        hbox.pack_start(self.fmt_obox, expand=True, fill=True)
        hbox.pack_start(btn, expand=False, fill=False)
        table.attach(lwidget, 0, 1, row, row+1, yoptions=0)
        table.attach(hbox,    1, 3, row, row+1, yoptions=0)
        row += 1
        
        # Pa/Matronymic surname handling
        self.add_checkbox(table, 
                          _("Consider single pa/matronymic as surname"), 
                          row, 'preferences.patronimic-surname', stop=3,
                          extra_callback=self.cb_pa_sur_changed)
        row += 1

        # Date format:
        obox = gtk.combo_box_new_text()
        formats = DateHandler.get_date_formats()
        map(obox.append_text, formats)
        active = config.get('preferences.date-format')
        if active >= len(formats):
            active = 0
        obox.set_active(active)
        obox.connect('changed', self.date_format_changed)
        lwidget = BasicLabel("%s: " % _('Date format'))
        table.attach(lwidget, 0, 1, row, row+1, yoptions=0)
        table.attach(obox, 1, 3, row, row+1, yoptions=0)
        row += 1
        
        # Calendar format on report:
        obox = gtk.combo_box_new_text()
        map(obox.append_text, gen.lib.Date.ui_calendar_names)
        active = config.get('preferences.calendar-format-report')
        if active >= len(formats):
            active = 0
        obox.set_active(active)
        obox.connect('changed', self.date_calendar_changed)
        lwidget = BasicLabel("%s: " % _('Calendar on reports'))
        table.attach(lwidget, 0, 1, row, row+1, yoptions=0)
        table.attach(obox, 1, 3, row, row+1, yoptions=0)
        row += 1

        # Surname guessing:
        obox = gtk.combo_box_new_text()
        formats = _surname_styles
        map(obox.append_text, formats)
        obox.set_active(config.get('behavior.surname-guessing'))
        obox.connect('changed', 
                     lambda obj: config.set('behavior.surname-guessing', 
                                            obj.get_active()))
        lwidget = BasicLabel("%s: " % _('Surname guessing'))
        table.attach(lwidget, 0, 1, row, row+1, yoptions=0)
        table.attach(obox, 1, 3, row, row+1, yoptions=0)
        row += 1
        
        # Default Family Relationship
        obox = gtk.combo_box_new_text()
        formats = gen.lib.FamilyRelType().get_standard_names()
        map(obox.append_text, formats)
        obox.set_active(config.get('preferences.family-relation-type'))
        obox.connect('changed', 
                     lambda obj: config.set('preferences.family-relation-type',
                                            obj.get_active()))
        lwidget = BasicLabel("%s: " % _('Default family relationship'))
        table.attach(lwidget, 0, 1, row, row+1, yoptions=0)
        table.attach(obox, 1, 3, row, row+1, yoptions=0)
        row += 1

        #height multiple surname table 
        self.add_pos_int_entry(table, 
                _('Height multiple surname box (pixels)'),
                row, 'interface.surname-box-height', self.update_surn_height,
                col_attach=0)
        row += 1

        # Status bar:
        obox = gtk.combo_box_new_text()
        formats = [_("Active person's name and ID"), 
                   _("Relationship to home person")]
        map(obox.append_text, formats)
        active = config.get('interface.statusbar')
        if active < 2:
            obox.set_active(0)
        else:
            obox.set_active(1)
        obox.connect('changed', 
                     lambda obj: config.set('interface.statusbar', 2*obj.get_active()))
        lwidget = BasicLabel("%s: " % _('Status bar'))
        table.attach(lwidget, 0, 1, row, row+1, yoptions=0)
        table.attach(obox,    1, 3, row, row+1, yoptions=0)
        row += 1

        # Text in sidebar:
        self.add_checkbox(table, 
                          _("Show text in sidebar buttons (requires restart)"), 
                          row, 'interface.sidebar-text', stop=3)
        row += 1
        return _('Display'), table

    def add_text_panel(self, configdialog):
        row = 0
        table = gtk.Table(6, 8)
        table.set_border_width(12)
        table.set_col_spacings(6)
        table.set_row_spacings(6)
        self.add_entry(table, _('Missing surname'), row, 
                       'preferences.no-surname-text')
        row += 1
        self.add_entry(table, _('Missing given name'), row, 
                       'preferences.no-given-text')
        row += 1
        self.add_entry(table, _('Missing record'), row, 
                       'preferences.no-record-text')
        row += 1
        self.add_entry(table, _('Private surname'), row, 
                       'preferences.private-surname-text')
        row += 1
        self.add_entry(table, _('Private given name'), row, 
                       'preferences.private-given-text')
        row += 1
        self.add_entry(table, _('Private record'), row, 
                       'preferences.private-record-text')
        row += 1
        return _('Text'), table

    def cb_name_dialog(self, obj):
        the_list = self.fmt_obox.get_model()
        the_iter = self.fmt_obox.get_active_iter()
        self.old_format = the_list.get_value(the_iter, COL_FMT)
        win = DisplayNameEditor(self.uistate, self.dbstate, self.track, self)

    def check_for_type_changed(self, obj):
        active = obj.get_active()
        if active == 0:  # update
            config.set('behavior.check-for-update-types', ["update"])
        elif active == 1:  # update
            config.set('behavior.check-for-update-types', ["new"])
        elif active == 2:  # update
            config.set('behavior.check-for-update-types', ["update", "new"])

    def toggle_hide_previous_addons(self, obj):
        active = obj.get_active()
        config.set('behavior.do-not-show-previously-seen-updates',  
                   bool(active))

    def check_for_updates_changed(self, obj):
        active = obj.get_active()
        config.set('behavior.check-for-updates', active)

    def date_format_changed(self, obj):
        config.set('preferences.date-format', obj.get_active())
        OkDialog(_('Change is not immediate'), 
                 _('Changing the data format will not take '
                   'effect until the next time Gramps is started.'))

    def date_calendar_changed(self, obj): 
        config.set('preferences.calendar-format-report', obj.get_active())
    
    def add_date_panel(self, configdialog):
        table = gtk.Table(2, 7)
        table.set_border_width(12)
        table.set_col_spacings(6)
        table.set_row_spacings(6)

        self.add_pos_int_entry(table, 
                _('Date about range'),
                0, 'behavior.date-about-range', self.update_int_entry)
        self.add_pos_int_entry(table, 
                _('Date after range'),
                1, 'behavior.date-after-range', self.update_int_entry)
        self.add_pos_int_entry(table, 
                _('Date before range'),
                2, 'behavior.date-before-range', self.update_int_entry)
        self.add_pos_int_entry(table, 
                _('Maximum age probably alive'),
                3, 'behavior.max-age-prob-alive', self.update_int_entry)
        self.add_pos_int_entry(table, 
                _('Maximum sibling age difference'),
                4, 'behavior.max-sib-age-diff', self.update_int_entry)
        self.add_pos_int_entry(table, 
                _('Minimum years between generations'),
                5, 'behavior.min-generation-years', self.update_int_entry)
        self.add_pos_int_entry(table, 
                _('Average years between generations'),
                6, 'behavior.avg-generation-gap', self.update_int_entry)
        self.add_pos_int_entry(table,
                _('Markup for invalid date format'), 
                7, 'preferences.invalid-date-format',
                self.update_markup_entry,
                helptext = _('Convenience markups are:\n'
                '<b>&lt;b&gt;Bold&lt;/b&gt;</b>\n'
                '<big>&lt;big&gt;Makes font relatively larger&lt;/big&gt;</big>\n'
                '<i>&lt;i&gt;Italic&lt;/i&gt;</i>\n'
                '<s>&lt;s&gt;Strikethrough&lt;/s&gt;</s>\n'
                '<sub>&lt;sub&gt;Subscript&lt;/sub&gt;</sub>\n'
                '<sup>&lt;sup&gt;Superscript&lt;/sup&gt;</sup>\n'
                '<small>&lt;small&gt;Makes font relatively smaller&lt;/small&gt;</small>\n'
                '<tt>&lt;tt&gt;Monospace font&lt;/tt&gt;</tt>\n'
                '<u>&lt;u&gt;Underline&lt;/u&gt;</u>\n\n'
                'For example: &lt;u&gt;&lt;b&gt;%s&lt;/b&gt;&lt;/u&gt;\n'
                'will display <u><b>Underlined bold date</b></u>\n')
                )

        return _('Dates'), table
        
    def add_behavior_panel(self, configdialog):
        table = gtk.Table(2, 8)
        table.set_border_width(12)
        table.set_col_spacings(6)
        table.set_row_spacings(6)

        self.add_checkbox(table, 
                _('Add default source on import'), 
                0, 'preferences.default-source')
        obj = self.add_checkbox(table, 
                _('Enable spelling checker'), 
                1, 'behavior.spellcheck')
        if not HAVE_GTKSPELL:
            obj.set_sensitive(False)
            obj.set_tooltip_text(_("Spelling checker is not installed"))
        self.add_checkbox(table, 
                _('Display Tip of the Day'), 
                2, 'behavior.use-tips')
        self.add_checkbox(table, 
                _('Remember last view displayed'), 
                3, 'preferences.use-last-view')
        self.add_pos_int_entry(table, 
                _('Max generations for relationships'),
                4, 'behavior.generation-depth', self.update_gen_depth)
        self.path_entry = gtk.Entry()
        self.add_path_box(table, 
                _('Base path for relative media paths'),
                5, self.path_entry, self.dbstate.db.get_mediapath(),
                self.set_mediapath, self.select_mediapath)

        # Check for updates:
        obox = gtk.combo_box_new_text()
        formats = [_("Never"), 
                   _("Once a month"), 
                   _("Once a week"), 
                   _("Once a day"), 
                   _("Always"), ]
        map(obox.append_text, formats)
        active = config.get('behavior.check-for-updates')
        obox.set_active(active)
        obox.connect('changed', self.check_for_updates_changed)
        lwidget = BasicLabel("%s: " % _('Check for updates'))
        table.attach(lwidget, 1, 2, 6, 7, yoptions=0)
        table.attach(obox,    2, 3, 6, 7, yoptions=0)

        self.whattype_box = gtk.combo_box_new_text()
        formats = [_("Updated addons only"), 
                   _("New addons only"), 
                   _("New and updated addons"),]
        map(self.whattype_box.append_text, formats)
        whattype = config.get('behavior.check-for-update-types')
        if "new" in whattype and "update" in whattype:
            self.whattype_box.set_active(2)
        elif "new" in whattype:
            self.whattype_box.set_active(1)
        elif "update" in whattype:
            self.whattype_box.set_active(0)
        self.whattype_box.connect('changed', self.check_for_type_changed)
        lwidget = BasicLabel("%s: " % _('What to check'))
        table.attach(lwidget, 1, 2, 7, 8, yoptions=0)
        table.attach(self.whattype_box, 2, 3, 7, 8, yoptions=0)

        self.add_entry(table, _('Where to check'), 8, 'behavior.addons-url', col_attach=1)

        checkbutton = gtk.CheckButton(
            _("Do not ask about previously notified addons"))
        checkbutton.set_active(config.get('behavior.do-not-show-previously-seen-updates'))
        checkbutton.connect("toggled", self.toggle_hide_previous_addons)

        table.attach(checkbutton, 1, 2, 9, 10, yoptions=0)
        button = gtk.Button(_("Check now"))
        button.connect("clicked", self.check_for_updates)
        table.attach(button, 3, 4, 9, 10, yoptions=0)

        return _('General'), table

    def check_for_updates(self, button):
        try:
            addon_update_list = available_updates()
        except:
            OkDialog(_("Checking Addons Failed"),
                     _("The addon repository appears to be unavailable. "
                       "Please try again later."),
                     self.window)
            return

        if len(addon_update_list) > 0:
            try:
                PluginWindows.UpdateAddons(self.uistate, [], addon_update_list)
            except WindowActiveError:
                pass
        else:
            check_types = config.get('behavior.check-for-update-types')
            OkDialog(_("There are no available addons of this type"),
                     _("Checked for '%s'") %
                     _("' and '").join([_(t) for t in check_types]),
                     self.window)

        # List of translated strings used here
        # Dead code for l10n
        _('new'), _('update')

        self.uistate.viewmanager.do_reg_plugins(self.dbstate, self.uistate)

    def add_famtree_panel(self, configdialog):
        table = gtk.Table(2, 2)
        table.set_border_width(12)
        table.set_col_spacings(6)
        table.set_row_spacings(6)


        self.dbpath_entry = gtk.Entry()
        self.add_path_box(table, 
                _('Family Tree Database path'),
                0, self.dbpath_entry, config.get('behavior.database-path'),
                self.set_dbpath, self.select_dbpath)

        #self.add_entry(table, 
        #        _('Family Tree Database path'), 
        #        0, 'behavior.database-path')
        self.add_checkbox(table, 
                _('Automatically load last family tree'), 
                1, 'behavior.autoload')
                
        return _('Family Tree'), table

    def set_mediapath(self, *obj):
        if self.path_entry.get_text().strip():
            self.dbstate.db.set_mediapath(self.path_entry.get_text())
        else:
            self.dbstate.db.set_mediapath(None)

    def select_mediapath(self, *obj):
        f = gtk.FileChooserDialog(
            _("Select media directory"),
            action=gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
            buttons=(gtk.STOCK_CANCEL,
                     gtk.RESPONSE_CANCEL,
                     gtk.STOCK_APPLY,
                     gtk.RESPONSE_OK))
        mpath = self.dbstate.db.get_mediapath()
        if not mpath:
            mpath = const.HOME_DIR
        f.set_current_folder(os.path.dirname(mpath))

        status = f.run()
        if status == gtk.RESPONSE_OK:
            val = Utils.get_unicode_path_from_file_chooser(f.get_filename())
            if val:
                self.path_entry.set_text(val)
        f.destroy()

    def set_dbpath(self, *obj):
        path = self.dbpath_entry.get_text().strip()
        config.set('behavior.database-path', path)

    def select_dbpath(self, *obj):
        f = gtk.FileChooserDialog(
            _("Select database directory"),
            action=gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
            buttons=(gtk.STOCK_CANCEL,
                     gtk.RESPONSE_CANCEL,
                     gtk.STOCK_APPLY,
                     gtk.RESPONSE_OK))
        dbpath = config.get('behavior.database-path')
        if not dbpath:
            dbpath = os.path.join(os.environ['HOME'], '.gramps','grampsdb')
        f.set_current_folder(os.path.dirname(dbpath))

        status = f.run()
        if status == gtk.RESPONSE_OK:
            val = Utils.get_unicode_path_from_file_chooser(f.get_filename())
            if val:
                self.dbpath_entry.set_text(val)
        f.destroy()

    def update_idformat_entry(self, obj, constant):
        config.set(constant, unicode(obj.get_text()))
        self.dbstate.db.set_prefixes(
            config.get('preferences.iprefix'),
            config.get('preferences.oprefix'),
            config.get('preferences.fprefix'),
            config.get('preferences.sprefix'),
            config.get('preferences.cprefix'),
            config.get('preferences.pprefix'),
            config.get('preferences.eprefix'),
            config.get('preferences.rprefix'),
            config.get('preferences.nprefix') )

    def update_gen_depth(self, obj, constant):
        ok = True
        if not obj.get_text():
            return
        try:
            intval = int(obj.get_text())
        except:
            intval = config.get(constant)
            ok = False
        if intval < 0 :
            intval = config.get(constant)
            ok = False
        if ok:
            config.set(constant, intval)
            #immediately use this value in displaystate.
            self.uistate.set_gendepth(intval)
        else:
            obj.set_text(str(intval))

    def update_surn_height(self, obj, constant):
        ok = True
        if not obj.get_text():
            return
        try:
            intval = int(obj.get_text())
        except:
            intval = config.get(constant)
            ok = False
        if intval < 0 :
            intval = config.get(constant)
            ok = False
        if ok:
            config.set(constant, intval)
        else:
            obj.set_text(str(intval))

    def build_menu_names(self, obj):
        return (_('Preferences'), None)

    # FIXME: is this needed?
    def _set_button(self, stock):
        button = gtk.Button()
        image = gtk.Image()
        image.set_from_stock(stock, gtk.ICON_SIZE_BUTTON)
        image.show()
        button.add(image)
        button.show()
        return button
