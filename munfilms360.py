from bottle import *
from functools import reduce
import os
import serial


# MOTOR INTERFACE

class Motor:
    rpm = 8.5
    turns = 1
    serialPort = serial.Serial('/dev/ttyACM0')

    def __init__(self):
        self.serialPort.baudrate = 56000
        self.reconnect()

    def reconnect(self):
        if (self.serialPort.is_open):
            self.serialPort.close()
        self.serialPort.open()

    def send_command(self, command, param):
        self.serialPort.write(
            (command + (str(param) if param else '')).encode('utf-8'))

    def set_turns(self, turns):
        self.turns = turns

    def get_turns(self):
        return self.turns

    def set_rpm(self, rpm):
        self.rpm = rpm
        self.send_command('rpm', rpm)

    def get_rpm(self):
        return self.rpm

    def set_home(self):
        self.send_command('fix', False)

    def go_home(self):
        self.send_command('hom', False)

    def turn(self):
        self.send_command('rev', self.turns)

    def turn_degrees(self, degrees):
        self.send_command('deg', degrees)

# DEFINITIONS

cwd = os.path.dirname(os.path.realpath(__file__))
motor = Motor()

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
            h1('Loopers 360') +
            homepage() +
            img('', src = 'static/gif-web-alpha2.gif', klass = 'logo'),
            klass = 'wrapper'
        )
    )

def homepage():
    return (
        div(
            a('home', img('', src = 'static/home.png')) +
            a('turn', img('', src = 'static/turn.png')) +
            a('stop', img('', src = 'static/stop.png')),
            klass = 'controls') +
        h3('Configuració') +
        div(
            form(
                'setspeed',
                span('Velocitat (RPM):', klass = 'label') +
                input('', name = 'speed', klass = 'input') +
                span('(' + str(motor.get_rpm()) + ')', klass = 'value') +
                button('OK')) +
            form(
                'setturns',
                span('Voltes:', klass = 'label') +
                input('', name = 'turns', klass = 'input') +
                span('(' + str(motor.get_turns()) + ')', klass = 'value') +
                button('OK')) +
            form('sethome', button('Fixar posició inicial')),
            klass = 'config'
        )
    )

@route('/home')
def gohome():
    motor.go_home()
    redirect('/')

@route('/turn')
def turn():
    motor.turn()
    redirect('/')

@route('/stop')
def stop():
    motor.reconnect()
    redirect('/')

@post('/setspeed')
def setspeed():
    motor.set_rpm(min(float(request.forms.get('speed') or 1), 100))
    redirect('/')

@post('/setturns')
def setturns():
    motor.set_turns(float(request.forms.get('turns') or 1))
    redirect('/')

@post('/sethome')
def sethome():
    motor.set_home()
    redirect('/')

run(host='0.0.0.0', port=80, debug=True)

