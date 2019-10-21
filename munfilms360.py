import odrive
from odrive.enums import *
from bottle import *
from functools import reduce
import time

# DEFINITIONS

ppr = 8192
turns = 1
rpms = 10

# MOTOR INITIALIZATION

print('Looking for an ODrive...')
odrv0 = odrive.find_any()

print('Calibrating ODrive...')
odrv0.axis0.requested_state = AXIS_STATE_FULL_CALIBRATION_SEQUENCE
while odrv0.axis0.current_state != AXIS_STATE_IDLE:
    time.sleep(0.1)

print('ODrive calibrated. Setting state to Close Loop Control');
odrv0.axis0.requested_state = AXIS_STATE_CLOSED_LOOP_CONTROL

# MOTOR CONTROL

def set_position(position):
    odrv0.axis0.controller.config.control_mode = CTRL_MODE_POSITION_CONTROL
    odrv0.axis0.controller.pos_setpoint = position    

def current_position():
    return odrv0.axis0.encoder.pos_estimate

def closest_home():
    return (current_position() // ppr) * ppr

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
    return static_file(filename, root='static')

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
                a('turn', img('', src = 'static/turn.png')),
                klass = 'controls'
            ) +
            h3('Configuració') +
            div(
                form(
                    'setspeed',
                    span('Velocitat (RPM):', klass = 'label') +
                        input('', name = 'speed') + 
                        span('(' + str(rpms) + ')', klass = 'value') +
                        button('OK')) +
                form(
                    'setturns',
                    span('Voltes:', klass = 'label') +
                        input('', name = 'turns') +
                        span('(' + str(turns) + ')', klass = 'value') +
                        button('OK')) +
                p('', klass = 'position') + pos_updater_script(),
                klass = 'config') +
            img('', src = 'static/gif-web-alpha2.gif', klass = 'logo'),
            klass = 'wrapper'
        )
    )

@route('/home')
def gohome():
    set_position(closest_home())
    redirect('/')

@route('/turn')
def turn():
    set_position(current_position() + (ppr * turns))
    redirect('/')

@post('/setturns')
def setturns():
    global turns
    turns = float(request.forms.get('turns'))
    redirect('/')

@post('/setpos')
def setpos():
    set_position(request.forms.get('position'))
    redirect('/')

@get('/getpos')
def getpos():
    return str(current_position())

run(host='0.0.0.0', port=8080, debug=True)
