import serial
import os

# The final version of this program is running on the raspberry pi and is backed up on google drive


class DataPacket:
    varNames = ['systemStartTime',
                'currentSystemTime',
                'rollRadians',
                'pitchRadians',
                'yawRadians',
                'longitude',
                'latitude',
                'heading',
                'speed',
                'satellites',
                'throttleValue',
                'rudderValue',
                'aileronValue',
                'elevatorValue']

    def __init__(self):
        self.dataDictionary = {DataPacket.varNames[0]: '',
                               DataPacket.varNames[1]: '',
                               DataPacket.varNames[2]: '',
                               DataPacket.varNames[3]: '',
                               DataPacket.varNames[4]: '',
                               DataPacket.varNames[5]: '',
                               DataPacket.varNames[6]: '',
                               DataPacket.varNames[7]: '',
                               DataPacket.varNames[8]: '',
                               DataPacket.varNames[9]: '',
                               DataPacket.varNames[10]: '',
                               DataPacket.varNames[11]: '',
                               DataPacket.varNames[12]: '',
                               DataPacket.varNames[13]: ''}

    def update_packet(self, data_list):
        if len(data_list) != len(DataPacket.varNames):
            return
        else:
            for num in range(0, len(DataPacket.varNames)):
                self.dataDictionary[DataPacket.varNames[num]] = data_list[num]

    def get_formatted_data_line(self, data_line):
        return DataPacket.varNames[data_line] + ': ' + self.dataDictionary.get(DataPacket.varNames[data_line]) + '\n'

    def __str__(self):
        string_to_return = ''
        for num in range(0, len(DataPacket.varNames)):
            string_to_return += self.get_formatted_data_line(num)
        return string_to_return


class SerialParser:
    DATA_START = '|S|'
    DATA_SEPARATOR = '|'
    DATA_END = '|E|'
    DATA_MODE = 'd'
    TEXT_FILE_MODE = 't'

    def __init__(self, serial_port, baud_rate):
        self.ser = serial.Serial(serial_port, baud_rate)
        self.ser.baudrate = baud_rate

    def parse_new_data(self):
        bits_to_parse = self.ser.readline()
        string_to_parse = ''
        try:
            string_to_parse = bits_to_parse.decode('utf-8', 'backslashreplace')
        except:
            print('There was an exception encountered while decoding the incoming bit stream')
        index = string_to_parse.find(SerialParser.DATA_START) + len(SerialParser.DATA_START) - 1
        string_to_parse = string_to_parse[index: len(string_to_parse)]

        iterations = 0
        data_list = []
        is_not_end_line = True
        while is_not_end_line:
            if string_to_parse[0: len(SerialParser.DATA_END)] == SerialParser.DATA_END:
                is_not_end_line = False
            else:
                string_to_parse = string_to_parse[1: len(string_to_parse)]
                end = string_to_parse.find(SerialParser.DATA_SEPARATOR)
                data = string_to_parse[0: end]
                string_to_parse = string_to_parse[len(data): len(string_to_parse)]
                data_list.append(data)
                iterations += 1
            if iterations > 20:
                print('Infinite iteration through received packet')
                return None
        return data_list

    def parse_new_data_raw(self):
        bits_to_parse = self.ser.readline()
        try:
            raw_string = bits_to_parse.decode('utf-8', 'backslashreplace')
        except:
            print('There was an exception encountered while decoding the incoming bit stream')
            return ''
        return raw_string

    def get_system_boolean(self):
        while True:
            bits_to_parse = self.ser.readline()
            raw_string = ''

            try:
                raw_string = bits_to_parse.decode('utf-8', 'backslashreplace')
            except:
                print("There was a exception encountered in decoding the incoming bit stream")

            if raw_string[0] == SerialParser.DATA_MODE:
                print('The program will not write to a text file in this cycle')
                return False
            elif raw_string[0] == SerialParser.TEXT_FILE_MODE:
                print('The program will write to a text file in this cycle')
                return True


# Global variables necessary for program operation
BAUD_RATE = 128000
TXT_FILE = '/home/pi/Desktop/FlightPacketHistory.txt'
DEBUG_PRINT = True


def check_max_size():
    raw_size = os.popen('du -h' + TXT_FILE).read()
    index_m = raw_size.find('M')
    if index_m == 1:
        return True
    else:
        size = int(raw_size[0: 1])
        if size >= 8:
            return False
        else:
            return True


# Setup code, gathering run type and opening necessary ports
port = os.popen("ls /dev/ttyACM*").read()
parser = SerialParser(str(port)[0:12], BAUD_RATE)
WRITE_TO_TEXT = parser.get_system_boolean()
packet = DataPacket()

continue_run = True
if WRITE_TO_TEXT:
    file = open(TXT_FILE, 'w')
    while continue_run:
        file.write(parser.parse_new_data_raw())
        continue_run = check_max_size()
else:
    print('Starting Xbee Communications')
    xbee_serial = serial.Serial('/dev/serial0')
    xbee_serial.baudrate = 115200
    while True:
        raw_str = parser.parse_new_data_raw()
        if raw_str is not None:
            xbee_serial.write(raw_str.encode())
            if DEBUG_PRINT:
                print(raw_str)
