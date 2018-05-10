#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2010       Craig J. Anderson
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
Provide the SubstKeywords class that will replace keywords in a passed
string with information about the person/marriage/spouse. For sample:

foo = SubstKeywords(database, person_handle)
print foo.replace_and_clean(['$n was born on $b.'])

Will return a value such as:

Mary Smith was born on 3/28/1923.
"""

#------------------------------------------------------------------------
#
# Gramps modules
#
#------------------------------------------------------------------------
from gen.display.name import displayer as name_displayer
import DateHandler
import gen.lib
from gen.utils import get_birth_or_fallback, get_death_or_fallback

#------------------------------------------------------------------------
#
# Local constants
#
#------------------------------------------------------------------------
class TextTypes():
    """Four enumerations that are used to for the four main parts of a string.
    
    and used for states.  Separator is not used in states.
    text   -> remove or display
    remove -> display
    """
    separator, text, remove, display = range(4)
TXT = TextTypes()


#------------------------------------------------------------------------
#
# Formatting classes
#
#------------------------------------------------------------------------
class GenericFormat(object):
    """A Generic parsing class.  Will be subclassed by specific format strings
    """
    
    def __init__(self, string_in):
        self.string_in = string_in
    
    def _default_format(self, item):
        """ The default format if there is no format string """
        pass
    
    def is_blank(self, item):
        """ if the information is not known (item is None), remove the format
        string information from the input string if any.
        """
        if item is None:
            self.string_in.remove_start_end("(", ")")
            return True
        return False
    
    def generic_format(self, item, code, uppr, function):
        """the main parsing engine.
        
        Needed are the following:  the input string
        code - List of one character (string) codes (all lowercase)
        uppr - list of one character (string) codes that can be uppercased
            each needs to have a lowercase equivalent in code
        function - list of functions.
        there is a one to one relationship with character codes and functions.
        """
        if self.string_in.this != "(":
            return self._default_format(item)
        self.string_in.step()
        
        main = VarStringMain(TXT.remove)
        separator = SeparatorParse(self.string_in)
        #code given in args
        #function given in args
        
        while self.string_in.this and self.string_in.this != ")":
            #Check to see if _in.this is in code
            to_upper = False
            if uppr.find(self.string_in.this) != -1:
                #and the result should be uppercased.
                to_upper = True
                where = code.find(self.string_in.this.lower())
            else:
                where = code.find(self.string_in.this)
            if where != -1:
                self.string_in.step()
                tmp = function[where]()
                if to_upper:
                    tmp = tmp.upper()
                main.add_variable(tmp)
            elif separator.is_a():
                separator.parse_format(main)
            else:
                self.string_in.parse_format(main)
        
        if self.string_in.this == ")":
            self.string_in.step()
        
        if main.the_state == TXT.remove:
            return ""
        else:
            return main.get_string()[1]

#------------------------------------------------------------------------
# Name Format strings
#------------------------------------------------------------------------
class NameFormat(GenericFormat):
    """ The name format class.
    If no format string, the name is displayed as per preference options
    otherwise, parse through a format string and put the name parts in
    """

    def get_name(self, person):
        """ A helper method for retrieving the person's name """
        if person:
            return person.get_primary_name()
        return None

    def _default_format(self, name):
        """ display the name as set in preferences """
        return name_displayer.sorted_name(name)
    
    def parse_format(self, name):
        """ Parse the name """
        if self.is_blank(name):
            return ""
        
        def common():
            """ return the common name of the person """
            return (name.get_call_name() or
                     name.get_first_name().split(' ')[0])

        code  = "tfcnxslg"
        upper = code.upper()
        function = [name.get_title,           #t
                    name.get_first_name,      #f
                    name.get_call_name,       #c
                    name.get_nick_name,       #n
                    common,                   #x
                    name.get_suffix,          #s
                    name.get_surname,         #l
                    name.get_family_nick_name #g
                    ]
        
        return self.generic_format(name, code, upper, function)

#------------------------------------------------------------------------
# Date Format strings
#------------------------------------------------------------------------
class DateFormat(GenericFormat):
    """ The date format class.
    If no format string, the date is displayed as per preference options
    otherwise, parse through a format string and put the date parts in
    """

    def get_date(self, event):
        """ A helper method for retrieving a date from an event """
        if event:
            return event.get_date_object()
        return None

    def _default_format(self, date):
        return DateHandler.displayer.display(date)
    
    def __count_chars(self, char, max_amount):
        """ count the year/month/day codes """
        count = 1  #already have seen/passed one
        while count < max_amount and self.string_in.this == char:
            self.string_in.step()
            count = count +1
        return count
    
    def parse_format(self, date):
        """ Parse the name """
    
        if self.is_blank(date):
            return ""
        
        def year():
            """  The year part only """
            year = unicode(date.get_year())
            count = self.__count_chars("y", 4)
            if year == "0":
                return ""
            
            if count == 1:  #found 'y'
                if len(year) == 1:
                    return year
                elif year[-2] == "0":
                    return year[-1]
                else:
                    return year[-2:]
            elif count == 2:  #found 'yy'
                tmp = "0" + year
                return tmp[-2:]
            elif count == 3:  #found 'yyy'
                if len(year) > 2:
                    return year
                else:
                    tmp = "00" + year
                    return tmp[-3:]
            else:  #count == 4  #found 'yyyy'
                tmp = "000" + year
                return tmp[-4:]


        def month(char_found = "m"):
            """  The month part only """
            month = unicode(date.get_month())
            count = self.__count_chars(char_found, 4)
            if month == "0":
                return ""
                
            if count == 1:
                return month
            elif count == 2:  #found 'mm'
                tmp = "0" + month
                return tmp[-2:]
            elif count == 3:   #found 'mmm'
                return DateHandler.displayer.short_months[int(month)]
            else: #found 'mmmm'
                return DateHandler.displayer.long_months[int(month)]
        
        def month_up():
            return month("M").upper()
            

        def day():
            """  The day part only """
            day = unicode(date.get_day())
            count = self.__count_chars("d", 2)
            if day == "0":  #0 means not defined!
                return ""
            
            if count == 1: #found 'd'
                return day
            else:  #found 'dd'
                tmp = "0" + day
                return tmp[-2:]


        def modifier():
            #ui_mods taken from date.py def lookup_modifier(self, modifier):
            ui_mods = ["", _("before"), _("after"), _("about"), 
                       "", "", ""]
            return ui_mods[date.get_modifier()].capitalize()

        
        code  = "ymdMo"
        upper = "O"
        function = [year, month, day, month_up, modifier]
        
        return self.generic_format(date, code, upper, function)

#------------------------------------------------------------------------
# Place Format strings
#------------------------------------------------------------------------
class PlaceFormat(GenericFormat):
    """ The place format class.
    If no format string, the place is displayed as per preference options
    otherwise, parse through a format string and put the place parts in
    """

    def get_place(self, database, event):
        """ A helper method for retrieving a place from an event """
        if event:
            bplace_handle = event.get_place_handle()
            if bplace_handle:
                return database.get_place_from_handle(bplace_handle)
        return None

    def _default_format(self, place):
        return place.get_title()
    
    def parse_format(self, place):
        """ Parse the place """

        if self.is_blank(place):
            return ""
        
        code = "elcuspnitxy"
        upper = code.upper()
        function = [place.get_main_location().get_street,
                    place.get_main_location().get_locality,
                    place.get_main_location().get_city,
                    place.get_main_location().get_county,
                    place.get_main_location().get_state,
                    place.get_main_location().get_postal_code,
                    place.get_main_location().get_country,
                    place.get_main_location().get_parish,
                    place.get_title,
                    place.get_longitude,
                    place.get_latitude
                    ]
        
        return self.generic_format(place, code, upper, function)

#------------------------------------------------------------------------
# Event Format strings
#------------------------------------------------------------------------
class EventFormat(GenericFormat):
    """ The event format class.
    If no format string, the event description is displayed
    otherwise, parse through the format string and put in the parts
        dates and places can have their own format strings
    """

    def __init__(self, database, _in):
        self.database = database
        GenericFormat.__init__(self, _in)
        
    def _default_format(self, event):
        if event is None:
            return ""
        else:
            return event.get_description()
    
    def __empty_format(self):
        """ clear out a sub format string """
        self.string_in.remove_start_end("(", ")")
        return ""
    
    def __empty_attrib(self):
        """ clear out an attribute name """
        self.string_in.remove_start_end("[", "]")
        return ""

    def parse_format(self, event):
        """ Parse the event format string.
        let the date or place classes handle any sub-format strings """

        if self.is_blank(event):
            return ""
        
        def format_date():
            """ start formatting a date in this event """
            date_format = DateFormat(self.string_in)
            return date_format.parse_format(date_format.get_date(event))
            
        def format_place():
            """ start formatting a place in this event """
            place_format = PlaceFormat(self.string_in)
            place = place_format.get_place(self.database, event)
            return place_format.parse_format(place)
                
        def format_attrib():
            """ Get the name and then get the attributes value """
            #Event's Atribute
            attrib_parse = AttributeParse(self.string_in)
            self.string_in.step()
            name = attrib_parse.get_name()
            if name:
                return attrib_parse.get_attribute(event.get_attribute_list(),
                                                  name)
            else:
                return ""
            
        code = "ndDia"
        upper = ""
        function = [event.get_description,
                    format_date,
                    format_place,
                    event.get_gramps_id,
                    format_attrib
                    ]
        
        return self.generic_format(event, code, upper, function)

    def parse_empty(self):
        """ remove the format string """
        
        code = "dDa"
        function = [self.__empty_format, self.__empty_format,
                    self.__empty_attrib]
        
        return self.generic_format(None, code, "", function)
        
#------------------------------------------------------------------------
#
# ConsumableString - Input string class
#
#------------------------------------------------------------------------
class ConsumableString(object):
    """
    A simple string implementation with extras to help with parsing.
    
    This will contain the string to be parsed.  or string in.
    There will only be one of these for each processed line.
    """
    def __init__(self, string):
        self.__this_string = string
        self.__setup()
    
    def __setup(self):
        """ update class attributes this and next """
        if len(self.__this_string) > 0:
            self.this = self.__this_string[0]
        else:
            self.this = None
        if len(self.__this_string) > 1:
            self.next = self.__this_string[1]
        else:
            self.next = None
    
    def step(self):
        """ remove the first char from the string """
        self.__this_string = self.__this_string[1:]
        self.__setup()
        return self.this
    
    def step2(self):
        """ remove the first two chars from the string """
        self.__this_string = self.__this_string[2:]
        self.__setup()
        return self.this
    
    def remove_start_end(self, start, end):
        """ Removes a start, end block from the string if there """
        if self.this == start:
            self.text_to_next(end)
    
    def __get_a_char_of_text(self):
        """ Removes one char of TEXT from the string and returns it. """
        if self.this == "\\":
            if self.next == None:
                rtrn = "\\"
            else:
                rtrn = self.next
            self.step2()
        else:
            rtrn = self.this
            self.step()
        return rtrn 
    
    def text_to_next(self, char):
        """ remove a format strings from here """
        new_str = ""
        while self.this is not None and self.this != char:
            new_str += self.__get_a_char_of_text()
        if self.this == char:
            self.step()
        return new_str
    
    def is_a(self):
        return True
    
    def parse_format(self, _out):
        rtrn = self.__get_a_char_of_text()

        if rtrn:
            _out.add_text(rtrn)
            

#------------------------------------------------------------------------
#
# Output string classes
#
#------------------------------------------------------------------------
#------------------------------------------------------------------------
# VarStringBase classes
#------------------------------------------------------------------------
class VarStringBase(object):
    """
    A list to hold tuple object (integer from TextTypes, string)
    
    This will contain the string that will be displayed.  or string out.
    it is used for groups and format strings.
    """
    def __init__(self, init_state):
        self.the_string = []
        self.the_state = init_state
    
    def add_text(self, text):
        pass
    
    def add_display(self, text):
        pass
    
    def add_remove(self):
        pass
    
    def add_separator(self, text):
        pass
    
    def get_string(self):
        """ Get the final displayed string """
        if self.the_string == []:
            return self.the_state, ""
        return self.the_state, self.the_string[0][1]
        
    def _last_type(self):
        """ get the type of the last item added to the list """
        if self.the_string != []:
            return self.the_string[-1][0]
        else:
            return None

#------------------------------------------------------------------------
# VarStringMain classes
#------------------------------------------------------------------------
class VarStringMain(VarStringBase):
    """
    The main level string out (Not within a group or format string).
    
    This group differs from the others as it starts with
     TXT.text as the state.  (format strings will use TXT.remove)
     and everything is __combine[d] properly
    """
    def __init__(self, start_state = TXT.text):
        VarStringBase.__init__(self, start_state)
        self.level = self
    
    def merge(self, acquisition):
        """ Merge the content of acquisition into this place. """
        if acquisition.the_state != TXT.display:
            return
        
        if acquisition.the_state > self.the_state:
            self.the_state = acquisition.the_state
            
        for (adding, txt_to_add) in acquisition.the_string:
            if adding == TXT.text:
                self.add_text(txt_to_add)
            elif adding == TXT.display:
                self.add_display(txt_to_add)
            elif adding == TXT.remove:
                self.add_remove()
            elif adding == TXT.separator:
                self.add_separator(txt_to_add)
    
    def __add(self, text):
        """  Add a new piece of text to the existing (at end). or add new """
        if self.the_string == []:
            self.the_string.append((self.the_state, text))
        else:
            self.the_string[-1] = \
                (TXT.text, self.the_string[-1][1] + text)
        
    def __combine(self, text):
        """ combine the last two elements on the list and add text to it """
        new_str = self.the_string[-1][1]
        self.the_string.pop()
        self.__add(new_str + text)
        
    def add_text(self, text):
        """ a new piece of text to be added.
        remove a (non displaying) variable at the end if there is one.
        or accept a separator (at the end) if there is one.
        """
        to_the_left = self._last_type()
        if to_the_left == TXT.remove:
            self.the_string.pop()
            to_the_left = self._last_type()
        
        if to_the_left is None:
            self.the_string.append((TXT.text, text))
        elif to_the_left == TXT.text:
            self.the_string[-1] = \
                (TXT.text, self.the_string[-1][1] + text)
        elif to_the_left == TXT.separator:
            self.__combine(text)

        
    def add_separator(self, text):
        """ a new separator to be added.
        remove a (non displaying) variable to the end it there is one
        and drop me
        remove an existing separator at the end (if there)
        or add me to the end.
        """
        to_the_left = self._last_type()
        if to_the_left == TXT.remove:
            self.the_string.pop()
            return
        
        if self.the_string == []:
            return
        elif to_the_left == TXT.text:
            self.the_string.append((TXT.separator, text))
        elif to_the_left == TXT.separator:
            self.the_string.pop()
            self.the_string.append((TXT.separator, text))
        
    def add_display(self, text):
        """ add text to the end and update the state """
        self.the_state = TXT.display
        self.add_text(text)
        
    def add_remove(self):
        """ work with an empty variable.  either:
            bump up the state if needed
            remove an empty variable on the end if one
            remove a separator at the end if one and myself and stop
            and add a empty variable to the end.
        """
        if self.the_state != TXT.display:
            self.the_state = TXT.remove
        
        to_the_left = self._last_type()
        if to_the_left == TXT.separator:
            self.the_string.pop()
            return
        elif to_the_left == TXT.remove:
            self.the_string.pop()
        
        self.the_string.append((TXT.remove, ""))
    
    def add_variable(self, text):
        """ A helper function to either call:
            add_remove if the text string is blank
            otherwise add_display
        """
        if text == "":
            self.add_remove()
        else:
            self.add_display(text)
    
#------------------------------------------------------------------------
# VarStringSecond classes
#------------------------------------------------------------------------
class VarStringSecond(VarStringBase):
    """The non-main level string out (within a group or format string).
    
    This group differs from main as it starts with
     TXT.remove as the state
     and everything is simply added to the end of a list.
     states are still updated properly
     it will be _combine(d) in the main level appropriately.
    """
    def __init__(self, start_state = TXT.remove):
        VarStringBase.__init__(self, start_state)
    
    def merge(self, acquisition):
        """ Merge the content of acquisition into this place. """
        if acquisition.the_state != TXT.display:
            return
        
        if acquisition.the_state > self.the_state:
            self.the_state = acquisition.the_state
            
        self.the_string.extend(acquisition.the_string)
    
    def add_text(self, text):
        to_the_left = self._last_type()
        if to_the_left is None:
            self.the_string.append((TXT.text, text))
        elif to_the_left == TXT.text:
            self.the_string[-1] = \
                (TXT.text, self.the_string[-1][1] + text)
        else:
            self.the_string.append((TXT.text, text))
        
    def add_separator(self, text):
        self.the_string.append((TXT.separator, text))
        
    def add_display(self, text):
        self.the_state = TXT.display
        self.add_text(text)
        
    def add_remove(self):
        """ add a 'remove' tag in the list """
        if self.the_state != TXT.display:
            self.the_state = TXT.remove
        self.the_string.append((TXT.remove, ""))
    
    def add_variable(self, text):
        if text == "":
            self.add_remove()
        else:
            self.add_display(text)
    

#------------------------------------------------------------------------
#
# Parsers
#
#------------------------------------------------------------------------
#------------------------------------------------------------------------
# level_parse
#------------------------------------------------------------------------
class LevelParse(object):
    """The main string out class.  This class does two things
    
    provides text handling of {} and adds/removes/combines levels as needed.
    provides outside methods add_... to the last (innermost) level.
    """

    def __init__(self, consumer_in):
        self._in = consumer_in
        if consumer_in.this == "{":
            self.__levels = [VarStringMain(TXT.remove)]
        else:
            self.__levels = [VarStringMain(TXT.display)]
        self.level = self.__levels[-1]
    
    def is_a(self):
        return self._in.this == "{" or self._in.this == "}"
    
    def __can_combine(self):
        return len(self.__levels) > 1
    
    def __combine_level(self):
        """ If the last (inner most) level is not to be removed,
        combine it to the left"""
        if not self.__can_combine():
            return
        self.__levels[-2].merge(self.__levels[-1])
        self.__levels.pop()
        self.level = self.__levels[-1]
    
    def combine_all(self):
        while len(self.__levels) > 1:
            self.__combine_level()
            
    def add_text(self, text):
        self.level.add_text(text)
        
    def add_separator(self, text):
        self.level.add_separator(text)
        
    def add_display(self, text):
        self.level.add_display(text)
        
    def add_remove(self):
        self.level.add_remove()
    
    def add_variable(self, text):
        self.level.add_variable(text)

    def get_string(self):
        return self.level.get_string()
    
    def parse_format(self, _out):  #_out is not used
        """ Parse the text to see what to do
        Only handles {}
        """
        if self._in.this == "{":
            self.__levels.append(VarStringSecond())
            self.level = self.__levels[-1]
        
        elif self._in.this == "}":
            if self.__can_combine():
                self.__combine_level()
            else:
                self.level.add_text("}")
        self._in.step()
        
#------------------------------------------------------------------------
# SeparatorParse
#------------------------------------------------------------------------
class SeparatorParse(object):
    """ parse out a separator """
    def __init__(self, consumer_in):
        self._in = consumer_in
        
    def is_a(self):
        return self._in.this == "<"

    def parse_format(self, _out):
        """ get the text and pass it to string_out.separator """
        self._in.step()
        _out.add_separator(
            self._in.text_to_next(">"))
        
#------------------------------------------------------------------------
# AttributeParse
#------------------------------------------------------------------------
class AttributeParse(object):
    """  Parse attributes """
    
    def __init__(self, consumer_in):
        self._in = consumer_in
        
    def get_name(self):
        """ Gets a name inside a [] block """
        if self._in.this != "[":
            return ""
        self._in.step()
        return self._in.text_to_next("]")
        
    def get_attribute(self, attrib_list, attrib_name):
        """ Get an attribute by name """
        if attrib_name == "":
            return ""
        for attr in attrib_list:
            if str(attr.get_type()) == attrib_name:
                return str(attr.get_value())
        return ""
    
    def is_a(self):
        """ check """
        return self._in.this == "a"
    
    def parse_format(self, _out, attrib_list):
        """ Get the attribute and add it to the string out """
        name = self.get_name()
        _out.add_variable(
            self.get_attribute(attrib_list, name))
        
#------------------------------------------------------------------------
# VariableParse
#------------------------------------------------------------------------
class VariableParse(object):
    """ Parse the individual variables """
    
    def __init__(self, friend, database, consumer_in):
        self.friend = friend
        self.database = database
        self._in = consumer_in
    
    def is_a(self):
        """ check """
        return self._in.this == "$" and self._in.next is not None and \
                              "nsijbBdDmMvVauetT".find(self._in.next) != -1

    def get_event_by_type(self, marriage, e_type):
        """ get an event from a type """
        if marriage is None:
            return None
        for e_ref in marriage.get_event_ref_list():
            if not e_ref:
                continue
            event = self.friend.database.get_event_from_handle(e_ref.ref)
            if event.get_type() == e_type:
                return event
        return None
    
    def get_event_by_name(self, person, event_name):
        """ get an event from a name. """
        if not person:
            return None
        for e_ref in person.get_event_ref_list():
            if not e_ref:
                continue
            event = self.friend.database.get_event_from_handle(e_ref.ref)
            if event.get_type().is_type(event_name):
                return event
        return None
    
    def empty_item(self, item, _out):
        """ return false if there is a valid item(date or place).
        Otherwise
            add a TXT.remove marker in the output string
            remove any format strings from the input string
        """
        if item is not None:
            return False
        
        _out.add_remove()
        self._in.remove_start_end("(", ")")
        return True
    
    def empty_attribute(self, person, _out):
        """ return false if there is a valid person.
        Otherwise
            add a TXT.remove marker in the output string
            remove any attribute name from the input string
        """
        if person:
            return False
        
        _out.add_remove()
        self._in.remove_start_end("[", "]")
        return True
    
    def __parse_date(self, event, _out):
        """ sub to process a date
        Given an event, get the date object, process the format,
        pass the result to string_out"""
        date_f = DateFormat(self._in)
        date = date_f.get_date(event)
        if self.empty_item(date, _out):
            return
        _out.add_variable( date_f.parse_format(date) )
    
    def __parse_place(self, event, _out):
        """ sub to process a date
        Given an event, get the place object, process the format,
        pass the result to string_out"""
        place_f = PlaceFormat(self._in)
        place = place_f.get_place(self.database, event)
        if self.empty_item(place, _out):
            return
        _out.add_variable( place_f.parse_format(place) )
    
    def __parse_name(self, person):
        name_format = NameFormat(self._in)
        name = name_format.get_name(person)
        return name_format.parse_format(name)
    
    def __parse_id(self, first_class_object):
        if first_class_object is not None:
            return first_class_object.get_gramps_id()
        else:
            return ""
    
    def __parse_event(self, person, attrib_parse):
        event = self.get_event_by_name(person, attrib_parse.get_name())
        event_f = EventFormat(self.database, self._in)
        if event:
            return event_f.parse_format(event)
        else:
            event_f.parse_empty()
            return ""
    
    def parse_format(self, _out):
        """Parse the $ variables. """
        if not self.is_a():
            return
        
        attrib_parse = AttributeParse(self._in)
        next_char = self._in.next
        self._in.step2()
        
        if next_char == "n":
            #Person's name
            _out.add_variable(
                self.__parse_name(self.friend.person))
        elif next_char == "s":
            #Souses name
            _out.add_variable(
                self.__parse_name(self.friend.spouse))
        
        elif next_char == "i":
            #Person's Id
            _out.add_variable(
                self.__parse_id(self.friend.person))
        elif next_char == "j":
            #Marriage Id
            _out.add_variable(
                self.__parse_id(self.friend.family))

        elif next_char == "b":
            #Person's Birth date
            if self.empty_item(self.friend.person, _out):
                return
            self.__parse_date(
                get_birth_or_fallback(self.friend.database, self.friend.person),
                _out)
        elif next_char == "d":
            #Person's Death date
            if self.empty_item(self.friend.person, _out):
                return
            self.__parse_date(
                get_death_or_fallback(self.friend.database, self.friend.person),
                _out)
        elif next_char == "m":
            #Marriage date
            if self.empty_item(self.friend.family, _out):
                return
            self.__parse_date(
                self.get_event_by_type(self.friend.family,
                                       gen.lib.EventType.MARRIAGE),
                _out)
        elif next_char == "v":
            #Divorce date
            if self.empty_item(self.friend.family, _out):
                return
            self.__parse_date(
                self.get_event_by_type(self.friend.family,
                                       gen.lib.EventType.DIVORCE),
                _out)
        elif next_char == "T":
            #Todays date
            date_f = DateFormat(self._in)
            from gen.lib.date import Today
            date = Today()
            if self.empty_item(date, _out):
                return
            _out.add_variable( date_f.parse_format(date) )

        elif next_char == "B":
            #Person's birth place
            if self.empty_item(self.friend.person, _out):
                return
            self.__parse_place(
                get_birth_or_fallback(self.friend.database, self.friend.person),
                _out)
        elif next_char == "D":
            #Person's death place
            if self.empty_item(self.friend.person, _out):
                return
            self.__parse_place(
                get_death_or_fallback(self.friend.database, self.friend.person),
                _out)
        elif next_char == "M":
            #Marriage place
            if self.empty_item(self.friend.family, _out):
                return
            self.__parse_place(
                self.get_event_by_type(self.friend.family,
                                       gen.lib.EventType.MARRIAGE),
                _out)
        elif next_char == "V":
            #Divorce place
            if self.empty_item(self.friend.family, _out):
                return
            self.__parse_place(
                self.get_event_by_type(self.friend.family,
                                       gen.lib.EventType.DIVORCE),
                _out)

        elif next_char == "a":
            #Person's Atribute
            if self.empty_attribute(self.friend.person, _out):
                return
            attrib_parse.parse_format(_out,
                                      self.friend.person.get_attribute_list())
        elif next_char == "u":
            #Marriage Atribute
            if self.empty_attribute(self.friend.family, _out):
                return
            attrib_parse.parse_format(_out,
                                      self.friend.family.get_attribute_list())
        
        elif next_char == "e":
            #person event
            _out.add_variable(
                self.__parse_event(self.friend.person, attrib_parse))
        elif next_char == "t":
            #person event
            _out.add_variable(
                self.__parse_event(self.friend.family, attrib_parse))
        

#------------------------------------------------------------------------
#
# SubstKeywords
#
#------------------------------------------------------------------------
class SubstKeywords(object):
    """Accepts a person/family with format lines and returns a new set of lines
    using variable substitution to make it.
    
    The individual variables are defined with the classes that look for them.
    
    Needed:
        Database object
        person_handle
            This will be the center person for the display
        family_handle
            this will specify the specific family/spouse to work with.
            If none given, then the first/preferred family/spouse is used
    """
    def __init__(self, database, person_handle, family_handle=None):
        """get the person and find the family/spouse to use for this display"""
        
        self.database = database
        self.person = database.get_person_from_handle(person_handle)
        self.family = None
        self.spouse = None
        self.line = None   #Consumable_string - set below
        
        if self.person is None:
            return
        
        fam_hand_list = self.person.get_family_handle_list()
        if fam_hand_list:
            if family_handle in fam_hand_list:
                self.family = database.get_family_from_handle(family_handle)
            else: 
                #Error.  [0] may give wrong marriage info.
                #only here because of OLD specifications.  Specs read:
                # * $S/%S 
                #   Displays the name of the person's preferred ...
                # 'preferred' means FIRST.  
                #The first might not be the correct marriage to display.
                #else: clause SHOULD be removed.
                self.family = database.get_family_from_handle(fam_hand_list[0])
            
            father_handle = self.family.get_father_handle()
            mother_handle = self.family.get_mother_handle()
            self.spouse = None
            if father_handle == person_handle:
                if mother_handle:
                    self.spouse = database.get_person_from_handle(mother_handle)
            else:
                if father_handle:
                    self.spouse = database.get_person_from_handle(father_handle)
    
    def __main_level(self):
        """parse each line of text and return the new displayable line
        
        There are four things we can find here
            A {} group which will make/end as needed.
            A <> separator
            A !  variable - Handled separately
            or text
        """
        #This is the upper most level of text
        #main = var_string_out()
        main = LevelParse(self.line)
        check = [main,
                 SeparatorParse(self.line),
                 VariableParse(self, self.database, self.line),
                 self.line]
        
        while self.line.this:
            for tmp in check:
                if tmp.is_a():
                    tmp.parse_format(main)
                    break
           
        main.combine_all()

        state, line = main.get_string()
        if state is TXT.remove:
            return None
        else:
            return line
    
    def replace_and_clean(self, lines):
        """
        return a new array of lines with all of the substitutions done
        """
        new = []
        for this_line in lines:
            if this_line == "":
                new.append(this_line)
                continue
            #print "- ", this_line
            self.line = ConsumableString(this_line)
            new_line = self.__main_level()
            #print "+ ", new_line
            if new_line is not None:
                new.append(new_line)
        
        if new == []:
            new = [u""]
        return new


#Acts 20:35 (New International Version)
#In everything I did, I showed you that by this kind of hard work
#we must help the weak, remembering the words the Lord Jesus himself
#said: 'It is more blessed to give than to receive.'


if __name__ == '__main__':
#-------------------------------------------------------------------------
#
# For Testing everything except VariableParse, SubstKeywords and EventFormat
# apply it as a script:
#
#     ==> in command line do "PYTHONPATH=??? python libsubstkeyword.py"
#
# You will need to put in your own path to the src directory
#
#-------------------------------------------------------------------------
    # pylint: disable-msg=C0103

    def combinations(c, r):
        # combinations('ABCD', 2) --> AB AC AD BC BD CD
        # combinations(range(4), 3) --> 012 013 023 123
        pool = tuple(range(c))
        n = len(pool)
        if r > n:
            return
        indices = range(r)
        yield tuple(pool[i] for i in indices)
        while True:
            for i in reversed(range(r)):
                if indices[i] != i + n - r:
                    break
            else:
                return
            indices[i] += 1
            for j in range(i+1, r):
                indices[j] = indices[j-1] + 1
            yield tuple(pool[i] for i in indices)

    def main_level_test(_in, testing_class, testing_what):
        """This is a mini def __main_level(self):
        """
        main = LevelParse(_in)
        sepa = SeparatorParse(_in)
        test = testing_class(_in)
        
        while _in.this:
            if main.is_a():
                main.parse_format(_in)
            elif sepa.is_a():
                sepa.parse_format(main)
            elif _in.this == "$":
                _in.step()
                main.add_variable(
                    test.parse_format(testing_what))
            else:
                _in.parse_format(main)

        main.combine_all()

        state, line = main.get_string()
        if state is TXT.remove:
            return None
        else:
            return line


    from gen.lib.date import Date
    y_or_n = ()
    date_to_test = Date()
    def date_set():
        date_to_test.set_yr_mon_day(
            1970 if 0 in y_or_n else 0,
            9 if 1 in y_or_n else 0,
            3 if 2 in y_or_n else 0
            )
        #print date_to_test
    
    line_in = "<Z>$(yyy) <a>$(<Z>Mm)<b>$(mm){<c>$(d)}{<d>$(yyyy)<e>}<f>$(yy)"
    consume_str = ConsumableString(line_in)
    
    print line_in
    print "#None are known"
    tmp = main_level_test(consume_str, DateFormat, date_to_test)
    print tmp
    print "Good" if tmp == " " else "!! bad !!"

    
    print
    print
    print "#One is known"
    answer = []
    for y_or_n in combinations(3, 1):
        date_set()
        consume_str = ConsumableString(line_in)
        tmp = main_level_test(consume_str, DateFormat, date_to_test)
        print tmp
        answer.append(tmp)
    print "Good" if answer == [
        "1970 d1970f70",
        " a99b09",
        " c3"
        ] else "!! bad !!"


    print
    print
    print "#Two are known"
    answer = []
    for y_or_n in combinations(3, 2):
        date_set()
        consume_str = ConsumableString(line_in)
        tmp = main_level_test(consume_str, DateFormat, date_to_test)
        print tmp
        answer.append(tmp)
    print "Good" if answer == [
        "1970 a99b09d1970f70",
        "1970 c3d1970f70",
        " a99b09c3"
        ] else "!! bad !!"


    print
    print
    print "#All are known"
    answer = []
    y_or_n = (0, 1, 2)
    date_set()
    consume_str = ConsumableString(line_in)
    tmp = main_level_test(consume_str, DateFormat, date_to_test)
    print tmp
    answer.append(tmp)
    print "Good" if answer == ["1970 a99b09c3d1970f70"
        ] else "!! bad !!"

    import sys
    sys.exit()
    print
    print
    print "============="
    print "============="

    from gen.lib.name import Name
    y_or_n = ()
    name_to_test = Name()
    def name_set():
        #code  = "tfcnxslg"
        name_to_test.set_call_name("Bob" if 0 in y_or_n else "")
        name_to_test.set_title("Dr." if 1 in y_or_n else "")
        name_to_test.set_first_name("Billy" if 2 in y_or_n else "")
        name_to_test.set_nick_name("Buck" if 3 in y_or_n else "")
        name_to_test.set_suffix("IV" if 4 in y_or_n else "")
        #now can we put something in for the last name?
        name_to_test.set_family_nick_name("The Clubs" if 5 in y_or_n else "")
    
    line_in = "{$(c)$(t)<1>{<2>$(f)}{<3>$(n){<0> <0>}<4>$(x)}$(s)<5>$(l)<6>$(g)<0>"
    consume_str = ConsumableString(line_in)
    
    print
    print
    print line_in
    print "#None are known"
    tmp = main_level_test(consume_str, NameFormat, name_to_test)
    print tmp
    print "Good" if tmp == None else "!! bad !!"


    print
    print
    print "#Two are known"
    answer = []
    for y_or_n in combinations(6, 2):
        name_set()
        consume_str = ConsumableString(line_in)
        tmp = main_level_test(consume_str, NameFormat, name_to_test)
        print tmp
        answer.append(tmp)
    print "Good" if answer == [
        "BobDr.4Bob",
        "Bob2Billy4Bob",
        "Bob3Buck4Bob",
        "Bob4BobIV",
        "Bob4BobThe Clubs",
        "Dr.2Billy4Billy",
        "Dr.3Buck",
        "Dr.1IV",
        "Dr.6The Clubs",
        "Billy3Buck4Billy",
        "Billy4BillyIV",
        "Billy4BillyThe Clubs",
        "BuckIV",
        "BuckThe Clubs",
        "IV6The Clubs"
        ] else "!! bad !!"


    print
    print
    print "#All are known"
    y_or_n = (0, 1, 2, 3, 4, 5)
    name_set()
    consume_str = ConsumableString(line_in)
    answer = main_level_test(consume_str, NameFormat, name_to_test)
    print answer
    print "Good" if answer == "BobDr.2Billy3Buck4BobIV6The Clubs" \
                            else "!! bad !!"


    print
    print
    print "============="
    print "============="

    from gen.lib.place import Place
    y_or_n = ()
    place_to_test = Place()
    def place_set():
        #code = "elcuspnitxy"
        main_loc = place_to_test.get_main_location()
        main_loc.set_street(
            "Lost River Ave." if 0 in y_or_n else ""
        )
        main_loc.set_locality(
            "Second district" if 1 in y_or_n else ""
        )
        main_loc.set_city(
            "Arco" if 2 in y_or_n else ""
        )
        main_loc.set_county(
            "Butte" if 3 in y_or_n else ""
        )
        main_loc.set_state(
            "Idaho" if 4 in y_or_n else ""
        )
        main_loc.set_postal_code(
            "83213" if 5 in y_or_n else ""
        )
        main_loc.set_country(
            "USA" if 6 in y_or_n else ""
        )
        main_loc.set_parish(
            "St Anns" if 7 in y_or_n else ""
        )
        place_to_test.set_title(
            "Atomic City" if 8 in y_or_n else ""
        )
        place_to_test.set_longitude(
            "N43H38'5\"N" if 9 in y_or_n else ""
        )
        place_to_test.set_latitude(
            "W113H18'5\"W" if 10 in y_or_n else ""
        )
    
    #code = "txy"
    line_in = "$(e)<1>{<2>$(l) <3> $(c)<4><0><5>{$(s)<6>$(p)<7>" + \
              "{<1>$(n)<2>}<3>$(i<0>)<4>}<5>$(t)<6>$(x)<7>}<8>$(y)"
    consume_str = ConsumableString(line_in)
    
    print
    print
    print line_in
    print "#None are known"
    tmp = main_level_test(consume_str, PlaceFormat, place_to_test)
    print tmp
    print "Good" if tmp == "" else "!! bad !!"


    print
    print
    print "#Three are known (string lengths only)"
    answer = []
    for y_or_n in combinations(11, 4):
        place_set()
        consume_str = ConsumableString(line_in)
        tmp = main_level_test(consume_str, PlaceFormat, place_to_test)
        #print tmp
        answer.append(len(tmp))
    print answer
    print "Good" if answer == [38, 44, 44, 42, 46, 50, 49, 50, 40, 40, 38, 42,
        46, 45, 46, 46, 44, 48, 52, 51, 52, 44, 48, 52, 51, 52, 46, 50, 49, 50,
        54, 53, 54, 57, 58, 57, 28, 28, 26, 30, 34, 33, 34, 34, 32, 36, 40, 39,
        40, 32, 36, 40, 39, 40, 34, 38, 37, 38, 42, 41, 42, 45, 46, 45, 30, 28,
        32, 36, 35, 36, 28, 32, 36, 35, 36, 30, 34, 33, 34, 38, 37, 38, 41, 42,
        41, 34, 38, 42, 41, 42, 36, 40, 39, 40, 44, 43, 44, 47, 48, 47, 36, 40,
        39, 40, 44, 43, 44, 47, 48, 47, 42, 41, 42, 45, 46, 45, 49, 50, 49, 53,
        28, 28, 26, 30, 34, 33, 34, 34, 32, 36, 40, 39, 40, 32, 36, 40, 39, 40,
        34, 38, 37, 38, 42, 41, 42, 45, 46, 45, 30, 28, 32, 36, 35, 36, 28, 32,
        36, 35, 36, 30, 34, 33, 34, 38, 37, 38, 41, 42, 41, 34, 38, 42, 41, 42,
        36, 40, 39, 40, 44, 43, 44, 47, 48, 47, 36, 40, 39, 40, 44, 43, 44, 47,
        48, 47, 42, 41, 42, 45, 46, 45, 49, 50, 49, 53, 19, 17, 21, 25, 24, 25,
        17, 21, 25, 24, 25, 19, 23, 22, 23, 27, 26, 27, 30, 31, 30, 23, 27, 31,
        30, 31, 25, 29, 28, 29, 33, 32, 33, 36, 37, 36, 25, 29, 28, 29, 33, 32,
        33, 36, 37, 36, 31, 30, 31, 34, 35, 34, 38, 39, 38, 42, 19, 23, 27, 26,
        27, 21, 25, 24, 25, 29, 28, 29, 32, 33, 32, 21, 25, 24, 25, 29, 28, 29,
        32, 33, 32, 27, 26, 27, 30, 31, 30, 34, 35, 34, 38, 27, 31, 30, 31, 35,
        34, 35, 38, 39, 38, 33, 32, 33, 36, 37, 36, 40, 41, 40, 44, 33, 32, 33,
        36, 37, 36, 40, 41, 40, 44, 38, 39, 38, 42, 46] else "!! bad !!"
    
    
