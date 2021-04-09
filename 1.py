import os
import datetime

for i in range(1, 1000):
    date = (datetime.datetime.now() + datetime.timedelta(days=i)).strftime("%m %d %y")
    os.mkdir(f"games_logs/{date}")
