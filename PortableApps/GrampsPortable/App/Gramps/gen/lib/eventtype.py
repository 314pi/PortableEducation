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
Provide the different event types
"""

#------------------------------------------------------------------------
#
# Python modules
#
#------------------------------------------------------------------------
from gen.ggettext import sgettext as _

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
from gen.lib.grampstype import GrampsType

class EventType(GrampsType):
    """
    Event types.
    
    .. attribute UNKNOWN:    Unknown
    .. attribute CUSTOM:    Custom
    .. attribute ADOPT:     Adopted
    .. attribute BIRTH:     Birth
    .. attribute DEATH:     Death
    .. attribute ADULT_CHRISTEN: Adult Christening
    .. attribute BAPTISM:      Baptism
    .. attribute BAR_MITZVAH:  Bar Mitzvah
    .. attribute BAS_MITZVAH:  Bas Mitzvah
    .. attribute BLESS:        Blessing
    .. attribute BURIAL:       Burial
    .. attribute CAUSE_DEATH:   Cause Of Death
    .. attribute CENSUS:        Census
    .. attribute CHRISTEN:      Christening
    .. attribute CONFIRMATION:   Confirmation
    .. attribute CREMATION:      Cremation
    .. attribute DEGREE:         Degree
    .. attribute EDUCATION:     Education
    .. attribute ELECTED:       Elected
    .. attribute EMIGRATION:    Emigration
    .. attribute FIRST_COMMUN:  First Communion
    .. attribute IMMIGRATION:   Immigration
    .. attribute GRADUATION:   Graduation
    .. attribute MED_INFO:     Medical Information
    .. attribute MILITARY_SERV:   Military Service
    .. attribute NATURALIZATION: Naturalization
    .. attribute NOB_TITLE:     Nobility Title
    .. attribute NUM_MARRIAGES:   Number of Marriages
    .. attribute OCCUPATION:      Occupation
    .. attribute ORDINATION:     Ordination
    .. attribute PROBATE:        Probate
    .. attribute PROPERTY:      Property
    .. attribute RELIGION:      Religion
    .. attribute RESIDENCE:    Residence
    .. attribute RETIREMENT:    Retirement
    .. attribute WILL:           Will
    .. attribute MARRIAGE:     Marriage
    .. attribute MARR_SETTL:     Marriage Settlement
    .. attribute MARR_LIC:       Marriage License
    .. attribute MARR_CONTR:     Marriage Contract
    .. attribute MARR_BANNS:     Marriage Banns
    .. attribute ENGAGEMENT:     Engagement
    .. attribute DIVORCE:        Divorce
    .. attribute DIV_FILING:     Divorce Filing
    .. attribute ANNULMENT:      Annulment
    .. attribute MARR_ALT:        Alternate Marriage
    """
    UNKNOWN        = -1
    CUSTOM         = 0
    MARRIAGE       = 1
    MARR_SETTL     = 2
    MARR_LIC       = 3
    MARR_CONTR     = 4
    MARR_BANNS     = 5
    ENGAGEMENT     = 6
    DIVORCE        = 7
    DIV_FILING     = 8
    ANNULMENT      = 9
    MARR_ALT       = 10
    ADOPT          = 11
    BIRTH          = 12
    DEATH          = 13
    ADULT_CHRISTEN = 14
    BAPTISM        = 15
    BAR_MITZVAH    = 16
    BAS_MITZVAH    = 17
    BLESS          = 18
    BURIAL         = 19
    CAUSE_DEATH    = 20
    CENSUS         = 21
    CHRISTEN       = 22
    CONFIRMATION   = 23
    CREMATION      = 24
    DEGREE         = 25
    EDUCATION      = 26
    ELECTED        = 27
    EMIGRATION     = 28
    FIRST_COMMUN   = 29
    IMMIGRATION    = 30
    GRADUATION     = 31
    MED_INFO       = 32
    MILITARY_SERV  = 33
    NATURALIZATION = 34
    NOB_TITLE      = 35
    NUM_MARRIAGES  = 36
    OCCUPATION     = 37
    ORDINATION     = 38
    PROBATE        = 39
    PROPERTY       = 40
    RELIGION       = 41
    RESIDENCE      = 42
    RETIREMENT     = 43
    WILL           = 44

    _MENU = [[_('Life Events'),
              [BIRTH, BAPTISM, DEATH, BURIAL, CREMATION, ADOPT]],
            [_('Family'),
              [ENGAGEMENT, MARRIAGE, DIVORCE, ANNULMENT, MARR_SETTL, MARR_LIC,
               MARR_CONTR, MARR_BANNS, DIV_FILING, MARR_ALT]],
            [_('Religious'),
              [CHRISTEN, ADULT_CHRISTEN, CONFIRMATION, FIRST_COMMUN, BLESS,
               BAR_MITZVAH, BAS_MITZVAH, RELIGION]],
            [_('Vocational'),
              [OCCUPATION, RETIREMENT, ELECTED, MILITARY_SERV, ORDINATION]],
            [_('Academic'),
              [EDUCATION, DEGREE, GRADUATION]],
            [_('Travel'),
              [EMIGRATION, IMMIGRATION, NATURALIZATION]],
            [_('Legal'),
              [PROBATE, WILL]],
            [_('Residence'),
              [RESIDENCE, CENSUS, PROPERTY]],
            [_('Other'),
              [CAUSE_DEATH, MED_INFO, NOB_TITLE, NUM_MARRIAGES]]]

    _CUSTOM = CUSTOM
    _DEFAULT = BIRTH

    _DATAMAP = [
        (UNKNOWN         , _("Unknown"),              "Unknown"),
        (CUSTOM          , _("Custom"),               "Custom"),
        (ADOPT           , _("Adopted"),              "Adopted"),
        (BIRTH           , _("Birth"),                "Birth"),
        (DEATH           , _("Death"),                "Death"),
        (ADULT_CHRISTEN  , _("Adult Christening"),    "Adult Christening"),
        (BAPTISM         , _("Baptism"),              "Baptism"),
        (BAR_MITZVAH     , _("Bar Mitzvah"),          "Bar Mitzvah"),
        (BAS_MITZVAH     , _("Bat Mitzvah"),          "Bas Mitzvah"),
        (BLESS           , _("Blessing"),             "Blessing"),
        (BURIAL          , _("Burial"),               "Burial"),
        (CAUSE_DEATH     , _("Cause Of Death"),       "Cause Of Death"),
        (CENSUS          , _("Census"),               "Census"),
        (CHRISTEN        , _("Christening"),          "Christening"),
        (CONFIRMATION    , _("Confirmation"),         "Confirmation"),
        (CREMATION       , _("Cremation"),            "Cremation"),
        (DEGREE          , _("Degree"),               "Degree"),
        (EDUCATION       , _("Education"),            "Education"),
        (ELECTED         , _("Elected"),              "Elected"),
        (EMIGRATION      , _("Emigration"),           "Emigration"),
        (FIRST_COMMUN    , _("First Communion"),      "First Communion"),
        (IMMIGRATION     , _("Immigration"),          "Immigration"),
        (GRADUATION      , _("Graduation"),           "Graduation"),
        (MED_INFO        , _("Medical Information"),  "Medical Information"),
        (MILITARY_SERV   , _("Military Service"),     "Military Service"),
        (NATURALIZATION  , _("Naturalization"),       "Naturalization"),
        (NOB_TITLE       , _("Nobility Title"),       "Nobility Title"),
        (NUM_MARRIAGES   , _("Number of Marriages"),  "Number of Marriages"),
        (OCCUPATION      , _("Occupation"),           "Occupation"),
        (ORDINATION      , _("Ordination"),           "Ordination"),
        (PROBATE         , _("Probate"),              "Probate"),
        (PROPERTY        , _("Property"),             "Property"),
        (RELIGION        , _("Religion"),             "Religion"),
        (RESIDENCE       , _("Residence"),            "Residence"),
        (RETIREMENT      , _("Retirement"),           "Retirement"),
        (WILL            , _("Will"),                 "Will"),
        (MARRIAGE        , _("Marriage"),             "Marriage"),
        (MARR_SETTL      , _("Marriage Settlement"),  "Marriage Settlement"),
        (MARR_LIC        , _("Marriage License"),     "Marriage License"),
        (MARR_CONTR      , _("Marriage Contract"),    "Marriage Contract"),
        (MARR_BANNS      , _("Marriage Banns"),       "Marriage Banns"),
        (ENGAGEMENT      , _("Engagement"),           "Engagement"),
        (DIVORCE         , _("Divorce"),              "Divorce"),
        (DIV_FILING      , _("Divorce Filing"),       "Divorce Filing"),
        (ANNULMENT       , _("Annulment"),            "Annulment"),
        (MARR_ALT        , _("Alternate Marriage"),   "Alternate Marriage"),
        ]

    _ABBREVIATIONS = {
        BIRTH: _("birth abbreviation|b."),
        DEATH: _("death abbreviation|d."),
        MARRIAGE: _("marriage abbreviation|m."),
        UNKNOWN: _("Unknown abbreviation|unkn."),
        CUSTOM: _("Custom abbreviation|cust."),
        ADOPT: _("Adopted abbreviation|adop."),
        ADULT_CHRISTEN : _("Adult Christening abbreviation|a.chr."),
        BAPTISM: _("Baptism abbreviation|bap."),
        BAR_MITZVAH : _("Bar Mitzvah abbreviation|bar."),
        BAS_MITZVAH : _("Bat Mitzvah abbreviation|bat."),
        BLESS: _("Blessing abbreviation|bles."),
        BURIAL: _("Burial abbreviation|bur."),
        CAUSE_DEATH : _("Cause Of Death abbreviation|d.cau."),
        CENSUS: _("Census abbreviation|cens."),
        CHRISTEN: _("Christening abbreviation|chr."),
        CONFIRMATION: _("Confirmation abbreviation|conf."),
        CREMATION: _("Cremation abbreviation|crem."),
        DEGREE: _("Degree abbreviation|deg."),
        EDUCATION: _("Education abbreviation|edu."),
        ELECTED: _("Elected abbreviation|elec."),
        EMIGRATION: _("Emigration abbreviation|em."),
        FIRST_COMMUN: _("First Communion abbreviation|f.comm."),
        IMMIGRATION: _("Immigration abbreviation|im."),
        GRADUATION: _("Graduation abbreviation|grad."),
        MED_INFO: _("Medical Information abbreviation|medinf."),
        MILITARY_SERV: _("Military Service abbreviation|milser."),
        NATURALIZATION: _("Naturalization abbreviation|nat."),
        NOB_TITLE: _("Nobility Title abbreviation|nob."),
        NUM_MARRIAGES: _("Number of Marriages abbreviation|n.o.mar."),
        OCCUPATION: _("Occupation abbreviation|occ."),
        ORDINATION: _("Ordination abbreviation|ord."),
        PROBATE: _("Probate abbreviation|prob."),
        PROPERTY: _("Property abbreviation|prop."),
        RELIGION: _("Religion abbreviation|rel."),
        RESIDENCE: _("Residence abbreviation|res."),
        RETIREMENT: _("Retirement abbreviation|ret."),
        WILL: _("Will abbreviation|will."),
        MARR_SETTL: _("Marriage Settlement abbreviation|m.set."),
        MARR_LIC: _("Marriage License abbreviation|m.lic."),
        MARR_CONTR: _("Marriage Contract abbreviation|m.con."),
        MARR_BANNS: _("Marriage Banns abbreviation|m.ban."),
        MARR_ALT: _("Alternate Marriage abbreviation|alt.mar."),
        ENGAGEMENT: _("Engagement abbreviation|engd."),
        DIVORCE: _("Divorce abbreviation|div."),
        DIV_FILING: _("Divorce Filing abbreviation|div.f."),
        ANNULMENT: _("Annulment abbreviation|annul.")
        }

    def __init__(self, value=None):
        GrampsType.__init__(self, value)
        
    def is_birth(self):
        """
        Returns True if EventType is BIRTH, False
        otherwise.
        """
        return self.value == self.BIRTH

    def is_baptism(self):
        """
        Returns True if EventType is BAPTISM, False
        otherwise.
        """
        return self.value == self.BAPTISM
    
    def is_death(self):
        """
        Returns True if EventType is DEATH, False
        otherwise.
        """
        return self.value == self.DEATH
    
    def is_burial(self):
        """
        Returns True if EventType is BURIAL, False
        otherwise.
        """
        return self.value == self.BURIAL

    def is_birth_fallback(self):
        """
        Returns True if EventType is a birth fallback, False
        otherwise.
        """
        return self.value in [self.CHRISTEN, 
                              self.BAPTISM]
    
    def is_death_fallback(self):
        """
        Returns True if EventType is a death fallback, False
        otherwise.
        """
        return self.value in [self.BURIAL, 
                              self.CREMATION, 
                              self.CAUSE_DEATH]
    def is_marriage(self):
        """
        Returns True if EventType is MARRIAGE, False otherwise.
        """
        return self.value == self.MARRIAGE

    def is_marriage_fallback(self):
        """
        Returns True if EventType is a marriage fallback, False
        otherwise.
        """
        return self.value in [self.ENGAGEMENT, 
                              self.MARR_ALT]

    def is_divorce(self):
        """
        Returns True if EventType is DIVORCE, False otherwise.
        """
        return self.value == self.DIVORCE

    def is_divorce_fallback(self):
        """
        Returns True if EventType is a divorce fallback, False
        otherwise.
        """
        return self.value in [self.ANNULMENT, 
                              self.DIV_FILING]

    def is_relationship_event(self):
        """
        Returns True is EventType is a relationship type event.
        """
        return self.value in [self.DIVORCE, self.MARRIAGE, self.ANNULMENT]

    def is_type(self, event_name):
        """
        Returns True if EventType has name EVENT_NAME, False otherwise.
        """
        event_type = [tup for tup in self._DATAMAP if tup[2] == event_name]
        if len(event_type) > 0:
            return self.value == event_type[0][0] # first one, the code
        return False

    def get_abbreviation(self):
        """
        Returns the abbreviation for this event. Uses the explicitly
        given abbreviations, or first letter of each word, or the first
        three letters. Appends a period after the abbreviation,
        but not if string is in _ABBREVIATIONS.
        """
        if self.value in self._ABBREVIATIONS:
            return self._ABBREVIATIONS[self.value]
        else:
            abbrev = unicode(self)
            if " " in abbrev:
                return ".".join([letter[0].lower() for letter in abbrev.split()]) + "."
            else:
                return abbrev[:3].lower() + "."
