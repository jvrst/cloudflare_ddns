# Cloudflare-DDNS
No-dependencies Python script to update cloudflare DNS settings.

- Definitely not supported: python3.7
- Maybe supported: 3.8, 3.9
- Supported: 3.10+

Notes:
---
- Decided to use sqlite3 for the IPs for easy tracking (want to easily know how many times it changes)
- Could've used the logs, but those will be rotated so that's a bit harder to then track back.
- Used `ifconfig.me` because there's no DNS resolver in the stdlib

## Setup
1. Run this:
```
cp config.json.example config.json
```

2. Make sure the settings are correct, add as many projects as necessary (I have a couple of sites pointing to the same loadbalancer IP)

3. Test it out.

4. Optional: add to crontab

```sh
*/5 * * * * /usr/bin/python3 /home/user/cloudflare_ddns/cloudflare_dns.py
```

