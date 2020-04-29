import config
import telebot
from telebot import types
from aiohttp import web
import ssl
import sqlite3
import os

DB_LOCATION = os.path.dirname(__file__) + '/database.db'

bot = telebot.TeleBot(config.API_TOKEN)

app = web.Application()

# process only requests with correct bot token
async def handle(request):
  if request.match_info.get("token") == bot.token:
    request_body_dict = await request.json()
    update = telebot.types.Update.de_json(request_body_dict)
    bot.process_new_updates([update])
    return web.Response()
  else:
    return web.Response(status=403)  

app.router.add_post("/{token}/", handle)

# Precreate db if it does not exist yet
def create_db():
  conn = sqlite3.connect(DB_LOCATION)
  conn.execute('CREATE TABLE IF NOT EXISTS accounts (tg_id TEXT PRIMARY KEY, mc_login TEXT)')
  conn.execute('CREATE TABLE IF NOT EXISTS iplist (mc_login TEXT, ip TEXT)')
  conn.close()

# Resolve telegram id into minecraft login
def tg2login(tg_id):
  conn = sqlite3.connect(DB_LOCATION)
  cursorObj = conn.cursor()
  cursorObj.execute('SELECT mc_login FROM accounts WHERE tg_id=?', (tg_id,))
  mc_login = cursorObj.fetchone()
  if mc_login:
    mc_login = mc_login[0]
  else:
    mc_login = False
  conn.close()  
  return mc_login

# User link request
def user_request(message, mc_login):
  for admin_tg_id in config.TG_ADMIN_ID:
    msg_string = []
    msg_string.append("Lietotāja reģistrācijas pieprasījums.\n")
    msg_string.append("Telegrammas lietotājs: [{} {} ({})](tg://user?id={})\n".format(message.chat.first_name, message.chat.last_name, message.chat.username, message.chat.id))
    msg_string.append("Minecraft lietotājs: {}\n".format(mc_login))

    markup = types.ReplyKeyboardMarkup()
    markup.row("/link {} {}\n".format(message.chat.id, mc_login))
    markup.row('/cancel')
    bot.send_message(admin_tg_id, "".join(msg_string), parse_mode="Markdown", reply_markup=markup)

# Make sure db is created
create_db()

# Help handler
@bot.message_handler(commands=["help"])
def send_help(message):
  help_string = []
  help_string.append("*ENL MC bots*\n\n")
  help_string.append("/me - Mans mc lietotāja vārds\n")
  help_string.append("/ip_list - Manas atļautās adreses\n")
  help_string.append("/ip_add - Pievienot jaunu adresi\n")
  help_string.append("/ip_remove - Noņemt adresi\n")

  if (message.chat.id in config.TG_ADMIN_ID):
    help_string.append("\n")
    help_string.append("*Administratora komandas*.\n\n")
    help_string.append("/link [telegrammas_id] [minecraft_niks] \n")
  #   help_string.append("/ip_list_all - Visas atļautās adreses\n")

  bot.send_message(message.chat.id, "".join(help_string), parse_mode="Markdown")

# Remove keyboard
@bot.message_handler(commands=["cancel"])
def cancel(message):
  markup = types.ReplyKeyboardRemove(selective=False)
  bot.send_message(message.chat.id, "Ok!", reply_markup=markup)

# Show my id
@bot.message_handler(commands=["me"])
def me(message):
  mc_login = tg2login(message.chat.id)
  
  if (mc_login):
    bot.send_message(message.chat.id, mc_login)
  
  else:
    msg_parts = message.text.split()
    
    if len(msg_parts) > 1:
      user_request(message, msg_parts[1])
      bot.send_message(message.chat.id, "Lietotājs pieteikts un tiks drīzumā izskatīts.")

    else:  
      bot.send_message(message.chat.id, "Lietotājs nav reģistrēts.\nLai pieteiktu savu lietotāju, atbildi ar /me [lietotāja vārds].")

# Link tg account to mc login. Admin only.
@bot.message_handler(regexp="/link")
def link(message):
  
  # Admin user check
  if (message.chat.id in config.TG_ADMIN_ID):
  
    msg_parts = message.text.split()
    
    if len(msg_parts) > 2:
      
      tg_id = msg_parts[1]
      mc_login = msg_parts[2]

      conn = sqlite3.connect(DB_LOCATION)
      cur = conn.cursor()
      cur.execute('INSERT OR REPLACE INTO accounts ("tg_id", "mc_login") VALUES (?, ?)', (tg_id, mc_login))
      conn.commit()
      conn.close()
      
      markup = types.ReplyKeyboardRemove(selective=False)
      bot.send_message(message.chat.id, "Lietotājs apstiprināts!", reply_markup=markup)

    else:
      bot.send_message(message.chat.id, "Komandas sintakse: /link [tg_id] [mc_login]")


# IP list
@bot.message_handler(commands=["ip_list", "ip-list", "iplist"])
@bot.message_handler(regexp="ip list")
def iplist(message):
  
  mc_login = tg2login(message.chat.id)
  if (mc_login):
    conn = sqlite3.connect(DB_LOCATION)
    conn.row_factory = lambda cursor, row: row[0]
    curr = conn.cursor()
    curr.execute('SELECT ip FROM iplist WHERE mc_login=?', (mc_login,))
    ip_list = curr.fetchall()
    conn.close()  
    
    bot.send_message(message.chat.id, "Tavs IP adrešu saraksts: \n{}".format("\n".join(ip_list)))

# IP Add
@bot.message_handler(commands=["ip_add", "ip-add", "ipadd"])
def ipadd(message):
  
  mc_login = tg2login(message.chat.id)
  if (mc_login):

    msg_parts = message.text.split()
    
    if len(msg_parts) > 1:
      
      ip = msg_parts[1]
      
      conn = sqlite3.connect(DB_LOCATION)
      cur = conn.cursor()
      cur.execute('INSERT OR REPLACE INTO iplist ("mc_login", "ip") VALUES (?, ?)', (mc_login, ip))
      conn.commit()
      conn.close()
      
      bot.send_message(message.chat.id, "Adrese pievienota!")

      iplist(message)


# IP Remove
@bot.message_handler(commands=["ip_del", "ip-del", "ipdel", "ip_remove", "ipremove", "ip-remove"])
def ipdel(message):
  
  mc_login = tg2login(message.chat.id)
  if (mc_login):

    msg_parts = message.text.split()
    
    if len(msg_parts) > 1:
      
      ip = msg_parts[1]

      conn = sqlite3.connect(DB_LOCATION)
      cur = conn.cursor()
      cur.execute('DELETE FROM iplist WHERE mc_login=? AND ip=?', (mc_login, ip))
      conn.commit()
      conn.close()
      
      bot.send_message(message.chat.id, "Adrese izņemta no saraksta!")

      iplist(message)

# - - -

context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
context.load_cert_chain(config.WEBHOOK_SSL_CERT, config.WEBHOOK_SSL_PRIV)

# start aiohttp server (our bot)
web.run_app(
    app,
    host=config.WEBHOOK_LISTEN,
    port=config.WEBHOOK_PORT,
    ssl_context=context,
)
