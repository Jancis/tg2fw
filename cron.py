import sqlite3
import os
import subprocess

DB_LOCATION = os.path.dirname(__file__) + '/database.db'

# Return ip whitelist
def iplist():
  
  conn = sqlite3.connect(DB_LOCATION)
  # conn.row_factory = lambda cursor, row: row[0]
  conn.row_factory = lambda cursor, row: {'mc_login': row[0], 'ip': row[1]}
  curr = conn.cursor()
  curr.execute('SELECT mc_login, ip FROM iplist')
  ip_list = curr.fetchall()
  conn.close()  
  return ip_list

# Clean previous entries
subprocess.call('iptables -D INPUT -m tcp -p tcp --dport {} -j mcwhitelist'.format(config.MINECRAFT_PORT), shell=True)
subprocess.call('iptables -F mcwhitelist', shell=True)
subprocess.call('iptables --delete-chain mcwhitelist', shell=True)

# Start new chain and allow localhost
subprocess.call('iptables --new mcwhitelist', shell=True)
subprocess.call('iptables -A mcwhitelist --src 127.0.0.1 -j ACCEPT', shell=True)


# iptables = subprocess.call('iptables -I FORWARD -eth 0 -m '+protocol+' -t'+protocol+'--dport '+port+'-j DNAT --to-destination'+ipAddress, shell=True)

# Add ip addresses to whitelist  
for entry in iplist():
  subprocess.call('iptables -A mcwhitelist --src {}/32 -j ACCEPT'.format(entry['ip']), shell=True)

# Drop packets from other hosts
subprocess.call('iptables -A mcwhitelist -j DROP', shell=True)

# Use chain for packets to minecraft port
subprocess.call('iptables -I INPUT -m tcp -p tcp --dport {} -j mcwhitelist'.format(config.MINECRAFT_PORT), shell=True)
