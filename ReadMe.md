# TinyVideoShootingOperator

## 概要

- 指定された座標に向かう。
- 到着した座標をより円周を飛行し撮影を行う。(今回はカメラ操作なし、飛行のみ。)
- 撮影後帰投する。

## 方式

- 向かう座標の指定、到着の判定はWaypointで行う。
- 丘陵等への衝突回避はTerrain Followingで行う。
  - Mission Planer、QGCなどのGCSをドローンへ接続した状態で実行する。
- 撮影時の周回飛行はCircle Modeで行う。

## 手順

- 前準備
  - settings.jsonに目的地の緯度経度、および飛行高度を設定する。
    - targetLocation.lat : 目的地緯度
    - targetLocation.lon : 目的地経度
    - altitude : 飛行高度。Terrainからこの高さを保ちながら飛行し、この高さで撮影を行う。メートルで指定する。
    - circleSettings.radius : 円周半径(パラメータCIRCLE_RADIUSに指定する値)
    - circleSettings.rate : 角速度(パラメータCIRCLE_RATEに指定する値)

- 撮影
  - スクリプトを起動する。
  - 目的地の緯度経度、飛行高度、撮影時の円周半径および角速度が表示されるため良ければ'y'を入力して飛行開始。'n'を入力して中断。
  - 目的地に到着すると"到着"の表示後、目的地周辺の周回飛行を開始。'R'が入力されるまで続ける。
  - 'R'が入力されたら帰投する。

- 備考
  - 今回は撮影時の周回飛行をCircle modeで行ったがCircle modeの間、高度が保持されない現象が確認できた。
  - SITL固有の問題であるかは切り分けできなかったが、Circleは高度の変更を受け付けるmodeであるため、スロットルが低い状態になっていると類推し、Circle modeの間は属性リスナーのコールバックでrc overrideを用いスロットルを保持し続けるようにして回避している。
  - 現状のArdupilotの仕様を考えるとCircleのように周回するWaypointを設定するのが妥当だと考える。今後そちらも試したい。
