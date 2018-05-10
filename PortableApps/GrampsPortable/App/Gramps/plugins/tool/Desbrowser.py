#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2007  Donald N. Allingham
# Copyright (C) 2008       Brian G. Matherly
# Copyright (C) 2010       Jakim Friant
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

"""Tools/Analysis and Exploration/Interactive Descendant Browser"""

#------------------------------------------------------------------------
#
# GTK/GNOME modules
#
#------------------------------------------------------------------------
import gtk

#------------------------------------------------------------------------
#
# GRAMPS modules
#
#------------------------------------------------------------------------
import const
from gen.display.name import displayer as name_displayer
from gui.plug import tool
import GrampsDisplay
import ManagedWindow
from gen.ggettext import sgettext as _
from glade import Glade
from gui.editors import EditPerson

#------------------------------------------------------------------------
#
# Constants
#
#------------------------------------------------------------------------
WIKI_HELP_PAGE = '%s_-_Tools' % const.URL_MANUAL_PAGE
WIKI_HELP_SEC = _('manual|Interactive_Descendant_Browser...')

class DesBrowse(tool.ActivePersonTool, ManagedWindow.ManagedWindow):

    def __init__(self, dbstate, uistate, options_class, name, callback=None):

        tool.ActivePersonTool.__init__(self, dbstate, uistate, options_class,
                                       name)
        if self.fail:
            return

        self.dbstate = dbstate
        active_handle = uistate.get_active('Person')
        self.active = dbstate.db.get_person_from_handle(active_handle)
        self.callback = callback
        self.active_name = _("Descendant Browser: %s") % (
                                name_displayer.display(self.active)
                                )

        ManagedWindow.ManagedWindow.__init__(self, uistate, [], self)

        self.glade = Glade()
        self.glade.connect_signals({
            "destroy_passed_object" : self.close,
            "on_help_clicked"       : self.on_help_clicked,
            "on_delete_event"       : self.close,
            })

        window = self.glade.toplevel
        self.set_window(window,self.glade.get_object('title'),
                        self.active_name)
        
        self.tree = self.glade.get_object("tree1")
        col = gtk.TreeViewColumn('',gtk.CellRendererText(),text=0)
        self.tree.append_column(col)
        self.tree.set_rules_hint(True)
        self.tree.set_headers_visible(False)
        self.tree.connect('event',self.button_press_event)
        self.make_new_model()

        self.show()

    def build_menu_names(self, obj):
        return (self.active_name,_("Descendant Browser tool"))

    def make_new_model(self):
        self.model = gtk.TreeStore(str, object)
        self.tree.set_model(self.model)
        self.add_to_tree(None, None, self.active.get_handle())
        self.tree.expand_all()

    def on_help_clicked(self, obj):
        """Display the relevant portion of GRAMPS manual"""
        GrampsDisplay.help(webpage=WIKI_HELP_PAGE, section=WIKI_HELP_SEC)

    def add_to_tree(self, parent_id, sib_id, person_handle):
        item_id = self.model.insert_after(parent_id, sib_id)
        person = self.db.get_person_from_handle(person_handle)
        
        self.model.set(item_id, 0, name_displayer.display(person))
        self.model.set(item_id, 1, person_handle)
        prev_id = None
        for family_handle in person.get_family_handle_list():
            family = self.db.get_family_from_handle(family_handle)
            for child_ref in family.get_child_ref_list():
                prev_id = self.add_to_tree(item_id, prev_id, child_ref.ref)
        return item_id
    
    def button_press_event(self, obj,event):
        if event.type == gtk.gdk._2BUTTON_PRESS and event.button == 1:
            store, node = self.tree.get_selection().get_selected()
            if node:
                person_handle = store.get_value(node, 1)
                person = self.db.get_person_from_handle(person_handle)
                EditPerson(self.dbstate, self.uistate, self.track, person,
                           self.this_callback)

    def this_callback(self, obj):
        self.callback()
        self.make_new_model()

#------------------------------------------------------------------------
#
# 
#
#------------------------------------------------------------------------
class DesBrowseOptions(tool.ToolOptions):
    """
    Defines options and provides handling interface.
    """

    def __init__(self, name,person_id=None):
        tool.ToolOptions.__init__(self, name,person_id)
