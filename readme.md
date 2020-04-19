# Track - automatic time tracker for computer work

Track logs the time you're actively working on your desktop computer as well as
the applications you're using in order to create a time chart of your
working day.

Track does *not* connect *anywhere* and shares your information with nobody!

Actually this is why I started this project in the first place..

However at the current development stage Track stores all data unencrypted,
so please ensure nobody has access to your Track directory (usually `~/.track`).

Unlike [KTimeTracker](https://www.kde.org/applications/utilities/ktimetracker/)
or [Hamster](https://projecthamster.wordpress.com/about/) Track aims at zero
user interaction. Once configured you just (auto)start it and Track runs on
it's own.

This is an early screenshot to give an idea of how Track works:
![recent screenshot](track-screenshot.png)

**What it does**:
* logs times when your computer is active and which applications are in focus
* handles a list of regex-rules which assign certain activities to private work

**What it does not**:
* manage an abstract task list you would have to maintain
* send any information to someone

**When you should use Track**:
* in case you're working mainly on a computer like software developers
* if you want to know how long you've been at work today
* if you want to know how much of your private time you spent on the computer
* if you want to waste your time with another self profiling tool

The current *project state* is (still! damn!) very early (see the
[schedule](progress.md)).

Very basic features are still missing so it might be wise to come back in a
week or so.
However it's totally save to use the tool and it's providing some interesting
information already.


## Categories and rules

In order to get an idea how much of the day you spend for work and how much
for private stuff (or how much you spend on project A or project B) track allows
you to define special *rules* which assign each running program to a category.

Right now categories are still just numbers. In the future I plan to allow
arbitrary categories (or category trees), e.g.:

* work
  - project A
  - project B
  - browsing on github.com
* private stuff
  - project C
* procrastinating
  - browsing on reddit.com

The technical approach is very simple: you define standard Python *regex* rules
which are matched against the *title* of the active window.

For example - in a very simple world - it might be enough to define that browsing
the internet using Firefox is private stuff (category 1) and everything else
is work (category 0). In this case you would just define one rule:

    regex=".*-Mozilla Firefox.*" -> category=1

This way every program whose title does not match `.*-Mozilla Firefox.*` would
be assigned to the default category 0 and all *Firefox* browser windows would
result in category 1 (which you might be *private* in your eyes).


## Requirements

Basically you Python3 with `PyQt5`, `psutil` and `zmq` installed. Some PyQt5 versions do not
behave well and you will need build-essentials etc to make it work.
For me installing the following packages worked:

* Linux with X11 (Wayland had some problems when I last checked it)
* or Windows - it once worked but currently I have no way to check it
* Python 3+
* `python3-devel` or equivalent via `apt`, `dnf`, etc.
* `PyQt5` via pip (v5.14 worked for me)
* `zmq` via pip
* `psutil` via pip

Try this pip command: `pip3 install --user --upgrade psutil zmq PyQt5==5.14`


## How to run

Just clone the repository and run `track`.

To list starting / endings times of recorded days run `track-cli list`


## Know limitations / shortcomings

* Currently Track seems to not work well with Wayland, which might be an issue of both Track and
  Wayland. When your're on Linux consider using X11.
* I started this project 5 years ago when my Python skills were still very weak. Please do either
  not look at the code or help me improve it.
* Track *records* data but still does not evaluate it. `track-cli` does some steps in that
  direction.
* No check for plausibility: if - for example - your computer wakes up at 3:12 for just a second
  this incident will be recorded and currently there is no way to remove this stray event and
  your day will officially start at 3:12
* Setup / autostart worked once upon a time but doesn't now. But as a Linux Pro you know what to do.
