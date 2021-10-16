from datetime import datetime
import holidays


us_holidays = holidays.UnitedStates()


def rnd(f):
    return round(f, 2)

def sdate():
    return str(datetime.now())[:19]

def get_last_market_day():
    c = 1
    date = datetime.today()
    if datetime.now().hour < 10:
        date = datetime.today() - timedelta(days=c)

    while (not date.isoweekday() in range(1, 6)) or date in us_holidays:

        date = datetime.today() - timedelta(days=c)
        c += 1
    return str(date)[:10]

def today():
    return str(datetime.now())[:10]