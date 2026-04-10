#!/usr/bin/env python3
import os
import json
import subprocess
import base64
import time
import urllib.parse
from flask import Flask, request, jsonify, send_from_directory

import bot_config as config

app = Flask(__name__)
STATIC_DIR = '/opt/root/www'

# ---------- Статика ----------
@app.route('/')
def index():
    return send_from_directory(STATIC_DIR, 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory(STATIC_DIR, path)

# ---------- API (без авторизации) ----------
@app.route('/api/status', methods=['GET'])
def status():
    bot_version = "unknown"
    try:
        with open('/opt/etc/bot.py', 'r') as f:
            for line in f:
                if line.startswith('# ВЕРСИЯ СКРИПТА'):
                    bot_version = line.replace('# ', '').strip()
    except:
        pass

    bot_id = "не установлен"
    try:
        with open('/opt/etc/id', 'r') as f:
            for line in f:
                if line.startswith('# Ваш идентификатор'):
                    bot_id = line.replace('# ', '').strip()
    except:
        pass

    vless_key = ""
    try:
        with open('/opt/etc/xray/key', 'r') as f:
            vless_key = f.read().strip()
    except:
        pass

    hostname = subprocess.getoutput('hostname').strip()
    ss_key = ""
    try:
        with open('/opt/etc/shadowsocks.json', 'r') as f:
            data = json.load(f)
            method = data.get('method', '')
            password = data.get('password', '')
            server = data.get('server', [''])[0]
            port = data.get('server_port', '')
            if method and password and server and port:
                ss_key = f"ss://{method}:{password}@{server}:{port}"
    except:
        pass

    return jsonify({
        'bot_version': bot_version,
        'bot_id': bot_id,
        'vless_key': vless_key,
        'hostname': hostname,
        'ss_key': ss_key
    })

@app.route('/api/lists', methods=['GET'])
def get_lists():
    try:
        dirname = '/opt/etc/unblock/'
        files = [f.replace('.txt', '') for f in os.listdir(dirname) if f.endswith('.txt')]
        return jsonify({'lists': files})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/lists/<listname>', methods=['GET'])
def get_list_content(listname):
    path = f'/opt/etc/unblock/{listname}.txt'
    try:
        with open(path, 'r') as f:
            lines = [line.strip() for line in f if line.strip()]
        return jsonify({'list': listname, 'domains': lines})
    except FileNotFoundError:
        return jsonify({'list': listname, 'domains': []})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/lists/<listname>', methods=['POST'])
def modify_list(listname):
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data'}), 400
    action = data.get('action')
    domains = data.get('domains', [])
    if not domains:
        return jsonify({'error': 'No domains provided'}), 400

    path = f'/opt/etc/unblock/{listname}.txt'
    current = set()
    try:
        with open(path, 'r') as f:
            for line in f:
                d = line.strip()
                if d:
                    current.add(d)
    except FileNotFoundError:
        pass

    if action == 'add':
        added = 0
        for d in domains:
            d = d.strip()
            if d and d not in current:
                current.add(d)
                added += 1
        if added:
            with open(path, 'w') as f:
                for d in sorted(current):
                    f.write(d + '\n')
            subprocess.run(['/opt/bin/unblock_update.sh'], check=False)
            return jsonify({'status': 'added', 'count': added})
        else:
            return jsonify({'status': 'no_change', 'message': 'Nothing new'})
    elif action == 'remove':
        removed = 0
        for d in domains:
            d = d.strip()
            if d in current:
                current.discard(d)
                removed += 1
        if removed:
            with open(path, 'w') as f:
                for d in sorted(current):
                    f.write(d + '\n')
            subprocess.run(['/opt/bin/unblock_update.sh'], check=False)
            return jsonify({'status': 'removed', 'count': removed})
        else:
            return jsonify({'status': 'no_change', 'message': 'Not found'})
    else:
        return jsonify({'error': 'Invalid action'}), 400

@app.route('/api/keys/shadowsocks', methods=['POST'])
def set_ss_key():
    data = request.get_json()
    key = data.get('key')
    if not key:
        return jsonify({'error': 'No key provided'}), 400

    try:
        # Парсинг ss://...
        encodedkey = key.split('//')[1].split('@')[0] + '=='
        password = base64.b64decode(encodedkey).decode().split(':')[1]
        server = key.split('@')[1].split('/')[0].split(':')[0]
        port = key.split('@')[1].split('/')[0].split(':')[1].split('#')[0]
        method = base64.b64decode(encodedkey).decode().split(':')[0]

        config_data = {
            "server": [server],
            "mode": "tcp_and_udp",
            "server_port": int(port),
            "password": password,
            "timeout": 86400,
            "method": method,
            "local_address": "::",
            "local_port": config.localportsh,
            "fast_open": False,
            "ipv6_first": True
        }
        with open('/opt/etc/shadowsocks.json', 'w') as f:
            json.dump(config_data, f, indent=2)

        os.system('/opt/etc/init.d/S22shadowsocks restart')
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/keys/vless', methods=['POST'])
def set_vless_key():
    data = request.get_json()
    key = data.get('key')
    if not key:
        return jsonify({'error': 'No key provided'}), 400

    try:
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
                  '                "flow": "' + str(flow) + '",\n' \
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
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/service/restart', methods=['POST'])
def restart_services():
    os.system('/opt/etc/init.d/S22shadowsocks restart')
    os.system('/opt/etc/init.d/S24xray restart')
    return jsonify({'status': 'ok'})

@app.route('/api/service/reboot', methods=['POST'])
def reboot_router():
    os.system("ndmc -c system reboot")
    return jsonify({'status': 'ok', 'message': 'Rebooting...'})

@app.route('/api/service/dns_override', methods=['POST'])
def dns_override():
    data = request.get_json()
    action = data.get('action')
    if action == 'enable':
        os.system("ndmc -c 'opkg dns-override'")
    elif action == 'disable':
        os.system("ndmc -c 'no opkg dns-override'")
    else:
        return jsonify({'error': 'Invalid action'}), 400
    time.sleep(5)
    os.system("ndmc -c 'system configuration save'")
    os.system("ndmc -c 'system reboot'")
    return jsonify({'status': 'ok'})

@app.route('/api/update/check', methods=['GET'])
def check_update():
    # Можно получить реальную версию с GitHub
    current = "2.2.4"
    latest = "2.2.5"
    return jsonify({'current': current, 'latest': latest})

@app.route('/api/update/perform', methods=['POST'])
def perform_update():
    os.system("curl -s -o /opt/root/script.sh https://raw.githubusercontent.com/Yurbos/bypass_keenetic/main/script.sh")
    os.chmod("/opt/root/script.sh", 0o0755)
    subprocess.run(['/opt/root/script.sh', '-update'], check=False)
    os.system("/opt/etc/init.d/S100bot restart")
    os.system("/opt/etc/init.d/S101web restart")
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)