import odrive
from odrive.enums import *
from bottle import *
import time

# DEFINITIONS

ppr = 8192

# MOTOR INITIALIZATION

print('Looking for an ODrive...')
odrv0 = odrive.find_any()

print('Callibrating ODrive...')
odrv0.axis0.requested_state = AXIS_STATE_FULL_CALIBRATION_SEQUENCE
while odrv0.axis0.current_state != AXIS_STATE_IDLE:
    time.sleep(0.1)

print('ODrive callibrated. Setting state to Close Loop Control');
odrv0.axis0.requested_state = AXIS_STATE_CLOSED_LOOP_CONTROL

# MOTOR CONTROL

def set_position(position):
    odrv0.axis0.controller.config.control_mode = CTRL_MODE_POSITION_CONTROL
    odrv0.axis0.controller.pos_setpoint = position    

def current_position():
    return odrv0.axis0.encoder.pos_estimate

def closest_home():
    return current_position() % ppr

# HTML GENERATION

def form(action, body):
    return '<form action=/' + action + ' method="POST">' + body + '</form>'

def tag(tagname, body):
    return '<' + tagname + '>' + body + '</' + tagname + '>'

def a(href, body):
    return '<a href="' + href + '">' + body + '</a>'

def button(label):
    return '<input value="' + label + '" type="submit" />'

def p(body):
    return tag('p', body)

def h1(body):
    return tag('h1', body)

# HTTP ROUTES

@route('/')
def index():
    return (
        h1('MunFilms 360') +
        p(form('home', button('Torna a casa'))) +
        p(form('setpos',
            'Fixa posició a <input name="position"></input>' +
            button('OK'))) +
        p(form(
            '/',
            'posició actual: ' + str(current_position()) + button('actualitza')
            ))
        )

@post('/home')
def gohome():
    set_position(closest_home())
    redirect('/')

@post('/setpos')
def setpos():
    set_position(request.forms.get('position'))
    redirect('/')

run(host='localhost', port=8080, debug=True)
