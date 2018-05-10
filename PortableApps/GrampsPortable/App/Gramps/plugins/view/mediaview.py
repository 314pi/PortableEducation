# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2001-2006  Donald N. Allingham
# Copyright (C) 2008       Gary Burton
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
Media View.
"""

#-------------------------------------------------------------------------
#
# Python modules
#
#-------------------------------------------------------------------------
from gen.ggettext import gettext as _
import urlparse
import os
import sys
import cPickle as pickle
import urllib
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
from gui.utils import open_file_with_default_application
from gui.views.listview import ListView
from gui.views.treemodels import MediaModel
import ThumbNails
import const
import constfunc
import config
import Utils
import Bookmarks
import gen.mime
import gen.lib
from gen.db import DbTxn
from gui.editors import EditMedia, DeleteMediaQuery
import Errors
from Filters.SideBar import MediaSidebarFilter
from DdTargets import DdTargets
from QuestionDialog import ErrorDialog
from gen.plug import CATEGORY_QR_MEDIA

#-------------------------------------------------------------------------
#
# MediaView
#
#-------------------------------------------------------------------------
class MediaView(ListView):
    """
    Provide the Media View interface on the GRAMPS main window. This allows
    people to manage all media items in their database. This is very similar
    to the other list based views, with the exception that it also has a
    thumbnail image at the top of the view that must be updated when the
    selection changes or when the selected media object changes.
    """
    COL_TITLE = 0
    COL_ID = 1
    COL_TYPE = 2
    COL_PATH = 3
    COL_DATE = 4
    COL_TAGS = 5
    COL_CHAN = 6
    #name of the columns
    COLUMN_NAMES = [
        _('Title'), 
        _('ID'), 
        _('Type'), 
        _('Path'), 
        _('Date'), 
        _('Tags'), 
        _('Last Changed'), 
        ]
    # default setting with visible columns, order of the col, and their size
    CONFIGSETTINGS = (
        ('columns.visible', [COL_TITLE, COL_ID, COL_TYPE, COL_PATH,
                             COL_DATE]),
        ('columns.rank', [COL_TITLE, COL_ID, COL_TYPE, COL_PATH,
                           COL_DATE, COL_TAGS, COL_CHAN]),
        ('columns.size', [200, 75, 100, 200, 150, 100, 150])
        )    
    
    ADD_MSG     = _("Add a new media object")
    EDIT_MSG    = _("Edit the selected media object")
    DEL_MSG     = _("Delete the selected media object")
    MERGE_MSG   = _("Merge the selected media objects")
    FILTER_TYPE = 'MediaObject'
    QR_CATEGORY = CATEGORY_QR_MEDIA

    def __init__(self, pdata, dbstate, uistate, nav_group=0):

        signal_map = {
            'media-add'     : self.row_add, 
            'media-update'  : self.row_update, 
            'media-delete'  : self.row_delete, 
            'media-rebuild' : self.object_build,
            'tag-update'    : self.tag_updated
            }

        ListView.__init__(
            self, _('Media'), pdata, dbstate, uistate, 
            MediaView.COLUMN_NAMES, len(MediaView.COLUMN_NAMES), 
            MediaModel, 
            signal_map, dbstate.db.get_media_bookmarks(), 
            Bookmarks.MediaBookmarks, nav_group,
            filter_class=MediaSidebarFilter,
            multiple=True)

        self.func_list.update({
            '<CONTROL>J' : self.jump, 
            '<CONTROL>BackSpace' : self.key_delete, 
            })

        self.additional_uis.append(self.additional_ui())

    def navigation_type(self):
        return 'Media'

    def drag_info(self):
        """
        Return the type of DND targets that this view will accept. For Media 
        View, we will accept media objects.
        """
        return DdTargets.MEDIAOBJ

    def drag_dest_info(self):
        """
        Specify the drag type for objects dropped on the view
        """
        return DdTargets.URI_LIST

    def find_index(self, obj):
        """
        returns the index of the object within the associated data
        """
        return self.model.indexlist[obj]

    def drag_data_received(self, widget, context, x, y, sel_data, info, time):
        """
        Handle the standard gtk interface for drag_data_received.

        If the selection data is define, extract the value from sel_data.data, 
        and decide if this is a move or a reorder.
        The only data we accept on mediaview is dropping a file, so URI_LIST. 
        We assume this is what we obtain
        """
        if not sel_data:
            return
        #modern file managers provide URI_LIST. For Windows split sel_data.data
        if constfunc.win():
            files = sel_data.data.split('\n')
        else:
            files =  sel_data.get_uris()
        for file in files:
            clean_string = Utils.fix_encoding(
                            file.replace('\0',' ').replace("\r", " ").strip())
            protocol, site, mfile, j, k, l = urlparse.urlparse(clean_string)
            if protocol == "file":
                name = unicode(urllib.url2pathname(
                                mfile.encode(sys.getfilesystemencoding())))
                mime = gen.mime.get_type(name)
                if not gen.mime.is_valid_type(mime):
                    return
                photo = gen.lib.MediaObject()
                base_dir = unicode(Utils.media_path(self.dbstate.db))
                if os.path.exists(base_dir):
                    name = Utils.relative_path(name, base_dir)
                photo.set_path(name)
                photo.set_mime_type(mime)
                basename = os.path.basename(name)
                (root, ext) = os.path.splitext(basename)
                photo.set_description(root)
                with DbTxn(_("Drag Media Object"), self.dbstate.db) as trans:
                    self.dbstate.db.add_object(photo, trans)
        widget.emit_stop_by_name('drag_data_received')
                
    def get_bookmarks(self):
        """
        Return the bookmarks associated with this view
        """
        return self.dbstate.db.get_media_bookmarks()

    def define_actions(self):
        """
        Defines the UIManager actions specific to Media View. We need to make
        sure that the common List View actions are defined as well, so we
        call the parent function.
        """
        ListView.define_actions(self)

        self._add_action('FilterEdit', None, _('Media Filter Editor'), 
                         callback=self.filter_editor)
        self._add_action('OpenMedia', 'gramps-viewmedia', _('View'), 
                         tip=_("View in the default viewer"), 
                         callback=self.view_media)
        self._add_action('OpenContainingFolder', None, 
                         _('Open Containing _Folder'), 
                         tip=_("Open the folder containing the media file"), 
                         callback=self.open_containing_folder)

        self._add_action('QuickReport', None, _("Quick View"), None, None, None)
        self._add_action('Dummy', None, '  ', None, None, self.dummy_report)
                        
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

    def view_media(self, obj):
        """
        Launch external viewers for the selected objects.
        """
        for handle in self.selected_handles():
            ref_obj = self.dbstate.db.get_object_from_handle(handle)
            mpath = Utils.media_path_full(self.dbstate.db, ref_obj.get_path())
            open_file_with_default_application(mpath)

    def open_containing_folder(self, obj):
        """
        Launch external viewers for the selected objects.
        """
        for handle in self.selected_handles():
            ref_obj = self.dbstate.db.get_object_from_handle(handle)
            mpath = Utils.media_path_full(self.dbstate.db, ref_obj.get_path())
            if mpath:
                mfolder, mfile = os.path.split(mpath)
                open_file_with_default_application(mfolder)

    def get_stock(self):
        """
        Return the icon for this view
        """
        return 'gramps-media'

    def additional_ui(self):
        """
        Return the UIManager XML description of the menus
        """
        return '''<ui>
          <menubar name="MenuBar">
            <menu action="FileMenu">
              <placeholder name="LocalExport">
                <menuitem action="ExportTab"/>
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
            <menu action="GoMenu">
              <placeholder name="CommonGo">
                <menuitem action="Back"/>
                <menuitem action="Forward"/>
                <separator/>
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
            <separator/>
            <toolitem action="OpenMedia"/>
          </toolbar>
          <popup name="Popup">
            <menuitem action="Back"/>
            <menuitem action="Forward"/>
            <separator/>
            <menuitem action="OpenMedia"/>
            <menuitem action="OpenContainingFolder"/>
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

    def dummy_report(self, obj):
        """ For the xml UI definition of popup to work, the submenu 
            Quick Report must have an entry in the xml
            As this submenu will be dynamically built, we offer a dummy action
        """
        pass

    def add(self, obj):
        """Add a new media object to the media list"""
        try:
            EditMedia(self.dbstate, self.uistate, [], gen.lib.MediaObject())
        except Errors.WindowActiveError:
            pass

    def remove(self, obj):
        self.remove_selected_objects()

    def remove_object_from_handle(self, handle):
        """
        Remove the selected objects from the database after getting
        user verification.
        """
        the_lists = Utils.get_media_referents(handle, self.dbstate.db)
        object = self.dbstate.db.get_object_from_handle(handle)
        query = DeleteMediaQuery(self.dbstate, self.uistate, handle, the_lists)
        is_used = any(the_lists)
        return (query, is_used, object)

    def edit(self, obj):
        """
        Edit the selected objects in the EditMedia dialog
        """
        for handle in self.selected_handles():
            object = self.dbstate.db.get_object_from_handle(handle)
            try:
                EditMedia(self.dbstate, self.uistate, [], object)
            except Errors.WindowActiveError:
                pass

    def merge(self, obj):
        """
        Merge the selected objects.
        """
        mlist = self.selected_handles()

        if len(mlist) != 2:
            msg = _("Cannot merge media objects.")
            msg2 = _("Exactly two media objects must be selected to perform a "
            "merge. A second object can be selected by holding down the "
            "control key while clicking on the desired object.")
            ErrorDialog(msg, msg2)
        else:
            import Merge
            Merge.MergeMediaObjects(self.dbstate, self.uistate, mlist[0],
                                    mlist[1])

    def get_handle_from_gramps_id(self, gid):
        """
        returns the handle of the specified object
        """
        obj = self.dbstate.db.get_object_from_gramps_id(gid)
        if obj:
            return obj.get_handle()
        else:
            return None

    def tag_updated(self, handle_list):
        """
        Update tagged rows when a tag color changes.
        """
        all_links = set([])
        for tag_handle in handle_list:
            links = set([link[1] for link in
                         self.dbstate.db.find_backlink_handles(tag_handle,
                                                include_classes='MediaObject')])
            all_links = all_links.union(links)
        self.row_update(list(all_links))

    def add_tag(self, transaction, media_handle, tag_handle):
        """
        Add the given tag to the given media object.
        """
        media = self.dbstate.db.get_object_from_handle(media_handle)
        media.add_tag(tag_handle)
        self.dbstate.db.commit_media_object(media, transaction)

    def get_default_gramplets(self):
        """
        Define the default gramplets for the sidebar and bottombar.
        """
        return (("Media Filter",),
                ("Media Preview",
                 "Media Citations",
                 "Media Notes",
                 "Media Attributes",
                 "Metadata Viewer",
                 "Media Backlinks"))
