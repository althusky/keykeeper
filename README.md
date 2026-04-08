## Lightweight Secret Storage Server

An attempt to implement a secret storage service with a minimal entry threshold for personal use. I understand all the limitations and possible vulnerabilities of the service, but it is primarily intended for quick deployment and use in local networks.

The service opens a port for transferring secrets, but does not have a web interface for management. To work with and manage the server, an SSH connection is required.

---

## Quick Start

* To start the server, you must provide the database encryption key. It can be provided directly as a parameter `--db_key="key"` or after startup using the command `keykeeper serverkey activate [key]`

* The key is generated with `keykeeper serverkey generate`

* A new key can only be applied to a new database. For it to work, there must be no database dump file; otherwise, the system will try to open the dump with the new key.

```bash
cd project/folder
pip install -e . 

keykeeper serverkey generate
keykeeperd --db_key="..."  
```
### Manage server
```bash
keykeeper user edit user_name --create --active
keykeeper secret edit secret_name secret_value --create --active
keykeeper user secret user_name add secret_name
```

With docker.
```bash
docker buildx build -t keykeeper_image --load .

docker run --rm -d \
-p 8080:7012 \
--volume /volume/folder:/data \
--name keykeeper_container \
--env LOGLEVEL=INFO \
keykeeper_image --host=0.0.0.0 --port=7012 --db_file=/data/sqlite.bin --db_key="DB_KEY"
```
### Manage server in Docker mode
```bash
docker exec keykeeper_container keykeeper user edit user_name --create --active
docker exec keykeeper_container keykeeper secret edit secret_name secret_value --create --active
docker exec keykeeper_container keykeeper user secret user_name add secret_name
```

---

## Server CLI Interface

* The server does not have a web interface, so commands are executed directly via the host command line or through `docker exec`

* `keykeeper serverkey activate [key]` — passes the key and starts the database
* `keykeeper serverkey generate` — creates a key for a new database. This only generates a key and does not modify the database.
* ~~`keykeeper serverkey [db_key] [dump|load]` — get a copy of the database in plain JSON format (potentially dangerous command)~~


* `keykeeper user edit [user-name] --descr [descr] --create --active` — create/edit a user. On creation, returns the user key
* `keykeeper user ls` — list users
* `keykeeper user lock [user-name]` — lock user
* `keykeeper user unlock [user-name]` — unlock user
* ~~keykeeper user remove [user-name] — delete user~~
* `keykeeper user key [user-name] --change` — return key; if `change`, rotate and return a new one
* `keykeeper user secret [user-name] [ls|add|remove] [secret-name]` — list the user secrets, bind/unbind a user to a secret 
* `keykeeper secret edit [user-name] [value] --descr [descr] --readonly --active --create` — create a new secret

* `keykeeper secret ls` — list secrets
* ~~keykeeper secret [secret-name] [value] — set secret value~~
* ~~keykeeper secret lock [secret-name] — lock secret~~
* ~~keykeeper secret unlock [secret-name] — unlock secret~~
* ~~keykeeper secret remove [secret-name] — delete secret~~

---

## Client

* All client-side code is located in `keykeeper_protocol.py`
* Unfortunately, the Python standard library does not include encryption tools, so you need to install the only dependency:
  `python3 -m pip install pycryptodome`
* The main function is `keykeeper`, which is used to get or set a secret value
* Access does not use a username — only a key and a secret name are required

---

## Makefile 

* `make run` - Starts the server 
* `make stop` - Stops the server
* `make connect` - Connects to a running server in terminal mode and allows you to manage the server via the keykeeper command
* `make test` - Runs tests
