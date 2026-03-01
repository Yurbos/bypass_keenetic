#!/usr/bin/python3

# ВЕРСИЯ СКРИПТА 2.2.3

import asyncio
import subprocess
import os
import stat
import time

import telebot
from telebot import types
from telethon.sync import TelegramClient
import base64
import requests
import json
import bot_config as config

import sys
import urllib.parse

token = config.token
usernames = config.usernames
routerip = config.routerip
localportsh = config.localportsh
localportvless = config.localportvless
dnsovertlsport = config.dnsovertlsport
dnsoverhttpsport = config.dnsoverhttpsport

repo = "Yurbos"

# Начало работы программы
bot = telebot.TeleBot(token)
level = 0
bypass = -1
sid = "0"

# список смайлов для меню
#  ✅ ❌ ♻️ 📃 📆 🔑 📄 ❗ ️⚠️ ⚙️ 📝 📆 🗑 📄️⚠️ 🔰 ❔ ‼️ 📑
@bot.message_handler(commands=['start'])
def start(message):
    if message.from_user.username not in usernames:
        bot.send_message(message.chat.id, 'Вы не являетесь автором канала')
        return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
#    item1 = types.KeyboardButton("🔰 Установка и удаление")
    item2 = types.KeyboardButton("🔑 Ключи и мосты")
    item3 = types.KeyboardButton("📝 Списки обхода")
    item4 = types.KeyboardButton("⚙️ Сервис")
    markup.add(item2, item3, item4)
    bot.send_message(message.chat.id, '✅ Добро пожаловать в меню!', reply_markup=markup)

@bot.message_handler(content_types=['text'])
def bot_message(message):
    try:
        main = types.ReplyKeyboardMarkup(resize_keyboard=True)
#        m1 = types.KeyboardButton("🔰 Установка и удаление")
        m2 = types.KeyboardButton("🔑 Ключи и мосты")
        m3 = types.KeyboardButton("📝 Списки обхода")
        m4 = types.KeyboardButton("📄 Информация")
        m5 = types.KeyboardButton("⚙️ Сервис")
 #       main.add(m1, m2, m3)
        main.add(m2, m3)
        main.add(m4, m5)

        service = types.ReplyKeyboardMarkup(resize_keyboard=True)
        m1 = types.KeyboardButton("♻️ Перезагрузить сервисы")
        m2 = types.KeyboardButton("‼️Перезагрузить роутер")
        m3 = types.KeyboardButton("‼️DNS Override")
        m4 = types.KeyboardButton("🔄 Обновления")
        back = types.KeyboardButton("🔙 Назад")
        service.add(m1, m2)
        service.add(m3, m4)
        service.add(back)

        if message.from_user.username not in usernames:
            bot.send_message(message.chat.id, 'Вы не являетесь автором канала')
            return
        if message.chat.type == 'private':
            global level, bypass

            if message.text == '⚙️ Сервис':
                bot.send_message(message.chat.id, '⚙️ Сервисное меню!', reply_markup=service)
                return

            if message.text == '♻️ Перезагрузить сервисы' or message.text == 'Перезагрузить сервисы':
                bot.send_message(message.chat.id, '🔄 Выполняется перезагрузка сервисов!', reply_markup=service)
                os.system('/opt/etc/init.d/S22shadowsocks restart')
                os.system('/opt/etc/init.d/S24xray restart')
                bot.send_message(message.chat.id, '✅ Сервисы перезагружены!', reply_markup=service)
                return

            if message.text == '‼️Перезагрузить роутер' or message.text == 'Перезагрузить роутер':
                os.system("ndmc -c system reboot")
                service_router_reboot = "🔄 Роутер перезагружается!\nЭто займет около 2 минут."
                bot.send_message(message.chat.id, service_router_reboot, reply_markup=service)
                return

            if message.text == '‼️DNS Override' or message.text == 'DNS Override':
                service = types.ReplyKeyboardMarkup(resize_keyboard=True)
                m1 = types.KeyboardButton("✅ DNS Override ВКЛ")
                m2 = types.KeyboardButton("❌ DNS Override ВЫКЛ")
                back = types.KeyboardButton("🔙 Назад")
                service.add(m1, m2)
                service.add(back)
                bot.send_message(message.chat.id, '‼️DNS Override!', reply_markup=service)
                return

            if message.text == "✅ DNS Override ВКЛ" or message.text == "❌ DNS Override ВЫКЛ":
                if message.text == "✅ DNS Override ВКЛ":
                    os.system("ndmc -c 'opkg dns-override'")
                    time.sleep(5)
                    os.system("ndmc -c 'system configuration save'")
                    bot.send_message(message.chat.id, '✅ DNS Override включен!\n🔄 Роутер перезагружается.',
                                     reply_markup=service)
                    time.sleep(5)
                    os.system("ndmc -c 'system reboot'")
                    return

                if message.text == "❌ DNS Override ВЫКЛ":
                    os.system("ndmc -c 'no opkg dns-override'")
                    time.sleep(5)
                    os.system("ndmc -c 'system configuration save'")
                    bot.send_message(message.chat.id, '✅ DNS Override выключен!\n🔄 Роутер перезагружается.',
                                     reply_markup=service)
                    time.sleep(5)
                    os.system("ndmc -c 'system reboot'")
                    return

                service_router_reboot = "🔄 Роутер перезагружается!\n⏳ Это займет около 2 минут."
                bot.send_message(message.chat.id, service_router_reboot, reply_markup=service)
                return

            if message.text == '📄 Информация':
                url = "https://raw.githubusercontent.com/Yurbos/bypass_keenetic/main/Info.md"
                info_bot = requests.get(url).text
                bot.send_message(message.chat.id, info_bot, parse_mode='Markdown', disable_web_page_preview=True,
                                 reply_markup=main)
                hostname = subprocess.Popen(['hostname'], stdout=subprocess.PIPE)
                for line in hostname.stdout:
                    results_hostname = line.decode().strip()
                    bot.send_message(message.chat.id,'Имя устройства: ' + str(results_hostname), reply_markup=main)

                with open('/opt/etc/id', encoding='utf-8') as file:
                    for line in file.readlines():
                        if line.startswith('# Ваш идентификатор'):
                            s = line.replace('# ', '')
                            bot_id = s.strip()
                bot.send_message(message.chat.id, bot_id, disable_web_page_preview=True)
                bot.send_message(message.chat.id, 'Установленный ключ vless', disable_web_page_preview=True)
                vless_key = open('/opt/etc/xray/key', encoding='utf-8')
                bot.send_message(message.chat.id, vless_key, disable_web_page_preview=True)
                return

            if message.text == '/keys_free':
                url = "https://raw.githubusercontent.com/Yurbos/bypass_keenetic/main/keys.md"
                keys_free = requests.get(url).text
                bot.send_message(message.chat.id, keys_free, disable_web_page_preview=True)
                return

            if message.text == '🔄 Обновления' or message.text == '/check_update':
                url = "https://raw.githubusercontent.com/Yurbos/bypass_keenetic/main/version.md"
                bot_new_version = requests.get(url).text

                with open('/opt/etc/bot.py', encoding='utf-8') as file:
                    for line in file.readlines():
                        if line.startswith('# ВЕРСИЯ СКРИПТА'):
                            s = line.replace('# ', '')
                            bot_version = s.strip()

                service_bot_version = "*ВАША ТЕКУЩАЯ " + str(bot_version) + "*\n\n"
                service_new_version = "*ПОСЛЕДНЯЯ ДОСТУПНАЯ ВЕРСИЯ:*\n\n" + str(bot_new_version)
                service_update_info = service_bot_version + service_new_version
                # bot.send_message(message.chat.id, service_bot_version, parse_mode='Markdown', reply_markup=service)
                bot.send_message(message.chat.id, service_update_info, reply_markup=service)

                service_update_msg = "Если вы хотите обновить текущую версию на более новую, нажмите сюда /update"
                bot.send_message(message.chat.id, service_update_msg, reply_markup=service)
                return

            if message.text == '/update':
                bot.send_message(message.chat.id, 'Устанавливаются обновления, подождите!', reply_markup=service)
                os.system("curl -s -o /opt/root/script.sh https://raw.githubusercontent.com/Yurbos/bypass_keenetic/main/script.sh")
                os.chmod(r"/opt/root/script.sh", 0o0755)
                os.chmod('/opt/root/script.sh', stat.S_IRWXU)

                update = subprocess.Popen(['/opt/root/script.sh', '-update'], stdout=subprocess.PIPE)
                for line in update.stdout:
                    results_update = line.decode().strip()
                    bot.send_message(message.chat.id, str(results_update), reply_markup=service)
                time.sleep(5)
                os.system("/opt/etc/init.d/S100bot restart")
                return

            if message.text == '🔙 Назад' or message.text == "Назад":
                bot.send_message(message.chat.id, '✅ Добро пожаловать в меню!', reply_markup=main)
                level = 0
                bypass = -1
                return

            if level == 1:
                # значит это список обхода блокировок
                dirname = '/opt/etc/unblock/'
                dirfiles = os.listdir(dirname)

                for fln in dirfiles:
                    if fln == message.text + '.txt':
                        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                        item1 = types.KeyboardButton("📑 Показать список")
                        item2 = types.KeyboardButton("📝 Добавить в список")
                        item3 = types.KeyboardButton("🗑 Удалить из списка")
                        back = types.KeyboardButton("🔙 Назад")
                        markup.row(item1, item2, item3)
                        markup.row(back)
                        level = 2
                        bypass = message.text
                        bot.send_message(message.chat.id, "Меню " + bypass, reply_markup=markup)
                        return

                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                back = types.KeyboardButton("🔙 Назад")
                markup.add(back)
                bot.send_message(message.chat.id, "Не найден", reply_markup=markup)
                return

            if level == 2 and message.text == "📑 Показать список":
                file = open('/opt/etc/unblock/' + bypass + '.txt')
                flag = True
                s = ''
                sites = []
                for line in file:
                    sites.append(line)
                    flag = False
                if flag:
                    s = 'Список пуст'
                file.close()
                sites.sort()
                if not flag:
                    for line in sites:
                        s = str(s) + '\n' + line.replace("\n", "")
                if len(s) > 4096:
                    for x in range(0, len(s), 4096):
                        bot.send_message(message.chat.id, s[x:x + 4096])
                else:
                    bot.send_message(message.chat.id, s)
                #bot.send_message(message.chat.id, s)
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                item1 = types.KeyboardButton("📑 Показать список")
                item2 = types.KeyboardButton("📝 Добавить в список")
                item3 = types.KeyboardButton("🗑 Удалить из списка")
                back = types.KeyboardButton("🔙 Назад")
                markup.row(item1, item2, item3)
                markup.row(back)
                bot.send_message(message.chat.id, "Меню " + bypass, reply_markup=markup)
                return

            if level == 2 and message.text == "📝 Добавить в список":
                bot.send_message(message.chat.id,
                                 "Введите имя сайта или домена для разблокировки, "
                                 "либо воспользуйтесь меню для других действий")
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                back = types.KeyboardButton("🔙 Назад")
                markup.add(back)
                level = 3
                bot.send_message(message.chat.id, "Меню " + bypass, reply_markup=markup)
                return

            if level == 2 and message.text == "🗑 Удалить из списка":
                bot.send_message(message.chat.id,
                                 "Введите имя сайта или домена для удаления из листа разблокировки,"
                                 "либо возвратитесь в главное меню")
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                back = types.KeyboardButton("🔙 Назад")
                markup.add(back)
                level = 4
                bot.send_message(message.chat.id, "Меню " + bypass, reply_markup=markup)
                return

            if level == 3:
                f = open('/opt/etc/unblock/' + bypass + '.txt')
                mylist = set()
                for line in f:
                    mylist.add(line.replace('\n', ''))
                f.close()
                k = len(mylist)
                if len(message.text) > 1:
                    mas = message.text.split('\n')
                    for site in mas:
                        mylist.add(site)
                sortlist = []
                for line in mylist:
                    sortlist.append(line)
                sortlist.sort()
                f = open('/opt/etc/unblock/' + bypass + '.txt', 'w')
                for line in sortlist:
                    f.write(line + '\n')
                f.close()
                if k != len(sortlist):
                    bot.send_message(message.chat.id, "✅ Успешно добавлено")
                else:
                    bot.send_message(message.chat.id, "Было добавлено ранее")
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                item1 = types.KeyboardButton("📑 Показать список")
                item2 = types.KeyboardButton("📝 Добавить в список")
                item3 = types.KeyboardButton("🗑 Удалить из списка")
                back = types.KeyboardButton("🔙 Назад")
                markup.row(item1, item2, item3)
                markup.row(back)
                subprocess.call(["/opt/bin/unblock_update.sh"])
                level = 2
                bot.send_message(message.chat.id, "Меню " + bypass, reply_markup=markup)
                return

            if level == 4:
                f = open('/opt/etc/unblock/' + bypass + '.txt')
                mylist = set()
                for line in f:
                    mylist.add(line.replace('\n', ''))
                f.close()
                k = len(mylist)
                mas = message.text.split('\n')
                for site in mas:
                    mylist.discard(site)
                f = open('/opt/etc/unblock/' + bypass + '.txt', 'w')
                for line in mylist:
                    f.write(line + '\n')
                f.close()
                if k != len(mylist):
                    bot.send_message(message.chat.id, "✅ Успешно удалено")
                else:
                    bot.send_message(message.chat.id, "Не найдено в списке")
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                item1 = types.KeyboardButton("📑 Показать список")
                item2 = types.KeyboardButton("📝 Добавить в список")
                item3 = types.KeyboardButton("🗑 Удалить из списка")
                back = types.KeyboardButton("🔙 Назад")
                markup.row(item1, item2, item3)
                markup.row(back)
                level = 2
                subprocess.call(["/opt/bin/unblock_update.sh"])
                bot.send_message(message.chat.id, "Меню " + bypass, reply_markup=markup)
                return

            if level == 5:
                shadowsocks(message.text)
                time.sleep(2)
                os.system('/opt/etc/init.d/S22shadowsocks restart')
                level = 0
                bot.send_message(message.chat.id, '✅ Успешно обновлено', reply_markup=main)
                # return

            if level == 8:
                if message.text == 'Shadowsocks':
                    #bot.send_message(message.chat.id, "Скопируйте ключ сюда")
                    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                    back = types.KeyboardButton("🔙 Назад")
                    markup.add(back)
                    level = 5
                    bot.send_message(message.chat.id, "🔑 Скопируйте ключ сюда", reply_markup=markup)
                    return

                if message.text == 'Vless':
                    #bot.send_message(message.chat.id, "Скопируйте ключ сюда")
                    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                    back = types.KeyboardButton("🔙 Назад")
                    markup.add(back)
                    level = 9
                    bot.send_message(message.chat.id, "🔑 Скопируйте ключ сюда", reply_markup=markup)
                    return

            if level == 9:
                vless(message.text)
                os.system('/opt/etc/init.d/S24xray restart')
                level = 0
                bot.send_message(message.chat.id, '✅ Успешно обновлено', reply_markup=main)

            if message.text == '🔰 Установка и удаление':
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                item1 = types.KeyboardButton("♻️ Установка & переустановка")
                item2 = types.KeyboardButton("⚠️ Удаление")
                back = types.KeyboardButton("🔙 Назад")
                markup.row(item1, item2)
                markup.row(back)
                bot.send_message(message.chat.id, '🔰 Установка и удаление', reply_markup=markup)
                return

            if level == 100:
                f = open('/opt/etc/id', 'w')
                f.write('# Ваш идентификатор ' + message.text)
                f.close()
                level = 0
                bot.send_message(message.chat.id, '✅ Успешно обновлено', reply_markup=main)

#            if level == 101:
#                os.system("sed 's/^token\ =\ '.*'/token\ =\ '" + message.text"'/g' /opt/etc/bot_config.py")
#                level = 0
#                bot.send_message(message.chat.id, '✅ Успешно обновлено', reply_markup=main)

            if message.text == '♻️ Установка & переустановка':
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                item1 = types.KeyboardButton("‼️Основная")
                back = types.KeyboardButton("🔙 Назад")
                markup.row(item1)
                markup.row(back)
                bot.send_message(message.chat.id, 'Выберите версию', reply_markup=markup)
                return

            if message.text == "‼️Основная":
                url = "https://raw.githubusercontent.com/Yurbos/bypass_keenetic/main/script.sh".format(repo)
                os.system("curl -s -o /opt/root/script.sh " + url + "")
                os.chmod(r"/opt/root/script.sh", 0o0755)
                os.chmod('/opt/root/script.sh', stat.S_IRWXU)

                install = subprocess.Popen(['/opt/root/script.sh', '-install'], stdout=subprocess.PIPE)
                for line in install.stdout:
                    results_install = line.decode().strip()
                    bot.send_message(message.chat.id, str(results_install), reply_markup=main)

                bot.send_message(message.chat.id,
                                 "Установка завершена. Теперь нужно немного настроить роутер и перейти к "
                                 "спискам для разблокировок. "
                                 "Ключи для Vless, Shadowsocks необходимо установить вручную",
                                 reply_markup=main)

                bot.send_message(message.chat.id,
                                 "Что бы завершить настройку роутера, Зайдите в меню сервис -> DNS Override -> ВКЛ. (Нажать на кнопку 2 раза, не могу поправить багу) "
                                 "Учтите, после выполнения команды, роутер перезагрузится, это займет около 2 минут.",
                                 reply_markup=main)

                subprocess.call(["/opt/bin/unblock_update.sh"])
                # os.system('/opt/bin/unblock_update.sh')
                return

            if message.text == '⚠️ Удаление':
                os.system("curl -s -o /opt/root/script.sh https://raw.githubusercontent.com/Yurbos/bypass_keenetic/main/script.sh")
                os.chmod(r"/opt/root/script.sh", 0o0755)
                os.chmod('/opt/root/script.sh', stat.S_IRWXU)

                remove = subprocess.Popen(['/opt/root/script.sh', '-remove'], stdout=subprocess.PIPE)
                for line in remove.stdout:
                    results_remove = line.decode().strip()
                    bot.send_message(message.chat.id, str(results_remove), reply_markup=service)
                return

            if message.text == "📝 Списки обхода":
                level = 1
                dirname = '/opt/etc/unblock/'
                dirfiles = os.listdir(dirname)
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                markuplist = []
                for fln in dirfiles:
                    # markup.add(fln.replace(".txt", ""))
                    btn = fln.replace(".txt", "")
                    markuplist.append(btn)
                markup.add(*markuplist)
                back = types.KeyboardButton("🔙 Назад")
                markup.add(back)
                bot.send_message(message.chat.id, "📝 Списки обхода", reply_markup=markup)
                return

            if message.text == "🔑 Ключи и мосты":
                level = 8
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                item1 = types.KeyboardButton("Shadowsocks")
                item2 = types.KeyboardButton("Vless")
                markup.add(item1, item2)
                back = types.KeyboardButton("🔙 Назад")
                markup.add(back)
                bot.send_message(message.chat.id, "🔑 Ключи и мосты", reply_markup=markup)
                return

            if message.text == '/whoami':
                with open('/opt/etc/id', encoding='utf-8') as file:
                    for line in file.readlines():
                        if line.startswith('# Ваш идентификатор'):
                            s = line.replace('# ', '')
                            bot_id = s.strip()
                bot.send_message(message.chat.id, bot_id, disable_web_page_preview=True)

            if message.text == '/drport':
                with open('/opt/etc/config/dropbear.conf', encoding='utf-8') as file:
                    for line in file.readlines():
                        if line.startswith('PORT='):
                            s = line
                            drport = s.strip()
                bot.send_message(message.chat.id, drport, disable_web_page_preview=True)
                return
            
            if message.text == '/vlesskey':
                vless_key = open('/opt/etc/xray/key', encoding='utf-8')
                bot.send_message(message.chat.id, vless_key, disable_web_page_preview=True)
                return
            
            if message.text == '/setid':
               level = 100
               bot.send_message(message.chat.id, '🔑 Скопируйте ID сюда', disable_web_page_preview=True)
               return

            if message.text == '/settoken':
               level = 101
               bot.send_message(message.chat.id, '🔑 Скопируйте Token сюда', disable_web_page_preview=True)
               return

    except Exception as error:
        file = open("/opt/etc/error.log", "w")
        file.write(str(error))
        file.close()
        os.chmod(r"/opt/etc/error.log", 0o0755)

def vless(key):
    # global password, localportvless
    config_str = key

    # Разбор URL
    parsed = urllib.parse.urlparse(config_str)

    # --- Извлечение UUID, сервера и порта из netloc ---
    netloc = parsed.netloc  # например "25220c2-f0ae-4a66-99c5-6e1a44e81cc9@7.22.203.11:10051"

    if '@' in netloc:
        userinfo, hostport = netloc.split('@', 1)
    else:
        userinfo = None
        hostport = netloc

    vless_id = userinfo  # это UUID

    # Разделяем хост и порт
    if ':' in hostport:
        vless_ip, port_str = hostport.split(':', 1)
        try:
            vless_port = int(port_str)
        except ValueError:
            vless_port = port_str  # если порт не число, оставляем как строку
    else:
        vless_ip = hostport
        vless_port = None

    # --- Разбор query-параметров ---
    # parse_qs возвращает словарь {ключ: [значения]}, берём первое значение
    query_dict = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
    params = {k: v[0] for k, v in query_dict.items()}

    # Извлекаем параметры (если какого-то нет, будет None)
    vless_type = params.get('type')
    encryption = params.get('encryption')
    vless_security = params.get('security')
    vless_pbk = params.get('pbk')
    vless_fp = params.get('fp')
    vless_sni = params.get('sni')
    vless_sid = params.get('sid')
    vless_spx = params.get('spx')      # автоматически декодируется из %2F в '/'
    flow = params.get('flow')

    # --- Фрагмент (часть после #) ---
    fragment = parsed.fragment

    f = open('/opt/etc/xray/config.json', 'w')
    sh = '{\n' \
              '"dns": {\n' \
              '    "disableFallback": true,\n' \
              '    "servers": [\n' \
              '      {\n' \
              '        "address": "https://8.8.8.8/dns-query",\n' \
              '        "domains": [],\n' \
              '        "queryStrategy": ""\n' \
              '      },\n' \
              '      {\n' \
              '        "address": "localhost",\n' \
              '        "domains": [],\n' \
              '        "queryStrategy": ""\n' \
              '      }\n' \
              '    ],\n' \
              '    "tag": "dns"\n' \
              '  },\n' \
              '  "inbounds": [\n' \
              '    {\n' \
              '        "port": 10810,\n' \
              '        "listen": "::",\n' \
              '        "protocol": "dokodemo-door",\n' \
              '        "settings": {\n' \
              '          "network": "tcp",\n' \
              '          "followRedirect": true\n' \
              '        },\n' \
              '        "sniffing": {\n' \
              '          "enabled": true,\n' \
              '          "destOverride": [\n' \
              '            "http",\n' \
              '            "tls"\n' \
              '          ]\n' \
              '        }\n' \
              '      },\n' \
              '    {\n' \
              '      "listen": "127.0.0.1",\n' \
              '      "port": 2081,\n' \
              '      "protocol": "http",\n' \
              '      "sniffing": {\n' \
              '        "destOverride": [\n' \
              '          "http",\n' \
              '          "tls",\n' \
              '          "quic"\n' \
              '        ],\n' \
              '        "enabled": true,\n' \
              '        "metadataOnly": false,\n' \
              '        "routeOnly": true\n' \
              '      },\n' \
              '      "tag": "http-in"\n' \
              '    }\n' \
              '  ],\n' \
              '  "log": {\n' \
              '    "loglevel": "warning"\n' \
              '  },\n' \
              '  "outbounds": [\n' \
              '    {\n' \
              '      "domainStrategy": "AsIs",\n' \
              '      "flow": null,\n' \
              '      "protocol": "vless",\n' \
              '      "settings": {\n' \
              '        "vnext": [\n' \
              '          {\n' \
              '            "address": "' + str(vless_ip) + '",\n' \
              '            "port": ' + str(vless_port) + ',\n' \
              '            "users": [\n' \
              '              {\n' \
              '                "encryption": "none",\n' \
              '                "flow": "' + str(flow) + '"\n' \
              '                "id": "' + str(vless_id) +'"\n' \
              '              }\n' \
              '            ]\n' \
              '          }\n' \
              '        ]\n' \
              '      },\n' \
              '      "streamSettings": {\n' \
              '        "network": "' + str(vless_type) + '",\n' \
              '        "realitySettings": {\n' \
              '          "fingerprint": "' + str(vless_fp) + '",\n' \
              '          "publicKey": "' + str(vless_pbk) + '",\n' \
              '          "serverName": "' + str(vless_sni) + '",\n' \
              '          "shortId": "' + str(vless_sid) + '",\n' \
              '          "spiderX": "/"\n' \
              '        },\n' \
              '        "security": "' + str(vless_security) + '"\n' \
              '      },\n' \
              '      "tag": "proxy"\n' \
              '    },\n' \
              '    {\n' \
              '      "domainStrategy": "",\n' \
              '      "protocol": "freedom",\n' \
              '      "tag": "direct"\n' \
              '    },\n' \
              '    {\n' \
              '      "domainStrategy": "",\n' \
              '      "protocol": "freedom",\n' \
              '      "tag": "bypass"\n' \
              '    },\n' \
              '    {\n' \
              '      "protocol": "blackhole",\n' \
              '      "tag": "block"\n' \
              '    },\n' \
              '    {\n' \
              '      "protocol": "dns",\n' \
              '      "proxySettings": {\n' \
              '        "tag": "proxy",\n' \
              '        "transportLayer": true\n' \
              '      },\n' \
              '      "settings": {\n' \
              '        "address": "8.8.8.8",\n' \
              '        "network": "tcp",\n' \
              '        "port": 53,\n' \
              '        "userLevel": 1\n' \
              '      },\n' \
              '      "tag": "dns-out"\n' \
              '    }\n' \
              '  ],\n' \
              '  "policy": {\n' \
              '    "levels": {\n' \
              '      "1": {\n' \
              '        "connIdle": 30\n' \
              '      }\n' \
              '    },\n' \
              '    "system": {\n' \
              '      "statsOutboundDownlink": true,\n' \
              '      "statsOutboundUplink": true\n' \
              '    }\n' \
              '  },\n' \
              '  "routing": {\n' \
              '    "domainStrategy": "AsIs",\n' \
              '    "rules": [\n' \
              '      {\n' \
              '        "inboundTag": [\n' \
              '          "socks-in",\n' \
              '          "http-in"\n' \
              '        ],\n' \
              '        "outboundTag": "dns-out",\n' \
              '        "port": "53",\n' \
              '        "type": "field"\n' \
              '      },\n' \
              '      {\n' \
              '        "outboundTag": "proxy",\n' \
              '        "port": "0-65535",\n' \
              '        "type": "field"\n' \
              '      }\n' \
              '    ]\n' \
              '  },\n' \
              '  "stats": {}\n' \
              '}\n' \
              ''
    f.write(sh)
    f.close()
    os.system('/opt/etc/init.d/S24xray restart')
    #write key in store
    f = open('/opt/etc/xray/key', 'w')
    f.write(config_str)
    f.close()


def shadowsocks(key=None):
    # global password, localportsh
    encodedkey = str(key).split('//')[1].split('@')[0] + '=='
    password = str(str(base64.b64decode(encodedkey)[2:]).split(':')[1])[:-1]
    server = str(key).split('@')[1].split('/')[0].split(':')[0]
    port = str(key).split('@')[1].split('/')[0].split(':')[1].split('#')[0]
    method = str(str(base64.b64decode(encodedkey)).split(':')[0])[2:]
    f = open('/opt/etc/shadowsocks.json', 'w')
    sh = '{"server": ["' + server + '"], "mode": "tcp_and_udp", "server_port": ' \
         + str(port) + ', "password": "' + password + \
         '", "timeout": 86400,"method": "' + method + \
         '", "local_address": "::", "local_port": ' \
         + str(localportsh) + ', "fast_open": false,    "ipv6_first": true}'
    f.write(sh)
    f.close()

# bot.polling(none_stop=True)
try:
    bot.infinity_polling()
except Exception as err:
    fl = open("/opt/etc/error.log", "w")
    fl.write(str(err))
    fl.close()
