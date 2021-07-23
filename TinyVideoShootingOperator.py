#!/usr/bin/env python3
#-*- coding: utf-8 -*-

from dronekit import connect, Vehicle, VehicleMode, LocationGlobalRelative
from dronekit import Command, mavutil
import json
import time


'''定数'''
CONNECT_STRING = 'tcp:127.0.0.1:5763' # SITL only
SETTINGS_FILE_PATH = './settings.json'
SHOOTING_CIRCLE_RADIUS = 500 # cm
SHOOTING_CIRCLE_RATE = 12 # 角速度(deg)

'''ユーティリティ'''
class JSONObject:
  def __init__( self, dict ):
      vars(self).update( dict )

'''メイン'''
def main():
    # 飛行設定の取得
    with open(SETTINGS_FILE_PATH, 'r') as settings_file_content:
        settings = json.loads(settings_file_content.read(), 
                    object_hook=JSONObject)
    
    target_lat = settings.targetLocation.lat
    target_lon = settings.targetLocation.lon
    altitude = settings.altitude
    circle_radius = settings.circleSettings.radius
    circle_rate = settings.circleSettings.rate

    # 飛行設定の確認
    while True:
        print('目的地緯度:', target_lat)
        print('目的地経度:', target_lon)
        print('飛行高度:', altitude)
        print('周回半径:', circle_radius)
        print('周回各速度:', circle_rate)

        key_input = input('飛行開始:y, 中断:n => ' )

        if key_input[0] == 'y': 
            break
        elif key_input[0] == 'n':
            return
        
        print()

    ## 飛行設定が確認されたらドローンに接続しwaypointを設定する。
    vehicle = connect(CONNECT_STRING, wait_ready=True, timeout=60)
    print('ドローンへ接続')

    while not vehicle.home_location:
        if not vehicle.home_location:
                print("ホームロケーション取得中 ...")
        time.sleep(1)
    print('ホームロケーション:', vehicle.home_location)

    # ミッションの初期化
    cmds = vehicle.commands 
    cmds.download() 
    cmds.wait_ready()
    #time.sleep(5)
    cmds.clear()
    cmds.upload()

    # ミッション作成
    print('ミッション設定中 ...')
    mission_list = []
    target_waypoint = Command(0, 0, 0,
                            mavutil.mavlink.MAV_FRAME_GLOBAL_TERRAIN_ALT, 
                            mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,
                            0, 0, 
                            0, 3, 0, 0,
                            target_lat, target_lon, altitude
                            )
    dummy_cmd = target_waypoint
    mission_list.append(target_waypoint)
    mission_list.append(dummy_cmd)

    for cmd in mission_list:
        cmds.add(cmd)
    cmds.upload()

    cmds.next = 0
    last_waypoint = len(mission_list)
    print('ミッション設定完了')

    # Terrain Following 設定
    vehicle.parameters['TERRAIN_ENABLE'] = 1

    # Takeoff
    print('Takeoff ...')
    try:
        vehicle.wait_for_mode('GUIDED')
        vehicle.wait_for_armable()
        vehicle.arm()
        time.sleep(1)
        vehicle.wait_simple_takeoff(altitude, timeout=60)
    except TimeoutError as takeoffError: print("Takeoff is timeout!!!") # フェールセーフコード
    print('飛行高度到達')

    # ミッション実行、目的地へ移動開始
    print('飛行開始')
    vehicle.wait_for_mode('AUTO')

    while cmds.next != last_waypoint:
        print('目的地へ移動中 ...')
        time.sleep(1)
    
    print('移動完了')

    # プロポのThrottleをシミュレートする。
    # URL
    ## https://discuss.ardupilot.org/t/multirotor-in-sitl-wont-hold-alt-in-loiter-and-other-modes/6366/3
    ## https://gist.github.com/vo/9362500
    def alt_sim_rc3(self, attr_name, value):
        vehicle._master.mav.rc_channels_override_send(
            vehicle._master.target_system, 
            vehicle._master.target_component,
            0, 0, 1500, 0, 0, 0, 0, 0 
        )
    
    # 撮影開始
    while True: 
        key_input = input('撮影開始:C, 帰投: R => ')

        if key_input[0] == 'C':
            vehicle.parameters['CIRCLE_RADIUS'] = circle_radius
            vehicle.parameters['CIRCLE_RATE'] = circle_rate
            # コールバックを設定し、擬似的にスロットルをニュートラルに保つ。
            vehicle.add_attribute_listener(
                'location.global_relative_frame', 
                alt_sim_rc3
            )

            print('撮影開始')
            vehicle.wait_for_mode('CIRCLE')
            # time.sleep(5)
            # vehicle._master.mav.rc_channels_override_send(
            #    vehicle._master.target_system, 
            #     vehicle._master.target_component,
            #     0, 0, 0, 0, 0, 0, 0, 0 
            # )        
            break
        elif key_input[0] == 'R':
            print('帰投開始')
            vehicle.wait_for_mode('SMART_RTL')
            break

    # 帰投指示待ち
    if vehicle.mode.name != 'SMART_RTL':
        while True:
            key_input = input('帰投: R => ')

            if key_input[0] == 'R': 
                # RTLに入るのでスロットルから手を離す。
                vehicle.remove_attribute_listener(
                    'location.global_relative_frame.alt', 
                    alt_sim_rc3)
                print('帰投開始')
                vehicle.wait_for_mode('SMART_RTL')
                break

    print('帰投中 飛行指示終了')

if __name__ == '__main__':
    main()