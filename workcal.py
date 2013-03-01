#! /usr/bin/env python
"""
workcal.py
by len
input: word docx file with work schedule from Rupert
output: csv|ics for import to ical|google|outlook calendar
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

# System imports
import six #Remove when icalendar ported to python3
import os
import sys
import platform
import argparse
import re
import copy
from six.moves import configparser
from datetime import datetime, date, time, timedelta
import pytz
from icalendar import Calendar, Event, vDatetime
# Local imports
from docx import opendocx, getdocumenttext
from util import PersonEvent, GCalEvent

# Global setup & in config file
#MARK_BEGIN: Text string that marks begining of calendar in Word file as str
#USRTZ: User's timezone default to UTC as pytz obj
#CALL_START_TIME: Time when call should start as time obj
#CALL_END_TIME: Time when call should end as time obj
HEADER = ('Subject,Start Date,Start Time,End Date,End Time,All Day Event,'
          'Description,Location,Private') # minimum: Subject, Start Date
MONTH = {'JANUARY':'01','FEBRUARY':'02','MARCH':'03',
         'APRIL':'04','MAY':'05','JUNE':'06',
         'JULY':'07','AUGUST':'08','SEPTEMBER':'09',
         'OCTOBER':'10','NOVEMBER':'11','DECEMBER':'12'}
GMT = pytz.utc

def extractkey(str):
    l = str.split(":")
    return l[0].strip()

def extractvalue(str):
    l = str.split(":")
    return l[1].strip()

def process(textlist):
    #Careful: next month may be included; ('1' as mark is FRAGILE)
    heading = textlist[0:textlist.index('1')] #For year and month
    days = textlist[textlist.index('1'):] #For day, event and person
    #Identify year
    currentyear = str(date.today().year)
    for item in heading:
        if currentyear in item:
            year = currentyear
            break
        elif currentyear[0:3] in item:
            year = item.strip()
            break
    #Identify month
    for item in heading:
        if item in list(MONTH.keys()):
            month = MONTH[item]
            break
    #Create data structure: {date: [events]}
    d = {}
    lastday = 0 #Prior found day of month
    for item in days:
        if item.strip().isdigit():
            keydate = date(int(year), int(month), int(item))
            if keydate in d: #Handle duplicate days, i.e. '1'
                keydate = keydate + timedelta(days=lastday)
                year = keydate.year #New year?
                month = keydate.month #Next month?
            lastday = int(item)
        else: #Not a digit and likely an event/person
            try:
                d[keydate].append(item)
            except KeyError:
                d[keydate] = [item]
    #Make Event calendar objects
    s = []
    for i in sorted(d.keys()):
        #First item is person on service
        serviceevent = GCalEvent('Service', i)
        serviceevent.alldayevent = True
        s.append(PersonEvent(d[i][0], serviceevent))
        #Second item is person on call
        callevent = GCalEvent('Call', i)
        callevent.starttime = CALL_START_TIME
        callevent.enddate = i + timedelta(days=1)
        callevent.endtime = CALL_END_TIME
        callevent.alldayevent = False
        s.append(PersonEvent(d[i][1], callevent))
        #Check if additional events (i.e. Backup, Kaiser, meeting, etc.)
        other = d[i][2:]
        if other:
            for j in other:
                #Backup, lecture, or Kaiser listed as ex: "Kaiser: Tanaka"
                if ':' in j:
                    person = extractvalue(j)
                    subject = extractkey(j)
                    otherevent = GCalEvent(subject, i)
                    otherevent.alldayevent = True
                    pe = PersonEvent(person, otherevent)
                    s.append(pe)
                #Account for anything else ex: PICU Meeting
                else:
                    groupevent = GCalEvent(j, i)
                    groupevent.alldayevent = True
                    s.append(groupevent)
    return s

def createcsv(schedule, person):
    """Prints out in Google Calendar CSV format for args.person"""
    six.print_(HEADER)
    for item in schedule:
        if person == 'all': six.print_(item); continue
        if item.__class__.__name__ == 'PersonEvent':
            if item.person == person: six.print_(item.event)
        elif item.__class__.__name__ == 'GCalEvent':
            six.print_(item)

def createics(schedule, person):
    """Make or display icalendar file"""
    def handle_event(i):
        """Creates icalendar Event from a GCalEvent"""
        event = Event()
        id = (datetime.utcnow().strftime('%Y%m%d%H%M%f') + '-' +
              str(os.getpid()) + '-' + person)
        event.add('uid', id)
        event['dtstamp'] = vDatetime(datetime.utcnow()).to_ical() + 'Z'
        #util.Event basic needs subject and startdate
        event.add('summary', i.subject)
        if i.alldayevent:
            event.add('dtstart', i.startdate)
            event.add('dtend', i.startdate+timedelta(days=1))
        else:
            dtstart = USRTZ.localize(datetime.combine(i.startdate, i.starttime))
            dtend = USRTZ.localize(datetime.combine(i.enddate, i.endtime))
            event['dtstart'] = (vDatetime(dtstart.astimezone(GMT)).to_ical() )
            event['dtend'] = ( vDatetime(dtend.astimezone(GMT)).to_ical() )
        return event
    #Calendar setup (ics)
    workcal = Calendar()
    workcal.add('prodid', '-//tanakalen//workcal.py//EN')
    workcal.add('version', '2.0')
    workcal.add('method', 'PUBLISH')
    for item in schedule:
        if person == 'all':
            #handle Event: item
            if item.__class__.__name__ == 'PersonEvent':
                #copy item.event, change subject add item.person
                newevent = copy.deepcopy(item.event)
                newevent.subject = item.person + '-' + item.event.subject
                workcal.add_component(handle_event(newevent))
            else:
                workcal.add_component(handle_event(item))
            continue
        if item.__class__.__name__ == 'PersonEvent':
            if item.person == person:
                #handle Event: item.event
                workcal.add_component(handle_event(item.event))
        elif item.__class__.__name__ == 'GCalEvent':
            #handle Event: item
            workcal.add_component(handle_event(item))
    six.print_(workcal.to_ical())

def main(argv=None):
    #Load configuration
    f_config = ['.workcal/config', 'workcal.ini'] #TODO: make generic?
    config = configparser.SafeConfigParser()
    found = config.read(f_config)
    if found:
        global USRTZ
        USRTZ = pytz.timezone(config.get('core', 'timezone'))
        callst = config.get('core', 'call-start').split(':')
        callen = config.get('core', 'call-end').split(':')
        global CALL_START_TIME
        CALL_START_TIME = time(int(callst[0]), int(callst[1]))
        global CALL_END_TIME
        CALL_END_TIME = time(int(callen[0]), int(callen[1]))
        global MARK_BEGIN
        MARK_BEGIN = config.get('core', 'file-start')
    else:
        config.add_section('core')
        config.set('core', 'timezone', 'UTC')
        config.set('core', 'call-start', '16:30')
        config.set('core', 'call-end', '7:30')
        config.set('core', 'file-start', 'PICU SCHEDULE')
        if platform.system() == 'Windows':
            with open('workcal.ini', 'wb') as configfile:
                config.write(configfile)
        else:
            os.mkdir('.workcal')
            with open('.workcal/config', 'wb') as configfile:
                config.write(configfile)

    #Command line setup
    parser = argparse.ArgumentParser(prog='workcal',
        description='Process emailed Word file containing work schedule.',
        epilog="Ex:\n\tworkcal -f dec.docx -p Tanaka")
    parser.add_argument('-i', '--ics',
        help='output to iCalendar format [RFC 5545]',
        action='store_true')
    parser.add_argument('-f', '--file',
        help='file to get calendar information from',
        nargs='?', type=argparse.FileType('r'),
        default=sys.stdin)
    parser.add_argument('-p', '--person',
        help='schedule for person requested, otherwise all events listed',
        default='Tanaka')
    args = parser.parse_args()
    #Open file
    try:
        document = opendocx(args.file)
        paratextlist = getdocumenttext(document)
    except KeyError, TypeError: #File is not docx
        with open(args.file.name, 'rb') as f:
            document = f.read()
        ldoc = re.split('\r|\x07', document) #FRAGILE
        start = ldoc.index(MARK_BEGIN) #FRAGILE
        preparatextlist = [x for x in ldoc[start:] 
            if not re.search('[\x00-\x1f|\x7f-\xff]', x)]
        paratextlist = [x for x in preparatextlist if x != ''] #FRAGILE
    args.file.close()
    #Process file
    thismonth = process(paratextlist)
    #Print results
    if args.ics:
        createics(thismonth, args.person)
    else:
        createcsv(thismonth, args.person)

if __name__ == "__main__":
    try:
        exitcode = main()
    except Exception as err:
        six.print_('ERROR: {}'.format(err), file=sys.stderr)
        exitcode = 1
    sys.exit(exitcode)
    sys.exit(main())