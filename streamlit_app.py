import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import time
import random
from typing import Dict, List, Tuple

st.set_page_config(
    page_title="通信プロトコル",
    page_icon="🌐",
    layout="wide"
)

st.title("通信プロトコル（pp.115-116）")
st.caption("Created by Dit-Lab.(Daiki ITO)")
st.caption("Supported by Tomoaki ATSUMI")

st.markdown("""
### 📖 このアプリについて
インターネットでメッセージを送るとき、実は4つの段階に分けて処理されています。
手紙を送るときに封筒に入れて住所を書くように、データにも「住所」や「送り方の指示」が付けられます。
このアプリでは、その様子をアニメーションで見ることができます！
""")

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
        
        # 階層名とプロトコル例
        fig.add_annotation(
            x=1, y=y+0.4,
            text=f"{layer['name']}<br>({layer['example']})",
            showarrow=False,
            font=dict(size=9, color="black"),
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
        width=450,
        height=450,
        showlegend=False,
        margin=dict(l=30, r=30, t=50, b=30)
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
    """メッセージを送信パッケージに包装するプロセス"""
    delay = 1.0 / st.session_state.animation_speed
    
    add_log(f"[アプリケーション層] メッセージ '{message}' を準備しました。")
    time.sleep(delay)
    
    if protocol == "TCP":
        add_log("[トランスポート層] 送信方法の情報を付けました（TCP：確実に届ける）")
        headers = ['tcp']
    else:
        add_log("[トランスポート層] 送信方法の情報を付けました（UDP：速く送る）")
        headers = ['udp']
    
    time.sleep(delay)
    add_log("[インターネット層] インターネット上の住所を付けました（どこに送るか）")
    headers.append('ip')
    
    time.sleep(delay)
    add_log("[ネットワークインターフェース層] 最終的な配達用ラベルを付けました")
    headers.append('ethernet')
    
    time.sleep(delay)
    add_log("[送信中] 送信者 → 受信者 : パッケージを送信中です...")
    
    return headers

def simulate_decapsulation(headers: List[str]):
    """受信したパッケージからメッセージを取り出すプロセス"""
    delay = 1.0 / st.session_state.animation_speed
    
    add_log("[ネットワークインターフェース層] 受信者がパッケージを受け取りました。配達ラベルを外します。")
    time.sleep(delay)
    
    add_log("[インターネット層] インターネット住所のラベルを外します。")
    time.sleep(delay)
    
    if 'tcp' in headers:
        add_log("[トランスポート層] 送信方法の情報を外します（TCP）")
    else:
        add_log("[トランスポート層] 送信方法の情報を外します（UDP）")
    time.sleep(delay)
    
    add_log("[アプリケーション層] 元のメッセージを取り出しました！")

# メインUI
st.markdown("## 📚 インターネット通信の4つの階層")

# コントロールエリア
col1, col2, col3, col4 = st.columns([2, 2, 2, 2])

with col1:
    protocol = st.selectbox("送信方法を選択", ["TCP", "UDP"], 
                           help="TCP＝確実に届ける（書留郵便みたい）、UDP＝速く送る（普通郵便みたい）")

with col2:
    message = st.text_input("送りたいメッセージ", "Hello World!", help="友達に送りたいメッセージを入力してください")

with col3:
    if st.button("🚀 送信スタート！", disabled=st.session_state.animation_state == 'running'):
        st.session_state.animation_state = 'running'
        st.session_state.current_step = 0
        st.session_state.communication_logs = []
        st.session_state.packet_data = {
            'protocol': protocol,
            'message': message,
            'headers': []
        }

with col4:
    animation_speed = st.slider("再生速度", 0.5, 3.0, 1.0, 0.5, help="アニメーションの速さを調整できます")
    st.session_state.animation_speed = animation_speed

# リアルタイムメトリクス表示
if message:
    sizes = calculate_packet_size(protocol, message)
    efficiency = get_protocol_efficiency(protocol, message)
    
    metrics_col1, metrics_col2, metrics_col3, metrics_col4 = st.columns(4)
    
    with metrics_col1:
        st.metric("📝 メッセージサイズ", f"{sizes['data']} bytes", help="実際に送りたいメッセージの大きさ")
    
    with metrics_col2:
        header_size = sizes['tcp'] + sizes['udp'] + sizes['ip'] + sizes['ethernet']
        st.metric("📋 住所ラベルサイズ", f"{header_size} bytes", help="送り先や送り方の情報の大きさ")
    
    with metrics_col3:
        st.metric("📦 送信パッケージ全体", f"{sizes['total']} bytes", help="実際にインターネットを通る全体の大きさ")
    
    with metrics_col4:
        st.metric("💡 メッセージの割合", f"{efficiency:.1f}%", 
                 delta=f"{efficiency - 50:.1f}%" if efficiency != 50 else None,
                 help="全体のうち、実際のメッセージが占める割合")

# プロトコル説明
st.markdown("### 🔍 送信方法の違い")

if protocol == "TCP":
    st.info("""
    **TCP ＝ 「確実に届ける」方法（書留郵便みたい）**
    - 🔒 **確実性**: メッセージが必ず相手に届く、順番も正しい
    - 🔄 **事前確認**: 送る前に「今から送るよ」と相手に確認する
    - 📊 **速度調整**: 相手が忙しいときはゆっくり送る
    - 🛡️ **エラー対応**: 届かなかったら自動で再送信
    - ⚠️ **時間がかかる**: 確認作業が多いので少し遅い
    
    **使う場面**: ウェブサイト閲覧、ファイルダウンロード、メール送信
    """)
else:
    st.info("""
    **UDP ＝ 「速く送る」方法（普通郵便みたい）**
    - ⚡ **高速**: 余計な確認をしないのでとても速い
    - 📡 **シンプル**: 「送ったよ」だけ、相手の確認なし
    - 🎯 **軽量**: 最低限の情報だけで送信
    - 📱 **リアルタイム**: 動画や音声の配信に最適
    - ⚠️ **届かない場合もある**: たまにメッセージが消えることも
    
    **使う場面**: 動画視聴、オンラインゲーム、ライブ配信
    """)

# ビジュアライゼーションエリア
st.markdown("### 🎬 メッセージが送られる様子を見てみよう！")

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

# インタラクティブなラベル情報表示
st.markdown("### 📋 各段階で付けられる情報ラベル")

header_col1, header_col2 = st.columns([1, 2])

with header_col1:
    st.markdown("#### ラベルを選択:")
    if st.button("🔵 送信方法ラベル（TCP）", key="tcp_btn"):
        st.session_state.selected_header = 'tcp'
    if st.button("🔵 送信方法ラベル（UDP）", key="udp_btn"):
        st.session_state.selected_header = 'udp'
    if st.button("🟢 インターネット住所ラベル", key="ip_btn"):
        st.session_state.selected_header = 'ip'
    if st.button("🟤 配達用ラベル", key="eth_btn"):
        st.session_state.selected_header = 'ethernet'
    
    if st.button("🔄 選択解除"):
        st.session_state.selected_header = None

with header_col2:
    if st.session_state.selected_header:
        selected_info = HEADER_INFO[st.session_state.selected_header]
        
        # わかりやすい名前に変更
        friendly_names = {
            'tcp': '送信方法ラベル（TCP）',
            'udp': '送信方法ラベル（UDP）', 
            'ip': 'インターネット住所ラベル',
            'ethernet': '配達用ラベル'
        }
        
        st.markdown(f"#### {friendly_names[st.session_state.selected_header]}の詳細")
        
        # サイズ情報をわかりやすく
        if st.session_state.selected_header == 'tcp':
            st.info("**ラベルサイズ**: 20-60 bytes（確実に届けるための情報が多い）")
            st.markdown("**「確実に届ける」ために必要な情報:**")
        elif st.session_state.selected_header == 'udp':
            st.info("**ラベルサイズ**: 8 bytes（必要最小限の情報のみ）")
            st.markdown("**「速く送る」ために最小限の情報:**")
        elif st.session_state.selected_header == 'ip':
            st.info("**ラベルサイズ**: 20-60 bytes（インターネット上での配送情報）")
            st.markdown("**インターネット上で迷子にならないための情報:**")
        elif st.session_state.selected_header == 'ethernet':
            st.info("**ラベルサイズ**: 18 bytes（最終的な配達情報）")
            st.markdown("**最終的に相手に届けるための情報:**")
        
        for field, value in selected_info['fields'].items():
            st.markdown(f"- **{field}**: `{value}`")
    else:
        st.markdown("#### ラベルを選択すると詳細が表示されます")
        st.markdown("左のボタンから知りたいラベルを選択してください。")

# ログ表示エリア
with st.expander("▼ 送信の様子を詳しく見る", expanded=True):
    if st.session_state.communication_logs:
        for log in st.session_state.communication_logs[-10:]:  # 最新10件を表示
            st.text(log)
    else:
        st.text("「送信スタート！」ボタンを押すと、メッセージが送られる詳しい手順が表示されます。")

# リセットボタン
if st.button("🔄 リセット"):
    st.session_state.communication_logs = []
    st.session_state.animation_state = 'stopped'
    st.session_state.current_step = 0
    st.session_state.packet_data = {}
    st.rerun()

# プロトコル比較学習
st.markdown("---")
st.markdown("### 🔬 TCPとUDPを比較してみよう")

compare_col1, compare_col2 = st.columns(2)

with compare_col1:
    st.markdown("#### どちらが効率的？")
    if message:
        tcp_sizes = calculate_packet_size('TCP', message)
        udp_sizes = calculate_packet_size('UDP', message)
        tcp_efficiency = get_protocol_efficiency('TCP', message)
        udp_efficiency = get_protocol_efficiency('UDP', message)
        
        comparison_data = pd.DataFrame({
            '送信方法': ['TCP（確実）', 'UDP（高速）'],
            'ラベルサイズ (bytes)': [tcp_sizes['tcp'] + tcp_sizes['ip'] + tcp_sizes['ethernet'], 
                                   udp_sizes['udp'] + udp_sizes['ip'] + udp_sizes['ethernet']],
            '全体サイズ (bytes)': [tcp_sizes['total'], udp_sizes['total']],
            'メッセージ割合 (%)': [tcp_efficiency, udp_efficiency]
        })
        
        st.dataframe(comparison_data, use_container_width=True)
        
        # 効率比較グラフ
        fig_comparison = px.bar(comparison_data, x='送信方法', y='メッセージ割合 (%)', 
                               title='どちらがメッセージの割合が高い？',
                               color='送信方法',
                               color_discrete_map={'TCP（確実）': '#4ECDC4', 'UDP（高速）': '#FF6B6B'})
        st.plotly_chart(fig_comparison, use_container_width=True)

with compare_col2:
    st.markdown("#### メッセージが長いとどうなる？")
    
    test_messages = ["Hi", "Hello World!", "これは長いメッセージの例です。ネットワークプロトコルの効率を測定します。"]
    efficiency_data = []
    
    for msg in test_messages:
        tcp_eff = get_protocol_efficiency('TCP', msg)
        udp_eff = get_protocol_efficiency('UDP', msg)
        efficiency_data.append({
            'メッセージ長': len(msg),
            'TCP（確実）': tcp_eff,
            'UDP（高速）': udp_eff
        })
    
    efficiency_df = pd.DataFrame(efficiency_data)
    
    fig_efficiency = go.Figure()
    fig_efficiency.add_trace(go.Scatter(
        x=efficiency_df['メッセージ長'],
        y=efficiency_df['TCP（確実）'],
        mode='lines+markers',
        name='TCP（確実）',
        line=dict(color='#4ECDC4', width=3)
    ))
    fig_efficiency.add_trace(go.Scatter(
        x=efficiency_df['メッセージ長'],
        y=efficiency_df['UDP（高速）'],
        mode='lines+markers',
        name='UDP（高速）',
        line=dict(color='#FF6B6B', width=3)
    ))
    
    fig_efficiency.update_layout(
        title='メッセージが長いほど効率が良くなる！',
        xaxis_title='メッセージの長さ (文字数)',
        yaxis_title='メッセージの割合 (%)',
        height=300
    )
    
    st.plotly_chart(fig_efficiency, use_container_width=True)

# 学習のポイント
st.markdown("### 📖 覚えておこう！")

point_col1, point_col2 = st.columns(2)

with point_col1:
    st.markdown("""
    **🎁 メッセージの包装作業**
    - 送りたいメッセージに、送るための情報を段階的に付けていく
    - アプリ層 → 送信方法 → インターネット住所 → 配達ラベルの順
    
    **📦 受け取り時の開封作業**
    - 受信側では逆の順番でラベルを外していく
    - 配達ラベル → インターネット住所 → 送信方法 → 元のメッセージ
    
    **手紙を送るのと同じ仕組み！**
    """)

with point_col2:
    st.markdown("""
    **🚀 TCPとUDPの使い分け**
    - **TCP（確実）**: 絶対に届けたい重要なもの
      例：ウェブサイト、ファイルダウンロード、メール
    - **UDP（高速）**: 速さが重要で、たまに失敗してもOK
      例：YouTube動画、オンラインゲーム、ライブ配信
    
    **💡 面白い発見**
    - 短いメッセージほど「ラベル」の割合が大きい
    - 長いメッセージほど効率的になる
    - 実際のメッセージよりもラベルの方が大きいことがある！
    """)
