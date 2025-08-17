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
if 'selected_header' not in st.session_state:
    st.session_state.selected_header = None
if 'animation_speed' not in st.session_state:
    st.session_state.animation_speed = 1.0
if 'show_details' not in st.session_state:
    st.session_state.show_details = False
if 'packet_size' not in st.session_state:
    st.session_state.packet_size = 0

# TCP/IP階層モデルの定義
LAYERS = {
    'application': {'name': 'アプリケーション層', 'color': '#FF6B6B', 'example': 'HTTP', 'short_name': 'アプリ層'},
    'transport': {'name': 'トランスポート層', 'color': '#4ECDC4', 'example': 'TCP/UDP', 'short_name': 'トランスポート層'},
    'internet': {'name': 'インターネット層', 'color': '#45B7D1', 'example': 'IP', 'short_name': 'インターネット層'},
    'network_interface': {'name': 'ネットワークインターフェース層', 'color': '#96CEB4', 'example': 'Ethernet', 'short_name': 'NW I/F層'}
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

def calculate_packet_size(protocol: str, message: str) -> Dict[str, int]:
    """パケットサイズを計算する"""
    data_size = len(message.encode('utf-8'))
    
    sizes = {
        'data': data_size,
        'tcp': 20 if protocol == 'TCP' else 0,
        'udp': 8 if protocol == 'UDP' else 0,
        'ip': 20,
        'ethernet': 18  # 14 + 4 (FCS)
    }
    
    total_size = data_size
    if protocol == 'TCP':
        total_size += sizes['tcp']
    else:
        total_size += sizes['udp']
    total_size += sizes['ip'] + sizes['ethernet']
    
    sizes['total'] = total_size
    return sizes

def get_protocol_efficiency(protocol: str, message: str) -> float:
    """プロトコル効率を計算する"""
    sizes = calculate_packet_size(protocol, message)
    data_size = sizes['data']
    total_size = sizes['total']
    return (data_size / total_size) * 100 if total_size > 0 else 0

def create_layer_visualization(side: str, data_position: str = None, headers: List[str] = None, highlight_layer: str = None) -> go.Figure:
    """階層モデルの可視化を作成"""
    fig = go.Figure()
    
    # 基本の階層ボックスを描画
    layer_keys = list(LAYERS.keys())
    y_positions = [3, 2, 1, 0]  # 上から下へ
    
    for i, (layer_key, y) in enumerate(zip(layer_keys, y_positions)):
        layer = LAYERS[layer_key]
        
        # 階層ボックス（ハイライト効果付き）
        opacity = 0.7 if highlight_layer == layer_key else 0.3
        line_width = 4 if highlight_layer == layer_key else 2
        
        fig.add_shape(
            type="rect",
            x0=0, y0=y, x1=2, y1=y+0.8,
            fillcolor=layer['color'],
            opacity=opacity,
            line=dict(color=layer['color'], width=line_width)
        )
        
        # 階層名とプロトコル例（短縮名を使用）
        fig.add_annotation(
            x=1, y=y+0.4,
            text=f"{layer['short_name']}<br>({layer['example']})",
            showarrow=False,
            font=dict(size=11, color="black"),
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
        
        # ヘッダーブロック（クリック可能な効果付き）
        for i, header in enumerate(headers):
            header_info = HEADER_INFO.get(header)
            if header_info:
                # 選択されたヘッダーをハイライト
                border_color = "red" if st.session_state.selected_header == header else "black"
                border_width = 3 if st.session_state.selected_header == header else 1
                
                fig.add_shape(
                    type="rect",
                    x0=1.5-i*0.3, y0=y+0.1, x1=2.1-i*0.3, y1=y+0.7,
                    fillcolor=header_info['color'],
                    opacity=0.8,
                    line=dict(color=border_color, width=border_width)
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
    delay = 1.0 / st.session_state.animation_speed
    
    add_log(f"[アプリケーション層] データ '{message}' を生成しました。")
    time.sleep(delay)
    
    if protocol == "TCP":
        add_log("[トランスポート層] TCPヘッダを付与し、セグメントを生成しました。")
        headers = ['tcp']
    else:
        add_log("[トランスポート層] UDPヘッダを付与し、セグメントを生成しました。")
        headers = ['udp']
    
    time.sleep(delay)
    add_log("[インターネット層] IPヘッダを付与し、パケットを生成しました。")
    headers.append('ip')
    
    time.sleep(delay)
    add_log("[ネットワークインターフェース層] Ethernetヘッダを付与し、フレームを生成しました。")
    headers.append('ethernet')
    
    time.sleep(delay)
    add_log("[通信中] Client > Server : フレームを送信中です...")
    
    return headers

def simulate_decapsulation(headers: List[str]):
    """非カプセル化プロセスのシミュレーション"""
    delay = 1.0 / st.session_state.animation_speed
    
    add_log("[ネットワークインターフェース層] サーバがフレームを受信。Ethernetヘッダを分離します。")
    time.sleep(delay)
    
    add_log("[インターネット層] IPヘッダを分離します。")
    time.sleep(delay)
    
    if 'tcp' in headers:
        add_log("[トランスポート層] TCPヘッダを分離します。")
    else:
        add_log("[トランスポート層] UDPヘッダを分離します。")
    time.sleep(delay)
    
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
    animation_speed = st.slider("アニメーション速度", 0.5, 3.0, 1.0, 0.5, help="アニメーションの再生速度")
    st.session_state.animation_speed = animation_speed

# リアルタイムメトリクス表示
if message:
    sizes = calculate_packet_size(protocol, message)
    efficiency = get_protocol_efficiency(protocol, message)
    
    metrics_col1, metrics_col2, metrics_col3, metrics_col4 = st.columns(4)
    
    with metrics_col1:
        st.metric("データサイズ", f"{sizes['data']} bytes", help="実際のメッセージのサイズ")
    
    with metrics_col2:
        header_size = sizes['tcp'] + sizes['udp'] + sizes['ip'] + sizes['ethernet']
        st.metric("ヘッダサイズ", f"{header_size} bytes", help="プロトコルヘッダの合計サイズ")
    
    with metrics_col3:
        st.metric("総パケットサイズ", f"{sizes['total']} bytes", help="送信される全体のサイズ")
    
    with metrics_col4:
        st.metric("効率", f"{efficiency:.1f}%", 
                 delta=f"{efficiency - 50:.1f}%" if efficiency != 50 else None,
                 help="データサイズ / 総サイズの割合")

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
        time.sleep(0.5 / st.session_state.animation_speed)
        st.rerun()
    elif st.session_state.animation_state == 'receiving':
        if st.session_state.current_step == 5:
            simulate_decapsulation(st.session_state.packet_data['headers'])
            st.session_state.current_step = 9
            st.session_state.animation_state = 'completed'
        time.sleep(1.0 / st.session_state.animation_speed)
        st.rerun()
    elif st.session_state.animation_state == 'completed':
        st.session_state.animation_state = 'stopped'
        st.success("✅ 通信が完了しました！")
        st.rerun()

# インタラクティブなヘッダ情報表示
st.markdown("### 📋 プロトコルヘッダ情報")

header_col1, header_col2 = st.columns([1, 2])

with header_col1:
    st.markdown("#### ヘッダを選択:")
    if st.button("🔵 TCPヘッダ", key="tcp_btn"):
        st.session_state.selected_header = 'tcp'
    if st.button("🔵 UDPヘッダ", key="udp_btn"):
        st.session_state.selected_header = 'udp'
    if st.button("🟢 IPヘッダ", key="ip_btn"):
        st.session_state.selected_header = 'ip'
    if st.button("🟤 Ethernetヘッダ", key="eth_btn"):
        st.session_state.selected_header = 'ethernet'
    
    if st.button("🔄 選択解除"):
        st.session_state.selected_header = None

with header_col2:
    if st.session_state.selected_header:
        selected_info = HEADER_INFO[st.session_state.selected_header]
        st.markdown(f"#### {selected_info['name']}の詳細構造")
        
        # ヘッダサイズ情報を追加
        if st.session_state.selected_header == 'tcp':
            st.info("**サイズ**: 20-60 bytes (オプション含む)")
        elif st.session_state.selected_header == 'udp':
            st.info("**サイズ**: 8 bytes (固定)")
        elif st.session_state.selected_header == 'ip':
            st.info("**サイズ**: 20-60 bytes (オプション含む)")
        elif st.session_state.selected_header == 'ethernet':
            st.info("**サイズ**: 18 bytes (ヘッダ14 + FCS4)")
        
        for field, value in selected_info['fields'].items():
            st.markdown(f"- **{field}**: `{value}`")
    else:
        st.markdown("#### ヘッダを選択すると詳細が表示されます")
        st.markdown("左のボタンから確認したいヘッダを選択してください。")

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

# プロトコル比較学習
st.markdown("---")
st.markdown("### 🔬 プロトコル比較学習")

compare_col1, compare_col2 = st.columns(2)

with compare_col1:
    st.markdown("#### TCP vs UDP 効率比較")
    if message:
        tcp_sizes = calculate_packet_size('TCP', message)
        udp_sizes = calculate_packet_size('UDP', message)
        tcp_efficiency = get_protocol_efficiency('TCP', message)
        udp_efficiency = get_protocol_efficiency('UDP', message)
        
        comparison_data = pd.DataFrame({
            'プロトコル': ['TCP', 'UDP'],
            'ヘッダサイズ (bytes)': [tcp_sizes['tcp'] + tcp_sizes['ip'] + tcp_sizes['ethernet'], 
                                   udp_sizes['udp'] + udp_sizes['ip'] + udp_sizes['ethernet']],
            '総サイズ (bytes)': [tcp_sizes['total'], udp_sizes['total']],
            '効率 (%)': [tcp_efficiency, udp_efficiency]
        })
        
        st.dataframe(comparison_data, use_container_width=True)
        
        # 効率比較グラフ
        fig_comparison = px.bar(comparison_data, x='プロトコル', y='効率 (%)', 
                               title='プロトコル効率比較',
                               color='プロトコル',
                               color_discrete_map={'TCP': '#4ECDC4', 'UDP': '#FF6B6B'})
        st.plotly_chart(fig_comparison, use_container_width=True)

with compare_col2:
    st.markdown("#### メッセージ長による効率変化")
    
    test_messages = ["Hi", "Hello World!", "これは長いメッセージの例です。ネットワークプロトコルの効率を測定します。"]
    efficiency_data = []
    
    for msg in test_messages:
        tcp_eff = get_protocol_efficiency('TCP', msg)
        udp_eff = get_protocol_efficiency('UDP', msg)
        efficiency_data.append({
            'メッセージ長': len(msg),
            'TCP効率': tcp_eff,
            'UDP効率': udp_eff
        })
    
    efficiency_df = pd.DataFrame(efficiency_data)
    
    fig_efficiency = go.Figure()
    fig_efficiency.add_trace(go.Scatter(
        x=efficiency_df['メッセージ長'],
        y=efficiency_df['TCP効率'],
        mode='lines+markers',
        name='TCP',
        line=dict(color='#4ECDC4', width=3)
    ))
    fig_efficiency.add_trace(go.Scatter(
        x=efficiency_df['メッセージ長'],
        y=efficiency_df['UDP効率'],
        mode='lines+markers',
        name='UDP',
        line=dict(color='#FF6B6B', width=3)
    ))
    
    fig_efficiency.update_layout(
        title='メッセージ長と効率の関係',
        xaxis_title='メッセージ長 (文字)',
        yaxis_title='効率 (%)',
        height=300
    )
    
    st.plotly_chart(fig_efficiency, use_container_width=True)

# 学習のポイント
st.markdown("### 📖 学習のポイント")

point_col1, point_col2 = st.columns(2)

with point_col1:
    st.markdown("""
    **カプセル化 (Encapsulation)**
    - データが送信側で各階層を下向きに通過する際、各層で専用のヘッダが付与される
    - アプリケーション → トランスポート → インターネット → ネットワークインターフェース
    
    **非カプセル化 (Decapsulation)**
    - データが受信側で各階層を上向きに通過する際、各層でヘッダが取り除かれる
    - ネットワークインターフェース → インターネット → トランスポート → アプリケーション
    """)

with point_col2:
    st.markdown("""
    **TCP vs UDP の使い分け**
    - **TCP**: 信頼性重視（Webブラウジング、ファイル転送、メール）
    - **UDP**: 速度重視（動画配信、オンラインゲーム、DNS）
    
    **効率に関する重要なポイント**
    - 短いメッセージではヘッダのオーバーヘッドが大きい
    - 長いメッセージでは効率が向上する
    - アプリケーションの要件に応じて適切なプロトコルを選択
    """)