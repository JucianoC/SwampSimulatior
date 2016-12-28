from interface import Interface
from control import Control

if __name__ == '__main__':


    ctl = Control(100, 10, 99, 1000)
    gui = Interface()

    ctl.set_interface(gui)
    gui.set_control(ctl)

    gui.start()
