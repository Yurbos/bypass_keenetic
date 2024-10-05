## Описание проекта

Данный репозиторий - это форк реализации от уважаемого [Ziwork](https://github.com/ziwork/bypass_keenetic "https://github.com/ziwork/bypass_keenetic") тут сможете найти основную информацию по проекту.

**!Реализация сделана исключительно для себя, под свои нужды!**

## Установка

Выполните команды по очереди

```bash
opkg install curl nano-full python3 python3-pip
```

```bash
curl -O https://bootstrap.pypa.io/get-pip.py
```

```bash
python get-pip.py
```

```bash
pip install pyTelegramBotAPI telethon pathlib
```

```bash
curl -o /opt/etc/bot.py https://raw.githubusercontent.com/Yurbos/bypass_keenetic/main/bot.py
```

```bash
curl -o /opt/etc/bot_config.py https://raw.githubusercontent.com/Yurbos/bypass_keenetic/main/bot_config.py
```

```bash
nano /opt/etc/bot_config.py
```

Заполните ключ api бота и логин из телеграмма, сохраните файл.

Запустите бота

```bash
python3 /opt/etc/bot.py
```

Заходим в свой телеграм-бот, если необходимо нажимаем `/start`

`Установка и удаление` -> `Установка & переустановка` -> `Fork by Yurbos`:

При установке возможно будет ошибка `Starting dnsmasq... failed` Игнорируем. (После включения `DNS Override` и перезагрузки роутера должно заработать).

Далее, так как парсинг из ссылки `vless` еще не реализован, нужно руками подправить конфигурацию для `xray`

```bash
nano /opt/etc/xray/config.json
```

Подставьте свои данные в нужные места из своего клиентского `vless` конфига, сохраните файл.

Добавьте через бота в список обхода для `vless` неодбодимые вам домены.

В меню бота -> `Сервис` -> `DNS Override` -> `Вкл DNS Override`, после чего ваш роутер перезагрузится. (Возможно придется нажать несколько раз, так  как не всегда срабатывает с первого раза.)

Готово.

## Справка

Запустить xray можно командой

```bash
xray run -c /opt/etc/xray/config.json
```

Проверить статус xray

```bash
/opt/etc/init.d/S24xray status
```

Проверить запущен ли бот

```bash
ps | grep bot
```

Убить процесс бота

```bash
Kill <ID_Процесса>
```

## Ссылки на исходные репозитории

[https://github.com/ziwork/bypass_keenetic](https://github.com/ziwork/bypass_keenetic "https://github.com/ziwork/bypass_keenetic")

[https://github.com/tas-unn/bypass_keenetic](https://github.com/tas-unn/bypass_keenetic "https://github.com/tas-unn/bypass_keenetic")
