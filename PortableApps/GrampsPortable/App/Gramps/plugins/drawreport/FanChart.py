#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2003-2006 Donald N. Allingham
# Copyright (C) 2007-2008 Brian G. Matherly
# Copyright (C) 2010       Jakim Friant
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

#------------------------------------------------------------------------
#
# python modules
#
#------------------------------------------------------------------------
from gen.ggettext import gettext as _
from math import pi, cos, sin, log10

def log2(val):
	"""
	Calculate the log base 2 of a value.
	"""
	return int(log10(val)/log10(2))

#------------------------------------------------------------------------
#
# gramps modules
#
#------------------------------------------------------------------------
from Errors import ReportError
from gen.plug.docgen import (FontStyle, ParagraphStyle, GraphicsStyle,
                             FONT_SANS_SERIF, PARA_ALIGN_CENTER)
from gen.plug.menu import EnumeratedListOption, NumberOption, PersonOption
from gen.plug.report import Report
from gen.plug.report import utils as ReportUtils
from gen.plug.report import MenuReportOptions
import config

#------------------------------------------------------------------------
#
# private constants
#
#------------------------------------------------------------------------
FULL_CIRCLE = 0
HALF_CIRCLE = 1
QUAR_CIRCLE = 2

BACKGROUND_WHITE = 0
BACKGROUND_GEN   = 1

RADIAL_UPRIGHT    = 0
RADIAL_ROUNDABOUT = 1

pt2cm = ReportUtils.pt2cm

cal = config.get('preferences.calendar-format-report')

#------------------------------------------------------------------------
#
# private functions
#
#------------------------------------------------------------------------
def draw_wedge(doc,  style,  centerx,  centery,  radius,  start_angle, 
               end_angle,  short_radius=0):
    """
    Draw a wedge shape.
    """
    while end_angle < start_angle:
        end_angle += 360

    p = []
    
    degreestoradians = pi / 180.0
    radiansdelta = degreestoradians / 2
    sangle = start_angle * degreestoradians
    eangle = end_angle * degreestoradians
    while eangle < sangle:
        eangle = eangle + 2 * pi
    angle = sangle

    if short_radius == 0:
        if (end_angle - start_angle) != 360:
            p.append((centerx, centery))
    else:
        origx = (centerx + cos(angle) * short_radius)
        origy = (centery + sin(angle) * short_radius)
        p.append((origx, origy))
        
    while angle < eangle:
        x = centerx + cos(angle) * radius
        y = centery + sin(angle) * radius
        p.append((x, y))
        angle = angle + radiansdelta
    x = centerx + cos(eangle) * radius
    y = centery + sin(eangle) * radius
    p.append((x, y))

    if short_radius:
        x = centerx + cos(eangle) * short_radius
        y = centery + sin(eangle) * short_radius
        p.append((x, y))

        angle = eangle
        while angle >= sangle:
            x = centerx + cos(angle) * short_radius
            y = centery + sin(angle) * short_radius
            p.append((x, y))
            angle -= radiansdelta
    doc.draw_path(style, p)

    delta = (eangle - sangle) / 2.0
    rad = short_radius + (radius - short_radius) / 2.0

    return ( (centerx + cos(sangle + delta) * rad), 
             (centery + sin(sangle + delta) * rad))

#------------------------------------------------------------------------
#
# FanChart
#
#------------------------------------------------------------------------
class FanChart(Report):

    def __init__(self, database, options, user):
        """
        Create the FanChart object that produces the report.
        
        The arguments are:

        database        - the GRAMPS database instance
        options         - instance of the Options class for this report
        user            - a gen.user.User instance

        This report needs the following parameters (class variables)
        that come in the options class.
        
        maxgen          - Maximum number of generations to include.
        circle          - Draw a full circle, half circle, or quarter circle.
        background      - Background color is generation dependent or white.
        radial          - Print radial texts roundabout or as upright as possible.
        """

        menu = options.menu
        self.max_generations = menu.get_option_by_name('maxgen').get_value()
        self.circle          = menu.get_option_by_name('circle').get_value()
        self.background      = menu.get_option_by_name('background').get_value()
        self.radial          = menu.get_option_by_name('radial').get_value()
        pid                  = menu.get_option_by_name('pid').get_value()
        self.center_person = database.get_person_from_gramps_id(pid)
        if (self.center_person == None) :
            raise ReportError(_("Person %s is not in the Database") % pid )

        self.background_style = []
        self.text_style = []
        for i in range (0, self.max_generations+1):
            if self.background == BACKGROUND_WHITE:
                background_style_name = 'background_style_white'
            else:
                background_style_name = 'background_style' + '%d' % i
            self.background_style.append(background_style_name)
            text_style_name = 'text_style' + '%d' % i
            self.text_style.append(text_style_name)
        
        self.calendar = 0

        Report.__init__(self, database, options, user)

        self.height = 0
        self.map = [None] * 2**self.max_generations
        self.text = {}

    def apply_filter(self,person_handle,index):
        """traverse the ancestors recursively until either the end
        of a line is found, or until we reach the maximum number of 
        generations that we want to deal with"""
        
        if (not person_handle) or (index >= 2**self.max_generations):
            return
        self.map[index-1] = person_handle
        self.text[index-1] = self.get_info(person_handle, log2(index))

        person = self.database.get_person_from_handle(person_handle)
        family_handle = person.get_main_parents_family_handle()
        if family_handle:
            family = self.database.get_family_from_handle(family_handle)
            self.apply_filter(family.get_father_handle(),index*2)
            self.apply_filter(family.get_mother_handle(),(index*2)+1)


    def write_report(self):

        self.doc.start_page()
        
        self.apply_filter(self.center_person.get_handle(),1)
        n = self.center_person.get_primary_name().get_regular_name()

        if self.circle == FULL_CIRCLE:
            max_angle = 360.0
            start_angle = 90
            max_circular = 5
            x = self.doc.get_usable_width() / 2.0
            y = self.doc.get_usable_height() / 2.0
            min_xy = min (x, y)

        elif self.circle == HALF_CIRCLE:
            max_angle = 180.0
            start_angle = 180
            max_circular = 3
            x = (self.doc.get_usable_width()/2.0)
            y = self.doc.get_usable_height()
            min_xy = min (x, y)

        else:  # quarter circle
            max_angle = 90.0
            start_angle = 270
            max_circular = 2
            x = 0
            y = self.doc.get_usable_height()
            min_xy = min (self.doc.get_usable_width(), y)

        if self.circle == FULL_CIRCLE or self.circle == QUAR_CIRCLE:
            # adjust only if full circle or 1/4 circle in landscape mode
            if self.doc.get_usable_height() <= self.doc.get_usable_width():
                # Should be in Landscape now
                style_sheet = self.doc.get_style_sheet()
                fontsize = pt2cm(style_sheet.get_paragraph_style('FC-Title').get_font().get_size())
                # y is vertical distance to center of circle, move center down 1 fontsize
                y += fontsize
                # min_XY is the diameter of the circle, subtract two fontsize
                # so we dont draw outside bottom of the paper
                min_xy = min(min_xy,y-2*fontsize)
        if self.max_generations > max_circular:
            block_size = min_xy / (self.max_generations * 2 - max_circular)
        else:
            block_size = min_xy / self.max_generations
        text = _("%(generations)d Generation Fan Chart for %(person)s" ) % \
                 { 'generations' : self.max_generations, 'person' : n }
        self.doc.center_text ('t', text, self.doc.get_usable_width() / 2, 0)

        for generation in range (0, min (max_circular, self.max_generations)):
            self.draw_circular (x, y, start_angle, max_angle, block_size, generation)
        for generation in range (max_circular, self.max_generations):
            self.draw_radial (x, y, start_angle, max_angle, block_size, generation)

        self.doc.end_page()


    def get_info(self,person_handle,generation):
        person = self.database.get_person_from_handle(person_handle)
        pn = person.get_primary_name()
        self.calendar = config.get('preferences.calendar-format-report')

        birth_ref = person.get_birth_ref()
        if birth_ref:
            birth = self.database.get_event_from_handle(birth_ref.ref)
            b = birth.get_date_object().to_calendar(self.calendar).get_year()
            if b == 0:
                b = ""
        else:
            b = ""

        death_ref = person.get_death_ref()
        if death_ref:
            death = self.database.get_event_from_handle(death_ref.ref)
            d = death.get_date_object().to_calendar(self.calendar).get_year()
            if d == 0:
                d = ""
        else:
            d = ""
        if b and d:
            val = "%s - %s" % (str(b),str(d))
        elif b:
            val = "* %s" % (str(b))
        elif d:
            val = "+ %s" % (str(d))
        else:
            val = ""

        if generation == 7:
            if (pn.get_first_name() != "") and (pn.get_surname() != ""):
                name = pn.get_first_name() + " " + pn.get_surname()
            else:
                name = pn.get_first_name() + pn.get_surname()

            if self.circle == FULL_CIRCLE:
                return [ name, val ]
            elif self.circle == HALF_CIRCLE:
                return [ name, val ]
            else:
                if (name != "") and (val != ""):
                    string = name + ", " + val
                else:
                    string = name + val
                return [string]
        elif generation == 6:
            if self.circle == FULL_CIRCLE:
                return [ pn.get_first_name(), pn.get_surname(), val ]
            elif self.circle == HALF_CIRCLE:
                return [ pn.get_first_name(), pn.get_surname(), val ]
            else:
                if (pn.get_first_name() != "") and (pn.get_surname() != ""):
                    name = pn.get_first_name() + " " + pn.get_surname()
                else:
                    name = pn.get_first_name() + pn.get_surname()
                return [ name, val ]
        else:
            return [ pn.get_first_name(), pn.get_surname(), val ]


    def draw_circular(self, x, y, start_angle, max_angle, size, generation):
        segments = 2**generation
        delta = max_angle / segments
        end_angle = start_angle
        text_angle = start_angle - 270 + (delta / 2.0)
        rad1 = size * generation
        rad2 = size * (generation + 1)
        background_style = self.background_style[generation]
        text_style = self.text_style[generation]

        for index in range(segments - 1, 2*segments - 1):
            start_angle = end_angle
            end_angle = start_angle + delta
            (xc,yc) = draw_wedge(self.doc, background_style, x, y, rad2,
                                 start_angle, end_angle, rad1)
            if self.map[index]:
                if (generation == 0) and self.circle == FULL_CIRCLE:
                    yc = y
                self.doc.rotate_text(text_style, self.text[index],
                                     xc, yc, text_angle)
            text_angle += delta


    def draw_radial(self, x, y, start_angle, max_angle, size, generation):
        segments = 2**generation
        delta = max_angle / segments
        end_angle = start_angle
        text_angle = start_angle - delta / 2.0
        background_style = self.background_style[generation]
        text_style = self.text_style[generation]
        if self.circle == FULL_CIRCLE:
            rad1 = size * ((generation * 2) - 5)
            rad2 = size * ((generation * 2) - 3)
        elif self.circle == HALF_CIRCLE:
            rad1 = size * ((generation * 2) - 3)
            rad2 = size * ((generation * 2) - 1)
        else:  # quarter circle
            rad1 = size * ((generation * 2) - 2)
            rad2 = size * (generation * 2)
            
        for index in range(segments - 1, 2*segments - 1):
            start_angle = end_angle
            end_angle = start_angle + delta
            (xc,yc) = draw_wedge(self.doc,background_style, x, y, rad2,
                                 start_angle, end_angle, rad1)
            text_angle += delta
            if self.map[index]:
                if self.radial == RADIAL_UPRIGHT and (start_angle >= 90) and (start_angle < 270):
                    self.doc.rotate_text(text_style, self.text[index],
                                         xc, yc, text_angle + 180)
                else:
                    self.doc.rotate_text(text_style, self.text[index],
                                         xc, yc, text_angle)

#------------------------------------------------------------------------
#
# 
#
#------------------------------------------------------------------------
class FanChartOptions(MenuReportOptions):

    def __init__(self, name, dbase):
        self.MAX_GENERATIONS = 8
        
        MenuReportOptions.__init__(self, name, dbase)
        
    def add_menu_options(self, menu):
        """
        Add options to the menu for the fan chart.
        """
        category_name = _("Report Options")
    
        pid = PersonOption(_("Center Person"))
        pid.set_help(_("The center person for the report"))
        menu.add_option(category_name, "pid", pid)
            
        max_gen = NumberOption(_("Generations"),5,1,self.MAX_GENERATIONS)
        max_gen.set_help(_("The number of generations to include in the report"))
        menu.add_option(category_name,"maxgen",max_gen)
        
        circle = EnumeratedListOption(_('Type of graph'),HALF_CIRCLE)
        circle.add_item(FULL_CIRCLE,_('full circle'))
        circle.add_item(HALF_CIRCLE,_('half circle'))
        circle.add_item(QUAR_CIRCLE,_('quarter circle'))
        circle.set_help( _("The form of the graph: full circle, half circle,"
                           " or quarter circle."))
        menu.add_option(category_name,"circle",circle)
        
        background = EnumeratedListOption(_('Background color'),BACKGROUND_GEN)
        background.add_item(BACKGROUND_WHITE,_('white'))
        background.add_item(BACKGROUND_GEN,_('generation dependent'))
        background.set_help(_("Background color is either white or generation"
                              " dependent"))
        menu.add_option(category_name,"background",background)
        
        radial = EnumeratedListOption( _('Orientation of radial texts'),
                                       RADIAL_UPRIGHT )
        radial.add_item(RADIAL_UPRIGHT,_('upright'))
        radial.add_item(RADIAL_ROUNDABOUT,_('roundabout'))
        radial.set_help(_("Print radial texts upright or roundabout"))
        menu.add_option(category_name,"radial",radial)

    def make_default_style(self,default_style):
        """Make the default output style for the Fan Chart report."""
        BACKGROUND_COLORS = [
                             (255, 63,  0), 
                             (255,175, 15), 
                             (255,223, 87), 
                             (255,255,111),
                             (159,255,159), 
                             (111,215,255), 
                             ( 79,151,255), 
                             (231, 23,255)   
                            ]

        #Paragraph Styles
        f = FontStyle()
        f.set_size(20)
        f.set_bold(1)
        f.set_type_face(FONT_SANS_SERIF)
        p = ParagraphStyle()
        p.set_font(f)
        p.set_alignment(PARA_ALIGN_CENTER)
        p.set_description(_('The style used for the title.'))
        default_style.add_paragraph_style("FC-Title",p)

        f = FontStyle()
        f.set_size(9)
        f.set_type_face(FONT_SANS_SERIF)
        p = ParagraphStyle()
        p.set_font(f)
        p.set_alignment(PARA_ALIGN_CENTER)
        p.set_description(_('The basic style used for the text display.'))
        default_style.add_paragraph_style("text_style", p)
            
        # GraphicsStyles
        g = GraphicsStyle()
        g.set_paragraph_style('FC-Title')
        g.set_line_width(0)
        default_style.add_draw_style("t",g)

        for i in range (0, self.MAX_GENERATIONS):
            g = GraphicsStyle()
            g.set_fill_color(BACKGROUND_COLORS[i])
            g.set_paragraph_style('FC-Normal')
            background_style_name = 'background_style' + '%d' % i
            default_style.add_draw_style(background_style_name,g)

            g = GraphicsStyle()
            g.set_fill_color(BACKGROUND_COLORS[i])
            g.set_paragraph_style('text_style')
            g.set_line_width(0)
            text_style_name = 'text_style' + '%d' % i
            default_style.add_draw_style(text_style_name,g)
            
        g = GraphicsStyle()
        g.set_fill_color((255,255,255))
        g.set_paragraph_style('FC-Normal')
        default_style.add_draw_style('background_style_white',g)
