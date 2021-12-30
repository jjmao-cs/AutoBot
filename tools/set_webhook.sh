#!/bin/bash
if [ "" != "$1" ]
then
    webhook=$1
    token="[ENTER_YUOR_TOKEN_HERE]"
    if [ "" != "$2" ]
    then
        token=$2
    fi
    echo "target webhook is $webhook"
    curl -s https://api.telegram.org/bot{$token}/setWebhook?url={$webhook} |\
        python3 -c "import sys, json; result = json.load(sys.stdin); print(str(result['ok'])+ '\n' +\
                                            result['description'])"
else
    echo "[Error] Missing parameters"
    echo "[Usage] set_webhook.sh \$webhook_url \$token(option)"
fi
echo ""
