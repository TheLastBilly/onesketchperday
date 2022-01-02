from django.utils import timezone
import os, base64
from calendar import monthrange

ID_LENGTH = 10

def getTimeStampFromDate(date):
    return getTimeStamp(date.year, date.month, date.day)

def getTimeStamp(year, month, day):
    return int(year)*10000 + int(month)*100 + int(day)

def getDateFromTimestamp(timestamp):
    year = int(timestamp/10000)
    month = int((timestamp - year*10000)/100)
    day = int(timestamp - int(timestamp/100)*100)

    if year > 3000:
        year = 3000
    if year < 2000:
        year = 2000
    
    if month < 1:
        month = 1
    if month > 12:
        month = 12

    maxDays = monthrange(year, month)[-1]
    if day > maxDays:
        day = maxDays
    if day < 1:
        day = 1

    return timezone.datetime(year, month, day)

def validateTimeStamp(timestamp):
    return getTimeStampFromDate(getDateFromTimestamp(timestamp))

def getRandomBase64String(lenght=ID_LENGTH):
    new_id = base64.b64encode(os.urandom(lenght))
    return str(new_id, "utf-8").replace('/', 's')[:lenght]