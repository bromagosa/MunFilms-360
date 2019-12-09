import odrive
from odrive.enums import *
from bottle import *
from functools import reduce
import time
import threading
import os

# DEFINITIONS

ppr = 8192
turns = 1
rpm = 30
home = 0

cwd = os.path.dirname(os.path.realpath(__file__))

# MOTOR INITIALIZATION

print('Looking for an ODrive...')
odrv0 = False
odrv_ready = False

def init_odrive():
    global odrv0
    global odrv_ready
    odrv0 = odrive.find_any()
    print('Calibrating ODrive...')
    odrv0.axis0.requested_state = AXIS_STATE_FULL_CALIBRATION_SEQUENCE
    while odrv0.axis0.current_state != AXIS_STATE_IDLE:
        time.sleep(0.1)
    print('ODrive calibrated. Setting state to Close Loop Control');
    odrv0.axis0.requested_state = AXIS_STATE_CLOSED_LOOP_CONTROL
    odrv0.axis0.controller.config.vel_limit = rpm * (ppr / 60)
    '''
    # INITIAL CONFIGURATION, IN CASE IT IS LOST SOMEDAY
    odrv0.axis0.motor.config.current_lim = 60
    odrv0.axis0.controller.config.vel_limit_tolerance = 5
    odrv0.axis0.encoder.config.cpr = 8192
    odrv0.axis0.motor.config.pole_pairs = 7
    odrv0.axis0.controller.config.vel_gain = 0.00086
    odrv0.axis0.controller.config.pos_gain = 146.8
    odrv0.axis0.controller.config.vel_integrator_gain = 0.5 * 20 * odrv0.axis0.controller.config.vel_gain
    '''
    print('ODrive ready for a spin :)')
    go_home()
    odrv_ready = True

init_thread = threading.Thread(target=init_odrive)
init_thread.start()

# MOTOR CONTROL

def calibrate_anticogging():
    print('Calibrating anti-cogging')
    odrv0.axis0.controller.config.vel_gain = 0.0005
    odrv0.axis0.controller.config.pos_gain = 300
    odrv0.axis0.controller.config.vel_integrator_gain = 0.0150
    odrv0.axis0.controller.start_anticogging_calibration()

def set_position(position):
    odrv0.axis0.controller.config.control_mode = CTRL_MODE_POSITION_CONTROL
    odrv0.axis0.controller.pos_setpoint = position

def set_rpm(rpm):
    odrv0.axis0.controller.config.vel_limit = rpm * (ppr / 60)

def current_position():
    return odrv0.axis0.encoder.pos_estimate

def closest_home():
    return ((current_position() // ppr) * ppr) + home

def go_home():
    closest = closest_home()
    set_rpm(25)
    set_position(closest)
    while (abs(current_position() - closest) > 50):
        time.sleep(0.1)
    print('got home')
    set_rpm(rpm)

# HTML GENERATION

def attributes(**kwargs):
    # turns arguments into a string of HTML attributes
    if (kwargs.values().__len__()):
        return reduce(
                (lambda a, b: a + b),
                map(
                    (lambda assoc: ' ' + assoc[0] + ' = "' + assoc[1] + '" '),
                    kwargs.items())
                ).replace('klass', 'class')
    else:
        return ''

def form(action, body):
    return '<form action=/' + action + ' method="POST">' + body + '</form>'

def tag(tagname, body, **kwargs):
    return ('<' + tagname + attributes(**kwargs) + '>'
            + body + '</' + tagname + '>')

def a(href, body, **kwargs):
    attr = kwargs
    attr['href'] = href
    return tag('a', body, **attr)

def button(label):
    return '<input value="' + label + '" type="submit" />'

def p(body, **kwargs):
    return tag('p', body, **kwargs)

def h1(body, **kwargs):
    return tag('h1', body, **kwargs)

def h3(body, **kwargs):
    return tag('h3', body, **kwargs)

def link(body, **kwargs):
    return tag('link', body, **kwargs)

def div(body, **kwargs):
    return tag('div', body, **kwargs)

def img(body, **kwargs):
    return tag('img', body, **kwargs)

def input(body, **kwargs):
    return tag('input', body, **kwargs)

def span(body, **kwargs):
    return tag('span', body, **kwargs)

# WIDGETS

def pos_updater_script():
    return """
    <script>
        p = document.querySelector('.position');
        setInterval(
            function () {
                var req = new XMLHttpRequest();
                req.addEventListener("load", function () {
                    p.innerHTML = 'posició actual: ' + this.responseText;
                });
                req.open("GET", "/getpos");
                req.send();
            }, 150);

    </script>
    """

# HTTP ROUTES

@route('/static/<filename>')
def server_static(filename):
    return static_file(filename, root = cwd + '/static')

@route('/')
def index():
    return (
        link('',
            href = 'static/style.css',
            type = 'text/css',
            rel = 'stylesheet') +
        div(
            h1('MunFilms 360') +
            div(
                a('home', img('', src = 'static/home.png')) +
                a('turn', img('', src = 'static/turn.png')) +
                a('stop', img('', src = 'static/stop.png')),
                klass = 'controls'
            ) +
            h3('Configuració') +
            div(
                form(
                    'setspeed',
                    span('Velocitat (RPM):', klass = 'label') +
                        input('', name = 'speed', klass = 'input') +
                        span('(' + str(rpm) + ')', klass = 'value') +
                        button('OK')) +
                form(
                    'setturns',
                    span('Voltes:', klass = 'label') +
                        input('', name = 'turns', klass = 'input') +
                        span('(' + str(turns) + ')', klass = 'value') +
                        button('OK')) +
                form('sethome', button('Fixar posició inicial')) +
                form('anticog', button('Calibratge automàtic')),
                klass = 'config') +
            img('', src = 'static/gif-web-alpha2.gif', klass = 'logo'),
            klass = 'wrapper'
        )
    )

@route('/home')
def gohome():
    if (odrv_ready):
        go_home()
    redirect('/')

@route('/turn')
def turn():
    if (odrv_ready):
        set_position(current_position() + (ppr * turns))
    redirect('/')

@route('/stop')
def stop():
    if (odrv_ready):
        odrv0.axis0.requested_state = AXIS_STATE_IDLE
        time.sleep(0.25)
        odrv0.axis0.requested_state = AXIS_STATE_CLOSED_LOOP_CONTROL
    redirect('/')

@post('/setspeed')
def setspeed():
    if (odrv_ready):
        global rpm
        rpm = min(float(request.forms.get('speed') or 0), 100)
        set_rpm(rpm)
    redirect('/')

@post('/setturns')
def setturns():
    global turns
    turns = float(request.forms.get('turns') or 0)
    redirect('/')

@post('/sethome')
def sethome():
    if (odrv_ready):
        global home
        home = abs(current_position()) % ppr
    redirect('/')

@post('/anticog')
def anticog():
    if (odrv_ready):
        calibrate_anticogging()
    redirect('/')

@get('/getpos')
def getpos():
    if (odrv_ready):
        return str(current_position())
    else:
        return 0

run(host='0.0.0.0', port=80, debug=True)
