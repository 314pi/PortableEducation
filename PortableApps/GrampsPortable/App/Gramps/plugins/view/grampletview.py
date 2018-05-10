#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2007  Donald N. Allingham
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
GrampletView interface.
"""

#-------------------------------------------------------------------------
#
# Python modules
#
#-------------------------------------------------------------------------
import gtk

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
from gui.views.pageview import PageView
from gen.ggettext import gettext as _
from gui.widgets.grampletpane import GrampletPane

class GrampletView(PageView): 
    """
    GrampletView interface
    """

    def __init__(self, pdata, dbstate, uistate):
        """
        Create a GrampletView, with the current dbstate and uistate
        """
        PageView.__init__(self, _('Gramplets'), pdata, dbstate, uistate)
        self.ui_def = '''<ui>
         <popup name="GrampletPopup">
            <menuitem action="AddGramplet"/>
            <menuitem action="RestoreGramplet"/>
          </popup>
        </ui>'''

    def build_interface(self):
        """
        Builds the container widget for the interface.
        Returns a gtk container widget.
        """
        top = self.build_widget()
        top.show_all()
        return top

    def build_widget(self):
        """
        Builds the container widget for the interface. Must be overridden by the
        the base class. Returns a gtk container widget.
        """
        # load the user's gramplets and set columns, etc
        self.widget = GrampletPane("Gramplets_grampletview_gramplets", self,
                            self.dbstate, self.uistate)
        return self.widget

    def get_stock(self):
        """
        Return image associated with the view, which is used for the 
        icon for the button.
        """
        return 'gramps-gramplet'
    
    def get_viewtype_stock(self):
        """Type of view in category
        """
        return 'gramps-gramplet'

    def define_actions(self):
        """
        Defines the UIManager actions.
        """
        self._add_action("AddGramplet", gtk.STOCK_ADD, _("Add a gramplet"))
        self._add_action("RestoreGramplet", None, _("Restore a gramplet"))

    def set_inactive(self):
        self.active = False
        self.widget.set_inactive()

    def set_active(self):
        self.active = True
        self.widget.set_active()

    def on_delete(self):
        self.widget.on_delete()
        self._config.save()

    def can_configure(self):
        """
        See :class:`~gui.views.pageview.PageView 
        :return: bool
        """
        return self.widget.can_configure()

    def _get_configure_page_funcs(self):
        """
        Return a list of functions that create gtk elements to use in the 
        notebook pages of the Configure dialog
        
        :return: list of functions
        """
        return self.widget._get_configure_page_funcs()

    def navigation_type(self):
        """
        Return a description of the specific nav_type items that are
        associated with this view. None means that there is no specific
        type.
        """
        return None
