"""datetime.py
"""

import time as tmod

def parse_tz_offset_minutes(val):
    """handle value list "06:00"  or "-5:30" or something like that.  '-5' will be -5 hours and '5' is 5 hours"""

    print(f"parse_tz_offset_minutes {val}")        
    sign = 1
    if type(val) == str:
        if '-' in val:
            val = val.split('-')[-1]
            sign = -1
            print("-1")
        if '+' in val:
            val = val.split('+')[-1]
            sign = 1
            print("1")
        if ':' in val:
            hm = val.split(':')
            print("{hm}")
            val = (int(hm[1])*60+int(hm[0])) * sign
        else:
            val=int(val) * sign
    if type(val) == float:
        minutes = val*60
    else:
        val = int(val)*60*sign    
    print(f"parsed {val}")
    return val
         