import AppConstants
from Exchanges.Idx import Idx
from Configs.input_base import InputBase


class InputIDX(InputBase):

    def __init__(self):
        InputBase.__init__(self)
        self.TickLimit = 200
        self.Exchange = Idx()

