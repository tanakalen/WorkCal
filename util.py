#! /usr/bin/env python
"""
util:
    Collection of utilities, classes, functions for workcal.py
"""
#
# Copyright (c) 2012 Len Tanaka
#
# Permission is hereby granted, free of charge, to any person obtaining a copy 
# of this software and associated documentation files (the "Software"), to deal 
# in the Software without restriction, including without limitation the rights 
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell 
# copies of the Software, and to permit persons to whom the Software is 
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from datetime import date, time, timedelta, tzinfo

class HST(tzinfo):
    def utcoffset(self, dt):
        return timedelta(hours=-10)
    def dst(self, dt):
        return timedelta(hours=-10)
    def tzname(self, dt):
        return 'US/Hawaii'

class GMT(tzinfo):
    def utcoffset(self, dt):
        return timedelta(0)
    def dst(self, dt):
        return timedelta(0)
    def tzname(self, dt):
        return 'UTC'

class Event:
    """Event object: represents basic elements of subject and start date"""
    subject = ''
    date = date.today()

    def __init__(self, subject, date):
        self.subject = subject
        self.date = date

    def __repr__(self):
        return ("{self.subject},{self.date:%m/%d/%y}".format(self=self))

class GCalEvent(Event):
    """Extends Event object to Google Calendar data:
         Subject,Start Date,Start Time,End Date,End Time,All Day Event,
         Description,Location,Private"""
    #subject inherited
    startdate = Event.date
    starttime = ''
    enddate = ''
    endtime = ''
    alldayevent = False
    description = ''
    location = '' #Future geolocation info
    private = ''

    def __init__(self, subject, date):
        self.subject = subject
        self.startdate = date
        #Other attributes are optional

    def __repr__(self):
        if self.alldayevent:
            return ("{self.subject},"
                    "{self.startdate:%m/%d/%y},"
                    ",,,,"
                    "{self.description},"
                    "{self.location},".format(self=self))
        else:
            return ("{self.subject},"
                    "{self.startdate:%m/%d/%y},"
                    "{self.starttime:%H:%M},"
                    "{self.enddate:%m/%d/%y},"
                    "{self.endtime:%H:%M},"
                    "{self.alldayevent},"
                    "{self.description},"
                    "{self.location},"
                    "{self.private}".format(self=self))

class PersonEvent:
    """Event attached to particular person"""
    person = ''
    event = ''

    def __init__(self, name, event):
        self.person = name
        self.event = event #from Event or GCalEvent

    def __repr__(self):
        return ("{self.person}-{self.event}".format(self=self))

def calcEaster(year):
    """Calculate the date of Easter
         from: http://www.oremus.org/liturgy/etc/ktf/app/easter.html
         param year
         returns date tuple (day, month, year)
    """
    gold = year % 19 + 1
    sol = (year - 1600) // 100 - (year - 1600) // 400
    lun = (((year - 1400) // 100) * 8) // 25
    _pasch = (3 - 11 * gold + sol - lun) % 30
    if (_pasch == 29) or (_pasch == 28 and gold > 11):
        pasch = _pasch - 1
    else:
        pasch = _pasch
    dom = (year + (year // 4) - (year // 100) + (year // 400)) % 7
    easter = pasch + 1 + (4 - dom - pasch) % 7
    if easter < 11:
        return (easter + 21, 3, year)
    else:
        return (easter - 10, 4, year)

def EasterDate(year):
    """EASTER DATE CALCULATION FOR YEARS 1583 TO 4099
       This algorithm is an arithmetic interpretation of the 3 step
       Easter Dating Method developed by Ron Mallen 1985, as a vast
       improvement on the method described in the Common Prayer Book
       from: https://www.assa.org.au/edm

       param year
       returns date tuple (day, month, year)
    """
    FirstDig = year // 100
    Remain19 = year % 19

    # calculate PFM date
    temp = (FirstDig - 15) // 2 + 202 - 11 * Remain19

    def f(x):
        return {
                21: temp - 1,
                24: temp - 1,
                25: temp - 1,
                27: temp - 1,
                28: temp - 1,
                29: temp - 1,
                30: temp - 1,
                31: temp - 1,
                32: temp - 1,
                34: temp - 1,
                35: temp - 1,
                38: temp - 1,
                33: temp - 2,
                36: temp - 2,
                37: temp - 2,
                39: temp - 2,
                40: temp - 2,
            }.get(x, temp)
    temp = f(FirstDig)
    temp = temp % 30

    tA = temp + 21
    if temp == 29:
        tA = tA - 1
    if (temp == 28) and (Remain19 > 10):
        tA = tA - 1

    # find the next Sunday
    tB = (tA - 19) % 7

    tC = (40 - FirstDig) % 4
    if tC == 3:
        tC = tC + 1
    if tC > 1:
        tC = tC + 1

    temp = year % 100
    tD = (temp + temp // 4) % 7

    tE = ((20 - tB - tC - tD) % 7) + 1
    d = tA + tE

    if d > 31:
        return (d-31, 4, year)
    else:
        return (d, 3, year)
