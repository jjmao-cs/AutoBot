"""
Author: Jonathan (jjmao.cs@gmail.com)
"""


import configparser
import logging
#import time
import os 

import telegram
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler
from telegram import ReplyKeyboardMarkup
from script import sign

# DEBUG
''' 
In "False" state, 
1) The signin timer will change from hour to seconds.
2) All sign.main will not be active. Such that the signin system won't be affect during testing.
''' 
release = True

# Files Settings
dir_path = os.path.dirname(os.path.realpath(__file__)) + '/'
config_file = dir_path + 'config.ini'

# Job description
job_description = '機房值班'

# Load data from config.ini file
config = configparser.ConfigParser()
config.read(config_file)

# Enums.
signout = 'SIGNOUT'
signin = 'SIGNIN'
TOKEN = config['TELEGRAM']['ACCESS_TOKEN']

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Welecome Message
welcome_message = 'Welcome! 目前提供\n' \
    '綁定/修改，如：「/add <portal學號> <portal密碼>」\n' \
    '查詢綁定，如：「/now」\n' \
    '移除綁定，如：「/del」\n' \
    '定時簽到，如：「/in <時間(hr)> (選填)」\n' \
    '直接簽退，如：「/out」'

# KeyBoard Default Message 
reply_keyboard_markup = ReplyKeyboardMarkup([['/in 8'],['/out']], resize_keyboard=True)


'''
    Return state or False when file can't open (not exist).
'''
def check_sign_state(user_id):
    with open(dir_path + str(user_id),"r+") as afile:
        return eval(afile.read())['STATE'] # Read dict from file
    #logger.error('User "%s" config file not found', user_id)

def change_sign_state(user_id):
    with open(dir_path + str(user_id),"r") as afile:
        r = eval(afile.read())
    with open(dir_path + str(user_id),"w") as afile:
        if r['STATE'] == signout:
            r['STATE'] = signin
            afile.write(str(r))
            return True
        elif r['STATE'] == signin:
            r['STATE'] = signout
            afile.write(str(r))
            return True
        else:
            logger.error('User "%s" can\'t change sign state.', user_id)
            raise ValueError


def get_account(user_id):
    try:
        with open(dir_path + str(user_id),"r") as afile:
            r = eval(afile.read())
            return r["ACCOUNT"], r['PASSWORD']
    except:
        return False, False


def add_account(user_id, account, password):
    with open(dir_path + str(user_id), "w") as afile:
        r = {}
        r['ACCOUNT'] = account
        r['PASSWORD'] = password
        r['STATE'] = signout
        
        afile.write(str(r))
        return True


def del_acconut(user_id):
    if os.path.exists(dir_path + str(user_id)):
        os.remove(dir_path + str(user_id))
        return True
    else:
        return False


def alarm(callbackcontext):
    """Send the alarm message."""
    job = callbackcontext.job
    user_id = job.context[1]
    due = job.context[2]
    callbackcontext.bot.send_message(job.context[0], text='值班'+str(due)+'小時')
    account, password = get_account(user_id)
    if account and password:
        if check_sign_state(user_id) == signin:
            ''' Comfirm the account information is correct '''
            if not sign.auth_check(account, password):
                callbackcontext.bot.send_message(job.context[0], text='[警告] \nPortal 驗證失敗\n請"手動"簽退')
                return
            if release:
                sign.main(account, password, job_description)
            callbackcontext.bot.send_message(job.context[0], text='簽退成功')
            change_sign_state(user_id)


def set_timer(update, context, due):
    """Add a job to the queue."""
    chat_id = update.message.chat_id
    user_id = str(update.message.from_user.id)

    '''Add job to queue and stop current one if there is a timer already'''
    if 'job' in context.chat_data:
        # To replace old job removal 
        old_job = context.chat_data['job']
        old_job.schedule_removal()
    ''' Transfer from sec. to hr. '''
    if release:
        due = due *3600
        new_job = context.job_queue.run_once(alarm, due, context=(chat_id,user_id,due/3600))
    else:
        new_job = context.job_queue.run_once(alarm, due, context=(chat_id,user_id,due)) # In non-release mode, due will mantain in seconds.
    context.chat_data['job'] = new_job
    logger.info('User "%s" set timer %d hr', user_id, due/3600)
    update.message.reply_text('計時器設定成功')


def unset_timer (update, context):
    """Remove the job if the user changed their mind."""
    if 'job' not in context.chat_data:
        return

    job = context.chat_data['job']
    job.schedule_removal()
    del context.chat_data['job']
    update.message.reply_text('[提醒] \n簽到計時尚未結束\n將停止計時並簽退')


#====================== Handlers ======================  

def start_handler(update, context):
    """Send a message when the command /start is issued."""
    update.message.reply_text(welcome_message)


def help_handler(update, context):
    """Send a message when the command /help is issued."""
    #update.message.reply_text(welcome_message, reply_markup=reply_keyboard_markup)
    update.message.reply_text(welcome_message, reply_markup=reply_keyboard_markup)


def add_handler(update, context):
    """Send a message when the command /add is issued."""
    text = update.message.text
    user_id = str(update.message.from_user.id)
    try:
        account = text.split()[1]
        password = text.split()[2]
    except IndexError:
        update.message.reply_text("[警告] 輸入格式錯誤")
        return
    
    """Comfirm the account information is correct"""
    if not sign.auth_check(account, password):
        update.message.reply_text("[警告] Portal 驗證失敗")
        return
    
    """Add Portal Account info into INI file"""
    add_account(user_id, account, password)
    update.message.reply_text("新增/修改 操作成功 xорошо!")


def now_handler(update, context):
    text = update.message.text
    user_id = str(update.message.from_user.id)

    """Lookup Portal Account info from INI file"""
    account, _ = get_account(user_id)
    if account:
        update.message.reply_text("綁定protal: "+account+" xорошо !")
    else:
        update.message.reply_text("未綁定任何帳號 xорошо !")


def del_handler(update, context):
    text = update.message.text
    user_id = str(update.message.from_user.id)

    """Delete Portal Account info from INI file"""
    if del_acconut(user_id):
        update.message.reply_text("移除綁定 操作成功 xорошо !")
    else:
        update.message.reply_text("[警告] 移除綁定失敗 : 帳號不存在 !")


def signin_handler(update, context):
    text = update.message.text
    user_id = str(update.message.from_user.id)
    due = 0

    ''' Check and Get account info '''
    if not os.path.exists(dir_path + str(user_id)):
        update.message.reply_text('[警告] \n帳號尚未綁定 POI~\n使用/add指令綁定修改帳號')
        return False
    account, password = get_account(user_id)
    ''' Check sign status info '''
    if check_sign_state(user_id) != signout:  
        update.message.reply_text('已經簽到  xорошо !\n欲修改簽到請先簽退')
        return
    ''' Check if input time valid '''
    try:
        due = int(text.split()[1])
        if due <= 8 and due > 0:
            set_timer(update, context, due) 
        else:
            raise ValueError
    except IndexError:
        update.message.reply_text('直接簽到...')
    except ValueError:
        update.message.reply_text('[警告] 時間設定錯誤 xорошо !')
        return
    ''' Sign In '''
    ''' Comfirm the account information is correct '''
    if not sign.auth_check(account, password):
        update.message.reply_text("[警告] Portal 驗證失敗")
        return
    if release:
        sign.main(account, password, job_description)
    update.message.reply_text('簽到成功')
    change_sign_state(user_id)


def signout_handler(update, context):
    user_id = str(update.message.from_user.id)

    ''' Check and Get account info '''
    if not os.path.exists(dir_path + str(user_id)):
        update.message.reply_text('[警告] \n帳號尚未綁定 POI~\n使用/add指令綁定修改帳號')
        return False
    account, password = get_account(user_id)
    ''' Check sign status info '''
    if check_sign_state(user_id) != signin:  
        update.message.reply_text('[警告] 沒有簽到記錄 xорошо !')
        return
    ''' Sign Out '''
    ''' Comfirm the account information is correct '''
    if not sign.auth_check(account, password):
        update.message.reply_text("[警告] Portal 驗證失敗")
        return 
    if release:
        sign.main(account, password, job_description)
    update.message.reply_text('簽退成功')
    change_sign_state(user_id)
    unset_timer(update, context)  


def uidQuery_handler(update, context):
    """Get your uid."""
    user_id = update.message.from_user.id
    update.message.reply_text(user_id)


def error_handler(update, context):
    """Log Errors caused by Updates."""
    logger.error('Update "%s" caused error "%s"', update, context.error)
    update.message.reply_text('[錯誤] \n非法字元或是錯誤出現，\n請擷取畫面聯絡管理員 Q_Q')


def reply_handler(update, context):
    """Reply message."""
    text = update.message.text
    user_id = update.message.from_user.id
    update.message.reply_text(text)


def main():
    updater = Updater(TOKEN, use_context=True)
    ''' New a dispatcher for bot '''
    dispatcher = updater.dispatcher
    '''
     Add handler for handling message, there are many kinds of message. 
     For this handler, it particular handle text message.
    '''
    dispatcher.add_handler(CommandHandler('start', start_handler))
    dispatcher.add_handler(CommandHandler('help', help_handler))
    dispatcher.add_handler(CommandHandler('add', add_handler))
    dispatcher.add_handler(CommandHandler('now', now_handler))
    dispatcher.add_handler(CommandHandler('del', del_handler))
    dispatcher.add_handler(CommandHandler('in', signin_handler))
    dispatcher.add_handler(CommandHandler('out', signout_handler))
    dispatcher.add_handler(CommandHandler('uid', uidQuery_handler))
    dispatcher.add_handler(MessageHandler(Filters.text, reply_handler))
    #dispatcher.add_error_handler(error_handler)


    print('handler set.')
    updater.start_webhook(listen='0.0.0.0',
                    port=443,
                    url_path=TOKEN,
                    key='self_ssl/private.key',
                    cert='self_ssl/cert.pem',
                    webhook_url='https://signbot.ee.ncu.edu.tw/'+TOKEN)


if __name__ == "__main__":
    # Running server
    main()

'''# Test Case
print(check_sign_state(308442768))
print(change_sign_state(308442768))
print(check_sign_state(308442768))'''