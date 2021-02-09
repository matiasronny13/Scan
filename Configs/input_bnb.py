import AppConstants
from Exchanges.Bnb import Bnb
from Configs.input_base import InputBase


class InputBNB(InputBase):

    def __init__(self):
        InputBase.__init__(self)
        self.Exchange = Bnb()
        self.TickLimit = 300
