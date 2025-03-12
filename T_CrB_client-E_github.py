


import os
import sys
import schedule
import time
import keyboard
import warnings
import socket
import threading
import glob
from datetime import datetime
from astropy.io import fits
import numpy as np
import astroalign as aa
import sep
import argparse
import configparser

warnings.filterwarnings('ignore')



class TcpClient:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.client = None
        self.linked = False

    def connect(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client.connect((self.ip, self.port))
            self.linked = True
            print('Server Online')
            #self.disconnect()
        except Exception as e:
            print(f'connection failure: {str(e)}')

    def disconnect(self):
        if self.client:
            self.client.close()
            self.linked = False
            print('Connection closed')

    def send_data(self, data):
        self.connect()
        if self.linked:
            try:
                if data:
                    self.client.send(data.encode('utf-8'))
                    print(f'Data sent: {data}')
            except Exception as e:
                print(f'Failed to send: {str(e)}')
            finally:
                self.disconnect()


def find_closest_date_directory_and_files(current_directory):
    def is_new_file(file_path):
        file_mtime = os.path.getmtime(file_path)
        current_time = time.time()
        return current_time - file_mtime > 30

    # 找到所有符合两种日期格式的目录
    date_directories = [d for d in glob.glob(os.path.join(current_directory, '20??????')) if
                        os.path.isdir(d) and len(os.path.basename(d)) == 8]
    date_directories += [d for d in glob.glob(os.path.join(current_directory, '20??-??-??')) if
                         os.path.isdir(d) and len(os.path.basename(d)) == 10]

    today = datetime.now()
    closest_dir = None
    min_diff = float('inf')

    for dir_path in date_directories:
        try:
            dir_name = os.path.basename(dir_path)
            if len(dir_name) == 8:  # 格式为20??????
                dir_date = datetime.strptime(dir_name, '%Y%m%d')
            elif len(dir_name) == 10:  # 格式为20??-??-??
                dir_date = datetime.strptime(dir_name, '%Y-%m-%d')
            else:
                continue

            date_diff = abs((dir_date - today).total_seconds())
            if date_diff < min_diff:
                min_diff = date_diff
                closest_dir = dir_path
        except ValueError:
            continue

    print(f'The catalog for the most recent date is: {closest_dir}')
    file_list = []
    if closest_dir:
        pattern = os.path.join(closest_dir, 'T_CrB*.f*')
        file_list = glob.glob(pattern)

    for i in range(len(file_list)):
        file_list[i] = file_list[i].replace("\\", "/")

    new_files = [file for file in file_list if is_new_file(file)]

    if new_files:
        set1 = set(old_files)
        set2 = set(new_files)
        unique_files = set2 - set1
        unique_files_list = list(unique_files)
        old_files.extend(unique_files_list)

        with open(f'{datetime.now().strftime("%Y%m%d")}processed_file.txt', 'a') as file:
            for item in unique_files_list:
                file.write(item + '\n')

        return os.path.basename(closest_dir) if closest_dir else None, unique_files_list
    else:
        return os.path.basename(closest_dir) if closest_dir else None, []


def photometry(newfile_data, newfile_hdr, order, fwhm, threshold):
    print(f'Beginning photometry')
    data = np.array(newfile_data, dtype=np.float32)
    hdr = newfile_hdr

    captime = hdr['DATE-OBS']
    filter = hdr.get('FILTER', 'Unfilter')

    bkg = sep.Background(data)
    data_sub = data - bkg
    objects = sep.extract(data_sub, threshold, err=bkg.globalrms)

    print(f'Found {len(objects)} stars')
    flux, fluxerr, flag = sep.sum_circle(data_sub, objects['x'], objects['y'], 3. * fwhm, err=bkg.globalrms,
                                         gain=1.0)

    # 根据键名获取对应的目标列表
    if order in target_coords_dict:
        print(f"Coordinates for {order}: {target_coords_dict[order]}")
        target_coords = target_coords_dict[order]
    else:
        print(f"No coordinates found for {order}")
        return

    # 得到感兴趣目标的测光列表
    targets_data = []

    for objname, x_target, y_target in target_coords:
        distances = np.sqrt((objects['x'] - x_target) ** 2 + (objects['y'] - y_target) ** 2)
        within_radius = distances <= 5
        if any(within_radius):
            index = np.argmin(distances[within_radius])
            idx_in_objects = np.where(within_radius)[0][index]
            target_info = {
                'captime': captime,
                'filter': filter,
                'objname': objname,
                'mag': -2.5 * np.log10(flux[idx_in_objects]),
            }
            targets_data.append(target_info)
        else:
            targets_data.append(
                {'captime': captime, 'filter': filter, 'objname': objname, 'mag': np.nan})

    print('Astronomical photometry of stars is:')
    for target in targets_data:
        print(target)

    return targets_data


def send_to_server(targets_list):
    client = TcpClient('xxx.xxx.xxx.xxx', xxxx)

    formatted_string = '+'.join(
        'captime,' + item['captime'] + ',filter,' + item['filter'] + ',objname,' + item['objname'] + ',mag,' + str(
            item['mag'])
        for item in targets_list
    )
    #print(formatted_string)

    say = station+"=" + formatted_string
    client.send_data(say)
    time.sleep(2)


def process_light_files(lightfnlst):
    if len(lightfnlst) == 0:
        print(f'No new images to process')
        return

    print(f'Images are being processed in real time...\nThe total number of scientific images to be processed is {len(lightfnlst)}')

    ny, nx = fits.getval(lightfnlst[0], 'NAXIS2'), fits.getval(lightfnlst[0], 'NAXIS1')
    print(f'image size={nx}*{ny}')

    for i in range(len(lightfnlst)):
        print("")
        print(f'Processing image {i + 1}=> {lightfnlst[i]}, The total number of scientific images to be processed is {len(lightfnlst)}')

        data = fits.getdata(lightfnlst[i])
        hdr = fits.getheader(lightfnlst[i])
        fnfilter = hdr.get('FILTER', 'Unfilter')

        try:
            print('Starting the first try')
            if fnfilter in filters:
                aa_order = f'{fnfilter}1'
                template1_data = fits.getdata(f'{current_directory}\\template\\{fnfilter}_template1.fits')
            else:
                raise ValueError(f"Unknown filter type: {fnfilter}")

            aa_img, footprint = aa.register(data, template1_data)
            targets_list = photometry(aa_img, hdr, aa_order, fwhm=3, threshold=1.5)  # 原本threshold=3
        except aa.MaxIterError:
            try:
                print('        Starting the second try')

                max_control_points = 100
                detection_sigma = 2
                min_area = 5

                if fnfilter in filters:
                    aa_order = f'{fnfilter}2'
                    template2_data = fits.getdata(f'{current_directory}\\template\\{fnfilter}_template2.fits')
                else:
                    raise ValueError(f"Unknown filter type: {fnfilter}")

                aa_img, footprint = aa.register(data, template2_data, max_control_points=max_control_points,
                                                detection_sigma=detection_sigma, min_area=min_area)
                targets_list = photometry(aa_img, hdr, aa_order, fwhm=3, threshold=3)  # 原本threshold=5
            except aa.MaxIterError:
                print('Aligning twice gives an error, skip this file')
                continue
            except ValueError as ve:
                print(f'Insufficient star points to complete alignment, error message:{ve}')
                continue
        except ValueError as ve:
            print(f'Insufficient star points to complete alignment, error message:{ve}')
            continue

        send_to_server(targets_list)


def stop_program(e):
    global running
    print("Program stops running")
    running = False
    sys.exit(1)


keyboard.on_press_key('F4', stop_program)


def run_jobs():
    print('~~~~~~~~~~~~~~~~~~~~~~~')
    print("Running tasks... Task start time: ", time.strftime("%Y-%m-%d %H:%M:%S"))

    closest_directory, file_list = find_closest_date_directory_and_files(current_directory)

    print("List of files.")
    for file in file_list:
        print(f'{file}\\n')

    process_light_files(file_list)

    print("ok~Time for this task to be completed: ", time.strftime("%Y-%m-%d %H:%M:%S"))

    lock.release()


def run_jobs_thread():
    if lock.acquire(blocking=False):
        job_thread = threading.Thread(target=run_jobs)
        job_thread.start()


def run_schedule():
    schedule.every(30).seconds.do(run_jobs_thread)
    while running:
        schedule.run_pending()
        time.sleep(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="T CrB Monitor Client")
    parser.add_argument('--dir', type=str, required=True, help='Monitoring paths to directories')
    args = parser.parse_args()

    current_directory = args.dir  # 获得当前程序所在目录路径

    print("The directory where the execution file is located is: ", current_directory)
    print(f"The path where the template file is located is:{current_directory}\\template\\")

    old_files = []
    file_path = f'{datetime.now().strftime("%Y%m%d")}processed_file.txt'
    try:
        with open(file_path, 'r') as file:
            old_files = [line.strip() for line in file]
    except FileNotFoundError:
        with open(file_path, 'w') as file:
            pass

    # 读取cfg.txt内容----------------------------------------
    cfg_file_path = 'cfg.txt'

    config = configparser.ConfigParser()
    config.read(cfg_file_path)

    # 获取默认参数:如站点编号等等
    station = config['DEFAULT']['station']
    other = config['DEFAULT']['other']
    print(f"station: {station}")

    # 创建一个字典来存储每个滤镜类型和其对应的目标坐标
    target_coords_dict = {}

    # 获取默认的滤镜列表
    filters = config['DEFAULT']['filter'].split(',')

    for filter_type in filters:
        for i in range(1, 3):  # 只提取 1 和 2 两种顺序
            order_key = f"{filter_type}{i}"
            if order_key in config:
                coords_str = config[order_key]['target_coords']
                coords_list = []
                for coord in coords_str.split(';'):
                    parts = coord.split(',')
                    obj_name = parts[0].strip()
                    x_coord = int(parts[1].strip())
                    y_coord = int(parts[2].strip())
                    coords_list.append((obj_name, x_coord, y_coord))
                # 将结果存储在字典中
                target_coords_dict[order_key] = coords_list

    # 以上为读取cfg.txt内容----------------------------------------以下为连接服务器内容
    client = TcpClient('xxx.xxx.xxx.xxx', xxxx)
    client.connect()
    if client.linked:
        lock = threading.Lock()
        running = True
        client.disconnect()
        print('The server attempted to connect successfully and hung up temporarily, and can now be monitored normally')
        threading.Thread(target=run_schedule).start()
    else:
        print("Unable to connect to server, program exits.")
        time.sleep(5)
        sys.exit(1)


