import genshinstats as gs
from genshinstats.errors import NotLoggedIn, TooManyRequests
from pyrogram import Client
from pyrogram import filters as Filters
from pyrogram.types import Message, User
from pyrogram.errors import BadRequest, FloodWait
import json
import time
from apscheduler.schedulers.background import BackgroundScheduler

# load config json
path = "./config.json"
with open(path, 'r+') as f:
    config = json.load(f)
f.close()

global_debug_flag = config.get("global_debug_flag")
global_log_flag = config.get("global_log_flag")

if global_log_flag:
    with open('bot.log', 'a') as log_file:
        log_file.write(f"[=====][{time.asctime(time.localtime(time.time()))}] == LOG START ==\n")

# set timezone for APScheduler
tz = config.get("tz")

# telegram developer api
api_id = config.get("api_id")
api_hash = config.get("api_hash")

# group chat id for broadcast msg
chat_id = config.get("tg_chat_id")

lang = config.get("lang")
resin_warning_limit = config.get("resin_warning_limit")
coin_warning_limit = config.get("coin_warning_limit")
bot_username = config.get("bot_username")

checkall_cron_hours = config.get("checkall_cron_hours")
reward_cron_hour = config.get("reward_cron_hour")
reward_cron_minute = config.get("reward_cron_minute")

# init bot api
bot_app = Client("my_account", api_id, api_hash)


# reformat date and time for debug print
def getLogTime():
    localtime = time.asctime(time.localtime(time.time()))
    return localtime


def log_to_file(string):
    if global_log_flag:
        with open('bot.log', 'a') as log_file:
            log_file.write(string+"\n")


def debug_print(string):
    payload = f"[DEBUG][{getLogTime()}]{string}"
    if global_debug_flag:
        print(payload)
        log_to_file(payload)


def error_print(string):
    payload = f"[ERROR][{getLogTime()}]{string}"
    print(payload)
    log_to_file(payload)


def log_print(string):
    payload = f"[ LOG ][{getLogTime()}]{string}"
    print(payload)
    log_to_file(payload)


# set cookie for genshinstats
def setGsCookie(user):
    gsCookieLtuid = config["user_data"][user]["gs_cookie"]["ltuid"]
    gsCookieLtoken = config["user_data"][user]["gs_cookie"]["ltoken"]
    gs.set_cookie(ltuid=gsCookieLtuid, ltoken=gsCookieLtoken)


# telegram user command handler - ping
@bot_app.on_message(Filters.command("ping") | Filters.command("ping@"+bot_username))
def ping(client: Client, message: Message):
    try:
        message.reply("pong!")
        log_print(f" Ping: {message.from_user.username}")
    except BadRequest as e:
        error_print(f"[TG400] Ping: {message.from_user.username}")
    except FloodWait as e:
        time.sleep(e.x)


# telegram user command handler - check my resin
@bot_app.on_message(Filters.command("resin") | Filters.command("resin@"+bot_username))
def checkResin(client: Client, message: Message):
    for user in config["user_data"]:
        try:
            if message.from_user.id == config["user_data"][user]["tg_uid"]:
                debug_print(f" Checking resin for {user}")
                setGsCookie(user)
                try:
                    notes = gs.get_notes(config["user_data"][user]["gs_uid"])
                except NotLoggedIn as e:
                    message.reply(f"查询失败[GS]")
                    error_print(f"[GS] {user}'s cookies have not been provided.")
                except TooManyRequests as e:
                    error_print(f"[GS] {user} made too many requests and got ratelimited")
                if notes['resin'] is not None:
                    message.reply(f"让我康康你的树脂有多少了: {notes['resin']}/{notes['max_resin']}")
                    log_print(f" Resin check: {message.from_user.username}")
                else:
                    log_print(f" Resin check: failed")
                debug_print(f" Checking for {user} finished")
        except BadRequest as e:
            error_print(f"[TG400] Resin check: {message.from_user.username}")
        except FloodWait as e:
            time.sleep(e.x)


# telegram user command handler - check my coin
@bot_app.on_message(Filters.command("coin") | Filters.command("coin@"+bot_username))
def debug_checkAll(client: Client, message: Message):
    for user in config["user_data"]:
        try:
            if message.from_user.id == config["user_data"][user]["tg_uid"]:
                debug_print(f" Checking coin for {user}")
                setGsCookie(user)
                try:
                    notes = gs.get_notes(config["user_data"][user]["gs_uid"])
                except NotLoggedIn as e:
                    message.reply(f"查询失败[GS]")
                    error_print(f"[GS] {user}'s cookies have not been provided.")
                except TooManyRequests as e:
                    error_print(f"[GS] {user} made too many requests and got ratelimited")
                if notes['realm_currency'] is not None:
                    message.reply(f"让我康康你的洞天宝钱有多少了: {notes['realm_currency']}/{notes['max_realm_currency']}")
                    log_print(f" Coin check: {message.from_user.username}")
                else:
                    log_print(f" Coin check: failed")
                debug_print(f" Checking coin for {user} finished")
        except BadRequest as e:
            error_print(f"[TG401] Coin check: {message.from_user.username}")
        except FloodWait as e:
            time.sleep(e.x)


# telegram debug command handler - debug check all
@bot_app.on_message(Filters.command("debug_checkall") | Filters.command("debug_checkall@"+bot_username))
def debug_checkall(client: Client, message: Message):
    try:
        message.reply("DEBUG: CheckAll start!")
        checkAllNotes()
        message.reply("DEBUG: CheckAll finished!")
        log_print(f" DEBUG CheckAll: {message.from_user.username}")
    except BadRequest as e:
        error_print(f"[TG400] DEBUG CheckAll: {message.from_user.username}")
    except FloodWait as e:
        time.sleep(e.x)


# telegram debug command handler - debug claim all
@bot_app.on_message(Filters.command("debug_claimall") | Filters.command("debug_claimall@"+bot_username))
def debug_claimall(client: Client, message: Message):
    try:
        message.reply("DEBUG: ClaimAll start!")
        claimAllDailyReward()
        message.reply("DEBUG: ClaimAll finished!")
        log_print(f" DEBUG ClaimAll: {message.from_user.username}")
    except BadRequest as e:
        error_print(f"[TG400] DEBUG ClaimAll: {message.from_user.username}")
    except FloodWait as e:
        time.sleep(e.x)


def claimAllDailyReward():
    for user in config["user_data"]:
        debug_print(f" Claiming for {user}")
        target_user = bot_app.get_users(config["user_data"][user]["tg_uid"])  # get user obj from tg
        try:
            setGsCookie(user)
            try:
                reward = gs.claim_daily_reward(lang=lang)
            except NotLoggedIn as e:
                error_print(f"[GS] {user}'s cookies have not been provided.")
            except TooManyRequests as e:
                error_print(f"[GS] {user} made too many requests and got ratelimited")
            if reward is not None:
                bot_app.send_message(chat_id, f"{target_user.username} 每日领好啦: {reward['cnt']}x {reward['name']}")
                log_print(f" Claimed daily reward - {reward['cnt']}x {reward['name']} {target_user.username}")
            else:
                bot_app.send_message(chat_id, f"{target_user.username} 每日领不了")
                log_print(f" Could not claim daily reward {target_user.username}")
        except BadRequest as e:
            error_print(f"[TG400] Resin check: {target_user.username}")
        except FloodWait as e:
            time.sleep(e.x)
        debug_print(f" Claiming for {user} finished")
    log_print(f" Claimed all!")


def checkAllNotes():
    for user in config["user_data"]:
        debug_print(f" Checking for {user}")
        target_user = bot_app.get_users(config["user_data"][user]["tg_uid"])  # get user obj from tg
        try:
            setGsCookie(user)
            try:
                notes = gs.get_notes(config["user_data"][user]["gs_uid"])
            except NotLoggedIn as e:
                error_print(f"[GS] {user}'s cookies have not been provided.")
            except TooManyRequests as e:
                error_print(f"[GS] {user} made too many requests and got ratelimited")
            if notes['resin'] > resin_warning_limit:
                bot_app.send_message(chat_id, f"@{target_user.username} 树脂要溢出啦: {notes['resin']}/{notes['max_resin']}")
                log_print(f" Resin reminder: {target_user.username}")
            if notes['realm_currency'] > coin_warning_limit:
                bot_app.send_message(chat_id, f"@{target_user.username} 洞天宝钱要溢出啦: {notes['realm_currency']}/{notes['max_realm_currency']}")
                log_print(f" Coin reminder: {target_user.username}")
        except BadRequest as e:
            error_print(f"[TG400] Resin check: {target_user.username}")
        except FloodWait as e:
            time.sleep(e.x)
        debug_print(f" Checking for {user} finished")
    log_print(f" Checked all!")


def taskList():
    scheduler = BackgroundScheduler(timezone=tz)
    scheduler.add_job(checkAllNotes, trigger='cron', hour=checkall_cron_hours, id='checkAllNotes')
    scheduler.add_job(claimAllDailyReward, trigger='cron', hour=reward_cron_hour, minute=reward_cron_minute, id='claimAllDailyReward')
    scheduler.start()


taskList()

print("\033[42;37m Ready! \33[0m")

bot_app.run()

print("\033[41;37m Bye! \33[0m")

