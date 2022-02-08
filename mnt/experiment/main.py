import time
import argparse
from pathlib import Path
from subprocess import check_output
from helpers import get_logger, parse_config_path, read_config
from zaber_motion import Library
from zaber_motion.ascii import Connection
from zaber_motion import Units
import RPi.GPIO as GPIO

class Experiment:
    def __init__(self, configs, nohome):
        self.configs = configs
        self.logger = self.get_logger() 
        self.init_gpio()
        self.actuator = Zaber(self.configs, self.logger, nohome)
        self.trial = 0

    def cycle(self):
        self.trial += 1
        self.logger.info(f"Starting trial {self.trial}")
        schedule = self.configs["experiment"]["schedule"].copy()
        for method, t in schedule.items():
            self.logger.debug(f"Method {method} scheduled at {t}")

        start = time.time()
        while len(schedule) > 0:
            executed_methods = []
            for method, t in schedule.items():
                time_elapsed = time.time() - start
                if t < time_elapsed:
                    self.logger.debug(f"Running method {method} after {time_elapsed}s")
                    getattr(self, method)()
                    executed_methods.append(method)

            for method in executed_methods:
                schedule.pop(method)

            time.sleep(0.1)

    def move_actuator(self):
        self.logger.info("Starting actuator")
        self.actuator.move_next()
        self.logger.info("Actuator moved")

    def cue_on(self):
        self.logger.info(f"Setting pin {self.cue_pin} (blink) to high")
        GPIO.output(self.cue_pin, True)

    def cue_off(self):
        self.logger.info(f"Setting pin {self.cue_pin} (blink) to low")
        GPIO.output(self.cue_pin, False)

    def pump(self):
        self.logger.info(f"Setting pin {self.pump_pin} (pump in) to high")
        GPIO.output(self.pump_pin, True)
        time.sleep(0.1)
        self.logger.info(f"Setting pin {self.pump_pin} (pump in) to low")
        GPIO.output(self.pump_pin, False)
        time.sleep(0.1)
        GPIO.output(self.pump_pin, True)
        time.sleep(0.1)
        self.logger.info(f"Setting pin {self.pump_pin} (pump in) to low")
        GPIO.output(self.pump_pin, False)

    def pump2(self):
        self.logger.info(f"Setting pin {self.pump_pin} (pump in) to high")
        GPIO.output(self.pump_pin, True)
        time.sleep(0.1)
        self.logger.info(f"Setting pin {self.pump_pin} (pump in) to low")
        GPIO.output(self.pump_pin, False)

    def pwm_on(self):
        self.logger.info(f"Setting pin {self.pwm_pin} (pwm_on) to high")
        GPIO.output(self.pwm_pin, True)

    def pwm_off(self):
        self.logger.info(f"Setting pin {self.pwm_pin} (pwm_on) to low")
        GPIO.output(self.pwm_pin, False)
            

    def get_logger(self):
        file_name = 'experiment.log'
        stream_level = self.configs["experiment"]["logging"]["stream_level"]
        file_level = self.configs["experiment"]["logging"]["file_level"]
        logger = get_logger("main", stream_level, file_level, file_name)
        logger.info(f"Log path:  {file_name}")
        logger.info(f"Log level: {file_level}")
        return logger

    def init_gpio(self):
        self.logger.debug("Initializing gpio")
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        self.cue_pin = int(self.configs["experiment"]["pins"]["cue"])
        GPIO.setup(self.cue_pin, GPIO.OUT)
        GPIO.output(self.cue_pin, False)

        self.pump_pin = int(self.configs["experiment"]["pins"]["pump"])
        GPIO.setup(self.pump_pin, GPIO.OUT)
        GPIO.output(self.pump_pin, False)


        self.pwm_pin = int(self.configs["experiment"]["pins"]["pwm"])
        GPIO.setup(self.pwm_pin, GPIO.OUT)
        GPIO.output(self.pwm_pin, False)


class Zaber:
    def __init__(self, configs, logger, nohome):
        self.logger = logger
        self.configs = configs
        self.nohome = nohome

        self.logger.debug("Initializing zaber")
        Library.enable_device_db_store()
        self.below_all = self.configs["actuator"]["below"]
        self.above_all = self.configs["actuator"]["above"]

        connection = Connection.open_serial_port("/dev/ttyUSB0") 
        device_list = connection.detect_devices()
        self.logger.info("Found {} devices".format(len(device_list)))

        device_below = device_list.pop(0) if device_list[0].serial_number == 84178 else device_list.pop(1)
        device_above = device_list[0]

        self.axis_below = device_below.get_axis(1)
        self.axis_above = device_above.get_axis(1)

        if nohome:
            self.logger.debug("Not moving axis to home position")
        else:
            self.logger.debug("Moving axis below to home position")
            self.axis_below.home(wait_until_idle=False)
            self.logger.debug("Moving axis above to home position")
            self.axis_above.home(wait_until_idle=True)
        self.index = 0

    def move(self, pos_below, pos_above):
            self.logger.debug(f"Moving axis below to {pos_below}mm")
            self.axis_below.move_absolute(pos_below, Units.LENGTH_MILLIMETRES, wait_until_idle=False)
            self.logger.debug(f"Moving axis above to {pos_below}mm")
            self.axis_above.move_absolute(pos_above, Units.LENGTH_MILLIMETRES, wait_until_idle=True)
            self.logger.info(f"Position of axis below: {self.axis_below.get_position(Units.LENGTH_MILLIMETRES)}mm")
            self.logger.info(f"Position of axis above: {self.axis_above.get_position(Units.LENGTH_MILLIMETRES)}mm")

    def move_next(self):
        self.logger.debug(f"Index: {self.index}")
        self.move(self.below_all[self.index], self.above_all[self.index])
        self.index += 1
        if self.index >= len(self.below_all):
            self.logger.info("Resetting index")
            self.index = 0
                



if __name__ == "__main__":
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("-c", "--config-path",
            help="Config path",
            dest="config_path", default="configs.toml", type=lambda x: Path(x).expanduser().absolute())
    parser.add_argument("-nh", "--no-home",
            help="Zaber doesn't return to home position",
            dest="nohome", action="store_true")

    args = parser.parse_args()
    config_path = args.config_path
    nohome = args.nohome
    configs = read_config(config_path)
    experiment = Experiment(configs, nohome)

    input("Press enter to start\n")
    while True:
        experiment.cycle()

