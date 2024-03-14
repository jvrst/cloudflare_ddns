import http.client
import sqlite3
import json
import urllib.parse
from dataclasses import dataclass
from typing import List

with open('config.json', 'r') as config_file:
    config = json.load(config_file)
    API_KEY = config["CLOUDFLARE_API_KEY"]
    EMAIL = config["CLOUDFLARE_EMAIL"]
    NTFY_HOST = config["NTFY_HOST"]
    NTFY_PATH = config["NTFY_PATH"]
    PROJECTS = config["PROJECTS"]


@dataclass
class CloudflareDNS():
    zone_id: str
    dns_record_id: str
    name: str
    proxied: bool = False


def get_external_ip():
    conn = http.client.HTTPConnection("ifconfig.me")
    conn.request("GET", "/ip")
    response = conn.getresponse()
    return response.read().decode()


def update_dns_record(zone_id, name, dns_record_id, ip, proxied=False):
    # 'X-Auth-Email': EMAIL,
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json',
    }
    body = json.dumps({
        'type': 'A',
        'name': name,
        'content': ip,
        'ttl': 120,
        'proxied': proxied
    })

    connection = http.client.HTTPSConnection("api.cloudflare.com")
    connection.request(
        "PUT", f"/client/v4/zones/{zone_id}/dns_records/{dns_record_id}", body, headers)
    response = connection.getresponse()
    return response.read().decode()


def send_notification(message: str):
    body = urllib.parse.urlencode({'message': message}).encode('utf-8')
    headers = {
        'Content-type': 'application/x-www-form-urlencoded'
    }
    connection = http.client.HTTPSConnection(NTFY_HOST)
    connection.request("POST", f"/{NTFY_PATH}", body, headers)
    response = connection.getresponse()
    return response.read().decode()


def update_all_records(sites: List[CloudflareDNS], ip):
    for site in sites:
        result = update_dns_record(
            zone_id=site.zone_id,
            name=site.name,
            dns_record_id=site.dns_record_id,
            ip=ip,
            proxied=site.proxied
        )
        print(f"Updated {site.name} DNS record:", result)


def parse_projects():
    sites = []
    for project in PROJECTS:
        site = CloudflareDNS(
            zone_id=project["zone_id"],
            dns_record_id=project["dns_record_id"],
            name=project["name"],
            proxied=project["proxied"]
        )
        sites.append(site)
    return sites

def main():
    external_ip = get_external_ip()
    conn = sqlite3.connect('cloudflare.db')
    c = conn.cursor()
    c.execute(
        'CREATE TABLE IF NOT EXISTS external_ip (ip TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')

    res = c.execute('SELECT * FROM external_ip ORDER BY ROWID DESC').fetchone()
    if res is None or res[0] != external_ip:
        c.execute('INSERT INTO external_ip (ip) VALUES (?)', (external_ip,))
        conn.commit()

        msg = "External IP changed, updating Cloudflare DNS settings"
        send_notification(msg)

        parsed_projects = parse_projects()
        update_all_records(parsed_projects, external_ip)
    else:
        print("IP address has not changed, skipping update")

    conn.close()


if __name__ == "__main__":
    main()