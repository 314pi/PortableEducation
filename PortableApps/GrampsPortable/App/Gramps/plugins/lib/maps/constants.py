#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2010 Serge Noiraud
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

"Geography constants"

#-------------------------------------------------------------------------
#
# standard python modules
#
#-------------------------------------------------------------------------
from gen.ggettext import gettext as _
import gen.lib
import os
import const
import osmgpsmap

#-------------------------------------------------------------------------
#
# Constants
#
#-------------------------------------------------------------------------
GEOGRAPHY_PATH = os.path.join(const.HOME_DIR, "maps")

ICONS = {
    gen.lib.EventType.BIRTH                : 'gramps-geo-birth',
    gen.lib.EventType.DEATH                : 'gramps-geo-death',
    gen.lib.EventType.MARRIAGE             : 'gramps-geo-marriage',
}

# map providers
OPENSTREETMAP           = 1
OPENSTREETMAP_RENDERER  = 2
OPENAERIALMAP           = 3
MAPS_FOR_FREE           = 4
GOOGLE_STREET           = 5
GOOGLE_SATELLITE        = 6
GOOGLE_HYBRID           = 7
VIRTUAL_EARTH_STREET    = 8
VIRTUAL_EARTH_SATELLITE = 9
VIRTUAL_EARTH_HYBRID    = 10
YAHOO_STREET            = 11
YAHOO_SATELLITE         = 12
YAHOO_HYBRID            = 13

tiles_path = {
    OPENSTREETMAP           : "openstreetmap",
    OPENSTREETMAP_RENDERER  : "openstreetmaprenderer",
    OPENAERIALMAP           : "openaerialmap",
    MAPS_FOR_FREE           : "mapsforfree",
    GOOGLE_STREET           : "googlestreet",
    GOOGLE_SATELLITE        : "googlesat",
    GOOGLE_HYBRID           : "googlehybrid",
    VIRTUAL_EARTH_STREET    : "virtualearthstreet",
    VIRTUAL_EARTH_SATELLITE : "virtualearthsat",
    VIRTUAL_EARTH_HYBRID    : "virtualearthhybrid",
    YAHOO_STREET            : "yahoostreet",
    YAHOO_SATELLITE         : "yahoosat",
    YAHOO_HYBRID            : "yahoohybrid",
}

map_title = {
    OPENSTREETMAP           : "OpenStreetMap",
    OPENSTREETMAP_RENDERER  : "OpenStreetMap renderer",
    OPENAERIALMAP           : "OpenAerialMap",
    MAPS_FOR_FREE           : "Maps For Free",
    GOOGLE_STREET           : "Google street",
    GOOGLE_SATELLITE        : "Google sat",
    GOOGLE_HYBRID           : "Google hybrid",
    VIRTUAL_EARTH_STREET    : "Virtualearth street",
    VIRTUAL_EARTH_SATELLITE : "Virtualearth sat",
    VIRTUAL_EARTH_HYBRID    : "Virtualearth hybrid",
    YAHOO_STREET            : "Yahoo street",
    YAHOO_SATELLITE         : "Yahoo sat",
    YAHOO_HYBRID            : "Yahoo hybrid",
}

map_type = {
    OPENSTREETMAP           : osmgpsmap.SOURCE_OPENSTREETMAP,
    OPENSTREETMAP_RENDERER  : osmgpsmap.SOURCE_OPENSTREETMAP_RENDERER,
    OPENAERIALMAP           : osmgpsmap.SOURCE_OPENAERIALMAP,
    MAPS_FOR_FREE           : osmgpsmap.SOURCE_MAPS_FOR_FREE,
    GOOGLE_STREET           : osmgpsmap.SOURCE_GOOGLE_STREET,
    GOOGLE_SATELLITE        : osmgpsmap.SOURCE_GOOGLE_SATELLITE,
    GOOGLE_HYBRID           : osmgpsmap.SOURCE_GOOGLE_HYBRID,
    VIRTUAL_EARTH_STREET    : osmgpsmap.SOURCE_VIRTUAL_EARTH_STREET,
    VIRTUAL_EARTH_SATELLITE : osmgpsmap.SOURCE_VIRTUAL_EARTH_SATELLITE,
    VIRTUAL_EARTH_HYBRID    : osmgpsmap.SOURCE_VIRTUAL_EARTH_HYBRID,
    YAHOO_STREET            : osmgpsmap.SOURCE_YAHOO_STREET,
    YAHOO_SATELLITE         : osmgpsmap.SOURCE_YAHOO_SATELLITE,
    YAHOO_HYBRID            : osmgpsmap.SOURCE_YAHOO_HYBRID,
}

