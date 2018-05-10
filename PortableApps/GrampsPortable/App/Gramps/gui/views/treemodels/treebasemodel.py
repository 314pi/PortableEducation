#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2007  Donald N. Allingham
# Copyright (C) 2009       Gary Burton
# Copyright (C) 2009-2011  Nick Hall
# Copyright (C) 2009       Benny Malengier
# Copyright (C) 2011       Tim G L lyons
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
# gui/views/treemodels/treebasemodel.py
# $Id$
#

"""
This module provides the model that is used for all hierarchical treeviews.
"""

#-------------------------------------------------------------------------
#
# Standard python modules
#
#-------------------------------------------------------------------------
from __future__ import with_statement
import time
import locale
from gen.ggettext import gettext as _
import logging

_LOG = logging.getLogger(".gui.treebasemodel")

#-------------------------------------------------------------------------
#
# GTK modules
#
#-------------------------------------------------------------------------
import gtk

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
from Utils import conv_unicode_tosrtkey_ongtk
import gui.widgets.progressdialog as progressdlg
from Lru import LRU
from bisect import bisect_right
from Filters import SearchFilter, ExactSearchFilter

#-------------------------------------------------------------------------
#
# Node
#
#-------------------------------------------------------------------------
class Node(object):
    """
    This class defines an individual node of a tree in the model.  The node
    stores the following data:

    name        Textual description of the node.
    sortkey     A key which defines the sort order of the node.
    ref         Reference to this node in the tree dictionary.
    handle      A Gramps handle.  Can be None if no Gramps object is
                associated with the node.
    parent      id of the parent node.
    prev        Link to the previous sibling via id.
    next        Link to the next sibling via id.

    children    A list of (sortkey, nodeid) tuples for the children of the node.
                This list is always kept sorted.
    """
    __slots__ = ('name', 'sortkey', 'ref', 'handle', 'secondary', 'parent',
                 'prev', 'next', 'children')#, '__weakref__')

    def __init__(self, ref, parent, sortkey, handle, secondary):
        self.name = sortkey
        if sortkey:
            self.sortkey = conv_unicode_tosrtkey_ongtk(sortkey)
        else:
            self.sortkey = None
        self.ref = ref
        self.handle = handle
        self.secondary = secondary
        self.parent = parent
        self.prev = None
        self.next = None
        self.children = []

    def set_handle(self, handle, secondary=False):
        """
        Assign the handle of a Gramps object to this node.
        """
        if not self.handle or handle == None:
            self.handle = handle
            self.secondary = secondary
        else:
            print ('WARNING: Attempt to add handle twice to the node (%s)' %
                    handle)

    def add_child(self, node, nodemap):
        """
        Add a node to the list of children for this node using the id's in
        nodemap.
        """
        nodeid = id(node)
        if len(self.children):
            index = bisect_right(self.children, (node.sortkey, nodeid))
            if index == 0:
                node.prev = None
                next_nodeid = self.children[0][1]
                next_node = nodemap.node(next_nodeid)
                next_node.prev = nodeid
                node.next = next_nodeid
            elif index == len(self.children):
                prev_nodeid = self.children[-1][1]
                prev_node = nodemap.node(prev_nodeid)
                prev_node.next = nodeid
                node.prev = prev_nodeid
                node.next = None
            else:
                prev_nodeid = self.children[index - 1][1]
                next_nodeid = self.children[index][1]
                prev_node = nodemap.node(prev_nodeid)
                next_node = nodemap.node(next_nodeid)
                prev_node.next = nodeid
                next_node.prev = nodeid
                node.prev = prev_nodeid
                node.next = next_nodeid

            self.children.insert(index, (node.sortkey, nodeid))

        else:
            self.children.append((node.sortkey, nodeid))
            
    def remove_child(self, node, nodemap):
        """
        Remove a node from the list of children for this node, using nodemap.
        """
        nodeid = id(node)
        index = bisect_right(self.children, (node.sortkey, nodeid)) - 1
        if not (self.children[index] == (node.sortkey, nodeid)):
            raise ValueError, str(node.name) + \
                        ' not present in self.children: ' + str(self.children)\
                        + ' at index ' + str(index)
        if index == 0:
            if len(self.children) > 1:
                nodemap.node(self.children[index+1][1]).prev = None
        elif index == len(self.children)-1:
            nodemap.node(self.children[index - 1][1]).next = None
        else:
            nodemap.node(self.children[index - 1][1]).next = \
                        self.children[index + 1][1]
            nodemap.node(self.children[index + 1][1]).prev = \
                        self.children[index - 1][1]

        self.children.pop(index)

#-------------------------------------------------------------------------
#
# NodeMap
#
#-------------------------------------------------------------------------
class NodeMap(object):
    """
    Map of id of Node classes to real object
    """
    def __init__(self):
        self.id2node = {}

    def destroy(self):
        """
        Unset all elements that can prevent garbage collection
        """
##        for key, item in self.id2node.iteritems():
##            item.prev = None
##            item.next = None
##            item.parent = None
##            item.children = []
        self.id2node.clear()
    
    def add_node(self, node):
        """
        Add a Node object to the map and return id of this node
        """
        nodeid = id(node)
        self.id2node[nodeid] = node
        return nodeid
    
    def del_node(self, node):
        """
        Remove a Node object from the map and return nodeid
        """
        nodeid = id(node)
        del self.id2node[nodeid]
        return nodeid
    
    def del_nodeid(self, nodeid):
        """
        Remove Node with id nodeid from the map
        """
        del self.id2node[nodeid]

    def node(self, nodeid):
        """
        Obtain the node object from it's id
        """
        return self.id2node[nodeid]

    def clear(self):
        """
        clear the map
        """
        self.id2node.clear()

#-------------------------------------------------------------------------
#
# TreeBaseModel
#
#-------------------------------------------------------------------------
class TreeBaseModel(gtk.GenericTreeModel):
    """
    The base class for all hierarchical treeview models.  The model defines the
    mapping between a unique node and a path. Paths are defined by a tuple.
    The first element is an integer specifying the position in the top
    level of the hierarchy.  The next element relates to the next level
    in the hierarchy.  The number of elements depends on the depth of the
    node within the hierarchy.

    The following data is stored:

    tree        A dictionary of unique identifiers which correspond to nodes in
                the hierarchy.  Each entry is a node object.
    handle2node A dictionary of gramps handles.  Each entry is a node object.
    nodemap     A NodeMap, mapping id's of the nodes to the node objects. Node
                refer to other nodes via id's in a linked list form.
    
    The model obtains data from database as needed and holds a cache of most
    recently used data.
    As iter for generictreemodel, node is used. This will be the handle for 
    database objects.
    
    Creation:
    db      :   the database
    tooltip_column :  column number of tooltip
    search         :  the search that must be shown
    skip           :  values not to show
    scol           :  column on which to sort
    order          :  order of the sort
    sort_map       :  mapping from columns seen on the GUI and the columns 
                      as defined here
    nrgroups       :  maximum number of grouping level, 0 = no group, 
                      1= one group, .... Some optimizations can be for only
                      one group. nrgroups=0 should never be used, as then a 
                      flatbasemodel should be used
    group_can_have_handle :
                      can groups have a handle. If False, this means groups 
                      are only used to group subnodes, not for holding data and
                      showing subnodes
    has_secondary  :  If True, the model contains two Gramps object types.
                      The suffix '2' is appended to variables relating to the
                      secondary object type.
    """

    # LRU cache size
    _CACHE_SIZE = 250
   
    def __init__(self, db, tooltip_column,
                    search=None, skip=set(),
                    scol=0, order=gtk.SORT_ASCENDING, sort_map=None,
                    nrgroups = 1,
                    group_can_have_handle = False,
                    has_secondary=False):
        cput = time.clock()
        gtk.GenericTreeModel.__init__(self)
        #two unused attributes pesent to correspond to flatbasemodel
        self.prev_handle = None
        self.prev_data = None
        
        self.__reverse = (order == gtk.SORT_DESCENDING)
        self.scol = scol
        self.nrgroups = nrgroups
        self.group_can_have_handle = group_can_have_handle
        self.has_secondary = has_secondary
        self.db = db
        
        self._set_base_data()

        # Initialise data structures
        self.tree = {}
        self.nodemap = NodeMap()
        self.handle2node = {}

        self.set_property("leak_references", False)
        #normally sort on first column, so scol=0
        if sort_map:
            #sort_map is the stored order of the columns and if they are
            #enabled or not. We need to store on scol of that map
            self.sort_map = [ f for f in sort_map if f[0]]
            #we need the model col, that corresponds with scol
            col = self.sort_map[scol][1]
            self.sort_func = self.smap[col]
            if self.has_secondary:
                self.sort_func2 = self.smap2[col]
            self.sort_col = col
        else:
            self.sort_func = self.smap[scol]
            if self.has_secondary:
                self.sort_func2 = self.smap2[scol]
            self.sort_col = scol
    
        self._in_build = False
        
        self.lru_data  = LRU(TreeBaseModel._CACHE_SIZE)

        self._tooltip_column = tooltip_column

        self.__total = 0
        self.__displayed = 0

        self.set_search(search)
        if self.has_secondary:
            self.rebuild_data(self.current_filter, self.current_filter2, skip)
        else:
            self.rebuild_data(self.current_filter, skip=skip)

        _LOG.debug(self.__class__.__name__ + ' __init__ ' +
                    str(time.clock() - cput) + ' sec')

    def destroy(self):
        """
        Unset all elements that prevent garbage collection
        """
        self.db = None
        self.sort_func = None
        if self.has_secondary:
            self.sort_func2 = None
        if self.nodemap:
            self.nodemap.destroy()
        self.nodemap = None
        self.rebuild_data = None
        self._build_data = None
        self.search = None
        self.search2 = None
        self.current_filter = None
        self.current_filter2 = None
        self.clear_cache()
        self.lru_data = None

    def _set_base_data(self):
        """
        This method must be overwritten in the inheriting class, setting 
        all needed information
        
        gen_cursor   : func to create cursor to loop over objects in model
        number_items : func to obtain number of items that are shown if all
                        shown
        map     : function to obtain the raw bsddb object datamap
        smap    : the map with functions to obtain sort value based on sort col
        fmap    : the map with functions to obtain value of a row with handle
        """
        self.gen_cursor = None
        self.number_items = None   # function 
        self.map = None
        self.smap = None
        self.fmap = None

        if self.has_secondary:
            self.gen_cursor2 = None
            self.number_items2 = None   # function 
            self.map2 = None
            self.smap2 = None
            self.fmap2 = None

    def displayed(self):
        """
        Return the number of rows displayed.
        """
        return self.__displayed
        
    def total(self):
        """
        Return the total number of rows without a filter or search condition.
        """
        return self.__total

    def tooltip_column(self):
        """
        Return the tooltip column.
        """
        return self._tooltip_column

    def color_column(self):
        """
        Return the color column.
        """
        return None

    def clear_cache(self, handle=None):
        """
        Clear the LRU cache.
        """
        if handle:
            try:
                del self.lru_data[handle]
            except KeyError:
                pass
        else:
            self.lru_data.clear()

    def clear(self):
        """
        Clear the data map.
        """
        #invalidate the iters within gtk
        self.invalidate_iters()
        self.tree.clear()
        self.handle2node.clear()
        self.nodemap.clear()
        #start with creating the new iters
        topnode = Node(None, None, None, None, False)
        self.nodemap.add_node(topnode)
        self.tree[None] = topnode

    def set_search(self, search):
        """
        Change the search function that filters the data in the model. 
        When this method is called, make sure:
        # you call self.rebuild_data() to recalculate what should be seen 
          in the model
        # you reattach the model to the treeview so that the treeview updates
          with the new entries
        """
        if search:
            if search[0] == 1: # Filter
                #following is None if no data given in filter sidebar
                self.search = search[1]
                if self.has_secondary:
                    self.search2 = search[1]
                    _LOG.debug("search2 filter %s %s" % (search[0], search[1]))
                self._build_data = self._rebuild_filter
            elif search[0] == 0: # Search
                if search[1]:
                    # we have search[1] = (index, text_unicode, inversion)
                    col, text, inv = search[1]
                    func = lambda x: self._get_value(x, col, secondary=False) or u""
                    if self.has_secondary:
                        func2 = lambda x: self._get_value(x, col, secondary=True) or u""
                    if search[2]:
                        self.search = ExactSearchFilter(func, text, inv)
                        if self.has_secondary:
                            self.search2 = ExactSearchFilter(func2, text, inv)
                    else:
                        self.search = SearchFilter(func, text, inv)
                        if self.has_secondary:
                            self.search2 = SearchFilter(func2, text, inv)
                else:
                    self.search = None
                    if self.has_secondary:
                        self.search2 = None
                        _LOG.debug("search2 search with no data")
                self._build_data = self._rebuild_search
            else: # Fast filter
                self.search = search[1]
                if self.has_secondary:
                    self.search2 = search[2]
                    _LOG.debug("search2 fast filter")
                self._build_data = self._rebuild_search
        else:
            self.search = None
            if self.has_secondary:
                self.search2 = search[2]
                _LOG.debug("search2 no search parameter")
            self._build_data = self._rebuild_search
            
        self.current_filter = self.search
        if self.has_secondary:
            self.current_filter2 = self.search2

    def rebuild_data(self, data_filter=None, data_filter2=None, skip=[]):
        """
        Rebuild the data map.
        
        When called externally (from listview), data_filter and data_filter2
        should be None; set_search will already have been called to establish
        the filter functions. When called internally (from __init__) both
        data_filter and data_filter2 will have been set from set_search
        """
        cput = time.clock()
        self.clear_cache()
        self._in_build = True

        if not self.db.is_open():
            return

        self.clear()
        if self.has_secondary:
            self._build_data(self.current_filter, self.current_filter2, skip)
        else:
            self._build_data(self.current_filter, None, skip)

        self._in_build = False

        self.current_filter = data_filter
        if self.has_secondary:
            self.current_filter2 = data_filter2

        _LOG.debug(self.__class__.__name__ + ' rebuild_data ' +
                    str(time.clock() - cput) + ' sec')

    def _rebuild_search(self, dfilter, dfilter2, skip):
        """
        Rebuild the data map where a search condition is applied.
        """
        self.__total = 0
        self.__displayed = 0

        items = self.number_items()
        _LOG.debug("rebuild search primary")
        self.__rebuild_search(dfilter, skip, items, 
                              self.gen_cursor, self.add_row)

        if self.has_secondary:
            _LOG.debug("rebuild search secondary")
            items = self.number_items2()
            self.__rebuild_search(dfilter2, skip, items, 
                                  self.gen_cursor2, self.add_row2)

    def __rebuild_search(self, dfilter, skip, items, gen_cursor, add_func):
        """
        Rebuild the data map for a single Gramps object type, where a search 
        condition is applied.
        """
        pmon = progressdlg.ProgressMonitor(progressdlg.GtkProgressDialog, 
                                            popup_time=2)
        status = progressdlg.LongOpStatus(msg=_("Building View"),
                            total_steps=items, interval=items//20, 
                            can_cancel=True)
        pmon.add_op(status)
        with gen_cursor() as cursor:
            for handle, data in cursor:
                status.heartbeat()
                if status.should_cancel():
                    break
                self.__total += 1
                if not (handle in skip or (dfilter and not
                                        dfilter.match(handle, self.db))):
                    _LOG.debug("    add %s %s" % (handle, data))
                    self.__displayed += 1
                    add_func(handle, data)
        if not status.was_cancelled():
            status.end()

    def _rebuild_filter(self, dfilter, dfilter2, skip):
        """
        Rebuild the data map where a filter is applied.
        """
        self.__total = 0
        self.__displayed = 0

        if not self.has_secondary:
            # The tree only has primary data
            items = self.number_items()
            _LOG.debug("rebuild filter primary")
            self.__rebuild_filter(dfilter, skip, items, 
                                  self.gen_cursor, self.map, self.add_row)
        else:
            # The tree has both primary and secondary data. The navigation type
            # (navtype) which governs the filters that are offered, is for the
            # secondary data.
                items = self.number_items2()
                _LOG.debug("rebuild filter secondary")
                self.__rebuild_filter(dfilter2, skip, items, 
                                      self.gen_cursor2, self.map2, self.add_row2)
            
    def __rebuild_filter(self, dfilter, skip, items, gen_cursor, data_map, 
                         add_func):
        """
        Rebuild the data map for a single Gramps object type, where a filter 
        is applied.
        """
        pmon = progressdlg.ProgressMonitor(progressdlg.GtkProgressDialog, 
                                            popup_time=2)
        status = progressdlg.LongOpStatus(msg=_("Building View"),
                              total_steps=3, interval=1)
        pmon.add_op(status)
        status_ppl = progressdlg.LongOpStatus(msg=_("Obtaining all rows"),
                        total_steps=items, interval=items//10)
        pmon.add_op(status_ppl)
        
        self.__total += items

        def beat(key):
            status_ppl.heartbeat()
            return key
        
        with gen_cursor() as cursor:
            handle_list = [beat(key) for key, data in cursor]
        status_ppl.end()
        status.heartbeat()

        if dfilter:
            _LOG.debug("rebuild filter %s" % dfilter)
            _LOG.debug("    list before filter %s" % handle_list)
            status_filter = progressdlg.LongOpStatus(msg=_("Applying filter"),
                        total_steps=items, interval=items//10)
            pmon.add_op(status_filter)
            handle_list = dfilter.apply(self.db, handle_list, 
                                        cb_progress=status_filter.heartbeat)
            _LOG.debug("    list after filter %s" % handle_list)
            status_filter.end()
        status.heartbeat()

        todisplay = len(handle_list)
        status_col = progressdlg.LongOpStatus(msg=_("Constructing column data"),
                total_steps=todisplay, interval=todisplay//10)
        pmon.add_op(status_col)
        for handle in handle_list:
            status_col.heartbeat()
            data = data_map(handle)
            if not handle in skip:
                add_func(handle, data)
                self.__displayed += 1
        status_col.end()
        status.end()
        
    def add_node(self, parent, child, sortkey, handle, add_parent=True,
                 secondary=False):
        """
        Add a node to the map.
        
        parent      The parent node for the child.  None for top level. If
                    this node does not exist, it will be added under the top
                    level if add_parent=True. For performance, if you have
                    added the parent, passing add_parent=False, will skip adding
                    missing parent
        child       A unique ID for the node.
        sortkey     A key by which to sort child nodes of each parent.
        handle      The gramps handle of the object corresponding to the
                    node.  None if the node does not have a handle.
        add_parent  Bool, if True, check if parent is present, if not add the 
                    parent as a top group with no handle
        """
        if add_parent and not (parent in self.tree):
            #add parent to self.tree as a node with no handle, as the first
            #group level
            self.add_node(None, parent, parent, None, add_parent=False)
        if child in self.tree:
            #a node is added that is already present,
            child_node = self.tree[child]
            self._add_dup_node(child_node, parent, child, sortkey, handle,
                               secondary)
        else:
            parent_node = self.tree[parent]
            child_node = Node(child, id(parent_node), sortkey, handle,
                              secondary)
            parent_node.add_child(child_node, self.nodemap)
            self.tree[child] = child_node
            self.nodemap.add_node(child_node)

            if not self._in_build:
                # emit row_inserted signal
                path = self.on_get_path(child_node)
                node = self.get_iter(path)
                self.row_inserted(path, node)
                if handle:
                    self.__total += 1
                    self.__displayed += 1

        if handle:
            self.handle2node[handle] = child_node

    def _add_dup_node(self, node, parent, child, sortkey, handle, secondary):
        """
        How to handle adding a node a second time
        Default: if group nodes can have handles, it is allowed to add it 
            again, and this time setting the handle
        Otherwise, a node should never be added twice!
        """
        if not self.group_can_have_handle:
            print ('WARNING: Attempt to add node twice to the model (%s: %s)' 
                   % (str(parent), str(child)))
            return
        if handle:
            node.set_handle(handle, secondary)
            if not self._in_build:
                self.__total += 1
                self.__displayed += 1

    def remove_node(self, node):
        """
        Remove a node from the map.
        """
        if node.children:
            del self.handle2node[node.handle]
            node.set_handle(None)
            self.__displayed -= 1
            self.__total -= 1
        elif node.parent: # don't remove the hidden root node
            path = self.on_get_path(node)
            self.nodemap.node(node.parent).remove_child(node, self.nodemap)
            del self.tree[node.ref]
            if node.handle is not None:
                del self.handle2node[node.handle]
                self.__displayed -= 1
                self.__total -= 1
            self.nodemap.del_node(node)
            del node
            
            # emit row_deleted signal
            self.row_deleted(path)
        
    def reverse_order(self):
        """
        Reverse the order of the map. This does not signal rows_reordered,
        so to propagate the change to the view, you need to reattach the
        model to the view. 
        """
        self.__reverse = not self.__reverse
        top_node = self.tree[None]
        self._reverse_level(top_node)

    def _reverse_level(self, node):
        """
        Reverse the order of a single level in the map and signal 
        rows_reordered so the view is updated.
        If many changes are done, it is better to detach the model, do the
        changes to reverse the level, and reattach the model, so the view
        does not update for every change signal.
        """
        if node.children:
            rows = range(len(node.children)-1,-1,-1)
            if node.parent is None:
                path = iter = None
            else:
                path = self.on_get_path(node)
                iter = self.get_iter(path)
            self.rows_reordered(path, iter, rows)
            if self.nrgroups > 1:
                for child in node.children:
                    self._reverse_level(self.nodemap.node(child[1]))

    def get_tree_levels(self):
        """
        Return the headings of the levels in the hierarchy.
        """
        raise NotImplementedError
        
    def add_row(self, handle, data):
        """
        Add a row to the model.  In general this will add more then one node by
        using the add_node method.
        """
        raise NotImplementedError

    def add_row_by_handle(self, handle):
        """
        Add a row to the model.
        """
        if self.get_node(handle) is not None:
            return # row already exists
        cput = time.clock()
        data = self.map(handle)
        if data:
            if not self.search or \
                    (self.search and self.search.match(handle, self.db)):
                self.add_row(handle, data)
        else:
            if not self.search2 or \
                    (self.search2 and self.search2.match(handle, self.db)):
                self.add_row2(handle, self.map2(handle))

        _LOG.debug(self.__class__.__name__ + ' add_row_by_handle ' +
                    str(time.clock() - cput) + ' sec')
        _LOG.debug("displayed %d / total: %d" % 
                   (self.__displayed, self.__total))

    def delete_row_by_handle(self, handle):
        """
        Delete a row from the model.
        """
        cput = time.clock()
        node = self.get_node(handle)
        if node is None:
            return # row not currently displayed

        self.clear_cache(handle)
        parent = self.nodemap.node(node.parent)
        self.remove_node(node)
        
        while parent is not None:
            next_parent = parent.parent and self.nodemap.node(parent.parent)
            if not parent.children:
                if parent.handle:
                    # emit row_has_child_toggled signal
                    path = self.on_get_path(parent)
                    node = self.get_iter(path)
                    self.row_has_child_toggled(path, node)
                else:
                    self.remove_node(parent)
            parent = next_parent
            
        _LOG.debug(self.__class__.__name__ + ' delete_row_by_handle ' +
                    str(time.clock() - cput) + ' sec')
        _LOG.debug("displayed %d / total: %d" % 
                   (self.__displayed, self.__total))

    def update_row_by_handle(self, handle):
        """
        Update a row in the model.
        """
        if self.get_node(handle) is None:
            return # row not currently displayed

        self.delete_row_by_handle(handle)
        self.add_row_by_handle(handle)
        
        # If the node hasn't moved, all we need is to call row_changed.
        #self.row_changed(path, node)
        
    def get_handle(self, node):
        """
        Get the gramps handle for a node.  Return None if the node does
        not correspond to a gramps object.
        """
        return node.handle
            
    def get_node(self, handle):
        """
        Get the node for a handle.
        """
        return self.handle2node.get(handle)

    def handle2path(self, handle):
        """
        Obtain from a handle, a path.
        Part of common api with flat/treebasemodel
        """
        return self.on_get_path(self.get_node(handle))

    # The following implement the public interface of gtk.GenericTreeModel

    def on_get_flags(self):
        """
        See gtk.GenericTreeModel
        """
        return gtk.TREE_MODEL_ITERS_PERSIST

    def on_get_n_columns(self):
        """
        Return the number of columns. Must be implemented in the child objects
        See gtk.GenericTreeModel
        """
        raise NotImplementedError

    def on_get_column_type(self, index):
        """
        See gtk.GenericTreeModel
        """
        if index == self._tooltip_column:
            return object
        return str

    def on_get_value(self, nodeid, col):
        """
        See gtk.GenericTreeModel
        """
        #print 'get_value', nodeid, col
        nodeid = id(nodeid)
        node = self.nodemap.node(nodeid)
        if node.handle is None:
            # Header rows dont get the foreground color set
            if col == self.color_column():
                return None

            # Return the node name for the first column
            if col == 0:
                return self.column_header(node)

        else:
            # return values for 'data' row, calling a function
            # according to column_defs table
            return self._get_value(node.handle, col, node.secondary)
            
    def _get_value(self, handle, col, secondary=None):
        """
        Returns the contents of a given column of a gramps object
        """
        if secondary is None:
            raise NotImplementedError
        
        if handle in self.lru_data:
            data = self.lru_data[handle]
        else:
            if not secondary:
                data = self.map(handle)
            else:
                data = self.map2(handle)
            if not self._in_build:
                self.lru_data[handle] = data
                
        if not secondary:
            # None is used to indicate this column has no data
            if self.fmap[col] is None:
                return None
            value = self.fmap[col](data)
        else:
            if self.fmap2[col] is None:
                return None
            value = self.fmap2[col](data)
            
        return value

    def on_get_iter(self, path):
        """
        Returns a node from a given path.
        """
        if not self.tree or not self.tree[None].children:
            return None
        node = self.tree[None]
        pathlist = list(path)
        for index in pathlist:
            _index = (-index - 1) if self.__reverse else index
            node = self.nodemap.node(node.children[_index][1])
        return node
        
    def on_get_path(self, node):
        """
        Returns a path from a given node.
        """
        pathlist = []
        while node.parent is not None:
            parent = self.nodemap.node(node.parent)
            index = -1
            while node is not None:
                # Step backwards
                nodeid = node.next if self.__reverse else node.prev
                node = nodeid and self.nodemap.node(nodeid)
                index += 1
            pathlist.append(index)
            node = parent

        if pathlist is not None:
            pathlist.reverse()
            return tuple(pathlist)
        else:
            return None
            
    def on_iter_next(self, node):
        """
        Get the next node with the same parent as the given node.
        """
        val = node.prev if self.__reverse else node.next
        return val and self.nodemap.node(val)

    def on_iter_children(self, node):
        """
        Get the first child of the given node.
        """
        if node is None:
            node = self.tree[None]
        if node.children:
            return self.nodemap.node(
                        node.children[-1 if self.__reverse else 0][1])
        else:
            return None
        
    def on_iter_has_child(self, node):
        """
        Find if the given node has any children.
        """
        if node is None:
            node = self.tree[None]
        return True if node.children else False

    def on_iter_n_children(self, node):
        """
        Get the number of children of the given node.
        """
        if node is None:
            node = self.tree[None]
        return len(node.children)

    def on_iter_nth_child(self, node, index):
        """
        Get the nth child of the given node.
        """
        if node is None:
            node = self.tree[None]
        if node.children:
            if len(node.children) > index:
                _index = (-index - 1) if self.__reverse else index
                return self.nodemap.node(node.children[_index][1])
            else:
                return None
        else:
            return None

    def on_iter_parent(self, node):
        """
        Get the parent of the given node.
        """
        return node.parent and self.nodemap.node(node.parent)
