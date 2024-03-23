import random

import paling

paling.init('web')                     # Give folder containing web files

@paling.expose
def py_random():
    return random.random()

@paling.expose                         # Expose this function to Javascript
def say_hello_py(x):
    print('Hello from %s' % x)

say_hello_py('Python World!')
paling.say_hello_js('Python World!')   # Call a Javascript function

paling.start('templates/hello.html', size=(300, 200), jinja_templates='templates')    # Start
