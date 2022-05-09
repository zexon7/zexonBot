import os
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import date, datetime, timezone, timedelta
import psycopg2  
import logging
import pandas as pd

# get the value of PORT from the environment if it is set, otherwise use 80
PORT = int(os.environ.get('PORT', 80))

'''
# create table
DATABASE_URL = 
conn = psycopg2.connect(DATABASE_URL, sslmode='require')
cursor = conn.cursor() # initialize a cursor to execute order
SQL_order = """CREATE TABLE schedules(schedule_date DATE, event TEXT, chat_id INTEGER);"""
cursor.execute(SQL_order)
cursor.close()
conn.commit() # comfirm order
conn.close()
'''

# logging for debug
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

''''
    ### Schedule function ###
    add schedule
    update schedule buttonlist
        update event buttonlist
            change event
            remove event
    remove schedule buttonlist
        remove schedule function
    show schedule

    ### Order function ###
    new order
    update order buttonlist
        change item
        remove item
    remove order
    close order
    
    show help list

    button function
        show schedule's event button list query
        update schedule's event query
        remove schedule query
        update order query

    notification 
        check_schedule
    
'''

# command handler
def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def start(update, context): 
    context.bot.send_message(chat_id=update.effective_chat.id, text="Welcome to my awesome bot!")
    logging.info('[userMessage]: %s' % update.message.text)

# hello function
def hello(update, context): # update is user, context is user input
    context.bot.send_message(chat_id=update.effective_chat.id, text='Hello, {}'.format(update.message.from_user.first_name))
    logging.info('[userMessage]: %s [user_id]: %s' % (update.message.text, update.message.from_user.id))

def getUrl(update, context):
    reply_markup = InlineKeyboardMarkup([[
        InlineKeyboardButton("", url = "")
    ]])
    update.send_message(context.message.chat.id, "Github", reply_markup = reply_markup)
    logging.info('[userMessage]: %s' % update.message.text)

# add schedule
def add_schedule(update, context):
    schedule = update.message.text[5:] # get message
    new_sch_date = ''.join(schedule[:10])
    #new_sch_date = datetime.strptime(, '%Y/%m/%d') # convert new schedule date to datetime format
    event = ''.join(schedule[11:])
    print(event)
    chat_id = update.effective_chat.id
    if len(event) == 0:
        context.bot.send_message(chat_id=update.effective_chat.id, text='Please insert event\'s name after date')
        return
    # connect to database
    conn = connect()
    schedules = read_data(chat_id)
    # if date exists in schedules
    if new_sch_date in schedules:
        schedules.get(new_sch_date).append('+' + event)
        print(schedules)
        context.bot.send_message(chat_id=update.effective_chat.id, text='Schedule added ' + new_sch_date + ' ' +event)
        # convert schedules into string
        result = convertDictToString(schedules)
        print(result)
        context.bot.send_message(chat_id=update.effective_chat.id, text=result) 
        # update database
        cursor = conn.cursor() # initialize a cursor to execute order 
        selected_date_event = " ".join(schedules.get(new_sch_date))
        record = (selected_date_event, new_sch_date, chat_id)
        sql = "UPDATE schedules SET event = %s WHERE schedule_date = %s and chat_id = %s"
        cursor.execute(sql, record)
        conn.commit()
        cursor.close()
        conn.close()
    else:
        # add new schedule
        schedules[new_sch_date] = [event]
        print(schedules)
        context.bot.send_message(chat_id=update.effective_chat.id, text='Schedule added ' + new_sch_date + ' ' +event)
        # convert schedules into string
        result = convertDictToString(schedules)
        print(result)
        context.bot.send_message(chat_id=update.effective_chat.id, text=result) 
        # update database
        cursor = conn.cursor()  
        record = (new_sch_date, '+' + event, chat_id)
        sql = "INSERT INTO schedules (schedule_date, event, chat_id) VALUES (%s, %s, %s)"
        cursor.execute(sql, record)
        conn.commit()
        cursor.close()
        conn.close()
        
    logging.info('[userMessage]: %s' % update.message.text)   

# update schedule buttonlist
def update_schedule_buttonlist(update, context):
    chat_id = update.effective_chat.id
    # if schedule exists
    schedules = read_data(chat_id)
    if schedules: 
        sorted_date = sorted(list(schedules.keys()))
        button_list = []
        for each in sorted_date:
            button_list.append(InlineKeyboardButton(each, callback_data = 'update' + each))
        reply_markup=InlineKeyboardMarkup(build_menu(button_list,n_cols=2)) # n_cols = 1 is for single column and mutliple rows
        context.bot.send_message(chat_id=update.effective_chat.id, text='Choose from the following', reply_markup=reply_markup)
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text='Schedule does not exist.')

# change event
def change_event(update, context):
    change_e_date = context.user_data["selected_date"]
    selected = context.user_data["selected_event"]
    selected_id = int(selected[0])
    change = update.message.text[3:]
    print(selected)
    print(change)
    chat_id = update.effective_chat.id
    conn = connect()
    schedules = read_data(chat_id)
    # get schedule's event list
    events = schedules.get(change_e_date)
    events = " ".join(events).split('+')
    print("button_list ", events)
    events = events[1:]
    events[selected_id] = '+' + change 
    schedules[change_e_date] = events
    print(schedules)
    # convert schedules into string
    result = convertDictToString(schedules)
    print(result)
    context.bot.send_message(chat_id=update.effective_chat.id, text='Event '+ selected[1:] + ' change to ' + change)
    context.bot.send_message(chat_id=update.effective_chat.id, text=result) 
    # update database
    cursor = conn.cursor()  
    record = (" ".join(schedules.get(change_e_date)), change_e_date)
    sql = "UPDATE schedules SET event = %s WHERE schedule_date = %s"
    cursor.execute(sql, record)
    conn.commit()
    cursor.close()
    conn.close()

# remove event
def remove_event(update, context):
    remove_e_date = context.user_data["selected_date"]
    selected = context.user_data["selected_event"]
    selected_id = int(selected[0])
    print(remove_e_date)
    print(selected)
    chat_id = update.effective_chat.id
    schedules = read_data(chat_id)
    conn = connect()
    # remove event from schedule
    result = convertDictToString(schedules)
    print(result)
    schedules[remove_e_date] = schedules.get(remove_e_date).pop(selected_id)
    context.bot.send_message(chat_id=update.effective_chat.id, text='Schedule removed.\n' + result) 
    # update database
    selected_date_event = schedules.get(remove_e_date)
    cursor = conn.cursor() 
    record = (" ".join(selected_date_event), remove_e_date)
    sql = "UPDATE schedules SET event = %s WHERE schedule_date = %s"
    cursor.execute(sql, record)
    conn.commit()
    cursor.close()
    conn.close()

# remove schedule buttonlist
def remove_schedule_buttonlist(update, context):
    chat_id = update.effective_chat.id
    schedules = read_data(chat_id)
    if schedules: 
        sorted_date = sorted(list(schedules.keys()))
        button_list = []
        for each in sorted_date :
            button_list.append(InlineKeyboardButton(each, callback_data = 'remove' + each))
        reply_markup=InlineKeyboardMarkup(build_menu(button_list,n_cols=2)) # n_cols = 1 is for single column and mutliple rows
        context.bot.send_message(chat_id=update.effective_chat.id, text='Choose from the following', reply_markup=reply_markup)
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text='Currently no schedule.')
    
# show schedule
def show_schedule(update, context):

    # insert from google sheet
    group_id = #telegram group chat id
    schedules = read_data(group_id)
    exist_date = sorted(list(schedules.keys()))
    print("Date in database :", exist_date)
    
    conn = connect()
    cursor = conn.cursor()
    # Google sheet id and name
    sheet_id = ""
    sheet_name = ""
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    df = pd.read_csv(url)
    for i in range(len(df)): 
        temp = list(df.iloc[i])
        temp = [x for x in temp if str(x) != 'nan']
        s_date = datetime.strptime(temp[0], '%Y/%m/%d').date()
        s_date = s_date.strftime("%Y/%m/%d")
        event = " ".join(['+'+ e for e in temp[1:]])
        # sql insert
        if s_date not in exist_date:
            record = (s_date, event, group_id)
            sql = "INSERT INTO schedules (schedule_date, event, chat_id) VALUES (%s, %s, %s)"
            cursor.execute(sql, record)
            conn.commit()
            print("New schedule : ", s_date, event)
            continue
        else:
            exist_date.remove(s_date)
            record = (event, s_date, group_id)
            sql = "UPDATE schedules SET event = %s WHERE schedule_date = %s and chat_id = %s"
            cursor.execute(sql, record)
            conn.commit()
            print("Update schedule : ", s_date, event)  

    # if date does not show on sheet, remove schedule
    for d in exist_date:
        sql = "DELETE FROM schedules WHERE schedule_date = %s"
        cursor.execute(sql, [d])
        conn.commit()

    # get corresponding chat id
    chat_id = update.effective_chat.id
    schedules = read_data(chat_id)
    print("Show schedule\n", schedules)
    if schedules: 
        schedules = convertDictToString(schedules)
        print(schedules)
        context.bot.send_message(chat_id=update.effective_chat.id, text=schedules) 
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text='Currently no schedule.')
    logging.info('[userMessage]: %s' % update.message.text) 









### Order function ###
def new_order(update, context):

    # read file
    orders = read_file('orders.txt')
    # username
    user = str(update.message.from_user.first_name)
    # new item name
    new_order = str(update.message.text[5:])

    # if there is no space between /new and [order]
    if update.message.text[4] != " ": 
        context.bot.send_message(chat_id=update.effective_chat.id, text='Invalid input.')
        return

    # if user's order exist 
    if user in orders: 
        orders[user] = orders.get(user) + " " + new_order # '+' for splitting user's order to list 
        print("User exist, add to user's order\n", orders)
    else:
        orders[user] = new_order

    write_file("orders", orders)
    result = dictToString(orders)
    context.bot.send_message(chat_id=update.effective_chat.id, text = result) 

    logging.info('[userMessage]: %s' % update.message.text) 

# update order buttonlist
def update_order_buttonlist(update, context):

    orders = read_file('orders.txt')
    user = str(update.message.from_user.first_name)

    if user in orders:
        items = orders.get(user) # get user's order
        items = items.split(" ") # split order into list
        button_list = []
        for i,each in enumerate(items):
            button_list.append(InlineKeyboardButton(each, callback_data = 'order'+ str(i) + each))
        reply_markup=InlineKeyboardMarkup(build_menu(button_list,n_cols=1)) # n_cols = 1 is for single column and mutliple rows
        context.bot.send_message(chat_id=update.effective_chat.id, text='Choose from the following', reply_markup=reply_markup)
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text='You don\'t have any order.')

# change item
def change_item(update, context):

    if update.message.text[3] != " ":
        context.bot.send_message(chat_id=update.effective_chat.id, text='Invalid input.')
        return

    orders = read_file('orders.txt')
    user = str(update.message.from_user.first_name)
    selected_item = context.user_data.get("selected_item") # item name to be changed
    new_item = update.message.text[4:] # new item name

    # change item in order
    change = orders.get(user)
    change = change.split(" ")
    change[int(selected_item[0])] = new_item # change item to new item by item id
    change = " ".join(change)
    orders[user] = change
    print("Current order after changing item\n", orders)

    update.message.reply_text('Item '+ selected_item[1:] + ' change to ' + new_item)
    write_file('orders', orders)
    result = dictToString(orders)
    context.bot.send_message(chat_id=update.effective_chat.id, text=result) 

# remove item
def remove_item(update, context):

    # read textfile
    orders = read_file('orders.txt')
    user = str(update.message.from_user.first_name)
    selected_item = context.user_data.get("selected_item")

    # remove item
    change = orders.get(user)
    change = change.split(" ")
    del change[int(selected_item[0])]
    if len(change) == 0:
        del orders[user]
    else:
        change = " ".join(change)
        orders[user] = change
    print("Current order after removing item\n", orders)

    update.message.reply_text('Item '+ selected_item[1:] + ' removed.')
    # if orders is empty, delete txt file
    if len(orders) == 0:
        os.remove('orders.txt')
        return
    write_file('orders', orders)
    result = dictToString(orders)
    context.bot.send_message(chat_id=update.effective_chat.id, text=result)  

# remove order
def remove_order(update, context):

    orders = read_file('orders.txt')
    user = str(update.message.from_user.first_name)

    if user in orders:
        del orders[user]
        if len(orders) == 0:
            os.remove('orders.txt')
            return
        write_file('orders', orders)
        result = dictToString(orders)
        context.bot.send_message(chat_id=update.effective_chat.id, text=result)
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text='You don\'t have any order.')

# close order
def close_order(update, context):
    
    orders = read_file('orders.txt')
    if orders:
        result = dictToString(orders)
        context.bot.send_message(chat_id=update.effective_chat.id, text=result)
        os.remove('orders.txt')
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text='Currently no order.')
    
# show help list
def help_list(update, context):
    help =  "hello or Hello to receive a greeting from bot\n"\
            "/add YYYY/MM/DD [your new event] to add your new schedule\n"\
            "/update to update your schedule\n"\
            "/remove to remove your schedule\n"\
            "/s to show schedule\n"\
            "/new [your order] to add your order\n"\
            "/want to change your order\n"\
            "/dontwant to remove your order\n"\
            "/done to close order\n"\
            "/notify to enable notification\n"\
            "/stopnotify to stop notification\n"
    context.bot.send_message(chat_id=update.effective_chat.id, text=help)

# button function
def button(update, context):

    query = update.callback_query
    query.answer()
    print("query data\n", query.data)
    #print(type(query.data))
    chat_id = update.effective_chat.id
    schedules = read_data(chat_id)
        
    if query.data.startswith("update"): # show schedule's event button list query
        print(query.data)
        selected = query.data[6:] # date
        reply_markup = update_event_buttonlist(str(selected), schedules)
        context.user_data["selected_date"] = selected 
        query.edit_message_text(text='Choose from the following', reply_markup=reply_markup)

    elif query.data.startswith("event"): # update schedule's event query
        print(query.data)
        selected_date = context.user_data["selected_date"]
        selected = query.data[5:] # event
        query.edit_message_text(text="Selected option: " + str(selected_date) + " " + str(selected[1:]) + "\nType /c [your new event] to change or /d to remove")
        context.user_data["selected_event"] = selected

    elif query.data.startswith("remove"): # remove schedule query
        print(query.data)
        selected = query.data[6:] # date
        selected_date = str(selected).replace("/", "-")
        selected_date = datetime.strptime(selected_date,"%Y-%m-%d").date()
        print(selected_date)
        # update database
        conn = connect()
        cursor = conn.cursor()
        sql = "DELETE FROM schedules WHERE schedule_date = %s"
        cursor.execute(sql, [selected_date])
        conn.commit()
        cursor.close()
        conn.close()
        schedules = read_data(chat_id)
        schedules = convertDictToString(schedules)
        if len(schedules) > 0:
            query.edit_message_text(text='Schedule removed.\n' + schedules) 
        else:
            query.edit_message_text(text='Schedule removed.')

    elif query.data.startswith("order"): # update order query
        selected = query.data[5:] # id with item's name
        query.edit_message_text(text=f"Selected option: {selected[1:]}\ntype /co [your new order] to change or /ro to remove")
        context.user_data["selected_item"] = selected

# notification according to chat_id
def check_schedule(live_bot):

    # get today's date
    today = date.today().strftime('%Y-%m-%d') 

    # if time is larger than 9.00 don't execute
    utc = datetime.utcnow().replace(tzinfo=timezone.utc)
    today_date_time = utc.astimezone(timezone(timedelta(hours=8)))
    current_time = today_date_time.strftime("%H:%M:%S")
    end = '09:00:00'
    if current_time > end:
        print("Current time : ", current_time)
        return
    
    conn = connect()
    cursor = conn.cursor() # initialize a cursor to execute order 
    # remove old schedule
    sql = "DELETE FROM schedules WHERE schedule_date < %s" 
    cursor.execute(sql, [today])
    conn.commit()
    
    # select today's schedule from database
    sql = "SELECT * FROM schedules WHERE schedule_date = %s" 
    cursor.execute(sql, [today])
    conn.commit()
    rows = cursor.fetchall()
    print(rows)
    schedules = {}
    for r in rows:
        r = list(r)
        id = r[2]
        #date_event = r[1].split(" ")
        date_event = r[1]
        print(date_event)
        schedules[id] = date_event # id : schedule
    print("chat_id schedules\n", schedules)
    cursor.close()
    conn.close()

    # if id has schedule today, send today's schedule
    for id in schedules: # for id in today's schedule
        schedule = schedules.get(id).split('+')
        print(schedule)
        today_schedule = ""
        for e in schedule: # convert list to string
            today_schedule += e + "\n"
        print("Today's schedule\n" + today_schedule)
        live_bot.bot.sendMessage(chat_id = id, text="Today's schedule\n" + today_schedule + "\n")
    






### function ###
# function to connect database:
def connect():
    # PostgreSQL connection
    DATABASE_URL = os.environ['DATABASE_URL']
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    return conn

# function to read database
def read_data(chat_id):
    conn = connect()
    cursor = conn.cursor() # initialize a cursor to execute order  
    sql = "SELECT schedule_date, event FROM schedules WHERE chat_id = %s ORDER BY schedule_date "
    cursor.execute(sql, [chat_id])
    conn.commit()
    rows = cursor.fetchall()
    print(rows)
    schedules = {}
    for r in rows:
        r = list(r)
        d = r[0].strftime("%Y/%m/%d")
        print(r[1].split(" "))
        schedules[d] = r[1].split(" ")
    print("Schedules", schedules)
    cursor.close()
    conn.close()
    return schedules

# function to convert dict to string
def convertDictToString(schedules):
    # sort date
    sorted_l = sorted(list(schedules.keys()))
    print(sorted_l)
    schedules = schedules
    print(schedules)
    # convert schedules into string
    stringlist = ""
    for d in sorted_l:
        print(schedules.get(d))
        #stringlist += d + schedules.get(d) +"\n"
        stringlist += d + " " + " ".join(schedules.get(d)).replace('+', '').replace("  ", " ") + "\n"
    print("convertDictToString function\n", stringlist)
    return stringlist

# function to read file
def read_file(filename):
    if os.path.exists(filename):
        data = {}
        with open(filename, encoding='utf-8') as FILE:
            for d in FILE:
                if d == '\n':
                    break
                d = d.replace('\n', '')
                d = d.split(':')
                print(d)
                data[d[0]] = "".join(d[1]) # convert list to string
        print("Current order:\n", data)
    else:
        data = {}
    return data

# function to write file
def write_file(filename, data):
    text = ""
    for key, value in data.items():
        text += key + ":" + value + "\n"
    with open(filename+'.txt', 'w', encoding='utf-8') as FILE: # write schedule in a textfile
        print(text, file=FILE)

# function to convert dict to string
def dictToString(data):   
    text = ""
    for key, value in data.items():
        value = value.replace('\n', '')
        text += key + " " + value + "\n"
    return text

# function to build button
def build_menu(buttons,n_cols,header_buttons=None,footer_buttons=None):
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)
    return menu

# update event buttonlist
def update_event_buttonlist(update_sch_date, schedules):
    events = schedules.get(update_sch_date)
    print("update event buttonlist", events)
    events = " ".join(events).split('+')
    print("update event buttonlist", events)
    button_list = []
    for i,each in enumerate(events[1:]):
        button_list.append(InlineKeyboardButton(each, callback_data = 'event' + str(i) + each))
    reply_markup=InlineKeyboardMarkup(build_menu(button_list,n_cols=1)) # n_cols = 1 is for single column and mutliple rows
    return reply_markup



### start bot ###
if __name__ == '__main__':
    
    # Bot's API token
    TOKEN = 
    updater = Updater(TOKEN)

    # for quick access
    bot = updater.dispatcher

    # handler
    bot.add_handler(MessageHandler(Filters.regex('^hello|Hello$'), hello))
    #bot.add_handler(CommandHandler('url', getUrl))
    bot.add_handler(CommandHandler('add', add_schedule))
    bot.add_handler(CommandHandler('update', update_schedule_buttonlist))
    bot.add_handler(CommandHandler('c', change_event))
    bot.add_handler(CommandHandler('d', remove_event))
    bot.add_handler(CommandHandler('remove', remove_schedule_buttonlist))
    bot.add_handler(CommandHandler('s', show_schedule))
    #bot.add_handler(MessageHandler(Filters.regex('^s$'), show_schedule))
    
    bot.add_handler(CommandHandler('new', new_order))
    bot.add_handler(CommandHandler('want', update_order_buttonlist))
    bot.add_handler(CommandHandler('co', change_item))
    bot.add_handler(CommandHandler('ro', remove_item))
    bot.add_handler(CommandHandler('dontwant', remove_order))
    bot.add_handler(CommandHandler('done', close_order))

    # execute when bot wake up on heroku
    check_schedule(bot)
    #bot.add_handler(CommandHandler("notify", notification))
    #bot.add_handler(CommandHandler("stopn", stop_notification))
    bot.add_handler(CommandHandler('help', help_list))

    # button event handler
    bot.add_handler(CallbackQueryHandler(button))
    
    #updater.start_polling() # start the bot

    # webhook setting
    #'''
    updater.start_webhook(listen="0.0.0.0",
                          port=int(PORT),
                          url_path=TOKEN,
                          webhook_url='' + TOKEN)
    #'''
    
    updater.idle() # for ctrl+c to stop bot