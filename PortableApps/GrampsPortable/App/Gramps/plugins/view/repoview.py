# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2001-2006  Donald N. Allingham
# Copyright (C) 2008       Gary Burton
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
Repository View
"""

#-------------------------------------------------------------------------
#
# GTK/Gnome modules
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
from gui.views.treemodels import RepositoryModel
import Bookmarks
import Errors
import config
from gui.editors import EditRepository, DeleteRepositoryQuery
from DdTargets import DdTargets
from QuestionDialog import ErrorDialog
from Filters.SideBar import RepoSidebarFilter
from gen.plug import CATEGORY_QR_REPOSITORY

#-------------------------------------------------------------------------
#
# internationalization
#
#-------------------------------------------------------------------------
from gen.ggettext import gettext as _


#-------------------------------------------------------------------------
#
# RepositoryView
#
#-------------------------------------------------------------------------
class RepositoryView(ListView):
    """ repository listview class 
    """
    COL_NAME = 0
    COL_ID = 1
    COL_TYPE = 2
    COL_URL = 3
    COL_STREET = 4
    COL_LOCALITY = 5
    COL_CITY = 6
    COL_STATE = 7
    COL_COUNTRY = 8
    COL_ZIP = 9
    COL_EMAIL = 10
    COL_SURL = 11
    COL_CHAN = 12

    COLUMN_NAMES = [
        _('Name'),
        _('ID'),
        _('Type'),
        _('Home URL'),
        _('Street'),
        _('Locality'),
        _('City'),
        _('State/County'),
        _('Country'),
        _('ZIP/Postal Code'),
        _('Email'),
        _('Search URL'),
        _('Last Changed'),
        ]
    # default setting with visible columns, order of the col, and their size
    CONFIGSETTINGS = (
        ('columns.visible', [COL_NAME, COL_ID, COL_TYPE, COL_URL, COL_STREET,
                             ]),
        ('columns.rank', [COL_NAME, COL_ID, COL_TYPE, COL_URL, COL_STREET,
                          COL_LOCALITY, COL_CITY, COL_STATE, COL_COUNTRY,
                          COL_ZIP, COL_EMAIL, COL_SURL, COL_CHAN]),
        ('columns.size', [200, 75, 100, 250, 100, 100, 100, 100, 100,
                             100, 100, 100, 100])
        )    
    ADD_MSG = _("Add a new repository")
    EDIT_MSG = _("Edit the selected repository")
    DEL_MSG = _("Delete the selected repository")
    MERGE_MSG = _("Merge the selected repositories")
    FILTER_TYPE = "Repository"
    QR_CATEGORY = CATEGORY_QR_REPOSITORY

    def __init__(self, pdata, dbstate, uistate, nav_group=0):

        signal_map = {
            'repository-add'     : self.row_add,
            'repository-update'  : self.row_update,
            'repository-delete'  : self.row_delete,
            'repository-rebuild' : self.object_build,
            }
        
        ListView.__init__(
            self, _('Repositories'), pdata, dbstate, uistate,
            RepositoryView.COLUMN_NAMES, len(RepositoryView.COLUMN_NAMES),
            RepositoryModel, signal_map,
            dbstate.db.get_repo_bookmarks(),
            Bookmarks.RepoBookmarks, nav_group,
            multiple=True,
            filter_class=RepoSidebarFilter)

        self.func_list.update({
            '<CONTROL>J' : self.jump,
            '<CONTROL>BackSpace' : self.key_delete,
            })

        self.additional_uis.append(self.additional_ui())

    def navigation_type(self):
        return 'Repository'

    def get_bookmarks(self):
        return self.dbstate.db.get_repo_bookmarks()

    def drag_info(self):
        return DdTargets.REPO_LINK

    def define_actions(self):
        ListView.define_actions(self)
        self._add_action('FilterEdit', None, _('Repository Filter Editor'),
                         callback=self.filter_editor,)
        self._add_action('QuickReport', None, 
                         _("Quick View"), None, None, None)
        self._add_action('Dummy', None, 
                         '  ', None, None, self.dummy_report)

    def get_stock(self):
        return 'gramps-repository'

    def additional_ui(self):
        return '''<ui>
          <menubar name="MenuBar">
            <menu action="FileMenu">
              <placeholder name="LocalExport">
                <menuitem action="ExportTab"/>
              </placeholder>
            </menu>
            <menu action="BookMenu">
              <placeholder name="AddEditBook">
                <menuitem action="AddBook"/>
                <menuitem action="EditBook"/>
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
            <menu name="QuickReport" action="QuickReport">
              <menuitem action="Dummy"/>
            </menu>
          </popup>
        </ui>'''

    def add(self, obj):
        EditRepository(self.dbstate, self.uistate, [], gen.lib.Repository())

    def remove(self, obj):
        self.remove_selected_objects()

    def remove_object_from_handle(self, handle):
        source_list = [
            item[1] for item in
            self.dbstate.db.find_backlink_handles(handle, ['Source'])]
        object = self.dbstate.db.get_repository_from_handle(handle)
        query = DeleteRepositoryQuery(self.dbstate, self.uistate, object,
                                      source_list)
        is_used = len(source_list) > 0
        return (query, is_used, object)

    def edit(self, obj):
        for handle in self.selected_handles():
            repos = self.dbstate.db.get_repository_from_handle(handle)
            try:
                EditRepository(self.dbstate, self.uistate, [], repos)
            except Errors.WindowActiveError:
                pass

    def merge(self, obj):
        """
        Merge the selected repositories.
        """
        mlist = self.selected_handles()

        if len(mlist) != 2:
            msg = _("Cannot merge repositories.")
            msg2 = _("Exactly two repositories must be selected to perform a "
                     "merge. A second repository can be selected by holding "
                     "down the control key while clicking on the desired "
                     "repository.")
            ErrorDialog(msg, msg2)
        else:
            import Merge
            Merge.MergeRepositories(self.dbstate, self.uistate, mlist[0],
                                    mlist[1])

    def get_handle_from_gramps_id(self, gid):
        obj = self.dbstate.db.get_repository_from_gramps_id(gid)
        if obj:
            return obj.get_handle()
        else:
            return None

    def dummy_report(self, obj):
        """ For the xml UI definition of popup to work, the submenu 
            Quick Report must have an entry in the xml
            As this submenu will be dynamically built, we offer a dummy action
        """
        pass

    def get_default_gramplets(self):
        """
        Define the default gramplets for the sidebar and bottombar.
        """
        return (("Repository Filter",),
                ("Repository Details",
                 "Repository Notes",
                 "Repository Backlinks"))
