# TPO Loadtest2

## How to set up:
#### If you need to have multiple versions of python on your computer, I highly recommend using a virtualenv.
1. You need to have python 3.9.6 or newer ("https://www.python.org/downloads/"). 
2. In the console navigate to the loadtest2 folder.
3. Now install all the depedencies found in requirements.txt with the command "py -m pip install -r requirements.txt". 

## How to set up with virtualenv:
1. You need to have python 3.9.6 or newer on your computer ("https://www.python.org/downloads/"). 
2. Install virtualenv with the command "py -m pip install virtualenv"
3. In the console navigate to locust2 folder.
4. Create virtualenv with the command "py -m venv .virtualenv"
5. Activate virtualenv with the command:
    - On windows: ".\.virtualenv\Scripts\activate"
    - On linux: "source ./.virtualenv/bin/activate"
6. You can see "(.virtualenv)" at the beginning of the command line, this indicates that the virtualenv is active.
7. Install dependencies with the command "pip install -r requirements.txt"
8. You will need virtualenv to be active when trying to start the program, otherwise it wont start. So repeat step nr. 5 if you don't see "(.virtualenv)" at the beginning of the command line.

## How to run:
1. Every aspect of a loadtest can be defined in config.py:
    - Set the loadtest environment.
    - Set the desired tasks to be run with the weights you want.
    - Set the loadtest stages.
    - Save the file.
2. In the console navigate to the loadtest2 folder.
3. You can start the loadtest with the command:
    - Without virtualenv: "py -m locust --headless".
    - With active virtualenv: "locust --headless".