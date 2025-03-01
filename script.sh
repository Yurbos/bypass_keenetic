#!/bin/sh

repo="Yurbos"

# ip роутера
lanip=$(ip addr show br0 | grep -Po "(?<=inet ).*(?=/)" | awk '{print $1}')
ssredir="ss-redir"
localportsh=$(grep "localportsh" /opt/etc/bot_config.py | grep -Eo "[0-9]{1,5}")
localportvless=$(grep "localportvless" /opt/etc/bot_config.py | grep -Eo "[0-9]{1,5}")
dnsovertlsport=$(grep "dnsovertlsport" /opt/etc/bot_config.py | grep -Eo "[0-9]{1,5}")
dnsoverhttpsport=$(grep "dnsoverhttpsport" /opt/etc/bot_config.py | grep -Eo "[0-9]{1,5}")
keen_os_full=$(curl -s localhost:79/rci/show/version/title | tr -d \",)
keen_os_short=$(curl -s localhost:79/rci/show/version/title | tr -d \", | cut -b 1)

if [ "$1" = "-remove" ]; then
    echo "Начинаем удаление"
    opkg remove bind-dig cron dnsmasq-full ipset iptables shadowsocks-libev-ss-redir shadowsocks-libev-config xray
    echo "Пакеты удалены, удаляем папки, файлы и настройки"
    ipset flush testset
    ipset flush unblocksh
    ipset flush unblockvless
    if ls -d /opt/etc/unblock/vpn-*.txt >/dev/null 2>&1; then
     for vpn_file_names in /opt/etc/unblock/vpn-*; do
     vpn_file_name=$(echo "$vpn_file_names" | awk -F '/' '{print $5}' | sed 's/.txt//')
     unblockvpn=$(echo unblock"$vpn_file_name")
     ipset flush "$unblockvpn"
     done
    fi

    chmod 777 /opt/etc/init.d/S22shadowsocks || rm -Rfv /opt/etc/init.d/S22shadowsocks
    chmod 777 /opt/etc/init.d/S24xray || rm -Rfv /opt/etc/init.d/S24xray
    chmod 777 /opt/etc/init.d/S56dnsmasq || rm -Rfv /opt/etc/init.d/S56dnsmasq
    chmod 777 /opt/etc/init.d/S99unblock || rm -Rfv /opt/etc/init.d/S99unblock
    chmod 777 /opt/etc/init.d/S100bot || rm -Rfv /opt/etc/init.d/S100bot
    chmod 777 /opt/etc/ndm/netfilter.d/100-redirect.sh || rm -rfv /opt/etc/ndm/netfilter.d/100-redirect.sh
    chmod 777 /opt/etc/ndm/ifstatechanged.d/100-unblock-vpn.sh || rm -rfv /opt/etc/ndm/ifstatechanged.d/100-unblock-vpn.sh
    chmod 777 /opt/etc/nmd/fs.d/100-ipset.sh || rm -rfv /opt/etc/nmd/fs.d/100-ipset.sh
    chmod 777 /opt/bin/unblock_dnsmasq.sh || rm -rfv /opt/bin/unblock_dnsmasq.sh
    chmod 777 /opt/bin/unblock_update.sh || rm -rfv /opt/bin/unblock_update.sh
    chmod 777 /opt/bin/unblock_ipset.sh || rm -rfv /opt/bin/unblock_ipset.sh
    chmod 777 /opt/etc/unblock.dnsmasq || rm -rfv /opt/etc/unblock.dnsmasq
    chmod 777 /opt/etc/dnsmasq.conf || rm -rfv /opt/etc/dnsmasq.conf
    chmod 777 /opt/etc/xray || rm -Rfv /opt/etc/xray
    echo "Созданные папки, файлы и настройки удалены"
    echo "Если вы хотите полностью отключить DNS Override, перейдите в меню Сервис -> DNS Override -> DNS Override ВЫКЛ. После чего включится встроенный (штатный) DNS и роутер перезагрузится."
    exit 0
fi

if [ "$1" = "-install" ]; then
    echo "Начинаем установку"
    echo "Ваша версия KeenOS" "${keen_os_full}"
    opkg update
    opkg install bind-dig cron dnsmasq-full ipset iptables shadowsocks-libev-ss-redir shadowsocks-libev-config xray
    pip install pyTelegramBotAPI telethon pathlib
    echo "Установка пакетов завершена. Продолжаем установку"

    # есть поддержка множества hash:net или нет, если нет, то при этом вы потеряете возможность разблокировки по диапазону и CIDR
    set_type="hash:net"
    ipset create testset hash:net -exist > /dev/null 2>&1
    retVal=$?
    if [ $retVal -ne 0 ]; then
        set_type="hash:ip"
    fi

    echo "Переменные роутера найдены"
    # создания множеств IP-адресов unblock
    curl -o /opt/etc/ndm/fs.d/100-ipset.sh https://raw.githubusercontent.com/${repo}/bypass_keenetic/main/100-ipset.sh
    chmod 755 /opt/etc/ndm/fs.d/100-ipset.sh || chmod +x /opt/etc/ndm/fs.d/100-ipset.sh
    sed -i "s/hash:net/${set_type}/g" /opt/etc/ndm/fs.d/100-ipset.sh
    echo "Созданы файлы под множества"

    curl -o /opt/etc/shadowsocks.json https://raw.githubusercontent.com/${repo}/bypass_keenetic/main/shadowsocks.json
    echo "Установлены настройки Shadowsocks"
    sed -i "s/ss-local/${ssredir}/g" /opt/etc/init.d/S22shadowsocks
    chmod 0755 /opt/etc/shadowsocks.json || chmod 755 /opt/etc/init.d/S22shadowsocks || chmod +x /opt/etc/init.d/S22shadowsocks
    echo "Установлен параметр ss-redir для Shadowsocks"

    chmod 777 /opt/etc/xray/config.json || rm -Rfv /opt/etc/xray/config.json
    curl -o /opt/etc/xray/config.json https://raw.githubusercontent.com/${repo}/bypass_keenetic/main/vlessconfig.json

    chmod 755 /opt/etc/init.d/S24xray || chmod +x /opt/etc/init.d/S24xray
    sed -i 's|ARGS="-confdir /opt/etc/xray"|ARGS="run -c /opt/etc/xray/config.json"|g' /opt/etc/init.d/S24xray > /dev/null 2>&1

    # unblock folder and files
    mkdir -p /opt/etc/unblock
    touch /opt/etc/hosts || chmod 0755 /opt/etc/hosts
    touch /opt/etc/unblock/shadowsocks.txt || chmod 0755 /opt/etc/unblock/shadowsocks.txt
    touch /opt/etc/unblock/vless.txt || chmod 0755 /opt/etc/unblock/vless.txt
    touch /opt/etc/unblock/vpn.txt || chmod 0755 /opt/etc/unblock/vpn.txt
    echo "Созданы файлы под сайты и ip-адреса для обхода блокировок для SS, xray, VPN"

    # unblock_ipset.sh
    curl -o /opt/bin/unblock_ipset.sh https://raw.githubusercontent.com/${repo}/bypass_keenetic/main/unblock_ipset.sh
    chmod 755 /opt/bin/unblock_ipset.sh || chmod +x /opt/bin/unblock_ipset.sh
    sed -i "s/40500/${dnsovertlsport}/g" /opt/bin/unblock_ipset.sh
    echo "Установлен скрипт для заполнения множеств unblock IP-адресами заданного списка доменов"

    # unblock_dnsmasq.sh
    curl -o /opt/bin/unblock_dnsmasq.sh https://raw.githubusercontent.com/${repo}/bypass_keenetic/main/unblock.dnsmasq
    chmod 755 /opt/bin/unblock_dnsmasq.sh || chmod +x /opt/bin/unblock_dnsmasq.sh
    sed -i "s/40500/${dnsovertlsport}/g" /opt/bin/unblock_dnsmasq.sh
    /opt/bin/unblock_dnsmasq.sh
    echo "Установлен скрипт для формирования дополнительного конфигурационного файла dnsmasq из заданного списка доменов и его запуск"

    # unblock_update.sh
    curl -o /opt/bin/unblock_update.sh https://raw.githubusercontent.com/${repo}/bypass_keenetic/main/unblock_update.sh
    chmod 755 /opt/bin/unblock_update.sh || chmod +x /opt/bin/unblock_update.sh
    echo "Установлен скрипт ручного принудительного обновления системы после редактирования списка доменов"

    # s99unblock
    curl -o /opt/etc/init.d/S99unblock https://raw.githubusercontent.com/${repo}/bypass_keenetic/main/S99unblock
    chmod 755 /opt/etc/init.d/S99unblock || chmod +x /opt/etc/init.d/S99unblock
    echo "Установлен cкрипт автоматического заполнения множества unblock при загрузке маршрутизатора"

    # s100bot
    curl -o /opt/etc/init.d/S100bot https://raw.githubusercontent.com/${repo}/bypass_keenetic/main/S100bot
    chmod 755 /opt/etc/init.d/S100bot || chmod +x /opt/etc/init.d/S100bot
    echo "Установлен cкрипт автоматического запуска бота"

    # 100-redirect.sh
    curl -o /opt/etc/ndm/netfilter.d/100-redirect.sh https://raw.githubusercontent.com/${repo}/bypass_keenetic/main/100-redirect.sh
    chmod 755 /opt/etc/ndm/netfilter.d/100-redirect.sh || chmod +x /opt/etc/ndm/netfilter.d/100-redirect.sh
    sed -i "s/hash:net/${set_type}/g" /opt/etc/ndm/netfilter.d/100-redirect.sh
    sed -i "s/192.168.1.1/${lanip}/g" /opt/etc/ndm/netfilter.d/100-redirect.sh
    sed -i "s/1082/${localportsh}/g" /opt/etc/ndm/netfilter.d/100-redirect.sh
    sed -i "s/10810/${localportvless}/g" /opt/etc/ndm/netfilter.d/100-redirect.sh
    echo "Установлено перенаправление пакетов с адресатами из unblock в: Shadowsocks, xray, VPN"

    # VPN script
    if [ "${keen_os_short}" = "4" ]; then
      echo "VPN для KeenOS 4+";
      curl -s -o /opt/etc/ndm/ifstatechanged.d/100-unblock-vpn.sh https://raw.githubusercontent.com/${repo}/bypass_keenetic/main/100-unblock-vpn-v4.sh
    elif [ "${keen_os_short}" = "3" ]; then
      echo "VPN для KeenOS 3+";
      curl -s -o /opt/etc/ndm/ifstatechanged.d/100-unblock-vpn.sh https://raw.githubusercontent.com/${repo}/bypass_keenetic/main/100-unblock-vpn.sh
    else
      echo "Your really KeenOS ???";
      curl -s -o /opt/etc/ndm/ifstatechanged.d/100-unblock-vpn.sh https://raw.githubusercontent.com/${repo}/bypass_keenetic/main/100-unblock-vpn.sh
    fi
    chmod 755 /opt/etc/ndm/ifstatechanged.d/100-unblock-vpn.sh || chmod +x /opt/etc/ndm/ifstatechanged.d/100-unblock-vpn.sh
    echo "Установлен скрипт проверки подключения и остановки VPN"

    # dnsmasq.conf
    chmod 777 /opt/etc/dnsmasq.conf || rm -rfv /opt/etc/dnsmasq.conf
    curl -o /opt/etc/dnsmasq.conf https://raw.githubusercontent.com/${repo}/bypass_keenetic/main/dnsmasq.conf
    chmod 755 /opt/etc/dnsmasq.conf
    sed -i "s/192.168.1.1/${lanip}/g" /opt/etc/dnsmasq.conf
    sed -i "s/40500/${dnsovertlsport}/g" /opt/etc/dnsmasq.conf
    sed -i "s/40508/${dnsoverhttpsport}/g" /opt/etc/dnsmasq.conf
    echo "Установлена настройка dnsmasq и подключение дополнительного конфигурационного файла к dnsmasq"

    # cron file
    chmod 777 /opt/etc/crontab || rm -Rfv /opt/etc/crontab
    curl -o /opt/etc/crontab https://raw.githubusercontent.com/${repo}/bypass_keenetic/main/crontab
    chmod 755 /opt/etc/crontab
    echo "Установлено добавление задачи в cron для периодического обновления содержимого множества"
    /opt/bin/unblock_update.sh
    echo "Установлены все изначальные скрипты и скрипты разблокировок, выполнена основная настройка бота"

    exit 0
fi

if [ "$1" = "-reinstall" ]; then
    curl -s -o /opt/root/script.sh https://raw.githubusercontent.com/${repo}/bypass_keenetic/main/script.sh
    chmod 755 /opt/root/script.sh || chmod +x /opt/root/script.sh
    echo "Начинаем переустановку"
    echo "Удаляем установленные пакеты и созданные файлы"
    /bin/sh /opt/root/script.sh -remove
    echo "Удаление завершено"
    echo "Выполняем установку"
    /bin/sh /opt/root/script.sh -install
    echo "Установка выполнена."
    exit 0
fi


if [ "$1" = "-update" ]; then
    echo "Начинаем обновление."
    opkg update > /dev/null 2>&1
    echo "Ваша версия KeenOS" "${keen_os_full}."
    echo "Пакеты обновлены."

    /opt/etc/init.d/S22shadowsocks stop > /dev/null 2>&1
    /opt/etc/init.d/S24xray stop > /dev/null 2>&1
    echo "Сервисы остановлены."

    now=$(date +"%Y.%m.%d.%H-%M")
    mkdir /opt/root/backup-"${now}"
    mv /opt/bin/unblock_ipset.sh /opt/root/backup-"${now}"/unblock_ipset.sh
    mv /opt/bin/unblock_dnsmasq.sh /opt/root/backup-"${now}"/unblock_dnsmasq.sh
    mv /opt/bin/unblock_update.sh /opt/root/backup-"${now}"/unblock_update.sh
    mv /opt/etc/dnsmasq.conf /opt/root/backup-"${now}"/dnsmasq.conf
    mv /opt/etc/ndm/fs.d/100-ipset.sh /opt/root/backup-"${now}"/100-ipset.sh
    mv /opt/etc/ndm/ifstatechanged.d/100-unblock-vpn.sh /opt/root/backup-"${now}"/100-unblock-vpn.sh
    mv /opt/etc/ndm/netfilter.d/100-redirect.sh /opt/root/backup-"${now}"/100-redirect.sh
    mv /opt/etc/bot.py /opt/root/backup-"${now}"/bot.py
    cp /opt/etc/bot_config.py /opt/root/backup-"${now}"/bot_config.py
    rm -R /opt/etc/ndm/ifstatechanged.d/100-unblock-vpn > /dev/null 2>&1
    chmod 755 /opt/root/backup-"${now}"/*
    echo "Бэкап создан."

    touch /opt/etc/hosts || chmod 0755 /opt/etc/hosts
    curl -s -o /opt/etc/ndm/fs.d/100-ipset.sh https://raw.githubusercontent.com/${repo}/bypass_keenetic/main/100-ipset.sh
    chmod 755 /opt/etc/ndm/fs.d/100-ipset.sh || chmod +x /opt/etc/ndm/fs.d/100-ipset.sh
    curl -s -o /opt/etc/ndm/netfilter.d/100-redirect.sh https://raw.githubusercontent.com/${repo}/bypass_keenetic/main/100-redirect.sh
    chmod 755 /opt/etc/ndm/netfilter.d/100-redirect.sh || chmod +x /opt/etc/ndm/netfilter.d/100-redirect.sh
    sed -i "s/hash:net/${set_type}/g" /opt/etc/ndm/netfilter.d/100-redirect.sh
    sed -i "s/192.168.1.1/${lanip}/g" /opt/etc/ndm/netfilter.d/100-redirect.sh
    sed -i "s/1082/${localportsh}/g" /opt/etc/ndm/netfilter.d/100-redirect.sh
    sed -i "s/10810/${localportvless}/g" /opt/etc/ndm/netfilter.d/100-redirect.sh
    sed -i 's|ARGS="-confdir /opt/etc/xray"|ARGS="run -c /opt/etc/xray/config.json"|g' /opt/etc/init.d/S24xray > /dev/null 2>&1

    if [ "${keen_os_short}" = "4" ]; then
      echo "KeenOS 4+";
      curl -s -o /opt/etc/ndm/ifstatechanged.d/100-unblock-vpn.sh https://raw.githubusercontent.com/${repo}/bypass_keenetic/main/100-unblock-vpn-v4.sh
    elif [ "${keen_os_short}" = "3" ]; then
      echo "KeenOS 3+";
      curl -s -o /opt/etc/ndm/ifstatechanged.d/100-unblock-vpn.sh https://raw.githubusercontent.com/${repo}/bypass_keenetic/main/100-unblock-vpn.sh
    else
      echo "Your really KeenOS ???";
      curl -s -o /opt/etc/ndm/ifstatechanged.d/100-unblock-vpn.sh https://raw.githubusercontent.com/${repo}/bypass_keenetic/main/100-unblock-vpn.sh
    fi
    chmod 755 /opt/etc/ndm/ifstatechanged.d/100-unblock-vpn.sh || chmod +x /opt/etc/ndm/ifstatechanged.d/100-unblock-vpn.sh

    curl -s -o /opt/bin/unblock_ipset.sh https://raw.githubusercontent.com/${repo}/bypass_keenetic/main/unblock_ipset.sh
    curl -s -o /opt/bin/unblock_dnsmasq.sh https://raw.githubusercontent.com/${repo}/bypass_keenetic/main/unblock.dnsmasq
    curl -s -o /opt/bin/unblock_update.sh https://raw.githubusercontent.com/${repo}/bypass_keenetic/main/unblock_update.sh
    chmod 755 /opt/bin/unblock_*.sh || chmod +x /opt/bin/unblock_*.sh
    sed -i "s/40500/${dnsovertlsport}/g" /opt/bin/unblock_ipset.sh
    sed -i "s/40500/${dnsovertlsport}/g" /opt/bin/unblock_dnsmasq.sh

    curl -s -o /opt/etc/dnsmasq.conf https://raw.githubusercontent.com/${repo}/bypass_keenetic/main/dnsmasq.conf
    chmod 755 /opt/etc/dnsmasq.conf
    sed -i "s/192.168.1.1/${lanip}/g" /opt/etc/dnsmasq.conf
    sed -i "s/40500/${dnsovertlsport}/g" /opt/etc/dnsmasq.conf
    sed -i "s/40508/${dnsoverhttpsport}/g" /opt/etc/dnsmasq.conf

    curl -s -o /opt/etc/bot.py https://raw.githubusercontent.com/${repo}/bypass_keenetic/main/bot.py
    chmod 755 /opt/etc/bot.py
    echo "Обновления скачены, права настроены."

    /opt/etc/init.d/S56dnsmasq restart > /dev/null 2>&1
    /opt/etc/init.d/S22shadowsocks start > /dev/null 2>&1
    /opt/etc/init.d/S24xray start > /dev/null 2>&1

    bot_old_version=$(grep "ВЕРСИЯ" /opt/etc/bot_config.py | grep -Eo "[0-9].{1,}")
    bot_new_version=$(grep "ВЕРСИЯ" /opt/etc/bot.py | grep -Eo "[0-9].{1,}")

    echo "Версия бота" "${bot_old_version}" "обновлена до" "${bot_new_version}."
    sleep 2
    sed -i "s/${bot_old_version}/${bot_new_version}/g" /opt/etc/bot_config.py
    echo PORT=2727 > /opt/etc/config/dropbear.conf
    echo "🔄 Обновление выполнено. Сервисы перезапущены."
#    echo "🔄 Роутер перезагружается! ⏳ Это займет около 2 минут."
    sleep 3
    exit 0

#   Сломан сиквенс, скрипт умиравет вместе с ботом, оставил вышее перезапуск роутера

#    bot_pid=$(ps | grep bot.py | awk '{print $1}')
#    for bot in ${bot_pid}; do kill "${bot}"; done
#    sleep 5
#    python3 /opt/etc/bot.py &
#    check_running=$(pidof python3 /opt/etc/bot.py)
#    if [ -z "${check_running}" ]; then
#      for bot in ${bot_pid}; do kill "${bot}"; done
#      sleep 3
#      python3 /opt/etc/bot.py &
#    else
#      echo "Бот запущен. Нажмите сюда: /start";
#    fi
#
#    exit 0
fi

if [ "$1" = "-reboot" ]; then
    ndmc -c 'opkg dns-override'
    sleep 3
    ndmc -c 'system configuration save'
    sleep 3
    echo "Перезагрузка роутера"
    ndmc -c 'system reboot'
fi

if [ "$1" = "-version" ]; then
    echo "Ваша версия KeenOS" "${keen_os_full}"
fi

if [ "$1" = "-help" ]; then
    echo "-install - use for install all needs for work"
    echo "-remove - use for remove all files script"
    echo "-update - use for get update files"
    echo "-reinstall - use for reinstall all files script"
fi

if [ -z "$1" ]; then
    echo "-install - use for install all needs for work"
    echo "-remove - use for remove all files script"
    echo "-update - use for get update files"
    echo "-reinstall - use for reinstall all files script"
fi
