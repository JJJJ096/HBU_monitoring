'''
Pyrometer 통신 및 데이터 수집 코드
Copyleft ⓒ Seonghun_ji
last update: 2024.09.03
Requirement package (pyserial)
'''
import configparser as conf
import time
from collections import deque
import serial
import threading


class Pyrometer_Communication:
    def __init__(self, config_path="./Monitoring/Sensors/ini_files/Pyrometer.ini") :
        
        '''Inintializes the sensor and communication'''
        self.config = conf.ConfigParser()
        self.config.read(config_path)
        
        self.adress = {key: value for key, value in self.config.items('adress')}
        self.data = {key: value for key, value in self.config.items('data')}
        print(f"adress:{self.adress}\ndata:{self.data}")
        self.open()

    def open(self):
        self.serial = serial.Serial(
                    port=self.adress['port'],
                    baudrate=int(self.adress['baudrate']),
                    parity=self.adress['parity'],
                    stopbits=int(self.adress['stopbits']),
                    bytesize=int(self.adress['bytesize']),
                    timeout=int(self.adress['timeout']))

        if self.serial.is_open:
            print(f"Serial port {self.adress['port']} opened successfully.")

            self.serial.write("00bum01\r".encode('ascii'))  # 필요한 인코딩 방식으로 수정 가능
            initial_response = self.serial.read_until(b'\r').decode('utf-8').strip()
            
            # 응답이 'ok'인지 확인
            if initial_response == 'ok':
                self.activate = True
                print("Connected to pyrometer.")
            else:
                self.activate = False
                print(f"Unexpected response: {initial_response}")

    def get_data(self):
        if self.activate:
            self.serial.write("00bup\r".encode())
            response = self.serial.read_until(b'\r').decode("utf-8").strip()
            
            if len(response) == 12:                             #(2컬러, 채널 1, 채널 2 온도)
                self.data['mpt'] = int(response[0:4], 16) / 10      # 2컬러 온도 (AAAA)
                self.data['1ct'] = int(response[4:8], 16) / 10      # 채널 1 온도 (BBBB)
                self.data['2ct']= int(response[8:12], 16) / 10      # 채널 2 온도 (CCCC)
            else:
                pass

        return self.data
    
    def close(self):
        self.activate = False
    
class Pyrometer_DB:
    def __init__(self, max_size=100) -> None:
        self.data_queue = deque(maxlen=max_size)
    
    def store_data(self, data):
        self.data_queue.append(data)

    def retrieve_data(self):
        if self.data_queue:
            return self.data_queue[-1]
        return print("Test Data queue is empty")

class Pyrometer_Collector(threading.Thread):
    def __init__(self, com, db):
        threading.Thread.__init__(self)
        self.com = com
        self.db = db
        self.running = True
        self.sample_rate = 100


    def run(self):
        while self.running:
            loop_start = time.perf_counter()
            if self.com.activate:
                data = self.com.get_data()
                if data:
                    self.db.store_data(data)
            else:
                time.sleep(0.5)
                #print("error_test")
            sleep_time = max(0, (1/self.sample_rate)-(time.perf_counter()-loop_start))
            time.sleep(sleep_time)
        time.sleep(0.1)
    
    def stop(self):
        self.running = False

if __name__ == "__main__":
    
    com = Pyrometer_Communication()
    db = Pyrometer_DB()
    collector = Pyrometer_Collector(com, db)
    collector.start()

    try:
        while True:
            if db.data_queue:
                data = db.retrieve_data()
                print(data)
            
            time.sleep(1)
    except:
        print('Error')

