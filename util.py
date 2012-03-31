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
    private = True

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

