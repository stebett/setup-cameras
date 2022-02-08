import time
from zaber_motion import Library
from zaber_motion.ascii import Connection
from zaber_motion import Units

class Zaber:
    def __init__(self):
        self.init_zaber()
        self.trial = 0

    def init_zaber(self):
        Library.enable_device_db_store()
        self.below_all = [ 10, 20, 30, 40 ]
        self.above_all = [ 10, 20, 30, 40 ]


        connection = Connection.open_serial_port("/dev/ttyUSB0") 
        device_list = connection.detect_devices()
        print("Found {} devices".format(len(device_list)))

        device_below = device_list.pop(0) if device_list[0].serial_number == 84178 else device_list.pop(1)
        device_above = device_list[0]

        self.axis_below = device_below.get_axis(1)
        self.axis_above = device_above.get_axis(1)

        self.axis_below.home(wait_until_idle=False)
        self.axis_above.home(wait_until_idle=True)

        self.zaber_index = 0

    def zaber_move(self, pos_below, pos_above):
        self.axis_below.move_absolute(pos_below, Units.LENGTH_MILLIMETRES, wait_until_idle=True)
        self.axis_above.move_absolute(pos_above, Units.LENGTH_MILLIMETRES, wait_until_idle=True)

        print(f"Position of axis below: {self.axis_below.get_position(Units.LENGTH_MILLIMETRES)}mm")
        print(f"Position of axis above: {self.axis_above.get_position(Units.LENGTH_MILLIMETRES)}mm")

    def zaber_move_next(self):
        print(f"Index: {self.zaber_index}")
        self.zaber_move(self.below_all[self.zaber_index], self.above_all[self.zaber_index])
        self.zaber_index += 1
        if self.zaber_index >= len(self.below_all):
            print("Resetting index")
            self.zaber_index = 0
                

    def cycle(self):
        self.trial += 1
        print(f"Starting trial {self.trial}")
        self.zaber_move_next()
        time.sleep(2)


if __name__ == "__main__":
    zaber = Zaber()

    while True:
        zaber.cycle()

