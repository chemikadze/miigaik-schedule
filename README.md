About
=====

Unofficial portal of MIIGAiK university schedule. Is not
affiliated with university in any sense, running only on
voluntary basis.

If you know how to make it better, feel free to send a PR
or [mail me](mailto:chemikadze+miigaik-schedule-ng@gmail.com).

Contributing
============

Install GAE, initialize venv and make linkenv (gae venv hack):
```
virtualenv .venv
source .venv/bin/activate
pip install git+https://github.com/ze-phyr-us/linkenv.git
pip install -r requirements.txt
linkenv .venv/lib/python2.7/site-packages gaenv
env -i bash -l
```
Start dev server:
```
dev_appserver.py .
```
Initialize test dataset
``` 
echo 'MIIGAIK_SCHEDULE_IMPORTER_SOURCE=mock.MockDataSource()' > /tmp/.miigaik-env
open http://localhost:8081/tasks/update_db
```
