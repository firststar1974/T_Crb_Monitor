import socket
import threading
import time
import os
from datetime import datetime, timedelta
import shutil
import pandas as pd
from pandas import Timedelta
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import matplotlib
import matplotlib.dates as mdates
from matplotlib import ticker
import warnings

warnings.filterwarnings('ignore')

matplotlib.use('Agg')

def id_locate(station):
    if station[:5]=="T_S50":
        return "S50用户 临时地点"
    ###############################
    if station=="TW001":
        return "Canada 加拿大温哥华"
    if station=="TW002":
        return "USA 美国新墨西哥州"
    if station=="TW003":
        return "Chile 智利"
    if station=="TW004":
        return "Canada 加拿大素里"
    if station=="TW005":
        return "USA 美国加州"
    if station=="TW006":
        return "USA 美国内华达州"
    if station=="TW007":
        return "Ireland 爱尔兰科克城"
    ###############################
    if station == "TE001":
        return "China 星明天文台"
    if station == "TE002":
        return "China 北京天文馆MuRT"
    if station == "TE003":
        return "China 云南武定"
    if station == "TE004":
        return "China 宁夏银川"
    if station == "TE005":
        return "China 甘肃平凉"
    if station == "TE006":
        return "China 河北张家口"
    if station == "TE007":
        return "China 河北石家庄"
    if station == "TE008":
        return "China 广东清远"
    if station == "TE009":
        return "China 江苏盱眙"
    if station == "TE010":
        return "strand， Norway 挪威"
    if station == "TE011":
        return "China 宁夏哈巴湖"
    if station == "TE012":
        return "China 四川稻城"
    if station == "TE013":
        return "China 浙江杭州"
    if station == "TE014":
        return "China 上海天文馆"
    if station == "TE015":
        return "China 云南丽江"
    if station == "TE016":
        return "China 广东深圳"
    if station == "TE017":
        return "China 四川稻城2"
    if station == "TE018":
        return "China 甘肃张掖"
    if station == "TE019":
        return "China 河北张家口2"
    if station == "TE020":
        return "China 云南大姚"
    if station == "TE021":
        return "China 北京怀柔"
    if station == "TE022":
        return "China 辽宁庄河"
    if station == "TE023":
        return "China 辽宁辽阳"
    if station == "TE024":
        return "Àger, Spain 西班牙阿赫尔"

# 触发报警函数
def trigger_alarm(captime, filter):
    print(f"报警触发: 观测时间: {captime}, 滤镜: {filter}")
    alert_file_path = "F:/HMT-check/plots/alert.txt"
    with open(alert_file_path, 'w') as file:
        file.write('ok\n')
    print(f'\033[1;31m——---------————报警触发: 观测时间: {captime}, 滤镜: {filter}拨打报警电话———----------———\n\033[0m')
    print(f'\033[1;31m——---------————报警触发: 观测时间: {captime}, 滤镜: {filter}拨打报警电话———----------———\n\033[0m')
    print(f'\033[1;31m——---------————报警触发: 观测时间: {captime}, 滤镜: {filter}拨打报警电话———----------———\n\033[0m')

    # 等待1分钟（60秒）
    time.sleep(60)

    # 删除文件中的内容
    with open(alert_file_path, 'w') as file:
        file.write('')
    print(f'报警解除: 观测时间: {captime}, 滤镜: {filter}')

# 全局变量，跟踪上次运行 plot_tcrb_median 的时间
last_plot_time = None

def recvs1(inf, addr):
    global last_plot_time
    try:
        inf.settimeout(10)  # 设置8秒的接收超时
        a1 = inf.recv(1024).decode('utf-8')
        print('1发来~~~~~~~' + a1)
        if a1.startswith('T'):  #接收到正确数据后的主要处理程序
            print('1发来\033[1;31m' + a1+'\033[0m')

            station_id, data_string = a1.split('=', 1)
            parsed_data = parse_data(station_id, data_string)
            # print(f"打印解析数据: {parsed_data}")

            # 检查 parsed_data 是否为 None 或为空
            if parsed_data is not None and len(parsed_data) > 0:
                excel_path,TCRB_filepath, TCRB_filepath_s= update_excel_with_targets(station_id, parsed_data)  # 写入excel表格

                plot_corrected_magnitude(station_id, excel_path)  #画图

                plot_tcrb_data(TCRB_filepath, 24)  # 画T CrB 24小时图
                plot_tcrb_data(TCRB_filepath_s, 6)  # 画T CrB 短时间小时图

                # 检查是否需要运行 plot_tcrb_median
                current_time = datetime.now()
                if last_plot_time is None or (current_time - last_plot_time) > timedelta(days=1):
                    plot_tcrb_median("T_CrB_median.xlsx")
                    backup_snapshots()  # 运行备份快照的函数
                    last_plot_time = current_time  # 更新最后运行时间
            else:
                print("解析数据为空或不合法，跳过处理。")

        else:
            raise ValueError("消息格式不正确，必须以'T'开头")
    except (socket.timeout, ValueError) as e:
        print(f"来自 {addr} 的连接错误: {e}", time.strftime("%Y-%m-%d %H:%M:%S"))
    finally:
        inf.close()
        print(f"连接 {addr} 已关闭", time.strftime("%Y-%m-%d %H:%M:%S"))


def parse_data(station_id, data):  # 切割数据成为一个列表，列表元素是字典
    # 从总列表中获得某个目标的星等信息
    def get_latest_mag(parsed_data, objname):
        filtered_data = [entry for entry in parsed_data if entry['objname'] == objname]
        if filtered_data:
            return filtered_data[-1]['mag_correct']
        return None

    # 标准情况下的D1和D2的视亮度星等值
    standard_mags = {
        'B': {'D1': 9.323, 'D2': 8.290, 'C3': 9.681},
        'G': {'D1': 7.799, 'D2': 7.895, 'C3': 9.334},
        'R': {'D1': 6.920, 'D2': 7.640, 'C3': 9.100},
        'Blue': {'D1': 9.323, 'D2': 8.290, 'C3': 9.681},
        'Green': {'D1': 7.799, 'D2': 7.895, 'C3': 9.334},
        'Red': {'D1': 6.920, 'D2': 7.640, 'C3': 9.100},
        'Unfilter': {'D1': 6.920 + 0.5, 'D2': 7.640 + 0.5, 'C3': 9.100 + 0.5},
        'IRCUT': {'D1': 7.590 + 0.5, 'D2': 7.640 + 0.5, 'C3': 9.100 + 0.5},    # 如果D1是SAO 84114,那么NOMAD星表给出B：9.206，V：8.212，R：7.590
    }

    data_list = data.split('+')
    parsed_data = []

    # 提取滤镜和D1/D2亮度值
    filter_type = None
    d1_mag = None
    d2_mag = None
    c3_mag = None

    for entry in data_list:
        parts = entry.split(',')
        if len(parts) == 8:
            objname = parts[5]
            filter_type = parts[3] if filter_type is None else filter_type

            if objname == 'D1':
                d1_mag = float(parts[7])
            elif objname == 'D2':
                d2_mag = float(parts[7])
            elif objname == 'C3':
                c3_mag = float(parts[7])

    # 计算差值并检查波动情况
    if filter_type in standard_mags:
        if d1_mag is not None and d2_mag is not None:
            correction_value = (d1_mag + d2_mag) / 2 - (
                    standard_mags[filter_type]['D1'] + standard_mags[filter_type]['D2']) / 2
            d1_corrected = d1_mag - correction_value
            d2_corrected = d2_mag - correction_value
            print(f"D1数据波动{abs(d1_corrected - standard_mags[filter_type]['D1'])}，D2数据波动{abs(d2_corrected - standard_mags[filter_type]['D2'])}")
            if abs(d1_corrected - standard_mags[filter_type]['D1']) > 0.5 or abs(
                    d2_corrected - standard_mags[filter_type]['D2']) > 0.5:
                print("\033[1;34mD1,D2数据波动过大，数据忽略\033[0m")
                return None
        elif d1_mag is not None and c3_mag is not None:
            correction_value = (d1_mag + c3_mag) / 2 - (
                    standard_mags[filter_type]['D1'] + standard_mags[filter_type]['C3']) / 2
            d1_corrected = d1_mag - correction_value
            c3_corrected = c3_mag - correction_value
            print(f"D1数据波动{abs(d1_corrected - standard_mags[filter_type]['D1'])}，C3数据波动{abs(c3_corrected - standard_mags[filter_type]['C3'])}")
            if abs(d1_corrected - standard_mags[filter_type]['D1']) > 0.5 or abs(
                    c3_corrected - standard_mags[filter_type]['C3']) > 0.5:
                print("\033[1;34mD1,C3数据波动过大，数据忽略\033[0m")
                return None
        elif d2_mag is not None and c3_mag is not None:
            correction_value = (d2_mag + c3_mag) / 2 - (
                    standard_mags[filter_type]['D2'] + standard_mags[filter_type]['C3']) / 2
            d2_corrected = d2_mag - correction_value
            c3_corrected = c3_mag - correction_value
            print(f"D2数据波动{abs(d2_corrected - standard_mags[filter_type]['D2'])}，C3数据波动{abs(c3_corrected - standard_mags[filter_type]['C3'])}")
            if abs(d2_corrected - standard_mags[filter_type]['D2']) > 0.5 or abs(
                    c3_corrected - standard_mags[filter_type]['C3']) > 0.5:
                print("\033[1;34mD2,C3数据波动过大，数据忽略\033[0m")
                return None
        else:
            correction_value = 0  # 如果D1和D2都没有值，则不做修正
    else:
        correction_value = 0

    # 修正其他星点的mag值
    for entry in data_list:
        parts = entry.split(',')
        if len(parts) == 8:
            mag_correct = float(parts[7]) - correction_value
            parsed_data.append({
                'captime': parts[1],
                'filter': parts[3],
                'objname': parts[5],
                'mag': float(parts[7]),
                'mag_correct': mag_correct
            })

    # 获取最新的T CrB, C2, C3, D2目标的改正星等
    t_crb_mag = get_latest_mag(parsed_data, 'T CrB')
    c2_mag = get_latest_mag(parsed_data, 'C2')
    c3_mag = get_latest_mag(parsed_data, 'C3')
    d1_mag = get_latest_mag(parsed_data, 'D1')
    d2_mag = get_latest_mag(parsed_data, 'D2')

    # 获取滤镜信息
    filter = parsed_data[-1]['filter'] if parsed_data else None

    # 根据不同滤镜类型和目标星等判断是否触发报警
    if filter and t_crb_mag is not None and c2_mag is not None and c3_mag is not None and d1_mag is not None and d2_mag is not None:
        if filter == 'R' or filter == 'Red' or filter == 'Unfilter':  # 如果是R或者Unfilter滤镜，且满足条件，则触发报警
            if t_crb_mag < d2_mag and d2_mag > d1_mag:
                trigger_alarm(parsed_data[-1]['captime'], filter)
            if t_crb_mag < 8.5:
                trigger_alarm(parsed_data[-1]['captime'], filter)
        elif filter == 'G' or filter == 'Green':  # 如果是G滤镜，且满足条件，则触发报警
            if t_crb_mag < d2_mag and t_crb_mag < d1_mag and c3_mag > d1_mag:
                trigger_alarm(parsed_data[-1]['captime'], filter)
            if t_crb_mag < 9.3:
                trigger_alarm(parsed_data[-1]['captime'], filter)
        elif filter == 'B' or filter == 'Blue':  # 如果是B滤镜，且满足条件，则触发报警
            if t_crb_mag < c2_mag and t_crb_mag < c3_mag and c3_mag > d1_mag and c3_mag > d2_mag:
                trigger_alarm(parsed_data[-1]['captime'], filter)
            if t_crb_mag < 10.5:
                trigger_alarm(parsed_data[-1]['captime'], filter)
        elif filter == 'IRCUT':  # 如果是IRCUT滤镜，且满足条件，则触发报警
            if t_crb_mag < d1_mag and t_crb_mag < d2_mag:
                trigger_alarm(parsed_data[-1]['captime'], filter)  # 如果是非R滤镜，且满足条件，则触发报警
            if t_crb_mag < 9.0:
                trigger_alarm(parsed_data[-1]['captime'], filter)
        else:
            if t_crb_mag < d1_mag and t_crb_mag < d2_mag:
                trigger_alarm(parsed_data[-1]['captime'], filter)  # 如果是非R滤镜，且满足条件，则触发报警

    return parsed_data


'''将感兴趣的目标的测光数据写入excel文件，输入参数是感兴趣的目标列表，最近24小时内的数据存储excel文件，历史数据存储excel文件'''
def update_excel_with_targets(station_id,targets_list):  # 参数1：站点ID，参数2：感兴趣的目标列表数据
    excel_filename = f"{station_id}_targets_photometry.xlsx"
    history_filename = f"{station_id}_history_data.xlsx"
    TCRB_excel = f"T_CrB_targets_photometry.xlsx"
    TCRB_history = f"T_CrB_history_data.xlsx"
    TCRB_excel_s = f"T_CrB_targets_photometry_s.xlsx"
    TCRB_median = f"T_CrB_median.xlsx"  # 新增的文件，用于保存T CrB的中值

    # 将感兴趣的目标数据转换为DataFrame
    df_new = pd.DataFrame(targets_list)

    # 移除包含NaN的行
    df_new = df_new.dropna()

    # 将日期字符串转换为datetime对象
    df_new['captime'] = pd.to_datetime(df_new['captime'])

    # 确定新数据中的最早时间
    new_data_earliest_time = df_new['captime'].min()

    # 如果主Excel文件存在，则读取内容，否则创建一个空的DataFrame
    try:
        df_existing = pd.read_excel(excel_filename)
        # 同样，将日期字符串转换为datetime对象
        df_existing['captime'] = pd.to_datetime(df_existing['captime'])
    except FileNotFoundError:
        df_existing = pd.DataFrame()

    # 检查并更新历史记录文件
    if not df_existing.empty:
        # 筛选出超过12小时的数据
        cutoff_time = new_data_earliest_time - timedelta(hours=12)
        history_data = df_existing[df_existing['captime'] < cutoff_time]

        if not history_data.empty:
            # 检查历史文件大小
            if os.path.exists(history_filename) and os.path.getsize(history_filename) > 1 * 1024 * 1024:  # 1MB
                # 重命名旧的历史文件
                first_date_str = history_data['captime'].dt.strftime('%Y%m%d').iloc[0]
                new_history_path = f'{station_id}_history_data_{first_date_str}.xlsx'
                os.rename(history_filename, new_history_path)

            # 如果历史文件存在，则读取并追加数据，否则创建新文件
            try:
                df_history = pd.read_excel(history_filename)
                df_history = pd.concat([df_history, history_data], ignore_index=True)
            except FileNotFoundError:
                df_history = history_data

            # 保存历史数据
            df_history.to_excel(history_filename, index=False)

            # 从现有数据中移除超出的历史数据
            df_existing = df_existing[df_existing['captime'] >= cutoff_time]

            # 计算T CrB的中值并保存
            df_tcrb_history = df_history[df_history['objname'] == 'T CrB']
            if not df_tcrb_history.empty:
                # 按日期和滤镜计算中值
                df_tcrb_history['date'] = df_tcrb_history['captime'].dt.date
                median_mag = df_tcrb_history.groupby(['date', 'filter'])['mag_correct'].median().reset_index()
                median_mag['station_id'] = station_id

                # 读取或创建TCRB_median文件
                try:
                    df_median_existing = pd.read_excel(TCRB_median)
                except FileNotFoundError:
                    df_median_existing = pd.DataFrame(columns=['date', 'filter', 'mag_correct', 'station_id'])

                df_median_updated = pd.concat([df_median_existing, median_mag], ignore_index=True)
                df_median_updated.to_excel(TCRB_median, index=False)

    # 追加新的数据
    df_updated = pd.concat([df_existing, df_new], ignore_index=True)

    # 对数据进行排序，这里按照captime升序排序
    df_updated.sort_values(by='captime', inplace=True)

    # 保存更新后的主Excel文件
    df_updated.to_excel(excel_filename, index=False)

    print(df_new)

    # 处理 T CrB 数据__________________________________________________________
    df_tcrb = df_new[df_new['objname'] == 'T CrB']
    cutoff_time_tcrb = pd.Timestamp.now() - timedelta(
        hours=32)  # 因为计算机时间是北京时间，而captime是世界时，因此想要最近24小时的数据，就需要设置24+8=32的差值。再减2效果一样

    if not df_tcrb.empty:
        # 添加站点名称
        df_tcrb['station_id'] = station_id

        try:
            df_tcrb_existing = pd.read_excel(TCRB_excel)
            df_tcrb_existing['captime'] = pd.to_datetime(df_tcrb_existing['captime'])
        except FileNotFoundError:
            df_tcrb_existing = pd.DataFrame()

        df_tcrb_updated = pd.concat([df_tcrb_existing, df_tcrb], ignore_index=True)
        df_tcrb_updated = df_tcrb_updated[df_tcrb_updated['captime'] >= cutoff_time_tcrb]
        df_tcrb_updated.sort_values(by='captime', inplace=True)
        df_tcrb_updated.to_excel(TCRB_excel, index=False)

        try:
            # df_tcrb_history = pd.read_excel(TCRB_history)
            df_tcrb_history = pd.read_excel(TCRB_history, engine='openpyxl')
            df_tcrb_history = pd.concat([df_tcrb_history, df_tcrb[df_tcrb['captime'] < cutoff_time_tcrb]],
                                        ignore_index=True)
        except FileNotFoundError:
            df_tcrb_history = df_tcrb[df_tcrb['captime'] < cutoff_time_tcrb]

        if os.path.exists(TCRB_history) and os.path.getsize(TCRB_history) > 500 * 1024:  # 500KB
            first_date_str_tcrb = df_tcrb_history['captime'].dt.strftime('%Y%m%d').iloc[0]
            new_history_path_tcrb = f'T_CrB_history_data_{first_date_str_tcrb}.xlsx'
            os.rename(TCRB_history, new_history_path_tcrb)

        df_tcrb_history.to_excel(TCRB_history, index=False)

        # 筛选最近 14 小时内的数据并存储到 TCRB_excel_s 文件中
        cutoff_time_tcrb_s = pd.Timestamp.now() - timedelta(hours=14)  # 最近6小时的数据存储到TCRB_excel_s
        df_tcrb_s = df_tcrb_updated[df_tcrb_updated['captime'] >= cutoff_time_tcrb_s]
        df_tcrb_s.sort_values(by='captime', inplace=True)
        df_tcrb_s.to_excel(TCRB_excel_s, index=False)

    return excel_filename, TCRB_excel, TCRB_excel_s


'''将excel文件记录的数据显示在png图像中，分为RGB三色测光图，输入参数是需要显示数据的excel文件，三色滤镜，返回三色png文件'''
def plot_corrected_magnitude(station_id, excel_path, filter_types=['R', 'G', 'B', 'Unfilter', 'Red', 'Green', 'Blue', 'IRCUT']):  #这里滤镜是不是有其他样式，比如Unfilter，Red等等


    # 设置中文字体
    font = FontProperties(fname=r"C:\Windows\Fonts\SimHei.ttf", size=14)  # Windows下的字体路径

    # 读取Excel文件
    df = pd.read_excel(excel_path)

    # 将'captime'转换为datetime格式
    df['captime'] = pd.to_datetime(df['captime'])

    # 为不同的目标和滤镜设置不同的样式
    styles = {
        'T CrB': {'color': 'red', 'marker': 'o', 'markersize': 6, 'linewidth': 2},
        'C1': {'color': 'black', 'marker': 's', 'markersize': 2, 'linewidth': 1},
        'C2': {'color': 'orange', 'marker': '^', 'markersize': 2, 'linewidth': 1},
        'C3': {'color': 'green', 'marker': 'D', 'markersize': 2, 'linewidth': 1},
        'D1': {'color': 'blue', 'marker': '*', 'markersize': 2, 'linewidth': 1},
        'D2': {'color': 'purple', 'marker': 'p', 'markersize': 2, 'linewidth': 1}
    }

    # 定义星期几对应的背景颜色（同色系）
    background_colors = [
        '#f8f1f8', '#80deea', '#e8f5e9', '#f2dfeb', '#e0f7fa', '#a5d6a7', '#fff9c4'
    ]

    for filter_type in filter_types:


        # 筛选指定滤镜的数据
        filter_df = df[df['filter'] == filter_type]

        # 检查是否有数据
        if filter_df.empty:
            print(f"没有指定滤镜数据，No data for filter type {filter_type}")
            continue

        # 判断是否有多于三个不同的时间记录
        unique_times = filter_df['captime'].nunique()
        if unique_times <= 3:
            print(f"数据点不足，只有 {unique_times} 个不同时间记录，跳过滤镜类型 {filter_type}")
            continue

        # 创建图像
        plt.figure(figsize=(8, 5))

        if not filter_df.empty:
            # 获取最后一个数据点的时间
            time_obj = filter_df['captime'].max()

            # 计算这一天中已经过去的总秒数
            seconds_passed = time_obj.hour * 3600 + time_obj.minute * 60 + time_obj.second
            # 一天的总秒数
            seconds_in_a_day = 86400
            # 返回过去的秒数占一天的小数部分，从而得到以天为单位的最后一个数据点的时间,取4位小数，第5位四舍五入
            last_time = round(seconds_passed / seconds_in_a_day, 4)

            # 获得完整的表示形式
            formatted_date = time_obj.strftime("%Y %m %d") + f"{last_time:.4f}"[1:]

            # 获取最后一个数据点的时间，并转换为北京时间（UTC+8）
            last_time_utc = filter_df['captime'].max()
            last_time_bjt = last_time_utc + Timedelta(hours=8)  # 改成北京时间UT+8小时
            last_time_str = last_time_bjt.strftime('%Y-%m-%d %H:%M')  # 转换为字符串
        else:
            formatted_date = "No data"
            last_time_str = "No data"

        # 获取星期几的索引（0 = Monday, 6 = Sunday）
        day_of_week = time_obj.weekday()
        # 设置对应的背景颜色
        plt.gca().set_facecolor(background_colors[day_of_week])

        # 绘制每个目标的改正星等
        for target, style in styles.items():
            target_df = filter_df[filter_df['objname'] == target]
            plt.plot(target_df['captime'], target_df['mag_correct'],
                     label=f'{target} ({filter_type})',
                     **style)
            # 在数据点最右侧标示名称
            if not target_df.empty:
                last_point = target_df.iloc[-1]
                plt.text(last_point['captime'] + timedelta(hours=0.05), last_point['mag_correct'], target,
                         fontsize=10, color=style['color'], weight='bold')

        idlocate = id_locate(station_id)
        # 设置横纵坐标轴的标题
        plt.xlabel(f'Observation Time ( UT )  Station：{station_id} location：{idlocate}', fontproperties=font)
        plt.ylabel('Corrected Magnitude')

        # 设置子图的边距
        plt.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)

        # 添加网格
        plt.grid(color='gray', linestyle='--', linewidth=0.5, alpha=0.7)

        # 反转y轴
        plt.gca().invert_yaxis()

        # 设置图例
        plt.legend(loc='upper left', fontsize=10)

        plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=1))  # 每6小时一个主刻度
        plt.gca().xaxis.set_minor_locator(mdates.MinuteLocator(byminute=[0, 30]))  # 每半小时一个次刻度
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
        plt.gcf().autofmt_xdate()

        plt.title(f'({filter_type} Filter) - Last Data Point: {formatted_date} (UT) | {last_time_str} (UT+8)' ,fontweight='bold')

        # 设置作者或版权信息
        author_info = f"@ 2024 {station_id} {idlocate}"

        # 添加版权信息
        # 使用坐标系比例 (1, 1) 代表图像的右下角
        # 'ha' 和 'va' 分别控制水平和垂直对齐方式
        plt.text(1, 0, author_info,
                 fontsize=10, color='gray',
                 ha='right', va='bottom', transform=plt.gca().transAxes, fontproperties=font)

        # 保存图像
        plot_file = f'F:/HMT-check/plots/corrected_magnitude_plot_{filter_type}_{station_id}.png'
        plt.savefig(plot_file, bbox_inches='tight')

        print(f"光变曲线已保存到: {plot_file}")

        # 关闭当前图像窗口以释放内存
        plt.close()

# 全局变量，箭头尾部的纵向偏移量
y_offset = 0

def plot_tcrb_data(TCRB_excel,hours):
    global y_offset
    # 设置中文字体
    font = FontProperties(fname=r"C:\Windows\Fonts\SimHei.ttf", size=14)  # Windows下的字体路径

    # 读取T_CrB的Excel文件
    df = pd.read_excel(TCRB_excel)

    # 将'captime'转换为datetime格式
    df['captime'] = pd.to_datetime(df['captime'])

    # 定义站点颜色列表，与基本滤镜颜色明显不同
    station_colors = [
        'darkcyan',  # 深青色
        'darkkhaki',  # 深黄褐色
        'darkslateblue',  # 深石板蓝色
        'deeppink',  # 深粉色
        'deepskyblue',  # 深天蓝色
        'firebrick',  # 火砖色
        'gold',  # 金色
        'indigo',  # 靛蓝色
        'mediumvioletred',  # 中紫罗兰红色
        'sienna'  # 赭色
    ]

    # 设置滤镜的颜色和样式
    filter_styles = {
        'B': {'markercolor': 'blue', 'marker': 'o', 'label': 'Blue'},
        'G': {'markercolor': 'green', 'marker': 's', 'label': 'Green'},
        'R': {'markercolor': 'red', 'marker': 'D', 'label': 'Red'},
        'Blue': {'markercolor': 'blue', 'marker': 'o', 'label': 'Blue'},
        'Green': {'markercolor': 'green', 'marker': 's', 'label': 'Green'},
        'Red': {'markercolor': 'red', 'marker': 'D', 'label': 'Red'},
        'Unfilter': {'markercolor': 'orange', 'marker': '^', 'label': 'Unfiltered'},
        'IRCUT': {'markercolor': 'purple', 'marker': '*', 'label': 'IRCUT'},
    }

    # 创建图像
    plt.figure(figsize=(15, 6))

    # 记录每个站点的颜色
    station_color_map = {}

    # 记录最后一个数据点信息
    last_points = []

    for i, station in enumerate(df['station_id'].unique()):
        # 指派站点颜色
        linecolor = station_colors[i % len(station_colors)]
        station_color_map[station] = linecolor

        for filter_type, filter_style in filter_styles.items():
            # 筛选每个站点和滤镜类型的数据
            station_df = df[(df['station_id'] == station) & (df['filter'] == filter_type)]

            # if station_df.empty:
            #     continue

            # 如果数据点少于4个，跳过处理
            if len(station_df) < 4:
                #print(f"{station}记录点只有{len(station_df)}个，跳过处理")
                continue

            # 舍去 mag_correct 大于 12 或者小于 0 的数据
            station_df = station_df[(station_df['mag_correct'] <= 12) & (station_df['mag_correct'] >= 0)]

            # 筛选数据点，确保间隔至少2分钟
            if not station_df.empty:
                selected_points = [station_df.iloc[0]]  # 保留第一个点
                for j in range(1, len(station_df)):
                    if (station_df.iloc[j]['captime'] - selected_points[-1]['captime']).total_seconds() >= 180:
                        selected_points.append(station_df.iloc[j])
                selected_points.append(station_df.iloc[-1])  # 保留最后一个点
                station_df = pd.DataFrame(selected_points).drop_duplicates().reset_index(drop=True)
##
            if station[:5] == "T_S50":  # 处理S50临时观测显示
                stationlabel=f'{station[5:]} (S50)'
                point_station='S50_tmp'
            else:
                stationlabel = f'{station} ({filter_type})'
                point_station = f'{station}'
##
            # 绘制每个站点和滤镜类型的光变曲线
            plt.plot(station_df['captime'], station_df['mag_correct'],
                     label=stationlabel,
                     color=linecolor,
                     marker=filter_style['marker'],
                     markerfacecolor=filter_style['markercolor'],
                     markeredgewidth=0.5,
                     markeredgecolor='black',
                     linestyle='-',  # 所有站点使用相同的线型
                     markersize=4.0, linewidth=2.0)

            # 存储最后一个数据点的信息
            if not station_df.empty:
                last_point = station_df.iloc[-1]
                last_points.append((station, last_point, linecolor))


            # 在第一个数据点标记站点名称
            if hours==24:
                if not station_df.empty:
                    first_point = station_df.iloc[0]
                    # 偏移标签以避免重叠
                    text_offset = -0.3
                    vertical_offset = -0.2
                    plt.text(first_point['captime'] + pd.Timedelta(hours=text_offset),
                             first_point['mag_correct'] + vertical_offset,
                             point_station,
                             fontsize=10, color=linecolor)
            else:
                if not station_df.empty:
                    first_point = station_df.iloc[0]
                    # 偏移标签以避免重叠
                    text_offset = -0.1
                    vertical_offset = -0.05
                    plt.text(first_point['captime'] + pd.Timedelta(hours=text_offset),
                             first_point['mag_correct'] + vertical_offset,
                             point_station,
                             fontsize=10, color=linecolor)

    # 标记最后一个数据点的站点名称，避免重叠（纵向偏移量在+-0.3范围内变化
    for i, (station, last_point, linecolor) in enumerate(last_points):

##
        if station[:5] == "T_S50":  # 处理S50临时观测显示
            stationlabel = f'{station[5:]} (S50)'
            point_station = 'S50_tmp'
        else:
            stationlabel = f'{station} ({filter_type})'
            point_station = f'{station}'
##

        for j in range(i):
            _, prev_last_point, _ = last_points[j]
            # 如果时间差小于0.5小时，增加垂直偏移量
            if abs((last_point['captime'] - prev_last_point['captime']).total_seconds()) < 1800:
                y_offset -= 0.3
            # 如果垂直偏移量小于-0.9，重置为0
            if y_offset < -1.0:
                y_offset = 0

        # 使用 annotate 添加箭头标记站点名称
        if hours == 24:
            # 使用 annotate 添加箭头标记站点名称
            plt.annotate(point_station,
                 xy=(last_point['captime'], last_point['mag_correct']),
                 xytext=(
                     last_point['captime'] + pd.Timedelta(hours=0.5),
                     last_point['mag_correct'] + 0.5 + y_offset),
                 arrowprops=dict(facecolor=linecolor, shrink=0.10),
                 fontsize=10, color=linecolor, weight='bold')


        else:

            plt.annotate(point_station,
                 xy=(last_point['captime'], last_point['mag_correct']),
                 xytext=(
                     last_point['captime'] + pd.Timedelta(hours=0.1),
                     last_point['mag_correct'] + 0.5 + y_offset),
                 arrowprops=dict(facecolor=linecolor, shrink=0.10),
                 fontsize=10, color=linecolor, weight='bold')

    # 获取最后一个数据点的时间
    if not df.empty:
        last_time_utc = df['captime'].max()
        last_time_bjt = last_time_utc + pd.Timedelta(hours=8)  # 改成北京时间UT+8小时
        last_time_str = last_time_bjt.strftime('%Y-%m-%d %H:%M')  # 转换为字符串

        # 计算这一天中已经过去的总秒数
        seconds_passed = last_time_utc.hour * 3600 + last_time_utc.minute * 60 + last_time_utc.second
        # 一天的总秒数
        seconds_in_a_day = 86400
        # 返回过去的秒数占一天的小数部分，从而得到以天为单位的最后一个数据点的时间,取4位小数，第5位四舍五入
        last_time_fraction = round(seconds_passed / seconds_in_a_day, 4)
        formatted_date = last_time_utc.strftime("%Y %m %d") + f"{last_time_fraction:.4f}"[1:]
    else:
        formatted_date = "No data"
        last_time_str = "No data"

    # 设置横纵坐标轴的标题
    plt.xlabel('Observation Time ( UT )', fontproperties=font)
    plt.ylabel('Corrected Magnitude', fontproperties=font)

    # 设置子图的边距
    plt.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.1)

    # 添加网格
    plt.grid(color='gray', linestyle='--', linewidth=0.5, alpha=0.7)

    # 反转y轴，设置y轴的最大值
    plt.gca().invert_yaxis()
    plt.ylim(12, plt.ylim()[1])

    # 设置y轴刻度间隔为0.5
    plt.gca().yaxis.set_major_locator(ticker.MultipleLocator(0.5))

    # 计算图例数量
    legend_labels = plt.legend().get_texts()
    legend_count = len(legend_labels)

    # 根据图例数量设置列数，超过25个图例就显示两列图例
    if legend_count > 25:
        plt.legend(loc='upper left', fontsize=10, ncol=2)
    else:
        plt.legend(loc='upper left', fontsize=10, ncol=1)

    # 设置x轴的日期格式
    plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=1))
    plt.gca().xaxis.set_minor_locator(mdates.MinuteLocator(byminute=[0, 30]))
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
    plt.gcf().autofmt_xdate()

    # 设置标题，包括最后一个数据点的时间
    plt.title(f'T CrB Light Curve Over {hours} Hours - Last Data Point: {formatted_date} (UT) | {last_time_str} (UT+8)',
              fontweight='bold')

    # 设置作者或版权信息
    author_info = "@ 2024 T CrB Global Monitoring Network  "
    plt.text(1, 0, author_info,
             fontsize=10, color='gray',
             ha='right', va='bottom', transform=plt.gca().transAxes, fontproperties=font)

    # 保存图像
    if hours==24:
        plot_file = f'F:/HMT-check/plots/T_CrB_light_curve.png'
    else:
        plot_file = f'F:/HMT-check/plots/T_CrB_light_curve_s.png'
    plt.savefig(plot_file, bbox_inches='tight')

    print(f"T CrB 光变曲线已保存到: {plot_file}")

    # 关闭当前图像窗口以释放内存
    plt.close()

def plot_tcrb_median(TCRB_median_excel, days=30):
    global y_offset
    # 设置中文字体
    font = FontProperties(fname=r"C:\Windows\Fonts\SimHei.ttf", size=14)  # Windows下的字体路径

    # 读取 T_CrB_median.xlsx 文件
    df = pd.read_excel(TCRB_median_excel)

    # 将 'date' 转换为 datetime 格式
    df['date'] = pd.to_datetime(df['date'])

    # 舍去中值小于0的数据,舍去大于12的数据
    df = df[df['mag_correct'] >= 0]
    df = df[df['mag_correct'] <= 12]

    # 只保留最近指定天数的数据
    cutoff_date = pd.Timestamp.now() - pd.Timedelta(days=days)
    df = df[df['date'] >= cutoff_date]

    # 定义站点颜色列表，与基本滤镜颜色明显不同
    station_colors = [
        'darkcyan',  # 深青色
        'darkkhaki',  # 深黄褐色
        'darkslateblue',  # 深石板蓝色
        'deeppink',  # 深粉色
        'deepskyblue',  # 深天蓝色
        'firebrick',  # 火砖色
        'gold',  # 金色
        'indigo',  # 靛蓝色
        'mediumvioletred',  # 中紫罗兰红色
        'sienna'  # 赭色
    ]

    # 设置滤镜的颜色和样式
    filter_styles = {
        'B': {'markercolor': 'blue', 'marker': 'o', 'label': 'Blue'},
        'G': {'markercolor': 'green', 'marker': 's', 'label': 'Green'},
        'R': {'markercolor': 'red', 'marker': 'D', 'label': 'Red'},
        'Blue': {'markercolor': 'blue', 'marker': 'o', 'label': 'Blue'},
        'Green': {'markercolor': 'green', 'marker': 's', 'label': 'Green'},
        'Red': {'markercolor': 'red', 'marker': 'D', 'label': 'Red'},
        'Unfilter': {'markercolor': 'orange', 'marker': '^', 'label': 'Unfiltered'},
        'IRCUT': {'markercolor': 'purple', 'marker': '*', 'label': 'IRCUT'},
    }

    # 创建图像
    plt.figure(figsize=(15, 8))

    # 记录每个站点的颜色
    station_color_map = {}

    # 记录最后一个数据点信息
    last_points = []

    for i, (station, filter_type) in enumerate(df.groupby(['station_id', 'filter']).groups.keys()):
##
        if station[:5] == "T_S50":  # 处理S50临时观测显示
            stationlabel = f'{station[5:]} (S50)'
            point_station = 'S50_tmp'
        else:
            stationlabel = f'{station} ({filter_type})'
            point_station = f'{station}'
##

        # 指派站点颜色
        linecolor = station_colors[i % len(station_colors)]
        station_color_map[station] = linecolor

        # 筛选该站点和滤镜的数据
        group_df = df[(df['station_id'] == station) & (df['filter'] == filter_type)]

        # 绘制每个站点和滤镜类型的中值光变曲线
        plt.plot(group_df['date'], group_df['mag_correct'],
                 label=stationlabel,
                 color=linecolor,
                 marker=filter_styles[filter_type]['marker'],
                 markerfacecolor=filter_styles[filter_type]['markercolor'],
                 markeredgewidth=0.5,
                 markeredgecolor='black',
                 linestyle='-',  # 所有站点使用相同的线型
                 markersize=6, linewidth=1.0)

        # 存储最后一个数据点的信息
        if not group_df.empty:
            last_point = group_df.iloc[-1]
            last_points.append((station, last_point, linecolor))

        # 在第一个数据点标记站点名称
        if not group_df.empty:
            first_point = group_df.iloc[0]
            # 偏移标签以避免重叠
            text_offset = -0.3
            vertical_offset = -0.2
            plt.text(first_point['date'] + pd.Timedelta(days=text_offset),
                     first_point['mag_correct'] + vertical_offset,
                     point_station,
                     fontsize=10, color=linecolor)

    # 标记最后一个数据点的站点名称，避免重叠（纵向偏移量在+-0.3范围内变化
    for i, (station, last_point, linecolor) in enumerate(last_points):

##
        if station[:5] == "T_S50":  # 处理S50临时观测显示
            point_station = 'S50_tmp'
        else:
            point_station = f'{station}'
##

        #y_offset = 0  # 初始化垂直偏移量
        for j in range(i):
            _, prev_last_point, _ = last_points[j]
            # 如果时间差小于0.5天，增加垂直偏移量
            if abs((last_point['date'] - prev_last_point['date']).total_seconds()) < 43200:  # 12小时 = 43200秒
                y_offset -= 0.2
            # 如果垂直偏移量小于-1.0，重置为0
            if y_offset < -1.0:
                y_offset = 0

        # 使用 annotate 添加箭头标记站点名称
        plt.annotate(point_station,
                     xy=(last_point['date'], last_point['mag_correct']),
                     xytext=(
                     last_point['date'] + pd.Timedelta(days=0.5), last_point['mag_correct'] + 0.5 + y_offset),
                     arrowprops=dict(facecolor=linecolor, shrink=0.10),
                     fontsize=10, color=linecolor, weight='bold')

    # 设置横纵坐标轴的标题
    plt.xlabel('Date', fontproperties=font)
    plt.ylabel('Median Magnitude', fontproperties=font)

    # 设置子图的边距
    plt.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.1)

    # 添加网格
    plt.grid(color='gray', linestyle='--', linewidth=0.5, alpha=0.7)

    # 反转y轴，设置y轴的最大值
    plt.gca().invert_yaxis()
    plt.ylim(df['mag_correct'].max() + 0.5, df['mag_correct'].min() - 0.5)

    # 设置y轴刻度间隔为0.5
    plt.gca().yaxis.set_major_locator(plt.MultipleLocator(0.5))

    # 设置x轴的日期格式
    plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=1))
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.gcf().autofmt_xdate()

    # 计算图例数量
    legend_labels = plt.legend().get_texts()
    legend_count = len(legend_labels)

    # 根据图例数量设置列数，超过20个图例就显示两列图例
    if legend_count > 20:
        plt.legend(loc='upper left', fontsize=10, ncol=2)
    else:
        plt.legend(loc='upper left', fontsize=10, ncol=1)

    # 设置标题
    plt.title('T CrB Median Magnitude Over Time by Station and Filter', fontweight='bold')

    # 设置作者或版权信息
    author_info = "@ 2024 T CrB Global Monitoring Network  "
    plt.text(1, 0, author_info,
             fontsize=10, color='gray',
             ha='right', va='bottom', transform=plt.gca().transAxes, fontproperties=font)

    # 保存图像
    plot_file = f'F:/HMT-check/plots/T_CrB_median_magnitude.png'
    plt.savefig(plot_file, bbox_inches='tight')

    print(f"T CrB 中值光变曲线已保存到: {plot_file}")

    # 关闭当前图像窗口以释放内存
    plt.close()


def backup_snapshots():
    # 获取当前日期，格式为 YYYYMMDD
    today = datetime.now().strftime('%Y%m%d')

    # 定义源目录和目标目录
    source_dir = 'F:/HMT-check/plots/snapshot_7min_0'
    backup_dir = f'F:/HMT-check/plots/{today}'

    # 如果目标目录不存在，则创建它
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)

    # 获取源目录中的所有文件
    files = os.listdir(source_dir)

    # 将文件复制到目标目录
    for file_name in files:
        full_file_name = os.path.join(source_dir, file_name)
        if os.path.isfile(full_file_name):
            shutil.copy(full_file_name, backup_dir)

    print(f"快照文件已备份到: {backup_dir}")


IP = 'xxx.xxx.xxx.xxx'  # 替换为实际IP地址
PORT = xxxx
# 创建目录
plots_dir = "plots"
if not os.path.exists(plots_dir):
    os.makedirs(plots_dir)

while True:
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((IP, PORT))
    server.listen(5)

    print("\033[1;35m[*] SocketServer 正在监听...任务开始时间：\033[0m", time.strftime("%Y-%m-%d %H:%M:%S"))

    try:
        client1, client_ip1 = server.accept()
        print(client_ip1[0] + ':' + str(client_ip1[1]) + ' 连接成功！', time.strftime("%Y-%m-%d %H:%M:%S"))

        receive1 = threading.Thread(target=recvs1, args=(client1, client_ip1))
        receive1.start()
        receive1.join()
        server.close()
        print("服务器关闭", time.strftime("%Y-%m-%d %H:%M:%S"))

    except KeyboardInterrupt:
        print("服务器关闭")
        server.close()
        break
