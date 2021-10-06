from paramiko import SSHClient, ssh_exception, AutoAddPolicy
from multiprocessing import Process
import keyboard
import time
import webbrowser
import signal


def setup_output(pin,opt):
    return "gpio -g mode " + str(pin) + " " + opt

def setup_pin_state(pin,option):
    return "gpio -g write " + str(pin) + " " + option 

def setup_pwm_state(pin,pwm):
    return "gpio -g pwm " + str(pin) + " " + str(pwm)

class motor():
    def __init__(self,enable,in_1,in_2):
        self.enable = enable
        self.in_1 = in_1
        self.in_2 = in_2
        self.pin_list = [enable,in_1,in_2]

class Racecar():
    username = "pi"
    password = "gatorade5"
    def __init__(self,ip,steer_motor,drive_motor):
        self.ip = ip
        self.stream_url = url = "http://" + ip + ":8080/stream.html"
        self.ssh_connect()
        print("Connection achieved")
        self.steer_motor = self.init_motor(steer_motor)
        self.drive_motor = self.init_motor(drive_motor)
    
    def ssh_connect(self):
        self.client = SSHClient()
        self.client.set_missing_host_key_policy(AutoAddPolicy())
        try:
            self.client.connect(self.ip,username = self.username, password = self.password)
        except ssh_exception.NoValidConnectionsError:
            print("Error Connecting")
            exit()
            return
    
    def exec_command(self,cmd):
        return self.client.exec_command(cmd)


    def init_motor(self,motor):
        for i in range(0,len(motor.pin_list)):
            if i == 0:
                self.exec_command(setup_output(motor.pin_list[i],"pwm"))
            else:
                self.exec_command(setup_output(motor.pin_list[i],"out"))
                self.exec_command(setup_pin_state(motor.pin_list[i],"0"))
        return motor
    
    def activate(self,direction):
        if direction == "forward":
            self.exec_command(setup_pwm_state(self.drive_motor.enable,"600"))
            self.exec_command(setup_pin_state(self.drive_motor.in_1,"1"))
            self.exec_command(setup_pin_state(self.drive_motor.in_2,"0"))
        if direction == "reverse":
            self.exec_command(setup_pwm_state(self.drive_motor.enable,"00"))
            self.exec_command(setup_pin_state(self.drive_motor.in_1,"0"))
            self.exec_command(setup_pin_state(self.drive_motor.in_2,"1"))
        if direction == "right":
            self.exec_command(setup_pwm_state(self.steer_motor.enable,"1023"))
            self.exec_command(setup_pin_state(self.steer_motor.in_1,"1"))
            self.exec_command(setup_pin_state(self.steer_motor.in_2,"0"))
        if direction == "left":
            self.exec_command(setup_pwm_state(self.steer_motor.enable,"1023"))
            self.exec_command(setup_pin_state(self.steer_motor.in_1,"0"))
            self.exec_command(setup_pin_state(self.steer_motor.in_2,"1"))

    def stop(self,motor):
        self.exec_command(setup_pwm_state(motor.enable,"0"))
        self.exec_command(setup_pin_state(motor.in_1,"0"))
        self.exec_command(setup_pin_state(motor.in_2,"0"))

drive = motor(18,23,24)
steer = motor(13,26,19)
racecar = Racecar("192.168.137.31",drive,steer)


def start_stream(): #starts the mjpg stream
    kill_Stream()
    stdin, stdout, stderr = racecar.exec_command('''cd Desktop/mjpg-streamer-experimental; ./mjpg_streamer -o "output_http.so -w ./www" -i "input_raspicam.so -hf"''')
    if(len(stderr.read()) > 0):
        print(stderr.read())
        return
    webbrowser.open(racecar.stream_url)
    stdin.close()

def kill_Stream(): #gets the PID of mjpg stream and kills it
    stdin, stdout, stderr = racecar.exec_command('pidof mjpg_streamer')
    kill_pid = "kill " + (stdout.read().decode('ascii'))
    stdin, stdout, stderr = racecar.exec_command(kill_pid)
    stdin.close()

def control_steer():
    try:
        while True:
            if keyboard.is_pressed('a'):
                racecar.activate("right")
                while keyboard.is_pressed('a'):
                    time.sleep(.1)
                racecar.stop(racecar.steer_motor)

            if keyboard.is_pressed('d'):
                racecar.activate("left")
                while keyboard.is_pressed('d'):
                    time.sleep(.1)
                racecar.stop(racecar.steer_motor)
    except KeyboardInterrupt:
        racecar.stop(racecar.steer_motor)
        kill_Stream()
        exit()

def control_motor():
    try:
        while True:
            if keyboard.is_pressed('w'):
                racecar.activate("forward")
                pwm = 600
                while keyboard.is_pressed('w'):
                    if pwm < 1000:
                        racecar.exec_command(setup_pwm_state(racecar.drive_motor.enable,str(pwm)))
                        pwm += 1
                racecar.stop(racecar.drive_motor)

            if keyboard.is_pressed('s'):
                racecar.activate("reverse")
                pwm = 600
                while keyboard.is_pressed('s'):
                    if pwm < 1000:
                        racecar.exec_command(setup_pwm_state(racecar.drive_motor.enable,str(pwm)))
                        pwm += 5
                racecar.stop(racecar.drive_motor)
    except KeyboardInterrupt:
        racecar.stop(racecar.drive_motor)
        kill_Stream()
        exit()

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    start_stream()
    procs = [Process(target=control_motor), Process(target=control_steer)]
    for proc in procs:
        proc.start()