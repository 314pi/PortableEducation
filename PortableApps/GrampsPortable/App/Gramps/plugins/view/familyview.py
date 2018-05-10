# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2001-2006  Donald N. Allingham
# Copyright (C) 2010       Nick Hall
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

"""
Family View.
"""

#-------------------------------------------------------------------------
#
# Standard python modules
#
#-------------------------------------------------------------------------
from gen.ggettext import gettext as _
import logging
_LOG = logging.getLogger(".plugins.eventview")
#-------------------------------------------------------------------------
#
# GNOME/GTK+ modules
#
#-------------------------------------------------------------------------
import gtk

#-------------------------------------------------------------------------
#
# gramps modules
#
#-------------------------------------------------------------------------
import gen.lib
from gui.views.listview import ListView
from gui.views.treemodels import FamilyModel
from gui.editors import EditFamily
import Bookmarks
import Errors
import config
from QuestionDialog import ErrorDialog
from Filters.SideBar import FamilySidebarFilter
from gen.plug import CATEGORY_QR_FAMILY
from DdTargets import DdTargets

#-------------------------------------------------------------------------
#
# FamilyView
#
#-------------------------------------------------------------------------
class FamilyView(ListView):
    """ FamilyView class, derived from the ListView
    """
    # columns in the model used in view
    COL_ID = 0
    COL_FATHER = 1
    COL_MOTHER = 2
    COL_REL = 3
    COL_MARDATE = 4
    COL_TAGS = 5
    COL_CHAN = 6
    # name of the columns
    MARKUP_COLS = [COL_MARDATE]
    COLUMN_NAMES = [
        _('ID'),
        _('Father'),
        _('Mother'),
        _('Relationship'),
        _('Marriage Date'),
        _('Tags'),
        _('Last Changed'),
        ]
    #default setting with visible columns, order of the col, and their size
    CONFIGSETTINGS = (
        ('columns.visible', [COL_ID, COL_FATHER, COL_MOTHER, COL_REL, 
                             COL_MARDATE]),
        ('columns.rank', [COL_ID, COL_FATHER, COL_MOTHER, COL_REL, 
                           COL_MARDATE, COL_TAGS, COL_CHAN]),
        ('columns.size', [75, 200, 200, 100, 100, 100, 100])
        )    

    ADD_MSG     = _("Add a new family")
    EDIT_MSG    = _("Edit the selected family")
    DEL_MSG     = _("Delete the selected family")
    MERGE_MSG   = _("Merge the selected families")
    FILTER_TYPE = "Family"
    QR_CATEGORY = CATEGORY_QR_FAMILY

    def __init__(self, pdata, dbstate, uistate, nav_group=0):

        signal_map = {
            'family-add'     : self.row_add,
            'family-update'  : self.row_update,
            'family-delete'  : self.row_delete,
            'family-rebuild' : self.object_build,
            'tag-update'     : self.tag_updated
            }

        ListView.__init__(
            self, _('Families'), pdata, dbstate, uistate,
            FamilyView.COLUMN_NAMES, len(FamilyView.COLUMN_NAMES), 
            FamilyModel,
            signal_map, dbstate.db.get_family_bookmarks(),
            Bookmarks.FamilyBookmarks, nav_group,
            multiple=True,
            filter_class=FamilySidebarFilter,
            markup=FamilyView.MARKUP_COLS)

        self.func_list.update({
            '<CONTROL>J' : self.jump,
            '<CONTROL>BackSpace' : self.key_delete,
            })

        uistate.connect('nameformat-changed', self.build_tree)

        self.additional_uis.append(self.additional_ui())

    def navigation_type(self):
        return 'Family'

    def get_stock(self):
        return 'gramps-family'

    def additional_ui(self):
        return '''<ui>
          <menubar name="MenuBar">
            <menu action="FileMenu">
              <placeholder name="LocalExport">
                <menuitem action="ExportTab"/>
              </placeholder>
            </menu>
            <menu action="GoMenu">
              <placeholder name="CommonGo">
                <menuitem action="Back"/>
                <menuitem action="Forward"/>
                <separator/>
              </placeholder>
            </menu>
            <menu action="EditMenu">
              <placeholder name="CommonEdit">
                <menuitem action="Add"/>
                <menuitem action="Edit"/>
                <menuitem action="Remove"/>
                <menuitem action="Merge"/>
              </placeholder>
              <menuitem action="FilterEdit"/>
            </menu>
           <menu action="BookMenu">
              <placeholder name="AddEditBook">
                <menuitem action="AddBook"/>
                <menuitem action="EditBook"/>
              </placeholder>
           </menu>
          </menubar>
          <toolbar name="ToolBar">
            <placeholder name="CommonNavigation">
              <toolitem action="Back"/>  
              <toolitem action="Forward"/>  
            </placeholder>
            <placeholder name="CommonEdit">
              <toolitem action="Add"/>
              <toolitem action="Edit"/>
              <toolitem action="Remove"/>
              <toolitem action="Merge"/>
            </placeholder>
          </toolbar>
          <popup name="Popup">
            <menuitem action="Back"/>
            <menuitem action="Forward"/>
            <separator/>
            <menuitem action="Add"/>
            <menuitem action="Edit"/>
            <menuitem action="Remove"/>
            <menuitem action="Merge"/>
            <separator/>
            <menuitem action="MakeFatherActive"/>
            <menuitem action="MakeMotherActive"/>
            <separator/>
            <menu name="QuickReport" action="QuickReport">
              <menuitem action="Dummy"/>
            </menu>
          </popup>
        </ui>'''

    def define_actions(self):
        """Add the Forward action group to handle the Forward button."""

        ListView.define_actions(self)

        self._add_action('FilterEdit', None, _('Family Filter Editor'),
                        callback=self.filter_editor,)
                        
        self.all_action = gtk.ActionGroup(self.title + "/FamilyAll")
        self.all_action.add_actions([
                ('MakeFatherActive', gtk.STOCK_APPLY, _("Make Father Active Person"), 
                 None, None, self._make_father_active),
                ('MakeMotherActive', gtk.STOCK_APPLY, _("Make Mother Active Person"), 
                 None, None, self._make_mother_active),
                ('QuickReport', None, _("Quick View"), None, None, None),
                ('Dummy', None, '  ', None, None, self.dummy_report),
                ])
        self._add_action_group(self.all_action)

    def set_active(self):
        """
        Called when the page is displayed.
        """
        ListView.set_active(self)
        self.uistate.viewmanager.tags.tag_enable()

    def set_inactive(self):
        """
        Called when the page is no longer displayed.
        """
        ListView.set_inactive(self)
        self.uistate.viewmanager.tags.tag_disable()

    def get_bookmarks(self):
        return self.dbstate.db.get_family_bookmarks()

    def add_bookmark(self, obj):
        mlist = self.selected_handles()
        if mlist:
            self.bookmarks.add(mlist[0])
        else:
            from QuestionDialog import WarningDialog
            WarningDialog(
                _("Could Not Set a Bookmark"), 
                _("A bookmark could not be set because "
                  "no one was selected."))
        
    def add(self, obj):
        family = gen.lib.Family()
        try:
            EditFamily(self.dbstate, self.uistate, [], family)
        except Errors.WindowActiveError:
            pass

    def remove(self, obj):
        from QuestionDialog import QuestionDialog2
        from Utils import data_recover_msg
        msg = _('Deleting item will remove it from the database.')
        msg = msg + '\n' + data_recover_msg
        q = QuestionDialog2(_('Delete %s?') % _('family'), msg,
                       _('_Delete Item'), _('Cancel'))
        if q.run():
            self.uistate.set_busy_cursor(1)
            map(self.dbstate.db.remove_family_relationships,
                self.selected_handles())
            self.build_tree()
            self.uistate.set_busy_cursor(0)
    
    def edit(self, obj):
        for handle in self.selected_handles():
            family = self.dbstate.db.get_family_from_handle(handle)
            try:
                EditFamily(self.dbstate, self.uistate, [], family)
            except Errors.WindowActiveError:
                pass
                
    def merge(self, obj):
        """
        Merge the selected families.
        """
        mlist = self.selected_handles()

        if len(mlist) != 2:
            msg = _("Cannot merge families.")
            msg2 = _("Exactly two families must be selected to perform a merge."
                     " A second family can be selected by holding down the "
                     "control key while clicking on the desired family.")
            ErrorDialog(msg, msg2)
        else:
            import Merge
            Merge.MergeFamilies(self.dbstate, self.uistate, mlist[0], mlist[1])

    def _make_father_active(self, obj):
        """
        Make the father of the family the active person.
        """
        fhandle = self.first_selected()
        if fhandle:
            family = self.dbstate.db.get_family_from_handle(fhandle)
            if family:
                self.uistate.set_active(family.father_handle, 'Person')

    def _make_mother_active(self, obj):
        """
        Make the mother of the family the active person.
        """
        fhandle = self.first_selected()
        if fhandle:
            family = self.dbstate.db.get_family_from_handle(fhandle)
            if family:
                self.uistate.set_active(family.mother_handle, 'Person')
            
    def dummy_report(self, obj):
        """ For the xml UI definition of popup to work, the submenu 
            Quick Report must have an entry in the xml
            As this submenu will be dynamically built, we offer a dummy action
        """
        pass

    def drag_info(self):
        """
        Indicate that the drag type is a FAMILY_LINK
        """
        return DdTargets.FAMILY_LINK

    def tag_updated(self, handle_list):
        """
        Update tagged rows when a tag color changes.
        """
        all_links = set([])
        for tag_handle in handle_list:
            links = set([link[1] for link in
                         self.dbstate.db.find_backlink_handles(tag_handle,
                                                    include_classes='Family')])
            all_links = all_links.union(links)
        self.row_update(list(all_links))

    def add_tag(self, transaction, family_handle, tag_handle):
        """
        Add the given tag to the given family.
        """
        family = self.dbstate.db.get_family_from_handle(family_handle)
        family.add_tag(tag_handle)
        self.dbstate.db.commit_family(family, transaction)

    def get_default_gramplets(self):
        """
        Define the default gramplets for the sidebar and bottombar.
        """
        return (("Family Filter",),
                ("Family Gallery",
                 "Family Events",
                 "Family Children",
                 "Family Citations",
                 "Family Notes",
                 "Family Attributes",
                 "Family Backlinks"))
