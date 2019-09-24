################################################################################
##     This script uses the Confluence calendar-service (not prod, AFAIK) to 
## build a Nagios contact group configuration for the management team and on-call
## individual. On-call calendar entries should be in the format:
##     Freeform text goes here: <NagiosContactIdentifier>
##  e.g. Lisa R On Call (216-555-1212): e0082643sms
################################################################################
import requests
import json
from datetime import date, timedelta, datetime
import os
from config import strSubCalendarID, strCalendarTitleDelimiter, strSMSContactList, strOutputFile, strConfluenceRESTCalendarService, strTimeZone, cmdBackUpContactGroupConfig, cmdRestoreContactGroupConfig, cmdCopyProposedContactsToNagios, cmdTestNagiosConfig, cmdRestartNagios, strContactGroup,  strContactGroupDescription
################################################################################
# Function definitions
################################################################################
# This function determines if a date falls between two dates
# Requirements: datetime
# Input: d0       -- datetime target date
#        rangeEnd -- datetime begining of range
#	 rangeEnd -- datetime ending of range
# Output: bool -- True if target date is in range, else False
################################################################################
def isDateBetween(d0, rangeStart, rangeEnd):
    if datetime.strptime(rangeStart, "%Y-%m-%d") <= datetime.strptime(d0, "%Y-%m-%d") <= datetime.strptime(rangeEnd, "%Y-%m-%d"):
        return True
    else:
        return False
################################################################################
# This function should send an alert but just prints screen output right now
# Requirements: none
# Input: strInput -- String to include in alert
# Output: None
################################################################################
def sendAlert(strInput):
    print(strInput)
################################################################################
# End of function definitions
################################################################################

# One week on-call rotation, so date range is today through today+6 days to identify current on-call 
strDateStart = (date.today()).strftime('%Y-%m-%d')
strDateEnd = (date.today()+timedelta(days=6)).strftime('%Y-%m-%d')

strCalendarServiceURI = "{}?subCalendarId={}&userTimeZoneId={}&start={}T00%3A00%3A00Z&end={}T00%3A00%3A00Z".format(strConfluenceRESTCalendarService, strSubCalendarID, strTimeZone, strDateStart, strDateEnd)
requestResponse = requests.get(strCalendarServiceURI, timeout=15, verify=False)
jsonResponse = requestResponse.json()

jsonEvents = jsonResponse.get('events')

for calendarItem in jsonEvents:
    strEventEnd = calendarItem.get('end').split('T')
    strEventEnd = strEventEnd[0]

    if isDateBetween(strEventEnd, strDateStart, strDateEnd):
        strRecordTitle = calendarItem.get('title')
        #print("{}:\t{}\t{}".format(strRecordTitle, calendarItem.get('start'), calendarItem.get('end') ) )

        strContact = strRecordTitle.split(strCalendarTitleDelimiter)
        try:
            strContact = strContact[1]
            strSMSContactList = "{}, {}".format(strSMSContactList, strContact)
        except:
            pass			# Do we want to notify someone of a malformed calendar entry?

fileOutput = open(strOutputFile, "w")
fileOutput.write("define contactgroup{{\n\tcontactgroup_name\t{}\n\talias\t\t\t{}\n\tmembers\t\t\t{}\n}}\n".format(strContactGroup, strContactGroupDescription, strSMSContactList)  )
fileOutput.close()

iBackupReturn = os.system(cmdBackUpContactGroupConfig)
if iBackupReturn == 0:
    iCopyFileToNagios = os.system(cmdCopyProposedContactsToNagios)
    if iCopyFileToNagios == 0:
        iConfigTestReturn = os.system(cmdTestNagiosConfig)
        if iConfigTestReturn == 0:					# Test returns 256 on bad config
            iNagiosRestart = os.system(cmdRestartNagios)
            if iNagiosRestart != 0:
                sendAlert("Nagios restart failed")
        else:
            sendAlert("Nagios config is invalid")
    else:
        sendAlert("Failed to copy proposed contact group config to Nagios")
else:
    sendAlert("Failed to back up running contact group config")
