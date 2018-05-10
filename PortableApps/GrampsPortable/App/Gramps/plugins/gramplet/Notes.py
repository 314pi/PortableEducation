# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2011 Nick Hall
# Copyright (C) 2011       Tim G L Lyons
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
#

from gen.plug import Gramplet
from gui.widgets.styledtexteditor import StyledTextEditor
from gui.widgets import SimpleButton
from gen.lib import StyledText
from gen.ggettext import gettext as _
import gtk

class Notes(Gramplet):
    """
    Displays the notes for an object.
    """
    def init(self):
        self.gui.WIDGET = self.build_gui()
        self.gui.get_container_widget().remove(self.gui.textview)
        self.gui.get_container_widget().add_with_viewport(self.gui.WIDGET)
        self.gui.WIDGET.show()

    def build_gui(self):
        """
        Build the GUI interface.
        """
        top = gtk.VBox(False)
        
        hbox = gtk.HBox()
        self.left = SimpleButton(gtk.STOCK_GO_BACK, self.left_clicked)
        self.left.set_sensitive(False)
        hbox.pack_start(self.left, False, False)
        self.right = SimpleButton(gtk.STOCK_GO_FORWARD, self.right_clicked)
        self.right.set_sensitive(False)
        hbox.pack_start(self.right, False, False)
        self.page = gtk.Label()
        hbox.pack_end(self.page, False, False, 10)
        
        scrolledwindow = gtk.ScrolledWindow()
        scrolledwindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.texteditor = StyledTextEditor()
        self.texteditor.set_editable(False)
        self.texteditor.set_wrap_mode(gtk.WRAP_WORD)
        scrolledwindow.add(self.texteditor)

        top.pack_start(hbox, False, False)
        top.pack_start(scrolledwindow, True, True)
        top.show_all()
        return top
        
    def get_notes(self, obj):
        """
        Get the note list for the current object.
        """
        self.left.set_sensitive(False)
        self.right.set_sensitive(False)
        self.texteditor.set_text(StyledText())
        self.note_list = obj.get_note_list()
        self.page.set_text('')
        if len(self.note_list) > 0:
            self.set_has_data(True)
            if len(self.note_list) > 1:
                self.right.set_sensitive(True)
            self.current = 0
            self.display_note()
        else:
            self.set_has_data(False)

    def clear_text(self):
        self.left.set_sensitive(False)
        self.right.set_sensitive(False)
        self.texteditor.set_text(StyledText())
        self.page.set_text('')
        self.current = 0

    def display_note(self):
        """
        Display the current note.
        """
        note_handle = self.note_list[self.current]
        note = self.dbstate.db.get_note_from_handle(note_handle)
        self.texteditor.set_text(note.get_styledtext())
        self.page.set_text(_('%d of %d') % (self.current + 1,
                                            len(self.note_list)))

    def left_clicked(self, button):
        """
        Display the previous note.
        """
        if self.current > 0:
            self.current -= 1
            self.right.set_sensitive(True)
            if self.current == 0:
                self.left.set_sensitive(False)
            self.display_note()

    def right_clicked(self, button):
        """
        Display the next note.
        """
        if self.current < len(self.note_list) - 1:
            self.current += 1
            self.left.set_sensitive(True)
            if self.current == len(self.note_list) - 1:
                self.right.set_sensitive(False)
            self.display_note()

    def get_has_data(self, obj):
        """
        Return True if the gramplet has data, else return False.
        """
        if obj is None: 
            return False
        if obj.get_note_list():
            return True
        return False

class PersonNotes(Notes):
    """
    Displays the notes for a person.
    """
    def db_changed(self):
        self.dbstate.db.connect('person-update', self.update)

    def active_changed(self, handle):
        self.update()

    def update_has_data(self):
        active_handle = self.get_active('Person')
        active = self.dbstate.db.get_person_from_handle(active_handle)
        self.set_has_data(self.get_has_data(active))
    
    def main(self):
        active_handle = self.get_active('Person')
        active = self.dbstate.db.get_person_from_handle(active_handle)
        if active:
            self.get_notes(active)
        else:
            self.clear_text()
            self.set_has_data(False)

class EventNotes(Notes):
    """
    Displays the notes for an event.
    """
    def db_changed(self):
        self.dbstate.db.connect('event-update', self.update)
        self.connect_signal('Event', self.update)

    def update_has_data(self):
        active_handle = self.get_active('Event')
        active = self.dbstate.db.get_event_from_handle(active_handle)
        self.set_has_data(self.get_has_data(active))
    
    def main(self):
        active_handle = self.get_active('Event')
        active = self.dbstate.db.get_event_from_handle(active_handle)
        if active:
            self.get_notes(active)
        else:
            self.clear_text()
            self.set_has_data(False)

class FamilyNotes(Notes):
    """
    Displays the notes for a family.
    """
    def db_changed(self):
        self.dbstate.db.connect('family-update', self.update)
        self.connect_signal('Family', self.update)

    def update_has_data(self):
        active_handle = self.get_active('Family')
        active = self.dbstate.db.get_family_from_handle(active_handle)
        self.set_has_data(self.get_has_data(active))
    
    def main(self):
        active_handle = self.get_active('Family')
        active = self.dbstate.db.get_family_from_handle(active_handle)
        if active:
            self.get_notes(active)
        else:
            self.clear_text()
            self.set_has_data(False)

class PlaceNotes(Notes):
    """
    Displays the notes for a place.
    """
    def db_changed(self):
        self.dbstate.db.connect('place-update', self.update)
        self.connect_signal('Place', self.update)

    def update_has_data(self):
        active_handle = self.get_active('Place')
        active = self.dbstate.db.get_place_from_handle(active_handle)
        self.set_has_data(self.get_has_data(active))
    
    def main(self):
        active_handle = self.get_active('Place')
        active = self.dbstate.db.get_place_from_handle(active_handle)
        if active:
            self.get_notes(active)
        else:
            self.clear_text()
            self.set_has_data(False)

class SourceNotes(Notes):
    """
    Displays the notes for a source.
    """
    def db_changed(self):
        self.dbstate.db.connect('source-update', self.update)
        self.connect_signal('Source', self.update)

    def update_has_data(self):
        active_handle = self.get_active('Source')
        active = self.dbstate.db.get_source_from_handle(active_handle)
        self.set_has_data(self.get_has_data(active))
    
    def main(self):
        active_handle = self.get_active('Source')
        active = self.dbstate.db.get_source_from_handle(active_handle)
        if active:
            self.get_notes(active)
        else:
            self.clear_text()
            self.set_has_data(False)

class CitationNotes(Notes):
    """
    Displays the notes for a Citation.
    """
    def db_changed(self):
        self.dbstate.db.connect('citation-update', self.update)
        self.connect_signal('Citation', self.update)

    def update_has_data(self):
        active_handle = self.get_active('Citation')
        active = self.dbstate.db.get_citation_from_handle(active_handle)
        self.set_has_data(self.get_has_data(active))
    
    def main(self):
        active_handle = self.get_active('Citation')
        active = self.dbstate.db.get_citation_from_handle(active_handle)
        if active:
            self.get_notes(active)
        else:
            self.clear_text()
            self.set_has_data(False)

class RepositoryNotes(Notes):
    """
    Displays the notes for a repository.
    """
    def db_changed(self):
        self.dbstate.db.connect('repository-update', self.update)
        self.connect_signal('Repository', self.update)

    def update_has_data(self):
        active_handle = self.get_active('Repository')
        active = self.dbstate.db.get_repository_from_handle(active_handle)
        self.set_has_data(self.get_has_data(active))
    
    def main(self):
        active_handle = self.get_active('Repository')
        active = self.dbstate.db.get_repository_from_handle(active_handle)
        if active:
            self.get_notes(active)
        else:
            self.clear_text()
            self.set_has_data(False)

class MediaNotes(Notes):
    """
    Displays the notes for a media object.
    """
    def db_changed(self):
        self.dbstate.db.connect('media-update', self.update)
        self.connect_signal('Media', self.update)

    def update_has_data(self):
        active_handle = self.get_active('Media')
        active = self.dbstate.db.get_object_from_handle(active_handle)
        self.set_has_data(self.get_has_data(active))
    
    def main(self):
        active_handle = self.get_active('Media')
        active = self.dbstate.db.get_object_from_handle(active_handle)
        if active:
            self.get_notes(active)
        else:
            self.clear_text()
            self.set_has_data(False)

