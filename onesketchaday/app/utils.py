import datetime, os, base64

ID_LENGTH = 10

def getTimeStampFromDate(date):
    return getTimeStamp(date.year, date.month, date.day)

def getTimeStamp(year, month, day):
    return int(year)*10000 + int(month)*100 + int(day)

def getDateFromTimestamp(timestamp):
    year = int(timestamp/10000)
    month = int((timestamp - year*10000)/100)
    day = int(timestamp - int(timestamp/100)*100)
    return datetime.datetime(year, month, day)

def getRandomBase64String(lenght=ID_LENGTH):
    new_id = base64.b64encode(os.urandom(lenght))
    return str(new_id, "utf-8").replace('/', 's')[:lenght]