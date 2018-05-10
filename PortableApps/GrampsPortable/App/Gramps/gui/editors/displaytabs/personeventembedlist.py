#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2006  Donald N. Allingham
# Copyright (C) 2009       B. Malengier
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
# python
#
#-------------------------------------------------------------------------
from gen.ggettext import gettext as _
import gobject

#-------------------------------------------------------------------------
#
# GRAMPS classes
#
#-------------------------------------------------------------------------
import gen.lib
from gen.display.name import displayer as name_displayer
from eventembedlist import EventEmbedList
from eventrefmodel import EventRefModel
import Errors

#-------------------------------------------------------------------------
#
# PersonEventEmbedList
#
#-------------------------------------------------------------------------
class PersonEventEmbedList(EventEmbedList):
    
    _WORKNAME = _("Personal")
    #_FAMNAME = _("With %(namepartner)s (%(famid)s)")
    _FAMNAME = _("Family")
    _UNKNOWNNAME = _("<Unknown>")
    
    _MSG = {
        'add'   : _('Add a new personal event'),
        'del'   : _('Remove the selected personal event'),
        'edit'  : _('Edit the selected personal event or edit family'),
        'share' : _('Share an existing event'),
        'up'    : _('Move the selected event upwards or change family order'),
        'down'  : _('Move the selected event downwards or change family order'),
        }

    def __init__(self, dbstate, uistate, track, obj):
        EventEmbedList.__init__(self, dbstate, uistate, track, obj,
                                build_model=EventRefModel )

    def get_data(self):
        if not self._data or self.changed:
            self._data = [self.obj.get_event_ref_list()]
            self._groups = [(self.obj.get_handle(), self._WORKNAME, '')]
            # own family events
            family_handle_list = self.obj.get_family_handle_list()
            if family_handle_list:
                for family_handle in family_handle_list:
                    family = self.dbstate.db.get_family_from_handle(family_handle)
                    father_handle = family.get_father_handle()
                    mother_handle = family.get_mother_handle()
                    if self.obj.get_handle()  == father_handle:
                        handlepartner = mother_handle
                    else:
                        handlepartner = father_handle
                    if handlepartner:
                        partner = self.dbstate.db.get_person_from_handle(
                                                    handlepartner)
                        groupname = name_displayer.display(partner)
                    else:
                        groupname = self._UNKNOWNNAME
                    self._data.append(family.get_event_ref_list())
                    self._groups.append((family_handle, self._FAMNAME,
                                         groupname))
            self.changed = False
        
        return self._data

    def default_role(self):
        return gen.lib.EventRoleType(gen.lib.EventRoleType.PRIMARY)

    def default_types(self):
        return [
            gen.lib.EventType(gen.lib.EventType.BIRTH),
            gen.lib.EventType(gen.lib.EventType.DEATH),
            gen.lib.EventType(gen.lib.EventType.BURIAL),
            ]

    def get_ref_editor(self):
        from gui.editors import EditEventRef
        return EditEventRef

    def editnotworkgroup(self, key):
        """
        Edit non native event in own editor
        """
        family = self.dbstate.db.get_family_from_handle(key)
        try:
            from gui.editors import EditFamily
            EditFamily(self.dbstate, self.uistate, [], family)
        except Errors.WindowActiveError:
            pass

    def _non_native_change(self):
        """
        handle change request of non native data
        """
        from QuestionDialog import WarningDialog
        WarningDialog(
                    _("Cannot change Family"),
                    _("You cannot change Family events in the Person Editor")
                    )
    def _move_up_group(self, groupindex):
        """
        move up pressed on the group
        If on a family group, allow to reorder the order of families
        as connected to this person.
        """
        ref = self.get_selected()
        if not ref or ref[1]:
            return
        if ref[0] == 0:
            #the workgroup: person events, cannot move up
            return
        if ref[0] == 1:
            #cannot move up, already first family
            return
        #change family list and rebuild the tabpage
        index = ref[0] - 1
        flist = self.obj.get_family_handle_list()
        handle = flist.pop(index)
        flist.insert(index-1, handle)
        self.changed = True
        self.rebuild()
        # select the row
        # New index is index-1 but for path, add another 1 for person events.
        path = (index,)
        self.tree.get_selection().select_path(path)
        gobject.idle_add(self.tree.scroll_to_cell, path)

    def _move_down_group(self, groupindex):
        """
        move down pressed on the group
        If on a family group, allow to reorder the order of families
        as connected to this person.
        """
        ref = self.get_selected()
        if not ref or ref[1]:
            return
        if ref[0] == 0:
            #person events, cannot move down
            return
        if ref[0] == len(self._groups)-1:
            #cannot move down, already last family
            return
        #change family list and rebuild the tabpage
        index = ref[0] -1
        flist = self.obj.get_family_handle_list()
        handle = flist.pop(index)
        flist.insert(index+1, handle)
        self.changed = True
        self.rebuild()
        # select the row
        # New index is index+1 but for path, add another 1 for person events.
        path = (index + 2,)
        self.tree.get_selection().select_path(path)
        gobject.idle_add(self.tree.scroll_to_cell, path)
