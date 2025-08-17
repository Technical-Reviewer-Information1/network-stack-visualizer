import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import time
import random
from typing import Dict, List, Tuple

st.set_page_config(
    page_title="ネットワークプロトコル可視化学習アプリ",
    page_icon="🌐",
    layout="wide"
)

st.title("🌐 ネットワークプロトコル可視化学習アプリ")
st.caption("Created by Dit-Lab.(Daiki ITO)")
st.caption("Supported by Tomoaki ATSUMI")

# セッション状態の初期化
if 'communication_logs' not in st.session_state:
    st.session_state.communication_logs = []
if 'animation_state' not in st.session_state:
    st.session_state.animation_state = 'stopped'
if 'current_step' not in st.session_state:
    st.session_state.current_step = 0
if 'packet_data' not in st.session_state:
    st.session_state.packet_data = {}

# TCP/IP階層モデルの定義
LAYERS = {
    'application': {'name': 'アプリケーション層', 'color': '#FF6B6B', 'example': 'HTTP'},
    'transport': {'name': 'トランスポート層', 'color': '#4ECDC4', 'example': 'TCP/UDP'},
    'internet': {'name': 'インターネット層', 'color': '#45B7D1', 'example': 'IP'},
    'network_interface': {'name': 'ネットワークインターフェース層', 'color': '#96CEB4', 'example': 'Ethernet'}
}

# ヘッダ情報の定義
HEADER_INFO = {
    'tcp': {
        'name': 'TCPヘッダ',
        'color': '#4ECDC4',
        'fields': {
            '送信元ポート': '8080',
            '宛先ポート': '80',
            'シーケンス番号': '1000',
            '確認応答番号': '2000',
            'ウィンドウサイズ': '65535',
            'チェックサム': '0x1A2B'
        }
    },
    'udp': {
        'name': 'UDPヘッダ',
        'color': '#4ECDC4',
        'fields': {
            '送信元ポート': '8080',
            '宛先ポート': '80',
            'データ長': '12',
            'チェックサム': '0x3C4D'
        }
    },
    'ip': {
        'name': 'IPヘッダ',
        'color': '#45B7D1',
        'fields': {
            'バージョン': '4',
            '送信元IPアドレス': '192.168.1.10',
            '宛先IPアドレス': '192.168.1.100',
            'TTL': '64',
            'プロトコル': '6 (TCP)',
            'チェックサム': '0x5E6F'
        }
    },
    'ethernet': {
        'name': 'Ethernetヘッダ',
        'color': '#96CEB4',
        'fields': {
            '送信元MACアドレス': '00:11:22:33:44:55',
            '宛先MACアドレス': '66:77:88:99:AA:BB',
            'タイプ': '0x0800 (IPv4)',
            'FCS': '0x12345678'
        }
    }
}

def add_log(message: str):
    """ログを追加する"""
    timestamp = time.strftime("%H:%M:%S")
    st.session_state.communication_logs.append(f"[{timestamp}] {message}")

def create_layer_visualization(side: str, data_position: str = None, headers: List[str] = None) -> go.Figure:
    """階層モデルの可視化を作成"""
    fig = go.Figure()
    
    # 基本の階層ボックスを描画
    layer_keys = list(LAYERS.keys())
    y_positions = [3, 2, 1, 0]  # 上から下へ
    
    for i, (layer_key, y) in enumerate(zip(layer_keys, y_positions)):
        layer = LAYERS[layer_key]
        
        # 階層ボックス
        fig.add_shape(
            type="rect",
            x0=0, y0=y, x1=2, y1=y+0.8,
            fillcolor=layer['color'],
            opacity=0.3,
            line=dict(color=layer['color'], width=2)
        )
        
        # 階層名とプロトコル例
        fig.add_annotation(
            x=1, y=y+0.4,
            text=f"{layer['name']}<br>({layer['example']})",
            showarrow=False,
            font=dict(size=12, color="black"),
            align="center"
        )
    
    # データとヘッダーの可視化
    if data_position and headers:
        layer_index = layer_keys.index(data_position)
        y = y_positions[layer_index]
        
        # データブロック
        fig.add_shape(
            type="rect",
            x0=2.2, y0=y+0.1, x1=2.8, y1=y+0.7,
            fillcolor="white",
            line=dict(color="black", width=1)
        )
        fig.add_annotation(
            x=2.5, y=y+0.4,
            text="データ",
            showarrow=False,
            font=dict(size=10)
        )
        
        # ヘッダーブロック
        for i, header in enumerate(headers):
            header_info = HEADER_INFO.get(header)
            if header_info:
                fig.add_shape(
                    type="rect",
                    x0=1.5-i*0.3, y0=y+0.1, x1=2.1-i*0.3, y1=y+0.7,
                    fillcolor=header_info['color'],
                    opacity=0.7,
                    line=dict(color="black", width=1)
                )
                fig.add_annotation(
                    x=1.8-i*0.3, y=y+0.4,
                    text=header_info['name'],
                    showarrow=False,
                    font=dict(size=8),
                    textangle=90
                )
    
    # レイアウト設定
    fig.update_layout(
        title=f"{side}",
        title_x=0.5,
        xaxis=dict(range=[-0.5, 3.5], showgrid=False, showticklabels=False),
        yaxis=dict(range=[-0.5, 4.5], showgrid=False, showticklabels=False),
        width=400,
        height=400,
        showlegend=False,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    return fig

def create_network_animation() -> go.Figure:
    """ネットワーク通信のアニメーション"""
    fig = go.Figure()
    
    # クライアントとサーバーの位置
    fig.add_shape(
        type="rect",
        x0=0, y0=0, x1=1, y1=1,
        fillcolor="lightblue",
        opacity=0.5,
        line=dict(color="blue", width=2)
    )
    fig.add_annotation(x=0.5, y=0.5, text="クライアント", showarrow=False)
    
    fig.add_shape(
        type="rect",
        x0=4, y0=0, x1=5, y1=1,
        fillcolor="lightgreen",
        opacity=0.5,
        line=dict(color="green", width=2)
    )
    fig.add_annotation(x=4.5, y=0.5, text="サーバー", showarrow=False)
    
    # ネットワーク線
    fig.add_shape(
        type="line",
        x0=1, y0=0.5, x1=4, y1=0.5,
        line=dict(color="gray", width=3)
    )
    
    # アニメーション中のパケット表示
    if st.session_state.animation_state == 'transmitting':
        packet_x = 1.5 + (st.session_state.current_step / 10) * 2
        fig.add_shape(
            type="circle",
            x0=packet_x-0.1, y0=0.4, x1=packet_x+0.1, y1=0.6,
            fillcolor="red",
            line=dict(color="darkred", width=2)
        )
        fig.add_annotation(
            x=packet_x, y=0.5,
            text="📦",
            showarrow=False,
            font=dict(size=20)
        )
    
    fig.update_layout(
        title="ネットワーク通信",
        title_x=0.5,
        xaxis=dict(range=[-0.5, 5.5], showgrid=False, showticklabels=False),
        yaxis=dict(range=[-0.5, 1.5], showgrid=False, showticklabels=False),
        width=600,
        height=200,
        showlegend=False,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    return fig

def simulate_encapsulation(protocol: str, message: str):
    """カプセル化プロセスのシミュレーション"""
    add_log(f"[アプリケーション層] データ '{message}' を生成しました。")
    time.sleep(1)
    
    if protocol == "TCP":
        add_log("[トランスポート層] TCPヘッダを付与し、セグメントを生成しました。")
        headers = ['tcp']
    else:
        add_log("[トランスポート層] UDPヘッダを付与し、セグメントを生成しました。")
        headers = ['udp']
    
    time.sleep(1)
    add_log("[インターネット層] IPヘッダを付与し、パケットを生成しました。")
    headers.append('ip')
    
    time.sleep(1)
    add_log("[ネットワークインターフェース層] Ethernetヘッダを付与し、フレームを生成しました。")
    headers.append('ethernet')
    
    time.sleep(1)
    add_log("[通信中] Client > Server : フレームを送信中です...")
    
    return headers

def simulate_decapsulation(headers: List[str]):
    """非カプセル化プロセスのシミュレーション"""
    add_log("[ネットワークインターフェース層] サーバがフレームを受信。Ethernetヘッダを分離します。")
    time.sleep(1)
    
    add_log("[インターネット層] IPヘッダを分離します。")
    time.sleep(1)
    
    if 'tcp' in headers:
        add_log("[トランスポート層] TCPヘッダを分離します。")
    else:
        add_log("[トランスポート層] UDPヘッダを分離します。")
    time.sleep(1)
    
    add_log("[アプリケーション層] 元のデータが復元されました。")

# メインUI
st.markdown("## 📚 TCP/IP階層モデルとプロトコル学習")

# コントロールエリア
col1, col2, col3, col4 = st.columns([2, 2, 2, 2])

with col1:
    protocol = st.selectbox("プロトコル選択", ["TCP", "UDP"], help="TCPは信頼性重視、UDPは速度重視のプロトコルです")

with col2:
    message = st.text_input("送信メッセージ", "Hello World!", help="送信するデータを入力してください")

with col3:
    if st.button("シミュレーション開始", disabled=st.session_state.animation_state == 'running'):
        st.session_state.animation_state = 'running'
        st.session_state.current_step = 0
        st.session_state.communication_logs = []
        st.session_state.packet_data = {
            'protocol': protocol,
            'message': message,
            'headers': []
        }

with col4:
    trouble_rate = st.slider("トラブル発生率", 0, 100, 10, help="パケットロスやエラーの発生確率")

# プロトコル説明
st.markdown("### 🔍 プロトコルの特徴")

if protocol == "TCP":
    st.info("""
    **TCP (Transmission Control Protocol)**
    - 🔒 **信頼性**: データの到達保証、順序保証
    - 🔄 **接続指向**: 3-way handshakeで接続確立
    - 📊 **フロー制御**: 受信側の処理能力に応じた制御
    - 🛡️ **エラー検出・再送**: チェックサムとACKによる確実な配送
    - ⚠️ **オーバーヘッド**: ヘッダサイズが大きく、処理が重い
    """)
else:
    st.info("""
    **UDP (User Datagram Protocol)**
    - ⚡ **高速**: 最小限のオーバーヘッド
    - 📡 **コネクションレス**: 接続確立不要
    - 🎯 **シンプル**: エラー検出のみ（再送なし）
    - 📱 **リアルタイム向け**: 動画・音声ストリーミングに最適
    - ⚠️ **信頼性なし**: データ欠損の可能性あり
    """)

# ビジュアライゼーションエリア
st.markdown("### 🎬 通信プロセスの可視化")

viz_col1, viz_col2, viz_col3 = st.columns([1, 1, 1])

with viz_col1:
    # クライアント側の階層表示
    if st.session_state.animation_state == 'running':
        if st.session_state.current_step < 4:
            layer_keys = list(LAYERS.keys())
            current_layer = layer_keys[st.session_state.current_step]
            headers = st.session_state.packet_data.get('headers', [])
            client_fig = create_layer_visualization("クライアント", current_layer, headers)
        else:
            client_fig = create_layer_visualization("クライアント")
    else:
        client_fig = create_layer_visualization("クライアント")
    
    st.plotly_chart(client_fig, use_container_width=True)

with viz_col2:
    # ネットワーク通信の表示
    network_fig = create_network_animation()
    st.plotly_chart(network_fig, use_container_width=True)

with viz_col3:
    # サーバー側の階層表示
    if st.session_state.animation_state == 'running':
        if st.session_state.current_step >= 5:
            layer_keys = list(LAYERS.keys())
            server_step = st.session_state.current_step - 5
            if server_step < 4:
                current_layer = layer_keys[3-server_step]  # 逆順
                headers = st.session_state.packet_data.get('headers', [])[:3-server_step]
                server_fig = create_layer_visualization("サーバー", current_layer, headers)
            else:
                server_fig = create_layer_visualization("サーバー")
        else:
            server_fig = create_layer_visualization("サーバー")
    else:
        server_fig = create_layer_visualization("サーバー")
    
    st.plotly_chart(server_fig, use_container_width=True)

# アニメーション制御
if st.session_state.animation_state == 'running':
    if st.session_state.current_step == 0:
        st.session_state.packet_data['headers'] = simulate_encapsulation(protocol, message)
        st.session_state.current_step = 4
        st.session_state.animation_state = 'transmitting'
        time.sleep(2)
        st.rerun()
    elif st.session_state.animation_state == 'transmitting':
        st.session_state.current_step += 1
        if st.session_state.current_step >= 10:
            st.session_state.animation_state = 'receiving'
            st.session_state.current_step = 5
        time.sleep(0.5)
        st.rerun()
    elif st.session_state.animation_state == 'receiving':
        if st.session_state.current_step == 5:
            simulate_decapsulation(st.session_state.packet_data['headers'])
            st.session_state.current_step = 9
            st.session_state.animation_state = 'completed'
        time.sleep(1)
        st.rerun()
    elif st.session_state.animation_state == 'completed':
        st.session_state.animation_state = 'stopped'
        st.success("✅ 通信が完了しました！")
        st.rerun()

# ヘッダ情報表示
st.markdown("### 📋 プロトコルヘッダ情報")

header_tabs = st.tabs(["TCP", "UDP", "IP", "Ethernet"])

with header_tabs[0]:
    st.markdown("#### TCPヘッダの構造")
    tcp_info = HEADER_INFO['tcp']
    for field, value in tcp_info['fields'].items():
        st.markdown(f"- **{field}**: `{value}`")

with header_tabs[1]:
    st.markdown("#### UDPヘッダの構造")
    udp_info = HEADER_INFO['udp']
    for field, value in udp_info['fields'].items():
        st.markdown(f"- **{field}**: `{value}`")

with header_tabs[2]:
    st.markdown("#### IPヘッダの構造")
    ip_info = HEADER_INFO['ip']
    for field, value in ip_info['fields'].items():
        st.markdown(f"- **{field}**: `{value}`")

with header_tabs[3]:
    st.markdown("#### Ethernetヘッダの構造")
    eth_info = HEADER_INFO['ethernet']
    for field, value in eth_info['fields'].items():
        st.markdown(f"- **{field}**: `{value}`")

# ログ表示エリア
with st.expander("▼ 通信ログを見る", expanded=True):
    if st.session_state.communication_logs:
        for log in st.session_state.communication_logs[-10:]:  # 最新10件を表示
            st.text(log)
    else:
        st.text("シミュレーションを開始すると、通信ログが表示されます。")

# リセットボタン
if st.button("🔄 リセット"):
    st.session_state.communication_logs = []
    st.session_state.animation_state = 'stopped'
    st.session_state.current_step = 0
    st.session_state.packet_data = {}
    st.rerun()

# フッター情報
st.markdown("---")
st.markdown("""
### 📖 学習のポイント

**カプセル化 (Encapsulation)**
- データが送信側で各階層を下向きに通過する際、各層で専用のヘッダが付与される
- アプリケーション → トランスポート → インターネット → ネットワークインターフェース

**非カプセル化 (Decapsulation)**
- データが受信側で各階層を上向きに通過する際、各層でヘッダが取り除かれる
- ネットワークインターフェース → インターネット → トランスポート → アプリケーション

**TCP vs UDP**
- TCP: 信頼性重視（ファイル転送、Webブラウジング）
- UDP: 速度重視（動画配信、オンラインゲーム）
""")