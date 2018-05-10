# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2011 Nick Hall
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

from gui.editors import EditEvent
from gen.lib import EventRoleType
from ListModel import ListModel, NOSORT
from gen.plug import Gramplet
from gui.dbguielement import DbGUIElement
from gen.ggettext import gettext as _
from gen.display.name import displayer as name_displayer
import DateHandler
import Errors
import Utils
import gtk

class Events(Gramplet, DbGUIElement):

    def __init__(self, gui, nav_group=0):
        Gramplet.__init__(self, gui, nav_group)
        DbGUIElement.__init__(self, self.dbstate.db)

    """
    Displays the events for a person or family.
    """
    def init(self):
        self.gui.WIDGET = self.build_gui()
        self.gui.get_container_widget().remove(self.gui.textview)
        self.gui.get_container_widget().add(self.gui.WIDGET)
        self.gui.WIDGET.show()

    def _connect_db_signals(self):
        """
        called on init of DbGUIElement, connect to db as required.
        """
        self.callman.register_callbacks({'event-update': self.changed})
        self.callman.connect_all(keys=['event'])

    def changed(self, handle):
        """
        Called when a registered event is updated.
        """
        self.update()

    def build_gui(self):
        """
        Build the GUI interface.
        """
        tip = _('Double-click on a row to edit the selected event.')
        self.set_tooltip(tip)
        top = gtk.TreeView()
        titles = [('', NOSORT, 50,),
                  (_('Type'), 1, 100),
                  (_('Main Participants'), 2, 200),
                  (_('Date'), 4, 100),
                  ('', 4, 100),
                  (_('Place'), 5, 400),
                  (_('Description'), 6, 150),
                  (_('Role'), 7, 100)]
        self.model = ListModel(top, titles, event_func=self.edit_event)
        return top
        
    def add_event_ref(self, event_ref, spouse=None):
        """
        Add an event to the model.
        """
        self.callman.register_handles({'event': [event_ref.ref]})
        event = self.dbstate.db.get_event_from_handle(event_ref.ref)
        event_date = DateHandler.get_date(event)
        event_sort = '%012d' % event.get_date_object().get_sort_value()
        place = ''
        handle = event.get_place_handle()
        if handle:
            place = self.dbstate.db.get_place_from_handle(handle).get_title()

        participants = ''
        if int(event_ref.get_role()) == EventRoleType.FAMILY:
            if spouse:
                participants = name_displayer.display(spouse)

        participants = Utils.get_participant_from_event(self.dbstate.db,
                                                        event_ref.ref)

        self.model.add((event.get_handle(),
                        str(event.get_type()),
                        participants,
                        event_date,
                        event_sort,
                        place,
                        event.get_description(),
                        str(event_ref.get_role())))

    def edit_event(self, treeview):
        """
        Edit the selected event.
        """
        model, iter_ = treeview.get_selection().get_selected()
        if iter_:
            handle = model.get_value(iter_, 0)
            try:
                event = self.dbstate.db.get_event_from_handle(handle)
                EditEvent(self.dbstate, self.uistate, [], event)
            except Errors.WindowActiveError:
                pass

class PersonEvents(Events):
    """
    Displays the events for a person.
    """
    def db_changed(self):
        self.dbstate.db.connect('person-update', self.update)

    def active_changed(self, handle):
        self.update()

    def update_has_data(self):
        active_handle = self.get_active('Person')
        active = self.dbstate.db.get_person_from_handle(active_handle)
        self.set_has_data(self.get_has_data(active))

    def get_has_data(self, active_person):
        """
        Return True if the gramplet has data, else return False.
        """
        if active_person:
            if active_person.get_event_ref_list():
                return True
            for family_handle in active_person.get_family_handle_list():
                family = self.dbstate.db.get_family_from_handle(family_handle)
                for event_ref in family.get_event_ref_list():
                    return True
        return False

    def main(self): # return false finishes
        active_handle = self.get_active('Person')
            
        self.model.clear()
        self.callman.unregister_all()
        if active_handle:
            self.display_person(active_handle)
        else:
            self.set_has_data(False)

    def display_person(self, active_handle):
        """
        Display the events for the active person.
        """
        active_person = self.dbstate.db.get_person_from_handle(active_handle)
        if not active_person:
            self.set_has_data(self.model.count > 0)
            return
        for event_ref in active_person.get_event_ref_list():
            self.add_event_ref(event_ref)
        for family_handle in active_person.get_family_handle_list():
            family = self.dbstate.db.get_family_from_handle(family_handle)
            father_handle = family.get_father_handle()
            mother_handle = family.get_mother_handle()
            if father_handle == active_handle:
                spouse = self.dbstate.db.get_person_from_handle(mother_handle)
            else:
                spouse = self.dbstate.db.get_person_from_handle(father_handle)
            for event_ref in family.get_event_ref_list():
                self.add_event_ref(event_ref, spouse)
        self.set_has_data(self.model.count > 0)

class FamilyEvents(Events):
    """
    Displays the events for a family.
    """
    def db_changed(self):
        self.dbstate.db.connect('family-update', self.update)
        self.connect_signal('Family', self.update)

    def update_has_data(self):
        active_handle = self.get_active('Family')
        active = self.dbstate.db.get_family_from_handle(active_handle)
        self.set_has_data(self.get_has_data(active))

    def get_has_data(self, active_family):
        """
        Return True if the gramplet has data, else return False.
        """
        if active_family:
            for event_ref in active_family.get_event_ref_list():
                return True
        return False

    def main(self): # return false finishes
        active_handle = self.get_active('Family')
            
        self.model.clear()
        self.callman.unregister_all()
        if active_handle:
            self.display_family(active_handle)
        else:
            self.set_has_data(False)

    def display_family(self, active_handle):
        """
        Display the events for the active family.
        """
        active_family = self.dbstate.db.get_family_from_handle(active_handle)
        for event_ref in active_family.get_event_ref_list():
            self.add_event_ref(event_ref)
        self.set_has_data(self.model.count > 0)

