# Support Chat Production Setup Guide

## 1. **Install production dependencies**

```bash
   pip install -r requirements_prod.txt
```

## 2. **Create environment file**

```bash
   cp .env.example .env
```

## 3. **Configure environment variables in `.env`**

```bash
   SUPPORT_CHAT_SECRET_KEY=your-secret-key-here
   SUPPORT_CHAT_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
   SUPPORT_CHAT_DB_NAME=support_chat_db
   SUPPORT_CHAT_DB_USER=support_chat_db_access
   SUPPORT_CHAT_DB_PASS=your_strong_db_password
   SUPPORT_CHAT_DB_HOST=localhost
   SUPPORT_CHAT_DB_PORT=5432
```

## 4. **Set up PostgreSQL database**

```bash
   sudo -u postgres psql
    CREATE DATABASE support_chat_db;
    CREATE USER support_chat_db_access WITH PASSWORD 'your_strong_db_password';
    ALTER ROLE support_chat_db_access SET client_encoding TO 'utf8';
    ALTER ROLE support_chat_db_access SET default_transaction_isolation TO 'read committed';
    ALTER ROLE support_chat_db_access SET timezone TO 'your_tz_database_timezone_string';
    GRANT ALL PRIVILEGES ON DATABASE support_chat_db TO support_chat_db_access;
    ALTER DATABASE support_chat_db OWNER TO support_chat_db_access;
   \q
```

## 5. **Run migrations**

```bash
   python manage.py migrate
```

## 6. **Create initial system manager**

```bash
   python manage.py create_system_manager \
       username email@etsu.edu password \
       "First" "Last" "System Manager" "Computing"
```

## 7. **Collect static files**

```bash
   python manage.py collectstatic --noinput
```

## 8. **Configure Gunicorn systemd service**

Create `/etc/systemd/system/support_chat.socket`:

```ini
   [Unit]
   Description=support_chat socket

   [Socket]
   ListenStream=/run/support_chat.sock

   [Install]
   WantedBy=sockets.target
```

Create `/etc/systemd/system/support_chat.service`:

```ini
   [Unit]
   Description=Green Unicorn support_chat daemon
   Requires=support_chat.socket
   After=network.target

   [Service]
   User=www-data
   Group=www-data
   WorkingDirectory=/path/to/support_chat
   Environment="PATH=/path/to/support_chat/.venv/bin"
   ExecStart=/path/to/support_chat/.venv/bin/gunicorn \
             --access-logfile - \
             --workers 3 \
             --bind unix:/run/support_chat.sock \
             support_chat.wsgi:application

   [Install]
   WantedBy=multi-user.target
```

## 9. **Configure Nginx** Create `/etc/nginx/sites-available/support_chat`:

```nginx
   server {
       listen 80;
       server_name yourdomain.com;

       location = /favicon.ico { access_log off; log_not_found off; }
       
       location /static/ {
           root /var/www/;
           expires 1y;
           add_header Cache-Control "public, immutable";
       }

       location /media/ {
           root /var/www/;
       }

       location / {
           include proxy_params;
           proxy_pass http://unix:/run/support_chat.sock;
       }
   }
```

Enable the site:

```bash
   sudo ln -s /etc/nginx/sites-available/support_chat /etc/nginx/sites-enabled
   sudo nginx -t
   sudo systemctl restart nginx
   sudo systemctl restart gunicorn
```

* NOTE: This might not work unless you run `sudo ufw allow 'Nginx HTTP'` (assuming you use Uncomplicated Firewall/ufw)

## 10.  **Configure your web domain (if not already done)**

Log into domain registrar site and go to DNS settings.
Find out [which nameservers your Domain Registrar uses](https://www.bluehost.com/help/article/modify-nameservers-other-registrars).

**a. Customize your web domain's nameservers**

To use a purchased domain on your Web server, you need to customize the domain's
nameservers. Your server host should tell you what their nameservers are and
your web domain registrar should provide a setting that allows you to set custom
nameservers.

For example, if your Web server is hosted by DigitalOcean, they actually have explicit
instructions for how to add their nameservers on a variety of different popular domain
registrars including Bluehost, GoDaddy, Namecheap, and several more (see [this page](https://docs.digitalocean.com/products/networking/dns/getting-started/dns-registrars/)).

Set custom nameservers (obviously use different ones if not deployed on DigitalOcean):

```
ns1.digitalocean.com
ns2.digitalocean.com
ns3.digitalocean.com
```

**b. Server host: Add A records**

Again, different Web server hosts should provide their own settings for managing
your Web server's DNS settings. In Digital Ocean I create my A records by going to:
`Create > Domains/DNS > Enter domain name`

You need to create the following records:
```
A: Host: @, Direct to: <site IP address>
A: Host: www, Direct to <site IP address>
```

Once these records are actually updated on the DNS (this can take some time),
your Nginx configuration will basically be able to accept traffic arriving
at your domain name on port 80 (otherwise, Nginx would need your public IP
address in the server_name field).

## 11. **Set Up HTTPS**!

Of course, you can't log in and interact securely over port 80, so you will next
need to encrypt your shit. I HATE setting up TLS and writing all the Nginx
configuration, so I use certbot to make my life easy! Here's a rundown:

`sudo apt install certbot python3-certbot-nginx` (If you're not using Ubuntu/Debian, screw you)

Make sure Nginx sans regular HTTP is allowed:

```
(assuming you use Uncomplicated Firewall/ufw)
sudo ufw allow 'Nginx Full'
sudo ufw delete allow 'Nginx HTTP'
```

Run certbot with these args (with your domain name, ofc):

`sudo certbot --nginx -d example.com -d www.example.com`

Run through the setup.

Now visit the https version of your site in a web browser to make sure it
works.

* If there was a 404 error and the server failed the acme challenge, you
will want to check that your DNS nameservers have been configured for your
server provider and that you have set the necessary A records pointing
your domain variants to your server IP address. I would wait 20-30 minutes
after setting the A records, based on my experience.

**Verify Certbot Auto-Renewal**

```
sudo systemctl status certbot.timer
sudo certbot renew --dry-run
```

## 12. **Secure SSH**

**Create an RSA keypair**

a. On your local machine: `ssh-keygen -t rsa -b 4096`
b. View your public key: `cat ~/.ssh/<name_of_key>.pub`
c. On your server: save the public key in the `~/.ssh/authorized_keys` file (create the file if it doesn't exist).

**Change the Default Port**

Change default port! 22 is the default. Set a different port because 22
is the first a hacker would try.

Common ports:

```
20 	tcp 		ftp-data
21 	tcp 		ftp server
22 	tcp 		ssh server
23 	tcp 		telnet server
25 	tcp 		email server
53 	tcp/udp 	Domain name server
69 	udp 		tftp server
80 	tcp 		HTTP server
110 tcp/udp 	POP3 server
123 tcp/udp 	NTP server
443 tcp 		HTTPS server
```

`sudo nano /etc/ssh/sshd_config`

-- Change the line "Port 22" to your port.

**Create SSH Config File:**

To avoid using the "-P" argument with ssh command on your local machine,
and to avoid having to specify the key to use each time you want to ssh
into your server, create an ssh config file: `~/.ssh/config`

Example local `.ssh/config` file:

```
Host example.com
    Hostname <ip_address> # (I prefer IP over domain name in case their is a problem with resolution)
    Port 4858 # (whatever port you chose in sshd_config)
    User ryan
    IdentityFile ~/.ssh/private_key_name
```

**Update IPTables Rules:**

```
sudo ufw allow <new_port>/tcp comment 'SSH port'
sudo ufw delete allow "OpenSSH"
sudo ufw status
```

Now you can test your SSH connection - `ssh example.com` - to make sure you can ssh from your local
machine to your server. Make sure you have some backup way of getting into your server (like a web-based
admin console or something) in case you bork your local machine or bork your server's ssh service or
something.

## 13. **Configure Fail2Ban**

You should set up fail2ban to monitor any exposed ports (like 443 and your SSH port).
Just find a tutorial. I'm too lazy and not a cybersecurity professional.

```
sudo apt install fail2ban
cd /etc/fail2ban
sudo cp jail.conf jail.local
sudo nano jail.local
```

Set rules for SSH as part of the [DEFAULT] config.

sudo systemctl restart fail2ban
systemctl status fail2ban


## 14. **Increase the SSH Timeout**

Servers apparently have a default timeout of about 15 minutes. This is not
good if you are running a major system upgrade. I have had an upgrade
interrupted and it caused breakage that made my webserver go down until I
cleaned up the mess and reinstalled everything.

sudo nano /etc/ssh/sshd_config

Find the (perhaps commented) lines, `ClientAliveInterval` and `ClientAliveCountMax`.
The alive interval is the amount of time that elapses in seconds before the host
sends a keep-alive request to your client. The alive count max variable specifies the
amount of times the server will send a keep-alive request that recieves no response.
After the max is reached with no response, the connection terminates. I set mine as such:

```
ClientAliveInterval 600
ClientAliveCountMax 4
```

This means that every 600 seconds (10 minutes) a keep-alive message is sent to my SSH
client. If I am inactive for as much as 40 minutes (the time for all 4 keep-alive messages)
to be sent, my connection will then be terminated. Finally, restart the ssh service to
apply your changes:

`sudo systemctl restart ssh`

## 15. **Start and enable services**

```bash
    sudo systemctl start support_chat.socket
    sudo systemctl enable support_chat.socket
    sudo systemctl start support_chat
    sudo systemctl enable support_chat
```

## Security Considerations

- Always use strong secret keys in production
- Enable HTTPS with TLS certificates
- Keep Django and dependencies updated
- Regular database backups recommended
- File uploads are validated and sanitized
- CSRF protection enabled
- Session hijacking protection via HTTP-only cookies

## Troubleshooting

### Static files not loading in production

```bash
python manage.py collectstatic --clear --noinput
sudo systemctl restart support_chat
```

### Database connection issues

Check environment variables and PostgreSQL service status:

```bash
sudo systemctl status postgresql
```

### Gunicorn socket errors

```bash
sudo systemctl status support_chat.socket
sudo systemctl status support_chat.service
sudo journalctl -u support_chat.service
```

### Permission issues with media files

```bash
sudo chown -R www-data:www-data /var/www/media
sudo chmod -R 755 /var/www/media
```

### General problems with services

Check the status of services using `systemctl status`. When you see errors, use `journalctl`
for more info. To ensure you can read logs with `journalctl` add your server's user account
to the correct groups:

```
usermod -aG sudo,adm,systemd-journal username
groups username
```

Let's say, for example, that when you run `systemctl status gunicorn`, you find that it exited
with an error. You can then check the log `journalctl -e -u gunicorn` to figure out more detail
so you can search the error and correct it.

Use the systemctl `start`, `stop`, and `restart` to start and stop services.
Use `sudo systemctl daemon-reload` after you make a change to an enabled service file.
