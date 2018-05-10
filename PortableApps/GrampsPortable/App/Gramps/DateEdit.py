#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2002-2006  Donald N. Allingham
# Copyright (C) 2009       Douglas S. Blank
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
Date editing module for GRAMPS. 

The DateEdit.DateEdit provides visual feedback to the user 
to indicate if the associated GtkEntry box contains a valid date.
Red means that the date is not valid, and will be viewed as a text string
instead of a date.

The DateEdit.DateEditor provides a dialog in which the date can be 
unambiguously built using UI controls such as menus and spin buttons.
"""

#-------------------------------------------------------------------------
#
# Python modules
#
#-------------------------------------------------------------------------


#-------------------------------------------------------------------------
#
# set up logging
#
#-------------------------------------------------------------------------
import logging
LOG = logging.getLogger(".DateEdit")

#-------------------------------------------------------------------------
#
# GNOME modules
#
#-------------------------------------------------------------------------
import gtk

#-------------------------------------------------------------------------
#
# gramps modules
#
#-------------------------------------------------------------------------
from gen.ggettext import sgettext as _
from gen.lib.date import Date, DateError, NextYear
import DateHandler
import const
import GrampsDisplay
import ManagedWindow
from Errors import ValidationError
from glade import Glade

#-------------------------------------------------------------------------
#
# Constants
#
#-------------------------------------------------------------------------
MOD_TEXT = ( 
    (Date.MOD_NONE       , _('Regular')),
    (Date.MOD_BEFORE     , _('Before')),
    (Date.MOD_AFTER      , _('After')),
    (Date.MOD_ABOUT      , _('About')),
    (Date.MOD_RANGE      , _('Range')),
    (Date.MOD_SPAN       , _('Span')),
    (Date.MOD_TEXTONLY   , _('Text only')) )

QUAL_TEXT = (
    (Date.QUAL_NONE,       _('Regular')), 
    (Date.QUAL_ESTIMATED,  _('Estimated')), 
    (Date.QUAL_CALCULATED, _('Calculated')) )

CAL_TO_MONTHS_NAMES = { 
    Date.CAL_GREGORIAN  : DateHandler.displayer.short_months,
    Date.CAL_JULIAN     : DateHandler.displayer.short_months,
    Date.CAL_HEBREW     : DateHandler.displayer.hebrew,
    Date.CAL_FRENCH     : DateHandler.displayer.french,
    Date.CAL_PERSIAN    : DateHandler.displayer.persian,
    Date.CAL_ISLAMIC    : DateHandler.displayer.islamic,
    Date.CAL_SWEDISH    : DateHandler.displayer.swedish }

WIKI_HELP_PAGE = '%s_-_Entering_and_Editing_Data:_Detailed_-_part_1' % const.URL_MANUAL_PAGE
WIKI_HELP_SEC = _('manual|Editing_Dates')

#-------------------------------------------------------------------------
#
# DateEdit
#
#-------------------------------------------------------------------------
class DateEdit(object):
    """Class that associates a pixmap with a text widget, providing visual
    feedback that indicates if the text widget contains a valid date"""

    def __init__(self, date_obj, text_obj, button_obj, uistate, track):
        """
        Create a connection between the date_obj, text_obj and the pixmap_obj.
        Assigns callbacks to parse and change date when the text
        in text_obj is changed, and to invoke Date Editor when the LED
        button_obj is pressed. 
        """
        self.uistate = uistate
        self.track = track
        self.date_obj = date_obj
        self.text_obj = text_obj
        self.button_obj = button_obj

        image = gtk.Image()
        image.set_from_stock('gramps-date-edit', gtk.ICON_SIZE_BUTTON)
        self.button_obj.set_image(image)
        self.button_obj.set_relief(gtk.RELIEF_NORMAL)
        self.pixmap_obj = button_obj.get_child()
        
        self.text_obj.connect('validate', self.validate)
        self.text_obj.connect('content-changed', self.set_date)
        self.button_obj.connect('clicked', self.invoke_date_editor)
        
        self.text_obj.set_text(DateHandler.displayer.display(self.date_obj))
        self.text_obj.validate()
        
    def set_date(self, widget):
        """
        Parse date from text entry to date object
        """
        date = DateHandler.parser.parse(unicode(self.text_obj.get_text()))
        self.date_obj.copy(date)
        
    def validate(self, widget, data):
        """
        Validate current date in text entry
        """
        # if text could not be parsed it is assumed invalid
        if self.date_obj.get_modifier() == Date.MOD_TEXTONLY:
            return ValidationError(_('Bad Date'))
        elif (self.date_obj.to_calendar(calendar_name=Date.CAL_GREGORIAN) >>
              NextYear()):
            return ValidationError(_('Date more than one year in the future'))

    def invoke_date_editor(self, obj):
        """
        Invokes Date Editor dialog when the user clicks the Calendar button.
        If date was in fact built, sets the date_obj to the newly built
        date.
        """
        date_dialog = DateEditorDialog(self.date_obj, self.uistate, self.track)
        the_date = date_dialog.return_date
        self.update_after_editor(the_date)

    def update_after_editor(self, date_obj):
        """
        Update text entry and validate it
        """
        if date_obj:
            # first we set the text entry, that emits 'content-changed'
            # signal thus the date object gets updated too
            self.text_obj.set_text(DateHandler.displayer.display(date_obj))
            self.text_obj.validate()
        
#-------------------------------------------------------------------------
#
# DateEditorDialog
#
#-------------------------------------------------------------------------
class DateEditorDialog(ManagedWindow.ManagedWindow):
    """
    Dialog allowing to build the date precisely, to correct possible 
    limitations of parsing and/or underlying structure of Date.
    """

    def __init__(self, date, uistate, track):
        """
        Initiate and display the dialog.
        """
        ManagedWindow.ManagedWindow.__init__(self, uistate, track, self)
        
        # Create self.date as a copy of the given Date object.
        self.date = Date(date)
        
        self.top = Glade()

        self.set_window(
            self.top.toplevel,
            self.top.get_object('title'),
            _('Date selection'))            
            
        self.statusbar = self.top.get_object('statusbar')

        self.ok_button = self.top.get_object('ok_button')
        self.calendar_box = self.top.get_object('calendar_box')
        for name in Date.ui_calendar_names:
            self.calendar_box.get_model().append([name])

        self.calendar_box.set_active(self.date.get_calendar())
        self.calendar_box.connect('changed', self.switch_calendar)

        self.quality_box = self.top.get_object('quality_box')
        for item_number in range(len(QUAL_TEXT)):
            self.quality_box.append_text(QUAL_TEXT[item_number][1])
            if self.date.get_quality() == QUAL_TEXT[item_number][0]:
                self.quality_box.set_active(item_number)

        self.type_box = self.top.get_object('type_box')
        for item_number in range(len(MOD_TEXT)):
            self.type_box.append_text(MOD_TEXT[item_number][1])
            if self.date.get_modifier() == MOD_TEXT[item_number][0]:
                self.type_box.set_active(item_number)
        self.type_box.connect('changed', self.switch_type)

        self.start_month_box = self.top.get_object('start_month_box')
        self.stop_month_box = self.top.get_object('stop_month_box')
        month_names = CAL_TO_MONTHS_NAMES[self.date.get_calendar()]
        for name in month_names:
            self.start_month_box.append_text(name)
            self.stop_month_box.append_text(name)
        self.start_month_box.set_active(self.date.get_month())
        self.stop_month_box.set_active(self.date.get_stop_month())
        
        self.start_day = self.top.get_object('start_day')
        self.start_day.set_value(self.date.get_day())
        self.start_year = self.top.get_object('start_year')
        self.start_year.set_value(self.date.get_year())

        self.stop_day = self.top.get_object('stop_day')
        self.stop_day.set_value(self.date.get_stop_day())
        self.stop_year = self.top.get_object('stop_year')
        self.stop_year.set_value(self.date.get_stop_year())
        
        self.dual_dated = self.top.get_object('dualdated')
        self.new_year = self.top.get_object('newyear')
        self.new_year.set_text(self.date.newyear_to_str())

        # Disable second date controls if not compound date
        if not self.date.is_compound():
            self.stop_day.set_sensitive(0)
            self.stop_month_box.set_sensitive(0)
            self.stop_year.set_sensitive(0)

        # Disable the rest of controls if a text-only date
        if self.date.get_modifier() == Date.MOD_TEXTONLY:
            self.start_day.set_sensitive(0)
            self.start_month_box.set_sensitive(0)
            self.start_year.set_sensitive(0)
            self.calendar_box.set_sensitive(0)
            self.quality_box.set_sensitive(0)
            self.dual_dated.set_sensitive(0)
            self.new_year.set_sensitive(0)

        self.text_entry = self.top.get_object('date_text_entry')
        self.text_entry.set_text(self.date.get_text())

        if self.date.get_slash():
            self.dual_dated.set_active(1)
            self.calendar_box.set_sensitive(0)
            self.calendar_box.set_active(Date.CAL_JULIAN)
        self.dual_dated.connect('toggled', self.switch_dual_dated)

        # The dialog is modal -- since dates don't have names, we don't
        # want to have several open dialogs, since then the user will
        # loose track of which is which. Much like opening files.
        
        self.validated_date = self.return_date = None

        for o in self.top.get_objects():
            try:
                if o != self.ok_button:
                    o.connect_after('changed', self.revalidate)
            except TypeError:
                pass # some of them don't support the signal, ignore them...
        self.revalidate()
        self.show()

        while True:
            response = self.window.run()
            if response == gtk.RESPONSE_HELP:
                GrampsDisplay.help(webpage=WIKI_HELP_PAGE,
                                   section=WIKI_HELP_SEC)
            elif response == gtk.RESPONSE_DELETE_EVENT:
                break
            else:
                if response == gtk.RESPONSE_OK:
                    # if the user pressed OK/enter while inside an edit field,
                    # e.g., the year,
                    # build_date_from_ui won't pick up the new text in the
                    # run of revalidate that allowed the OK!
                    if not self.revalidate():
                        continue
                    self.return_date = Date()
                    self.return_date.copy(self.validated_date)
                self.close()
                break

    def revalidate(self, obj = None):
        """
        If anything changed, revalidate the date and
        enable/disable the "OK" button based on the result.
        """
        (the_quality, the_modifier, the_calendar, the_value, 
         the_text, the_newyear) = self.build_date_from_ui()
        LOG.debug("revalidate: {0} changed, value: {1}".format(
            obj, the_value))
        d = Date(self.date)
        if not self.ok_button.get_sensitive():
            self.statusbar.pop(1)
        try:
            d.set(
                quality=the_quality,
                modifier=the_modifier,
                calendar=the_calendar,
                value=the_value,
                text=the_text,
                newyear=the_newyear)
            # didn't throw yet?
            self.validated_date = d
            LOG.debug("validated_date set to: {0}".format(d.dateval))
            self.ok_button.set_sensitive(1)
            self.calendar_box.set_sensitive(1)
            return True
        except DateError as e: 
            self.ok_button.set_sensitive(0)
            self.calendar_box.set_sensitive(0)
            self.statusbar.push(1, 
                    _("Correct the date or switch from `{cur_mode}' to `{text_mode}'"
                        ).format(
                            cur_mode = MOD_TEXT[self.type_box.get_active()][1],
                            text_mode = MOD_TEXT[-1][1]))
            return False

    def build_menu_names(self, obj):
        """
        Define the menu entry for the ManagedWindows
        """
        return (_("Date selection"), None)

    def build_date_from_ui(self):
        """
        Collect information from the UI controls and return 
        5-tuple of (quality,modifier,calendar,value,text) 
        """
        # It is important to not set date based on these controls. 
        # For example, changing the caledar makes the date inconsistent
        # until the callback of the calendar menu is finished. 
        # We need to be able to use this function from that callback,
        # so here we just report on the state of all widgets, without
        # actually modifying the date yet.
        
        modifier = MOD_TEXT[self.type_box.get_active()][0]
        text = self.text_entry.get_text()

        if modifier == Date.MOD_TEXTONLY:
            return (Date.QUAL_NONE, Date.MOD_TEXTONLY, Date.CAL_GREGORIAN,
                    Date.EMPTY,text, Date.NEWYEAR_JAN1)

        quality = QUAL_TEXT[self.quality_box.get_active()][0]

        if modifier in (Date.MOD_RANGE, Date.MOD_SPAN):
            value = (
                self.start_day.get_value_as_int(),
                self.start_month_box.get_active(),
                self.start_year.get_value_as_int(),
                self.dual_dated.get_active(),
                self.stop_day.get_value_as_int(),
                self.stop_month_box.get_active(),
                self.stop_year.get_value_as_int(),
                self.dual_dated.get_active())
        else:
            value = (
                self.start_day.get_value_as_int(),
                self.start_month_box.get_active(),
                self.start_year.get_value_as_int(),
                self.dual_dated.get_active())
        calendar = self.calendar_box.get_active()
        newyear = Date.newyear_to_code(self.new_year.get_text())
        return (quality, modifier, calendar, value, text, newyear)

    def switch_type(self, obj):
        """
        Disable/enable various date controls depending on the date 
        type selected via the menu.
        """

        the_modifier = MOD_TEXT[self.type_box.get_active()][0]
        
        # Disable/enable second date controls based on whether
        # the type allows compound dates
        if the_modifier in (Date.MOD_RANGE, Date.MOD_SPAN):
            stop_date_sensitivity = 1
        else:
            stop_date_sensitivity = 0
        self.stop_day.set_sensitive(stop_date_sensitivity)
        self.stop_month_box.set_sensitive(stop_date_sensitivity)
        self.stop_year.set_sensitive(stop_date_sensitivity)

        # Disable/enable the rest of the controls if the type is text-only.
        date_sensitivity = not the_modifier == Date.MOD_TEXTONLY
        self.start_day.set_sensitive(date_sensitivity)
        self.start_month_box.set_sensitive(date_sensitivity)
        self.start_year.set_sensitive(date_sensitivity)
        self.calendar_box.set_sensitive(date_sensitivity)
        self.quality_box.set_sensitive(date_sensitivity)
        self.dual_dated.set_sensitive(date_sensitivity)
        self.new_year.set_sensitive(date_sensitivity)

    def switch_dual_dated(self, obj):
        """
        Changed whether this is a dual dated year, or not.
        Dual dated years are represented in the Julian calendar
        so that the day/months don't changed in the Text representation.
        """
        if self.dual_dated.get_active():
            self.calendar_box.set_active(Date.CAL_JULIAN)
            self.calendar_box.set_sensitive(0)
        else:
            self.calendar_box.set_sensitive(1)

    def switch_calendar(self, obj):
        """
        Change month names and convert the date based on the calendar 
        selected via the menu.
        """
        
        old_cal = self.date.get_calendar()
        new_cal = self.calendar_box.get_active()
        LOG.debug(">>>switch_calendar: {0} changed, {1} -> {2}".format(
            obj, old_cal, new_cal))

        (the_quality, the_modifier, the_calendar, 
         the_value, the_text, the_newyear) = self.build_date_from_ui()
        try:
            self.date.set(
                    quality=the_quality,
                    modifier=the_modifier,
                    calendar=old_cal,
                    value=the_value,
                    text=the_text,
                    newyear=the_newyear)
        except DateError:
            pass
        else:
            if not self.date.is_empty():
                self.date.convert_calendar(new_cal)
        
        self.start_month_box.get_model().clear()
        self.stop_month_box.get_model().clear()
        month_names = CAL_TO_MONTHS_NAMES[new_cal]
        for name in month_names:
            self.start_month_box.append_text(name)
            self.stop_month_box.append_text(name)

        self.start_day.set_value(self.date.get_day())
        self.start_month_box.set_active(self.date.get_month())
        self.start_year.set_value(self.date.get_year())
        self.stop_day.set_value(self.date.get_stop_day())
        self.stop_month_box.set_active(self.date.get_stop_month())
        self.stop_year.set_value(self.date.get_stop_year())
        LOG.debug("<<<switch_calendar: {0} changed, {1} -> {2}".format(
            obj, old_cal, new_cal))
