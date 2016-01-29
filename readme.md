## track - automatic time tracker for computer work

Track logs your desktop active time and the applications you're using to 
create a time chart of your working day.

Unlike [KTimeTracker](https://www.kde.org/applications/utilities/ktimetracker/) 
or [Hamster](https://projecthamster.wordpress.com/about/) Track goes with
as little user interaction as possible. Once configured you just (auto)start it
and Track runs on it's own.

This is an early screenshot to give an idea of how Track works:
![recent screenshot](track-screenshot.png)

**What it does**:
* logs times your computer is active and which applications are in focus
* handles a list of rules which assign certain activities to private work

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


### categories and rules

In order to get an idea how much of the day you spend for work and how much 
for private stuff (or how much you spend on project A or project B) track allows
you to define special *rules* which assign each running program to a category.

Right now categories are still just numbers. In the future I plan to allow
arbitrary categories (or category trees), e.g.:

* work
    - project A
    - project A
* private stuff
** test
* procrastinating

The technical approach is very simple: you define standard Python *regex* rules
which are matched against the *title* of the active window.

For example - in a very simple world - it might be enough to define that browsing
the internet using Firefox is private stuff (category 1) and everything else
is work (category 0). In this case you would just define one rule:

    regex=".*-Mozilla Firefox.*" -> category=1

This way every program whose title does not match `.*-Mozilla Firefox.*` would
be assigned to the default category 0 and all *Firefox* browser windows would 
result in category 1 (which you might be *private* in your eyes).


### requirements

* Linux (Windows coming soon)
* Python 2.7 (Python 3 coming soon)
* PyQt4
* python-libwnck
* libXScrnSaver
* python-psutil

### how to run

Just clone the repository and run `track.py`.

