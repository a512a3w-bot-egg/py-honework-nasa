import streamlit as st
import requests
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime

# 網頁基本設定
st.set_page_config(page_title="NASA 3D 太空追蹤系統", layout="wide")
st.title("🌌 NASA 近地小行星 (NEO) 與 ISS 即時 3D 追蹤")
st.markdown("本專案使用 NASA Open Data 進行即時數據分析與 3D 視覺化。")

# --- 1. 取得資料的函數 ---

def get_iss_location():
    """取得 ISS 即時位置"""
    try:
        response = requests.get("http://api.open-notify.org/iss-now.json")
        data = response.json()
        lon = float(data['iss_position']['longitude'])
        lat = float(data['iss_position']['latitude'])
        return lon, lat
    except:
        return 0, 0

def get_asteroid_data():
    """取得今日近地小行星數據 (使用 NASA Demo Key)"""
    today = datetime.now().strftime('%Y-%m-%d')
    # 建議之後去 api.nasa.gov 申請自己的 Key 替換 DEMO_KEY
    url = f"https://api.nasa.gov/neo/rest/v1/feed?start_date={today}&end_date={today}&api_key=KETgR5I9vpaBcqRpTuk7DqFsPbKGJgMOUJs53J4r"
    try:
        response = requests.get(url)
        data = response.json()
        asteroids = data['near_earth_objects'][today]
        df_list = []
        for a in asteroids:
            df_list.append({
                "名稱": a['name'],
                "距離(km)": float(a['close_approach_data'][0]['miss_distance']['kilometers']),
                "直徑最大(m)": a['estimated_diameter']['meters']['estimated_diameter_max'],
                "是否有威脅": a['is_potentially_hazardous_asteroid']
            })
        return pd.DataFrame(df_list)
    except:
        return pd.DataFrame()

# --- 2. 座標轉換函數 (將經緯度/距離轉為 3D 座標) ---

def lat_lon_to_cartesian(lon, lat, r=1):
    """將經緯度轉換為 3D 空間的 XYZ 座標"""
    lon_rad = np.radians(lon)
    lat_rad = np.radians(lat)
    x = r * np.cos(lat_rad) * np.cos(lon_rad)
    y = r * np.cos(lat_rad) * np.sin(lon_rad)
    z = r * np.sin(lat_rad)
    return x, y, z

# --- 3. 繪製 3D 圖表 ---

st.sidebar.header("控制面板")
if st.sidebar.button("重新整理數據"):
    st.rerun()

# 取得數據
iss_lon, iss_lat = get_iss_location()
asteroid_df = get_asteroid_data()

# 建立 3D 圖形容器
fig = go.Figure()

# 繪製地球 (作為參考球體)
u, v = np.mgrid[0:2*np.pi:20j, 0:np.pi:10j]
x_earth = np.cos(u)*np.sin(v)
y_earth = np.sin(u)*np.sin(v)
z_earth = np.cos(v)
fig.add_trace(go.Surface(x=x_earth, y=y_earth, z=z_earth, colorscale='Blues', opacity=0.3, showscale=False, name="地球"))

# 繪製 ISS 位置 (稍微高於地表)
iss_x, iss_y, iss_z = lat_lon_to_cartesian(iss_lon, iss_lat, r=1.2)
fig.add_trace(go.Scatter3d(x=[iss_x], y=[iss_y], z=[iss_z], mode='markers+text', 
                         marker=dict(size=8, color='red'), text=["ISS 國際太空站"], name="ISS"))

# 繪製小行星 (距離地球較遠)
if not asteroid_df.empty:
    for _, row in asteroid_df.iterrows():
        # 為了視覺化效果，將距離縮小顯示，但保持相對關係
        # 小行星隨機分佈在球面上
        rand_lon = np.random.uniform(-180, 180)
        rand_lat = np.random.uniform(-90, 90)
        dist_scale = 2 + (row['距離(km)'] / 10000000) # 距離縮放比例
        ax, ay, az = lat_lon_to_cartesian(rand_lon, rand_lat, r=dist_scale)
        
        color = 'orange' if row['是否有威脅'] else 'green'
        fig.add_trace(go.Scatter3d(x=[ax], y=[ay], z=[az], mode='markers',
                                 marker=dict(size=5, color=color),
                                 hoverinfo='text',
                                 text=f"名稱: {row['名稱']}<br>距離: {row['距離(km)']:,.0f} km",
                                 name="小行星"))

# 設定圖表樣式
fig.update_layout(
    scene=dict(
        xaxis=dict(showbackground=False, visible=False),
        yaxis=dict(showbackground=False, visible=False),
        zaxis=dict(showbackground=False, visible=False),
        bgcolor="black"
    ),
    margin=dict(l=0, r=0, b=0, t=0),
    template="plotly_dark",
    height=700
)

# --- 4. 顯示網頁內容 ---

col1, col2 = st.columns([3, 1])

with col1:
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("📊 今日小行星列表")
    if not asteroid_df.empty:
        st.dataframe(asteroid_df[['名稱', '是否有威脅', '距離(km)']], use_container_width=True)
    else:
        st.warning("暫時無法取得 NASA 數據")
    
    st.info(f"🛰️ **ISS 當前位置**\n\n經度: {iss_lon}\n\n緯度: {iss_lat}")

st.markdown("---")
st.caption("數據來源: NASA NeoWs API & Open Notify ISS API")