## Structure

|--script
|   |--sign.py: key component communicate with NCU part-time sign page.
|--self_ssl **ADD CERT HERE**
|   |--cert.pem     (renew every 10 year next:2030)
|   |--private.key  (renew every 10 year next:2030)
|--signbotenv: python venv
|--tools/set_webhook.sh: bash script on setting webhook's token and url **TOKEN TOBE SET**
|--config.ini: Token from Telegram for main3.py **TOKEN TOBE SET**
|--main3.py: Main program for telegram
|--requirements.txt

## Info
- service log: sudo journalctl -u signbot

- get_message : https://api.telegram.org/bot{$token}/getUpdates
- change_webhok : https://api.telegram.org/bot{$token}/setWebhook?url={$webhook_url}
```
FQDN = signbot.ee.ncu.edu.tw
Port = 443
```
- self-sign-certificate: https://github.com/python-telegram-bot/python-telegram-bot/wiki/Webhooks#a-ssl-certificate
- python-venv & signbot.service: https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-gunicorn-and-nginx-on-ubuntu-20-04
- telegram-api: python-telegram-bot
