## Lightweight Secret Storage Server

An attempt to implement a secret storage service with a minimal entry threshold for personal use. I understand all limitations and possible vulnerabilities of the service, but it is primarily intended for quick deployment and use in local networks.

The service opens a port for transferring secrets, but does not have a web interface for management. To work with and manage the server, an SSH connection is required.

---

## Quick Start

* run with `python3 server.py`
  To start the server, you need to pass a database dump encryption key. It can be provided directly as a parameter `--db_key="key"` or after startup using the command `keykeeper.py serverkey activate [key]`

* The key is generated with `keykeeper serverkey generate`

* A new key can only be applied to a new database. For it to work, there must be no database dump file; otherwise, the system will try to open the dump with the new key.

```bash
keykeeper serverkey generate
python3 server.py --db_key="..."  
keykeeper user edit user_name --create --active
keykeeper secret edit secret_name secret_value --create --active
keykeeper user secret user_name add secret_name
```

---

## Server CLI Interface

* The server does not have a web interface, so commands are executed directly via the host command line or through `docker exec`

* `keykeeper serverkey activate [key]` — passes the key and starts the database
* `keykeeper serverkey generate` — creates a key for a new database. No actions are performed on the database itself
~`keykeeper serverkey json` — get a copy of the database in plain JSON format (potentially dangerous command)~~


* `keykeeper user edit [name] --descr [descr] --create --active` — create/edit a user. On creation, returns the user key
~keykeeper user ls — list users~~
~keykeeper user lock [name] — lock user~~
~keykeeper user unlock [name] — unlock user~~
~keykeeper user remove [name] — delete user~~
~keykeeper user key name [--change] — return key; if `change`, rotate and return a new one~~
* `keykeeper user secret [name] [ls|add|remove] [secret_name]` — bind a user to a secret
* `keykeeper secret edit [name] [value] --descr [descr] --readonly --active --create` — create a new secret

~keykeeper secret ls — list secrets~~
~keykeeper secret [name] [value] — set secret value~~
~keykeeper secret lock [name] — lock secret~~
~keykeeper secret unlock [name] — unlock secret~~
~keykeeper secret remove [name] — delete secret~~

---

## Client

* All client-side code is located in `keykeeper_protocol.py`
* Unfortunately, the Python standard library does not include encryption tools, so you need to install the only dependency:
  `python3 -m pip install pycryptodome`
* The main function is `keykeeper`, which is used to get or set a secret value
* Access does not use a username — only a key and a secret name are required

---

