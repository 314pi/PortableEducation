#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2001-2007  Donald N. Allingham
# Copyright (C) 2009-2010  Nick Hall
# Copyright (C) 2009       Benny Malengier
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
Provide the base classes for GRAMPS' DataView classes
"""

#----------------------------------------------------------------
#
# python modules
#
#----------------------------------------------------------------
import cPickle as pickle
import time
import logging

_LOG = logging.getLogger('.gui.listview')

#----------------------------------------------------------------
#
# gtk
#
#----------------------------------------------------------------
import gtk
import pango

#----------------------------------------------------------------
#
# GRAMPS 
#
#----------------------------------------------------------------
from gui.views.pageview import PageView
from gui.views.navigationview import NavigationView
from gui.columnorder import ColumnOrder
import config
import TreeTips
import Errors
from Filters import SearchBar
from gui.utils import add_menuitem
import const
import Utils
from QuestionDialog import QuestionDialog, QuestionDialog2
from gui.filtereditor import FilterEditor
from gen.ggettext import sgettext as _
from DdTargets import DdTargets
import gui.utils

#----------------------------------------------------------------
#
# Constants
#
#----------------------------------------------------------------
LISTFLAT = 0
LISTTREE = 1

#----------------------------------------------------------------
#
# ListView
#
#----------------------------------------------------------------
class ListView(NavigationView):
    COLUMN_NAMES = []
    #listview config settings that are always present related to the columns
    CONFIGSETTINGS = (
        ('columns.visible', []),
        ('columns.rank', []),
        ('columns.size', [])
        )
    ADD_MSG = ""
    EDIT_MSG = ""
    DEL_MSG = ""
    MERGE_MSG = ""
    FILTER_TYPE = None  # Set in inheriting class
    QR_CATEGORY = -1

    def __init__(self, title, pdata, dbstate, uistate, columns, handle_col, 
                 make_model, signal_map, get_bookmarks, bm_type, nav_group,
                 multiple=False, filter_class=None, markup=None):
        NavigationView.__init__(self, title, pdata, dbstate, uistate, 
                              get_bookmarks, bm_type, nav_group)
        #default is listviews keep themself in sync with database
        self._dirty_on_change_inactive = False
        
        self.filter_class = filter_class
        self.renderer = gtk.CellRendererText()
        self.renderer.set_property('ellipsize', pango.ELLIPSIZE_END)
        self.sort_col = 0
        self.sort_order = gtk.SORT_ASCENDING
        self.columns = []
        self.colinfo = columns
        self.handle_col = handle_col
        self.make_model = make_model
        self.model = None
        self.signal_map = signal_map
        self.multiple_selection = multiple
        self.generic_filter = None
        self.markup_columns = markup or []
        dbstate.connect('database-changed', self.change_db)
        self.connect_signals()

    def type_list(self):
        """
        set the listtype, this governs eg keybinding
        """
        return LISTFLAT

    ####################################################################
    # Build interface
    ####################################################################
    def build_widget(self):
        """
        Builds the interface and returns a gtk.Container type that
        contains the interface. This containter will be inserted into
        a gtk.Notebook page.
        """
        self.vbox = gtk.VBox()
        self.vbox.set_border_width(4)
        self.vbox.set_spacing(4)
        
        self.search_bar = SearchBar(self.dbstate, self.uistate, 
                                    self.search_build_tree)
        filter_box = self.search_bar.build()

        self.list = gtk.TreeView()
        self.list.set_rules_hint(True)
        self.list.set_headers_visible(True)
        self.list.set_headers_clickable(True)
        self.list.set_fixed_height_mode(True)
        self.list.connect('button-press-event', self._button_press)
        if self.type_list() == LISTFLAT:
            # Flat list
            self.list.connect('key-press-event', self._key_press)
        else:
            # Tree
            self.list.connect('key-press-event', self._key_press_tree)

        if self.drag_info():
            self.list.connect('drag_data_get', self.drag_data_get)
            self.list.connect('drag_begin', self.drag_begin)
        if self.drag_dest_info():
            self.list.connect('drag_data_received', self.drag_data_received)
            self.list.drag_dest_set(gtk.DEST_DEFAULT_MOTION |
                                    gtk.DEST_DEFAULT_DROP, 
                                    [self.drag_dest_info().target()], 
                                    gtk.gdk.ACTION_MOVE |
                                    gtk.gdk.ACTION_COPY)

        scrollwindow = gtk.ScrolledWindow()
        scrollwindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrollwindow.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        scrollwindow.add(self.list)

        self.vbox.pack_start(filter_box, False)
        self.vbox.pack_start(scrollwindow, True)

        self.renderer = gtk.CellRendererText()
        self.renderer.set_property('ellipsize', pango.ELLIPSIZE_END)

        self.columns = []
        self.build_columns()
        self.selection = self.list.get_selection()
        if self.multiple_selection:
            self.selection.set_mode(gtk.SELECTION_MULTIPLE)
        self.selection.connect('changed', self.row_changed)

        self.setup_filter()
        return self.vbox

    def define_actions(self):
        """
        Required define_actions function for PageView. Builds the action
        group information required. We extend beyond the normal here, 
        since we want to have more than one action group for the PersonView.
        Most PageViews really won't care about this.
        """
        
        NavigationView.define_actions(self)

        self.edit_action = gtk.ActionGroup(self.title + '/ChangeOrder')
        self.edit_action.add_actions([
                ('Add', gtk.STOCK_ADD, _("_Add..."), "<control>Insert", 
                    self.ADD_MSG, self.add), 
                ('Remove', gtk.STOCK_REMOVE, _("_Remove"), "<control>Delete", 
                    self.DEL_MSG, self.remove), 
                ('Merge', 'gramps-merge', _('_Merge...'), None,
                    self.MERGE_MSG, self.merge),
                ('ExportTab', None, _('Export View...'), None, None,
                    self.export), 
                ])

        self._add_action_group(self.edit_action)

        self._add_action('Edit', gtk.STOCK_EDIT, _("action|_Edit..."), 
                         accel="<control>Return", 
                         tip=self.EDIT_MSG, 
                         callback=self.edit)
        
    def build_columns(self):
        map(self.list.remove_column, self.columns)
            
        self.columns = []

        index = 0
        for pair in self.column_order():
            if not pair[0]: continue
            name = self.colinfo[pair[1]]

            column = gtk.TreeViewColumn(name, self.renderer)
            
            if self.model and self.model.color_column() is not None:
                column.set_cell_data_func(self.renderer, self.foreground_color)

            if pair[1] in self.markup_columns:
                column.add_attribute(self.renderer, 'markup', pair[1])
            else:
                column.add_attribute(self.renderer, 'text', pair[1])

            column.connect('clicked', self.column_clicked, index)
            column.set_resizable(True)
            column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
            column.set_fixed_width(pair[2])
            column.set_clickable(True)
            self.columns.append(column)
            self.list.append_column(column)
            index += 1

    def foreground_color(self, column, renderer, model, iter_):
        '''
        Set the foreground color of the cell renderer.  We use a cell data
        function because we don't want to set the color of untagged rows.
        '''
        fg_color = model.get_value(iter_, model.color_column())
        renderer.set_property('foreground', fg_color)

    def set_active(self):
        NavigationView.set_active(self)
        self.uistate.show_filter_results(self.dbstate, 
                                         self.model.displayed(), 
                                         self.model.total())

    def __build_tree(self):
        Utils.profile(self._build_tree)

    def build_tree(self, force_sidebar=False):
        if self.active:
            cput0 = time.clock()
            if not self.search_bar.is_visible():
                filter_info = (True, self.generic_filter, False)
            else:
                value = self.search_bar.get_value()
                filter_info = (False, value, value[0] in self.exact_search())

            if self.dirty or not self.model:
                if self.model:
                    self.list.set_model(None)
                    self.model.destroy()
                self.model = self.make_model(self.dbstate.db, self.sort_col, 
                                             search=filter_info,
                                             sort_map=self.column_order())
            else:
                #the entire data to show is already in memory.
                #run only the part that determines what to show
                self.list.set_model(None)
                self.model.set_search(filter_info)
                self.model.rebuild_data()
            
            cput1 = time.clock()
            self.build_columns()
            cput2 = time.clock()
            self.list.set_model(self.model)
            cput3 = time.clock()
            self.__display_column_sort()
            self.goto_active(None)

            if const.USE_TIPS and self.model.tooltip_column() is not None:
                self.tooltips = TreeTips.TreeTips(
                    self.list, self.model.tooltip_column(), True)
            self.dirty = False
            cput4 = time.clock()
            self.uistate.show_filter_results(self.dbstate, 
                                             self.model.displayed(), 
                                             self.model.total())
            _LOG.debug(self.__class__.__name__ + ' build_tree ' +
                    str(time.clock() - cput0) + ' sec')
            _LOG.debug('parts ' + str(cput1-cput0) + ' , ' 
                             + str(cput2-cput1) + ' , ' 
                             + str(cput3-cput2) + ' , ' 
                             + str(cput4-cput3) + ' , ' 
                             + str(time.clock() - cput4))
            
        else:
            self.dirty = True

    def search_build_tree(self):
        self.build_tree()

    def exact_search(self):
        """
        Returns a tuple indicating columns requiring an exact search
        """
        return ()

    def get_viewtype_stock(self):
        """Type of view in category, default listview is a flat list
        """
        return 'gramps-tree-list'

    def filter_editor(self, obj):
        try:
            FilterEditor(self.FILTER_TYPE , const.CUSTOM_FILTERS, 
                         self.dbstate, self.uistate)
        except Errors.WindowActiveError:
            return

    def setup_filter(self):
        """Build the default filters and add them to the filter menu."""
        self.search_bar.setup_filter(
            [(self.colinfo[pair[1]], pair[1], pair[1] in self.exact_search())
                for pair in self.column_order() if pair[0]])

    def sidebar_toggled(self, active):
        """
        Called when the sidebar is toggled.
        """
        if active:
            self.search_bar.hide()
        else:
            self.search_bar.show()

    ####################################################################
    # Navigation
    ####################################################################
    def goto_handle(self, handle):
        """
        Go to a given handle in the list.
        Required by the NavigationView interface.
        
        We have a bit of a problem due to the nature of how GTK works.
        We have to unselect the previous path and select the new path. However, 
        these cause a row change, which calls the row_change callback, which
        can end up calling change_active_person, which can call
        goto_active_person, causing a bit of recusion. Confusing, huh?

        Unfortunately, row_change has to be able to call change_active_person, 
        because this can occur from the interface in addition to programatically.

        To handle this, we set the self.inactive variable that we can check
        in row_change to look for this particular condition.
        """
        if not handle or handle in self.selected_handles():
            return

        if self.type_list() == LISTFLAT:
            # Flat
            try:
                path = self.model.on_get_path(handle)
            except:
                path = None
        else:
            # Tree
            path = None
            node = self.model.get_node(handle)
            if node:
                parent_node = self.model.on_iter_parent(node)
                if parent_node:
                    parent_path = self.model.on_get_path(parent_node)
                    if parent_path:
                        for i in range(len(parent_path)):
                            expand_path = tuple([x for x in parent_path[:i+1]])
                            self.list.expand_row(expand_path, False)
                path = self.model.on_get_path(node)

        if path is not None:
            self.selection.unselect_all()
            self.selection.select_path(path)
            self.list.scroll_to_cell(path, None, 1, 0.5, 0)
        else:
            self.selection.unselect_all()
            self.uistate.push_message(self.dbstate, 
                                      _("Active object not visible"))

    def add_bookmark(self, obj):
        mlist = []
        self.selection.selected_foreach(self.blist, mlist)

        if mlist:
            self.bookmarks.add(mlist[0])
        else:
            from QuestionDialog import WarningDialog
            WarningDialog(
                _("Could Not Set a Bookmark"), 
                _("A bookmark could not be set because "
                  "nothing was selected."))

    ####################################################################
    # 
    ####################################################################

    def drag_info(self):
        """
        Specify the drag type for a single selected row
        """
        return None

    def drag_list_info(self):
        """
        Specify the drag type for a multiple selected rows
        """
        return DdTargets.LINK_LIST

    def drag_dest_info(self):
        """
        Specify the drag type for objects dropped on the view
        """
        return None

    def drag_begin(self, widget, context):
        widget.drag_source_set_icon_stock(self.get_stock())
        return True
        
    def drag_data_get(self, widget, context, sel_data, info, time):
        selected_ids = self.selected_handles()

        if len(selected_ids) == 1:
            data = (self.drag_info().drag_type, id(self), selected_ids[0], 0)
            sel_data.set(sel_data.target, 8, pickle.dumps(data))
        elif len(selected_ids) > 1:
            data = (self.drag_list_info().drag_type, id(self), 
                    [(self.drag_info().drag_type, handle)
                        for handle in selected_ids], 
                    0)
            sel_data.set(sel_data.target, 8, pickle.dumps(data))
        return True

    def set_column_order(self):
        """
        change the order of the columns to that given in config file
        after config file changed. We reset the sort to the first column
        """
        #now we need to rebuild the model so it contains correct column info
        self.dirty = True
        #make sure we sort on first column. We have no idea where the 
        # column that was sorted on before is situated now. 
        self.sort_col = 0
        self.sort_order = gtk.SORT_ASCENDING
        self.setup_filter()
        self.build_tree()

    def column_order(self):
        """
        Column order is obtained from the config file of the listview. 
        A column order is a list of 3-tuples. The order in the list is the
        order the columns must appear in.
        For a column, the 3-tuple should be (enable, modelcol, sizecol), where
            enable: show this column or don't show it
            modelcol: column in the datamodel this column is build of
            size: size the column should have
        """
        order = self._config.get('columns.rank')
        size = self._config.get('columns.size')
        vis =  self._config.get('columns.visible')

        colord = [(1 if val in vis else 0, val, size)
            for val, size in zip(order, size)]
        return colord

    def get_column_widths(self):
             return [column.get_width() for column in self.columns]

    def remove_selected_objects(self):
        """
        Function to remove selected objects
        """
        prompt = True
        if len(self.selected_handles()) > 1:
            q = QuestionDialog2(
                _("Confirm every deletion?"),
                _("More than one item has been selected for deletion. "
                  "Ask before deleting each one?"),
                _("No"),
                _("Yes"))
            prompt = not q.run()
            
        if not prompt:
            self.uistate.set_busy_cursor(1)

        for handle in self.selected_handles():
            (query, is_used, object) = self.remove_object_from_handle(handle)
            if prompt:
                if is_used:
                    msg = _('This item is currently being used. '
                            'Deleting it will remove it from the database and '
                            'from all other items that reference it.')
                else:
                    msg = _('Deleting item will remove it from the database.')
                
                msg += ' ' + Utils.data_recover_msg
                #descr = object.get_description()
                #if descr == "":
                descr = object.get_gramps_id()
                self.uistate.set_busy_cursor(1)
                QuestionDialog(_('Delete %s?') % descr, msg,
                               _('_Delete Item'), query.query_response)
                self.uistate.set_busy_cursor(0)
            else:
                query.query_response()

        if not prompt:
            self.uistate.set_busy_cursor(0)
        
    def blist(self, store, path, node, sel_list):
        if store.get_flags() & gtk.TREE_MODEL_LIST_ONLY:
            handle = store.get_value(node, self.handle_col)
        else:
            handle = store.get_handle(store.on_get_iter(path))

        if handle is not None:
            sel_list.append(handle)

    def selected_handles(self):
        mlist = []
        if self.selection:
            self.selection.selected_foreach(self.blist, mlist)
        return mlist

    def first_selected(self):
        mlist = []
        self.selection.selected_foreach(self.blist, mlist)
        if mlist:
            return mlist[0]
        else:
            return None

    ####################################################################
    # Signal handlers
    ####################################################################
    def column_clicked(self, obj, data):
        """
        Called when a column is clicked.

        obj     A TreeViewColumn object of the column clicked
        data    The column index
        """
        self.uistate.set_busy_cursor(1)
        self.uistate.push_message(self.dbstate, _("Column clicked, sorting..."))
        cput = time.clock()
        same_col = False
        if self.sort_col != data:
            order = gtk.SORT_ASCENDING
        else:
            same_col = True
            if (self.columns[data].get_sort_order() == gtk.SORT_DESCENDING
                or not self.columns[data].get_sort_indicator()):
                order = gtk.SORT_ASCENDING
            else:
                order = gtk.SORT_DESCENDING

        self.sort_col = data
        self.sort_order = order
        handle = self.first_selected()

        if not self.search_bar.is_visible():
            filter_info = (True, self.generic_filter, False)
        else:
            value = self.search_bar.get_value()
            filter_info = (False, value, value[0] in self.exact_search())

        if same_col:
            self.model.reverse_order()
        else:
            self.model = self.make_model(self.dbstate.db, self.sort_col, 
                                         self.sort_order, 
                                         search=filter_info, 
                                         sort_map=self.column_order())

            self.list.set_model(self.model)

        self.__display_column_sort()

        if handle:
            self.goto_handle(handle)

        # set the search column to be the sorted column
        search_col = self.column_order()[data][1]
        self.list.set_search_column(search_col)
        
        self.uistate.set_busy_cursor(0)
        
        _LOG.debug('   ' + self.__class__.__name__ + ' column_clicked ' +
                    str(time.clock() - cput) + ' sec')

    def __display_column_sort(self):
        for i, c in enumerate(self.columns):
            c.set_sort_indicator(i == self.sort_col)
        self.columns[self.sort_col].set_sort_order(self.sort_order)

    def connect_signals(self):
        """
        Connect database signals defined in the signal map.
        """
        for sig in self.signal_map:
            self.callman.add_db_signal(sig, self.signal_map[sig])
        
    def change_db(self, db):
        """
        Called when the database is changed.
        """
        self._change_db(db)
        self.connect_signals()

        self.bookmarks.update_bookmarks(self.get_bookmarks())
        if self.active:
            #force rebuild of the model on build of tree
            self.dirty = True
            self.build_tree()
            self.bookmarks.redraw()
        else:
            self.dirty = True

    def row_changed(self, selection):
        """
        Called with a list selection is changed.

        Check the selected objects in the list and return those that have
        handles attached.  Set the active object to the first item in the
        list. If no row is selected, set the active object to None.
        """
        selected_ids = self.selected_handles()
        if len(selected_ids) > 0:
            self.change_active(selected_ids[0])

        if len(selected_ids) == 1:
            if self.drag_info():
                self.list.drag_source_set(gtk.gdk.BUTTON1_MASK, 
                                      [self.drag_info().target()], 
                                      gtk.gdk.ACTION_COPY)
        elif len(selected_ids) > 1:
            if self.drag_list_info():
                self.list.drag_source_set(gtk.gdk.BUTTON1_MASK, 
                                      [self.drag_list_info().target()], 
                                      gtk.gdk.ACTION_COPY)

        self.uistate.modify_statusbar(self.dbstate)

    def row_add(self, handle_list):
        """
        Called when an object is added.
        """
        if self.active or \
           (not self.dirty and not self._dirty_on_change_inactive):
            cput = time.clock()
            map(self.model.add_row_by_handle, handle_list)
            _LOG.debug('   ' + self.__class__.__name__ + ' row_add ' +
                    str(time.clock() - cput) + ' sec')
            if self.active:
                self.uistate.show_filter_results(self.dbstate, 
                                                 self.model.displayed(), 
                                                 self.model.total())
        else:
            self.dirty = True

    def row_update(self, handle_list):
        """
        Called when an object is updated.
        """
        if self.model:
            self.model.prev_handle = None
        if self.active or \
           (not self.dirty and not self._dirty_on_change_inactive):
            cput = time.clock()
            map(self.model.update_row_by_handle, handle_list)
            _LOG.debug('   ' + self.__class__.__name__ + ' row_update ' +
                    str(time.clock() - cput) + ' sec')
            # Ensure row is still selected after a change of postion in tree.
            if handle_list and not self.selected_handles():
                self.goto_handle(handle_list[-1])
        else:
            self.dirty = True

    def row_delete(self, handle_list):
        """
        Called when an object is deleted.
        """
        if self.active or \
           (not self.dirty and not self._dirty_on_change_inactive):
            cput = time.clock()
            map(self.model.delete_row_by_handle, handle_list)
            _LOG.debug('   '  + self.__class__.__name__ + ' row_delete ' +
                    str(time.clock() - cput) + ' sec')
            if self.active:
                self.uistate.show_filter_results(self.dbstate, 
                                                 self.model.displayed(), 
                                                 self.model.total())
        else:
            self.dirty = True

    def object_build(self, *args):
        """
        Called when the tree must be rebuilt and bookmarks redrawn.
        """
        self.dirty = True
        if self.active:
            # Save the currently selected handles, if any:
            selected_ids = self.selected_handles()
            self.bookmarks.redraw()
            self.build_tree()
            # Reselect one, if it still exists after rebuild:
            nav_type = self.navigation_type()
            lookup_handle = self.dbstate.db.get_table_metadata(nav_type)['handle_func']
            for handle in selected_ids:
                # Still exist?
                if lookup_handle(handle):
                    # Select it, and stop selecting:
                    self.change_active(handle)
                    break

    def _button_press(self, obj, event):
        """
        Called when a mouse is clicked.
        """
        if not self.dbstate.open:
            return False
        from QuickReports import (create_quickreport_menu, 
                                  create_web_connect_menu)
        if event.type == gtk.gdk._2BUTTON_PRESS and event.button == 1:
            if self.type_list() == LISTFLAT:
                self.edit(obj)
                return True
            else:
                # Tree
                store, paths = self.selection.get_selected_rows()
                if paths:
                    firstsel = paths[0]
                    firstnode = self.model.on_get_iter(firstsel)
                    if len(paths)==1 and firstnode.handle is None:
                        return self.expand_collapse_tree_branch()
                    else:
                        self.edit(obj)
                        return True
        elif gui.utils.is_right_click(event):
            menu = self.uistate.uimanager.get_widget('/Popup')
            #construct quick reports if needed
            if menu and self.QR_CATEGORY > -1 :
                qr_menu = self.uistate.uimanager.\
                            get_widget('/Popup/QuickReport').get_submenu()
                if qr_menu :
                    self.uistate.uimanager.\
                            get_widget('/Popup/QuickReport').remove_submenu()
                reportactions = []
                if menu and self.get_active():
                    (ui, reportactions) = create_quickreport_menu(
                                            self.QR_CATEGORY, 
                                            self.dbstate, 
                                            self.uistate,
                                            self.first_selected())
                if len(reportactions) > 1 :
                    qr_menu = gtk.Menu()
                    for action in reportactions[1:] :
                        add_menuitem(qr_menu, action[2], None, action[5])
                    self.uistate.uimanager.get_widget('/Popup/QuickReport').\
                            set_submenu(qr_menu)
            if menu and self.get_active():
                popup = self.uistate.uimanager.get_widget('/Popup/WebConnect')
                if popup:
                    qr_menu = popup.get_submenu()
                    webconnects = []
                    if qr_menu:
                        popup.remove_submenu()
                        webconnects = create_web_connect_menu(
                            self.dbstate, 
                            self.uistate,
                            self.navigation_type(),
                            self.first_selected())
                    if len(webconnects) > 1 :
                        qr_menu = gtk.Menu()
                        for action in webconnects[1:] :
                            add_menuitem(qr_menu, action[2], None, action[5])
                        popup.set_submenu(qr_menu)
            if menu:
                menu.popup(None, None, None, event.button, event.time)
                return True
            
        return False
    
    def _key_press(self, obj, event):
        """
        Called when a key is pressed on a flat listview
        ENTER --> edit selection
        """
        if not self.dbstate.open:
            return False
        if event.keyval in (gtk.keysyms.Return, gtk.keysyms.KP_Enter):
            self.edit(obj)
            return True
        return False

    def _key_press_tree(self, obj, event):
        """
        Called when a key is pressed on a tree listview
        ENTER --> edit selection or open group node
        SHIFT+ENTER --> open group node and all children nodes
        """
        if not self.dbstate.open:
            return False
        elif event.state & gtk.gdk.SHIFT_MASK:
            if event.keyval in (gtk.keysyms.Return, gtk.keysyms.KP_Enter):
                store, paths = self.selection.get_selected_rows()
                if paths:
                    firstsel = paths[0]
                    firstnode = self.model.on_get_iter(firstsel)
                    if len(paths) == 1 and firstnode.handle is None:
                        return self.expand_collapse_tree_branch()
        else:
            if event.keyval in (gtk.keysyms.Return, gtk.keysyms.KP_Enter):
                store, paths = self.selection.get_selected_rows()
                if paths:
                    firstsel = paths[0]
                    firstnode = self.model.on_get_iter(firstsel)
                    if len(paths) == 1 and firstnode.handle is None:
                        return self.expand_collapse_tree()
                    else:
                        self.edit(obj)
                        return True
            
        return False

    def expand_collapse_tree(self):
        """
        Expand or collapse the selected group node.
        Return True if change done, False otherwise
        """
        store, paths = self.selection.get_selected_rows()
        if paths:
            firstsel = paths[0]
            firstnode = self.model.on_get_iter(firstsel)
            if firstnode.handle:
                return False
            if self.list.row_expanded(firstsel):
                self.list.collapse_row(firstsel)
            else:
                self.list.expand_row(firstsel, False)
            return True
        return False

    def expand_collapse_tree_branch(self):
        """
        Expand or collapse the selected group node with all children.
        Return True if change done, False otherwise
        """
        store, paths = self.selection.get_selected_rows()
        if paths:
            firstsel = paths[0]
            firstnode = self.model.on_get_iter(firstsel)
            if firstnode.handle:
                return False
            if self.list.row_expanded(firstsel):
                self.list.collapse_row(firstsel)
            else:
                self.open_branch(None)
            return True
        return False

    def key_delete(self):
        self.remove(None)

    def change_page(self):
        """
        Called when a page is changed.
        """
        NavigationView.change_page(self)
        if self.model:
            self.uistate.show_filter_results(self.dbstate, 
                                             self.model.displayed(), 
                                             self.model.total())
        self.edit_action.set_visible(True)
        self.edit_action.set_sensitive(not self.dbstate.db.readonly)

    def on_delete(self):
        """
        Save the column widths when the view is shutdown.
        """
        widths = self.get_column_widths()
        order = self._config.get('columns.rank')
        size = self._config.get('columns.size')
        vis =  self._config.get('columns.visible')
        newsize = []
        index = 0
        for val, size in zip(order, size):
            if val in vis:
                size = widths[index]
                index += 1
            newsize.append(size)
        self._config.set('columns.size', newsize)
        PageView.on_delete(self)

    ####################################################################
    # Export data
    ####################################################################
    def export(self, obj):
        chooser = gtk.FileChooserDialog(
            _("Export View as Spreadsheet"), 
            self.uistate.window, 
            gtk.FILE_CHOOSER_ACTION_SAVE, 
            (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, 
             gtk.STOCK_SAVE, gtk.RESPONSE_OK))
        chooser.set_do_overwrite_confirmation(True)

        combobox = gtk.combo_box_new_text()
        label = gtk.Label(_("Format:"))
        label.set_alignment(1.0, 0.5)
        box = gtk.HBox()
        box.pack_start(label, True, True, padding=12)
        box.pack_start(combobox, False, False)
        combobox.append_text(_('CSV'))
        combobox.append_text(_('OpenDocument Spreadsheet'))
        combobox.set_active(0)
        box.show_all()
        chooser.set_extra_widget(box)

        while True:
            value = chooser.run()
            fn = chooser.get_filename()
            fn = Utils.get_unicode_path_from_file_chooser(fn)
            fl = combobox.get_active()
            if value == gtk.RESPONSE_OK:
                if fn:
                    chooser.destroy()
                    break
            else:
                chooser.destroy()
                return
        self.write_tabbed_file(fn, fl)

    def write_tabbed_file(self, name, type):
        """
        Write a tabbed file to the specified name. 
        
        The output file type is determined by the type variable.
        """
        from docgen import CSVTab, ODSTab
        ofile = None
        data_cols = [pair[1] for pair in self.column_order() if pair[0]]

        column_names = [self.colinfo[i] for i in data_cols]
        if type == 0:
            ofile = CSVTab(len(column_names))                        
        else:
            ofile = ODSTab(len(column_names))
        
        ofile.open(name)
        ofile.start_page()
        ofile.start_row()

        # Headings
        if self.model.get_flags() & gtk.TREE_MODEL_LIST_ONLY:
            headings = column_names
        else:
            levels = self.model.get_tree_levels()
            headings = levels + column_names[1:]
            data_cols = data_cols[1:]

        map(ofile.write_cell, headings)
        ofile.end_row()

        if self.model.get_flags() & gtk.TREE_MODEL_LIST_ONLY:
            # Flat model
            for row in self.model:
                ofile.start_row()
                for index in data_cols:
                    ofile.write_cell(row[index])
                ofile.end_row()
        else:
            # Tree model
            node = self.model.on_get_iter((0,))
            self.write_node(node, len(levels), [], ofile, data_cols)
        
        ofile.end_page()
        ofile.close()
        
    def write_node(self, node, depth, level, ofile, data_cols):
        if node is None:
            return
        while node is not None:
            new_level = level + [self.model.on_get_value(node, 0)]
            if self.model.get_handle(node):
                ofile.start_row()
                padded_level = new_level + [''] * (depth - len(new_level))
                map(ofile.write_cell, padded_level)
                for index in data_cols:
                    ofile.write_cell(self.model.on_get_value(node, index))
                ofile.end_row()

            first_child = self.model.on_iter_children(node)
            self.write_node(first_child, depth, new_level, ofile, data_cols)
            node = self.model.on_iter_next(node)

    ####################################################################
    # Template functions
    ####################################################################
    def get_bookmarks(self):
        """
        Template function to get bookmarks.
        We could implement this in the NavigationView
        """
        raise NotImplementedError
        
    def edit(self, obj):
        """
        Template function to allow the editing of the selected object
        """
        raise NotImplementedError

    def remove(self, handle):
        """
        Template function to allow the removal of an object by its handle
        """
        raise NotImplementedError

    def add(self, obj):
        """
        Template function to allow the adding of a new object
        """
        raise NotImplementedError

    def merge(self, obj):
        """
        Template function to allow the merger of two objects.
        """
        raise NotImplementedError

    def remove_object_from_handle(self, handle):
        """
        Template function to allow the removal of an object by its handle
        """
        raise NotImplementedError

    def open_all_nodes(self, obj):
        """
        Method for Treeviews to open all groups
        obj: for use of method in event callback 
        """
        self.uistate.status_text(_("Updating display..."))
        self.uistate.set_busy_cursor(True)

        self.list.expand_all()

        self.uistate.set_busy_cursor(False)
        self.uistate.modify_statusbar(self.dbstate)

    def close_all_nodes(self, obj):
        """
        Method for Treeviews to close all groups
        obj: for use of method in event callback
        """
        self.list.collapse_all()

    def open_branch(self, obj):
        """
        Expand the selected branches and all children.
        obj: for use of method in event callback
        """
        self.uistate.status_text(_("Updating display..."))
        self.uistate.set_busy_cursor(True)
        
        selected = self.selection.get_selected_rows()
        for path in selected[1]:
            self.list.expand_row(path, True)

        self.uistate.set_busy_cursor(False)
        self.uistate.modify_statusbar(self.dbstate)
        
    def close_branch(self, obj):
        """
        Collapse the selected branches.
        :param obj: not used, present only to allow the use of the method in
            event callback
        """
        selected = self.selection.get_selected_rows()
        for path in selected[1]:
            self.list.collapse_row(path)

    def can_configure(self):
        """
        See :class:`~gui.views.pageview.PageView 
        :return: bool
        """
        return True

    def config_connect(self):
        """
        Overwriten from  :class:`~gui.views.pageview.PageView method
        This method will be called after the ini file is initialized,
        use it to monitor changes in the ini file
        """
        #func = self.config_callback(self.build_tree)
        #self._config.connect('columns.visible', func)
        #self._config.connect('columns.rank', func)
        pass

    def _get_configure_page_funcs(self):
        """
        Return a list of functions that create gtk elements to use in the 
        notebook pages of the Configure dialog
        
        :return: list of functions
        """
        def columnpage(configdialog):
            return _('Columns'), ColumnOrder(self._config, self.COLUMN_NAMES,
                                            self.get_column_widths(),
                                            self.set_column_order,
                                            tree=self.type_list()==LISTTREE)
        return [columnpage]
