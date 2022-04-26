import random
import telebot
from telebot import types
token = "5315096949:AAEGED-vsSUIB8FA3n7ypGnNRv7jsPw--hU"
bot = telebot.TeleBot(token)
import logging
import psycopg2
from datetime import date, timedelta
import locale

locale.setlocale(locale.LC_TIME, '')

organization_field_length = 15
faculty_field_length = 10
group_field_length = 5

WEEK_TYPE_TOP='top'
WEEK_TYPE_BOTTOM='bottom'
SECONDS_IN_WEEK=604800
DAYS=("пн", "вт","ср","чт","пт","сб","вс")
BUTTON_CUR_WEEK='Расписание на текущую неделю'
BUTTON_NEXT_WEEK='Расписание на следующую неделю'

class ScheduleDB:
    def __init__(self):
        self.con = psycopg2.connect(
            dbname="bot",
            user="postgres",
            password="12345",
            host="localhost")
        self.cur = self.con.cursor()

        logging.basicConfig()
        self.logger = logging.getLogger('db-logger')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.con.commit()
        self.con.close()

@bot.message_handler(commands=['help'])
def help_command(message):
    bot.send_message(
        message.chat.id,
        '1) /go \n' +
        '2) /schedule \n' +
        '3) /MTYCI \n'
        '4) /week \n'

    )

@bot.message_handler(commands=['start'])
def start(message):
    keyboard = types.ReplyKeyboardMarkup()
    keyboard.row(*DAYS, BUTTON_CUR_WEEK, BUTTON_NEXT_WEEK)
    bot.send_message(message.chat.id, 'Здравствуйте, хотите узнать расписание занятий?', reply_markup=keyboard)



@bot.message_handler(commands=['MTYCI'])
def start_message(message):
    bot.send_message(message.chat.id, 'Tебе сюда – https://mtuci.ru/')

@bot.message_handler(commands=['schedule'])
def start_message(message):
    bot.send_message(message.chat.id, 'Tебе сюда – https://mtuci.ru/time-table/')

@bot.message_handler(commands=['week'])
def start_message(message):
    if weektype() == WEEK_TYPE_TOP:
        bot.send_message(message.chat.id, 'верхняя')
    else:
        bot.send_message(message.chat.id, 'нижняя')


@bot.message_handler(content_types=['text'])
def answer(message):
    if message.text.lower() in DAYS:
        today = date.today()
        daynum = DAYS.index(message.text.lower())
        bot.send_message(
            message.chat.id,
            render_schedule(today - timedelta(days = today.isoweekday() - daynum - 1))
        )
        return
    if message.text == BUTTON_CUR_WEEK:
        today = date.today()
        monday = date.today() - timedelta(days=today.isoweekday() - 1)
        sunday = monday + timedelta(days=5)
        bot.send_message(
            message.chat.id,
            render_schedule(monday, sunday)
        )
        return
    if message.text == BUTTON_NEXT_WEEK:
        today = date.today()
        monday = date.today() + timedelta(days=8 - today.isoweekday())
        sunday = monday + timedelta(days=5)
        bot.send_message(
            message.chat.id,
            render_schedule(monday, sunday)
        )
        return
    bot.send_message(message.chat.id,"Я вас не понимаю")

def weektype(dateobj=None):
    if not dateobj:
        dateobj = date.today()

    startyear = dateobj.year
    if dateobj.month < 8:
        startyear -= 1

    startobj = date(startyear, 9, 1)
    if startobj.isoweekday == 7:
        startobj += timedelta(days=1)
    elif startobj.isoweekday() != 1:
        startobj -= timedelta(days=startobj.isoweekday() - 1)

    delta = dateobj - startobj
    if delta.total_seconds() // SECONDS_IN_WEEK % 2:
        return WEEK_TYPE_BOTTOM
    return WEEK_TYPE_TOP

def render_schedule(begin, end=None):
    if not end:
        end = date(begin.year, begin.month, begin.day)
    cur = date(begin.year, begin.month, begin.day)
    ans = ''
    with ScheduleDB() as db:
        while cur < (end + timedelta(days=1)):
            ans += f"{cur.strftime('%A')}\n---------------------\n"
            if weektype(cur) == WEEK_TYPE_TOP:
                week = 'top'
            else:
                week = 'bottom'

            db.cur.execute("""
                SELECT
                    s.name,
                    tt.room_numb,
                    tt.start_time,
                    tea.full_name
                FROM timetable tt
                JOIN subject s
                    ON s.id = tt.subject
                JOIN teacher tea
                    ON tea.subject = s.id
                WHERE tt.week = %(week)s
                AND tt.day = %(day)s
            """, dict(week=week, day=DAYS[cur.isoweekday() - 1]))
            for item in db.cur.fetchall():
                ans += f'{item[0]}\t{item[1]}\t{item[2]}\t{item[3]}\n'

            ans += "---------------------\n"
            cur += timedelta(days=1)

    return ans

bot.polling(none_stop=True, interval=0)