'''
    File name: PCM.py
    Author: Roel Postelmans
    Date created: 2017
'''
from datetime import datetime
import re

from ..PCM import PCM


class I2S(PCM):
    '''
        I2S data parser for the saleae logic analyzer
    '''
    TIME_LOC = None
    VALUE_LOC = None
    CHANNEL_LOC = None
    FIRST_D = 1

    def __init__(self, csv_file, delimiter=','):
        '''
            Saleae I2S export parser initiator
        '''
        super(I2S, self).__init__(csv_file, self.FIRST_D)

        self.delimiter = delimiter
        self._calc_columns()

        self.start_time = self._convert_time_to_seconds(self.start_time)
        self.end_time = self._convert_time_to_seconds(self.end_time)

    def _convert_time_to_seconds(self, line: str) -> int:
        val = self.extract_value(line, self.TIME_LOC).replace('Z', '+00:00')
        try:
            # New ISO time format

            # extract nanoseconds, because python unable to process it.
            matched = re.match(r".*:\d\d(.\d\d\d\d\d\d\d\d\d)[+-]", val)
            nanosec = matched.group(1)
            val = val.replace(nanosec, "")
            return datetime.strptime(val, '%Y-%m-%dT%H:%M:%S%z').timestamp() + float(nanosec)
        except Exception:
            # Back compatibilty. float number with second resolution
            return float(val)

    def _calc_columns(self):
        vals = self.title.split(self.delimiter)
        try:
            self.TIME_LOC = vals.index("start_time")
        except:
            try:
                self.TIME_LOC = vals.index("Time [s]")
            except:
                print("start_time column is not founc in CSV. Please set 'Use ISO8601 timestamps' during export")
                raise Exception("Column 'start_time' or 'Time [s]' not found")

        try:
            self.VALUE_LOC = vals.index("data")
        except:
            try:
                self.VALUE_LOC = vals.index("Value")
            except:
                raise Exception("Column 'data' or 'Value' not found")

        try:
            self.CHANNEL_LOC = vals.index("channel")
        except:
            try:
                self.CHANNEL_LOC = vals.index("Channel")
            except:
                raise Exception("Column 'channel' not found")

    def extract_value(self, line, key):
        '''
            Extract a value from a string by a given position
        '''
        line = line.split(self.delimiter)
        line = line[key].rstrip()
        return line

    def determine_sample_rate(self):
        '''
            Calculate the sample rate based on the
            timestamps
        '''
        super(I2S, self).determine_sample_rate()
        # 2 samples per period
        self.sample_rate /= 2
        super(I2S, self).reset()
        return int(self.sample_rate)

    def pop_data(self):
        '''
            Extract the values from one line of data
        '''
        super(I2S, self).pop_data()
        # Skip header
        if self.sample_count <= self.FIRST_D:
            return self.pop_data()

        value = self.extract_value(self.line, self.VALUE_LOC)
        channel = self.extract_value(self.line, self.CHANNEL_LOC)

        if self.sample_count <= self.FIRST_D + 1:
            if int(channel, 0) != 1:
                return self.pop_data()

        return channel, value

    def close(self):
        '''
            Close the export file
        '''
        self.sample_count -= self.FIRST_D
        super(I2S, self).close()
