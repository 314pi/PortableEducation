#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2010  Doug Blank <doug.blank@gmail.com>
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
# python modules
#
#-------------------------------------------------------------------------
import gtk
import re

#-------------------------------------------------------------------------
#
# gramps modules
#
#-------------------------------------------------------------------------
from gen.ggettext import gettext as _
import ManagedWindow
import GrampsDisplay
from glade import Glade
from Simple import SimpleAccess

WEB, EVENT, FAMILY, MEDIA, NOTE, PERSON, PLACE, REPOSITORY, SOURCE = range(9)
OBJECT_MAP = {
    EVENT: "Event",
    FAMILY: "Family",
    MEDIA: "Media",
    NOTE: "Note",
    PERSON: "Person",
    PLACE: "Place", 
    REPOSITORY: "Repository",
    SOURCE: "Source",
    }

#-------------------------------------------------------------------------
#
# EditUrl class
#
#-------------------------------------------------------------------------
class EditLink(ManagedWindow.ManagedWindow):

    def __init__(self, dbstate, uistate, track, url, callback):
        self.url = url
        self.dbstate = dbstate
        self.simple_access = SimpleAccess(self.dbstate.db)
        self.callback = callback

        ManagedWindow.ManagedWindow.__init__(self, uistate, track, url)

        self._local_init()
        self._connect_signals()
        self.show()

    def _local_init(self):
        self.top = Glade()
        self.set_window(self.top.toplevel,
                        self.top.get_object("title"),
                        _('Link Editor'))
        self.table = self.top.get_object('table27')
        self.uri_list = gtk.combo_box_new_text()
        for text in [_("Internet Address"),       # 0 this order range above
                     _("Event"),      # 1 
                     _("Family"),     # 2 
                     _("Media"),      # 3
                     _("Note"),       # 4
                     _("Person"),     # 5
                     _("Place"),      # 6
                     _("Repository"), # 7
                     _("Source"),     # 8
                     ]:
            self.uri_list.append_text(text)
        self.table.attach(self.uri_list, 1, 2, 0, 1)
        self.pick_item = self.top.get_object('button1')
        #self.edit_item = self.top.get_object('button2')
        self.selected = self.top.get_object('label1')
        self.url_link = self.top.get_object('entry1')
        self.uri_list.connect("changed", self._on_type_changed)
        self.pick_item.connect("clicked", self._on_pick_one)
        #self.edit_item.connect("clicked", self._on_edit_one)
        if self.url.startswith("gramps://"):
            object_class, prop, value = self.url[9:].split("/", 2)
            if object_class == "Event":
                self.uri_list.set_active(EVENT)
            elif object_class == "Family":
                self.uri_list.set_active(FAMILY)
            elif object_class == "Media":
                self.uri_list.set_active(MEDIA)
            elif object_class == "Note":
                self.uri_list.set_active(NOTE)
            elif object_class == "Person":
                self.uri_list.set_active(PERSON)
            elif object_class == "Place":
                self.uri_list.set_active(PLACE)
            elif object_class == "Repository":
                self.uri_list.set_active(REPOSITORY)
            elif object_class == "Source":
                self.uri_list.set_active(SOURCE)
            # set texts:
            self.selected.set_text(self.display_link(
                    object_class, prop, value))
            self.url_link.set_text("gramps://%s/%s/%s" % 
                                   (object_class, prop, value))
        else:
            self.uri_list.set_active(WEB)
            self.url_link.set_text(self.url)
        self.url_link.connect("changed", self.update_ui)

    def update_ui(self, widget):
        url = self.url_link.get_text()
        # text needs to have 3 or more chars://and at least one char
        match = re.match("\w{3,}://\w+", url)
        if match:
            self.ok_button.set_sensitive(True)
        else:
            self.ok_button.set_sensitive(False)

    def display_link(self, obj_class, prop, value):
        return self.simple_access.display(obj_class, prop, value)

    def _on_edit_one(self, widget):
        # Not used due to modal dialog in StyledTextEditor
        from gui.editors import EditObject
        uri = self.url_link.get_text()
        if uri.startswith("gramps://"):
            obj_class, prop, value = uri[9:].split("/", 2)
            EditObject(self.dbstate, 
                       self.uistate, 
                       self.track, 
                       obj_class, prop, value)
        
    def _on_pick_one(self, widget):
        from gui.selectors import SelectorFactory
        object_class = OBJECT_MAP[self.uri_list.get_active()]
        Select = SelectorFactory(object_class)
        uri = self.url_link.get_text()
        default = None
        if uri.startswith("gramps://"):
            obj_class, prop, value = uri[9:].split("/", 2)
            if object_class == obj_class:
                if prop == "handle":
                    default = value
                elif (prop == "gramps_id" and 
                      object_class in self.dbstate.db.get_table_names()):
                    person = self.dbstate.db.get_table_metadata(object_class)["gramps_id_func"](value)
                    if person:
                        default = person.handle
        d = Select(self.dbstate, self.uistate, self.track, 
                   default=default)

        result = d.run()
        if result:
            prop = "handle"
            value = result.handle
            self.selected.set_text(self.display_link(
                    object_class, prop, value))
            self.url_link.set_text("gramps://%s/%s/%s" % 
                                   (object_class, prop, value))

    def _on_type_changed(self, widget):
        self.selected.set_text("")
        if self.uri_list.get_active() == WEB:
            self.url_link.set_sensitive(True)
            self.pick_item.set_sensitive(False)
        else:
            self.url_link.set_sensitive(False)
            self.pick_item.set_sensitive(True)

    def get_uri(self):
        if self.uri_list.get_active() == WEB:
            return self.url_link.get_text()
        else:
            return self.url_link.get_text()
            
    def _connect_signals(self):
        self.define_cancel_button(self.top.get_object('button125'))
        self.ok_button = self.top.get_object('button124')
        self.define_ok_button(self.ok_button, self.save)
        self.define_help_button(self.top.get_object('button130'))
        self.update_ui(self.url_link)
        
    def build_menu_names(self, obj):
        etitle =_('Link Editor')
        return (etitle, etitle)

    def define_ok_button(self,button,function):
        button.connect('clicked',function)

    def save(self, widget):
        self.callback(self.get_uri())
        self.close()

    def define_cancel_button(self,button):
        button.connect('clicked',self.close)

    def define_help_button(self, button, webpage='', section=''):
        button.connect('clicked', lambda x: GrampsDisplay.help(webpage,
                                                               section))
