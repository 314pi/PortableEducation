# -*- python -*-
# -*- coding: utf-8 -*-
#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2011  Serge Noiraud
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
Geography for places
"""
#-------------------------------------------------------------------------
#
# Python modules
#
#-------------------------------------------------------------------------
from gen.ggettext import gettext as _
import os
import sys
import time
import urlparse
import const
import operator
import locale
from gtk.keysyms import Tab as KEY_TAB
import socket
import gtk

#-------------------------------------------------------------------------
#
# set up logging
#
#-------------------------------------------------------------------------
import logging
_LOG = logging.getLogger("GeoGraphy.geoplaces")

#-------------------------------------------------------------------------
#
# Gramps Modules
#
#-------------------------------------------------------------------------
import gen.lib
import Utils
import config
import Errors
from gen.display.name import displayer as _nd
from PlaceUtils import conv_lat_lon
from gui.views.pageview import PageView
from gui.editors import EditPlace
from gui.selectors.selectplace import SelectPlace
from Filters.SideBar import PlaceSidebarFilter
from gui.views.navigationview import NavigationView
import Bookmarks
from Utils import navigation_label
from maps.geography import GeoGraphyView

#-------------------------------------------------------------------------
#
# Constants
#
#-------------------------------------------------------------------------

_UI_DEF = '''\
<ui>
<menubar name="MenuBar">
<menu action="GoMenu">
  <placeholder name="CommonGo">
    <menuitem action="Back"/>
    <menuitem action="Forward"/>
    <separator/>
  </placeholder>
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
</toolbar>
</ui>
'''

#-------------------------------------------------------------------------
#
# GeoView
#
#-------------------------------------------------------------------------
class GeoPlaces(GeoGraphyView):
    """
    The view used to render places map.
    """

    def __init__(self, pdata, dbstate, uistate, nav_group=0):
        GeoGraphyView.__init__(self, _('Places map'),
                                      pdata, dbstate, uistate, 
                                      dbstate.db.get_place_bookmarks(), 
                                      Bookmarks.PlaceBookmarks,
                                      nav_group)
        self.dbstate = dbstate
        self.uistate = uistate
        self.place_list = []
        self.place_without_coordinates = []
        self.minlat = self.maxlat = self.minlon = self.maxlon = 0.0
        self.minyear = 9999
        self.maxyear = 0
        self.nbplaces = 0
        self.nbmarkers = 0
        self.sort = []
        self.generic_filter = None
        self.additional_uis.append(self.additional_ui())
        self.no_show_places_in_status_bar = False

    def get_title(self):
        """
        Used to set the titlebar in the configuration window.
        """
        return _('GeoPlaces')

    def get_stock(self):
        """
        Returns the name of the stock icon to use for the display.
        This assumes that this icon has already been registered 
        as a stock icon.
        """
        return 'geo-show-place'
    
    def get_viewtype_stock(self):
        """Type of view in category
        """
        return 'geo-show-place'

    def additional_ui(self):
        """
        Specifies the UIManager XML code that defines the menus and buttons
        associated with the interface.
        """
        return _UI_DEF

    def navigation_type(self):
        """
        Indicates the navigation type. Navigation type can be the string
        name of any of the primary objects.
        """
        return 'Place'

    def get_bookmarks(self):
        """
        Return the bookmark object
        """
        return self.dbstate.db.get_place_bookmarks()

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

    def goto_handle(self, handle=None):
        """
        Rebuild the tree with the given places handle as the root.
        """
        if handle:
            self.change_active(handle)
            self._createmap(handle)
        self.uistate.modify_statusbar(self.dbstate)

    def show_all_places(self, menu, event, lat, lon):
        """
        Ask to show all places.
        """
        self._createmap(None)

    def build_tree(self):
        """
        This is called by the parent class when the view becomes visible. Since
        all handling of visibility is now in rebuild_trees, see that for more
        information.
        """
        active = self.uistate.get_active('Place')
        if active:
            self._createmap(active)
        else:
            self._createmap(None)

    def _create_one_place(self,place):
        """
        Create one entry for one place with a lat/lon.
        """
        if place is None:
            return
        descr = place.get_title()
        longitude = place.get_longitude()
        latitude = place.get_latitude()
        latitude, longitude = conv_lat_lon(latitude, longitude, "D.D8")
        # place.get_longitude and place.get_latitude return
        # one string. We have coordinates when the two values
        # contains non null string.
        if ( longitude and latitude ):
            self._append_to_places_list(descr, None, "",
                                        latitude, longitude,
                                        None, None,
                                        gen.lib.EventType.UNKNOWN,
                                        None, # person.gramps_id
                                        place.gramps_id,
                                        None, # event.gramps_id
                                        None # family.gramps_id
                                       )
        else:
            self._append_to_places_without_coord(place.gramps_id, descr)

    def _createmap(self,place_x):
        """
        Create all markers for each people's event in the database which has 
        a lat/lon.
        """
        dbstate = self.dbstate
        self.cal = config.get('preferences.calendar-format-report')
        self.place_list = []
        self.place_without_coordinates = []
        self.minlat = 0.0
        self.maxlat = 0.0
        self.minlon = 0.0
        self.maxlon = 0.0
        self.minyear = 9999
        self.maxyear = 0
        self.without = 0
        self.no_show_places_in_status_bar = False
        latitude = ""
        longitude = ""
        # base "villes de france" : 38101 places :
        # createmap : 8'50"; create_markers : 1'23"
        # base "villes de france" : 38101 places :
        # createmap : 8'50"; create_markers : 0'07" with pixbuf optimization
        _LOG.debug("%s" % time.strftime("start createmap : "
                   "%a %d %b %Y %H:%M:%S", time.gmtime()))
        if self.generic_filter:
            place_list = self.generic_filter.apply(dbstate.db)
            for place_handle in place_list:
                place = dbstate.db.get_place_from_handle(place_handle)
                self._create_one_place(place)
        else:
            if place_x is None:
                places_handle = dbstate.db.iter_place_handles()
                for place_hdl in places_handle:
                    place = dbstate.db.get_place_from_handle(place_hdl)
                    self._create_one_place(place)
            else:
                place = dbstate.db.get_place_from_handle(place_x)
                self._create_one_place(place)
        _LOG.debug("%s" % time.strftime(" stop createmap and\nbegin sort : "
                   "%a %d %b %Y %H:%M:%S", time.gmtime()))
        self.sort = sorted(self.place_list,
                           key=operator.itemgetter(0)
                          )
        _LOG.debug("%s" % time.strftime("  end sort : "
                   "%a %d %b %Y %H:%M:%S", time.gmtime()))
        if self.nbmarkers > 500 : # performance issue. Is it the good value ?
            self.no_show_places_in_status_bar = True
        self._create_markers()
        _LOG.debug("%s" % time.strftime("  end create_markers : "
                   "%a %d %b %Y %H:%M:%S", time.gmtime()))

    def bubble_message(self, event, lat, lon, marks):
        menu = gtk.Menu()
        menu.set_title("places")
        message = ""
        prevmark = None
        for mark in marks:
            if message != "":
                add_item = gtk.MenuItem(message)
                add_item.show()
                menu.append(add_item)
                itemoption = gtk.Menu()
                itemoption.set_title(message)
                itemoption.show()
                add_item.set_submenu(itemoption)
                modify = gtk.MenuItem(_("Edit Place"))
                modify.show()
                modify.connect("activate", self.edit_place,
                               event, lat, lon, prevmark)
                itemoption.append(modify)
                center = gtk.MenuItem(_("Center on this place"))
                center.show()
                center.connect("activate", self.center_here,
                               event, lat, lon, prevmark)
                itemoption.append(center)
            message = "%s" % mark[0]
            prevmark = mark
        add_item = gtk.MenuItem(message)
        add_item.show()
        menu.append(add_item)
        itemoption = gtk.Menu()
        itemoption.set_title(message)
        itemoption.show()
        add_item.set_submenu(itemoption)
        modify = gtk.MenuItem(_("Edit Place"))
        modify.show()
        modify.connect("activate", self.edit_place, event, lat, lon, prevmark)
        itemoption.append(modify)
        center = gtk.MenuItem(_("Center on this place"))
        center.show()
        center.connect("activate", self.center_here, event, lat, lon, prevmark)
        itemoption.append(center)
        menu.popup(None, None, None, 0, event.time)
        return 1

    def add_specific_menu(self, menu, event, lat, lon): 
        """ 
        Add specific entry to the navigation menu.
        """ 
        add_item = gtk.MenuItem()
        add_item.show()
        menu.append(add_item)
        add_item = gtk.MenuItem(_("Show all places"))
        add_item.connect("activate", self.show_all_places, event, lat , lon)
        add_item.show()
        menu.append(add_item)
        add_item = gtk.MenuItem(_("Centering on Place"))
        add_item.show()
        menu.append(add_item)
        itemoption = gtk.Menu()
        itemoption.set_title(_("Centering on Place"))
        itemoption.show()
        add_item.set_submenu(itemoption)
        oldplace = ""
        for mark in self.sort:
            if mark[0] != oldplace:
                oldplace = mark[0]
                modify = gtk.MenuItem(mark[0])
                modify.show()
                modify.connect("activate", self.goto_place, float(mark[3]), float(mark[4]))
                itemoption.append(modify)

    def goto_place(self, obj, lat, lon):
        """
        Center the map on latitude, longitude.
        """
        self.set_center(None, None, lat, lon)

    def get_default_gramplets(self):
        """
        Define the default gramplets for the sidebar and bottombar.
        """
        return (("Place Filter",),
                ())
