#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2008  Zsolt Foldvari
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

"Define text formatting tag types."

#------------------------------------------------------------------------
#
# Python modules
#
#------------------------------------------------------------------------
from gen.ggettext import gettext as _

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
from gen.lib.grampstype import GrampsType

#-------------------------------------------------------------------------
#
# StyledTextTagType class
#
#-------------------------------------------------------------------------
class StyledTextTagType(GrampsType):
    """Text formatting tag type definition.
    
    Here we only define new class variables. For details see :class:`~gen.lib.grampstype.GrampsType`.
    
    """
    NONE_TYPE = -1
    BOLD = 0
    ITALIC = 1
    UNDERLINE = 2
    FONTFACE = 3
    FONTSIZE = 4
    FONTCOLOR = 5
    HIGHLIGHT = 6
    SUPERSCRIPT = 7
    LINK = 8
    
    _CUSTOM = NONE_TYPE
    _DEFAULT = NONE_TYPE
    
    _DATAMAP = [
        (BOLD, _("Bold"), "bold"),
        (ITALIC, _("Italic"), "italic"),
        (UNDERLINE, _("Underline"), "underline"),
        (FONTFACE, _("Fontface"), "fontface"),
        (FONTSIZE, _("Fontsize"), "fontsize"),
        (FONTCOLOR, _("Fontcolor"), "fontcolor"),
        (HIGHLIGHT, _("Highlight"), "highlight"),
        (SUPERSCRIPT, _("Superscript"), "superscript"),
        (LINK, _("Link"), "link"),
    ]

    STYLE_TYPE = {
        BOLD: bool,
        ITALIC: bool,
        UNDERLINE: bool,
        FONTCOLOR: str,
        HIGHLIGHT: str,
        FONTFACE: str,
        FONTSIZE: int,
        SUPERSCRIPT: bool,
        LINK: str,
    }
    
    STYLE_DEFAULT = {
        BOLD: False,
        ITALIC: False,
        UNDERLINE: False,
        FONTCOLOR: '#000000',
        HIGHLIGHT: '#FFFFFF',
        FONTFACE: 'Sans',
        FONTSIZE: 10,
        SUPERSCRIPT: False,
        LINK: '',
    }

    def __init__(self, value=None):
        GrampsType.__init__(self, value)
