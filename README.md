*This is a proof of concept, a quick code mashup to learn making telegram bot with self-hosted callback in python. The purpose is anything you want. Code is free to disassemble and use if it's useful for anyone.*

## Iptables whitelist management via telegram bot callback

*1. INSTALL PYTHON 3 AND TELEGRAM CONNECTION LIBRARIES*

```
apt-get update
apt-get install python3-pip -y
pip3 install pyTelegramBotAPI aiohttp cchardet aiodns
```

*2. GET CERTBOT AND MAKE LE CERTIFICATE*

Install certbot

```
wget https://dl.eff.org/certbot-auto -O /usr/local/bin/certbot-auto
sudo chown root /usr/local/bin/certbot-auto
sudo chmod 0755 /usr/local/bin/certbot-auto
```

Generate certificate for YOUR.DOMAIN

```
sudo /usr/local/bin/certbot-auto certonly --apache -d YOUR.DOMAIN
```

Expected output

```
#  - Congratulations! Your certificate and chain have been saved at:
# /etc/letsencrypt/live/YOUR.DOMAIN/fullchain.pem
# Your key file has been saved at:
# /etc/letsencrypt/live/YOUR.DOMAIN/privkey.pem
```

*3. CREATE BOT*

Chat with `@BotFather` on telegram, type `/newbot`.

Get and save bot token.

*4. REGISTER CALLBACK*

Open this in browser: 

`https://api.telegram.org/botYOUR-TOKEN/setWebhook?url=https://YOUR.DOMAIN:8443/YOUR-TOKEN/`

Should get this output:
```
# ok  true
# result  true
# description  "Webhook was set"
```
