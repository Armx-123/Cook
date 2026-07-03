from random import randint as r

open("times.txt","w").close()
def cron():
    minute = r(0,59)
    hour = r(0,22)
    return minute,hour

for i in range(0,6,1):
    t= f"{cron()[0]} {cron()[1]} * * *"
    with open("times.txt","a") as f:
        f.write(t+"\n")
    print(t)
