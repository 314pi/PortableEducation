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

"""
An override to allow easy multiselections.
"""

import gtk

#-------------------------------------------------------------------------
#
# MultiTreeView class
#
#-------------------------------------------------------------------------
class MultiTreeView(gtk.TreeView):
    '''
    TreeView that captures mouse events to make drag and drop work properly
    '''
    def __init__(self):
        super(MultiTreeView, self).__init__()
        self.connect('button_press_event', self.on_button_press)
        self.connect('button_release_event', self.on_button_release)
        self.connect('key_press_event', self.key_press_event)
        self.defer_select = False

    __grid_lines_remove_vertical = {
        gtk.TREE_VIEW_GRID_LINES_NONE : gtk.TREE_VIEW_GRID_LINES_NONE,
        gtk.TREE_VIEW_GRID_LINES_HORIZONTAL : gtk.TREE_VIEW_GRID_LINES_HORIZONTAL,
        gtk.TREE_VIEW_GRID_LINES_VERTICAL : gtk.TREE_VIEW_GRID_LINES_NONE,
        gtk.TREE_VIEW_GRID_LINES_BOTH : gtk.TREE_VIEW_GRID_LINES_HORIZONTAL
    }
    def set_grid_lines(self, grid_lines):
        if self.get_direction() == gtk.TEXT_DIR_RTL:
            # Work around a gtk RTL bug, see #6871
            # On post-gramps34 branches should also check for gtk version <(3,8),
            # but this is always true here on gramps34!
            grid_lines = MultiTreeView.__grid_lines_remove_vertical[grid_lines]
        super(MultiTreeView, self).set_grid_lines(grid_lines)

    def key_press_event(self, widget, event):
        if event.type == gtk.gdk.KEY_PRESS:
            if event.keyval == gtk.keysyms.Delete:
                model, paths = self.get_selection().get_selected_rows()
                # reverse, to delete from the end
                paths.sort(key=lambda x:-x[0])
                for path in paths:
                    try:
                        node = model.get_iter(path)
                    except:
                        node = None
                    if node:
                        model.remove(node)
                return True

    def on_button_press(self, widget, event):
        # Here we intercept mouse clicks on selected items so that we can
        # drag multiple items without the click selecting only one
        target = self.get_path_at_pos(int(event.x), int(event.y))
        if (target 
            and event.type == gtk.gdk.BUTTON_PRESS
            and not (event.state & (gtk.gdk.CONTROL_MASK|gtk.gdk.SHIFT_MASK))
            and self.get_selection().path_is_selected(target[0])):
            # disable selection
            self.get_selection().set_select_function(lambda *ignore: False)
            self.defer_select = target[0]

    def on_button_release(self, widget, event):
        # re-enable selection
        self.get_selection().set_select_function(lambda *ignore: True)
        
        target = self.get_path_at_pos(int(event.x), int(event.y))
        if (self.defer_select and target 
            and self.defer_select == target[0]
            and not (event.x==0 and event.y==0)): # certain drag and drop
            self.set_cursor(target[0], target[1], False)
            
        self.defer_select=False

