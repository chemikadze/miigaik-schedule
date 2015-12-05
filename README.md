About
=====

Unofficial portal of MIIGAiK university schedule. Is not
affiliated with university in any sense, running only on
voluntary basis.

If you know how to make it better, feel free to send a PR
or [mail me](mailto:chemikadze+miigaik-schedule-ng@gmail.com).

Contributing
============

1. Install GAE
2. Initialize venv and make linkenv (gae venv hack):
```
$ virtualenv .venv
$ source .venv/bin/activate
(.venv)$ pip install git+https://github.com/ze-phyr-us/linkenv.git
(.venv)$ pip install -r requirements.txt
(.venv)$ linkenv .venv/lib/python2.7/site-packages gaenv
(.venv)$ env -i bash -l
$ dev_appserver.py .
```
3. Initialize test dataset
```
export
```
