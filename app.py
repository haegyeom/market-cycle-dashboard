import streamlit as st
import pandas as pd
import yfinance as yf
from fredapi import Fred
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 설정 및 API 연결
import os
FRED_API_KEY = st.secrets["FRED_API_KEY"]
fred = Fred(api_key=FRED_API_KEY)

st.set_page_config(page_title="Market Cycle Intelligence", layout="wide")

# --- UI 섹션: 헤더 및 슬로건 ---
st.title("🏛️ Market Cycle Intelligence")
st.subheader("시장은 가격이 아니라 '시스템'으로 움직입니다.")
st.markdown("""
본 대시보드는 단순한 주가 추종을 넘어 **트럭 판매량, 일본 금리, 신용융자 잔고, 버핏 지수**라는 4대 축을 통해 
현재 시장이 사이클의 어느 지점에 위치해 있는지 입체적으로 진단합니다.
""")

@st.cache_data
def load_data():
    try:
        data_map = {
            'Truck_Sales': 'HTRUCKSSAAR',      # 트럭 판매량 (K Units)
            'JPY_Rate': 'IRSTCI01JPM156N',     # 일본 금리 (%)
            'Margin_Debt': 'BOGZ1FL663067003Q',# 신용융자 잔고 ($ Millions)
            'GDP': 'GDP'                       # 버핏 지수 산출용 ($ Billions)
        }
        fetched = {name: fred.get_series(s_id, observation_start='2000-01-01') for name, s_id in data_map.items()}
        sp500 = yf.download('^GSPC', start='2000-01-01')['Close']
        
        df = pd.DataFrame(fetched)
        # yfinance 데이터 구조 대응
        df['SP500'] = sp500 if not isinstance(sp500, pd.DataFrame) else sp500.iloc[:, 0]
        df = df.ffill().bfill().dropna()
        
        # 버핏 지수 계산 (원본 비율)
        df['Buffett_Indicator'] = (df['SP500'] / df['GDP'])
        return df
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
        return None

df = load_data()

if df is not None:
    # --- 가이드 섹션: 인터랙티브 조작법 ---
    with st.expander("💡 대시보드 활용 및 인터랙티브 분석 가이드", expanded=True):
        st.markdown("""
        **1. 포커스 분석 (Legend Toggle)**
        - 차트 상단의 범례(Legend)를 클릭해 보세요. 특정 지표를 **숨기거나 다시 활성화**할 수 있습니다.
        - **활용 예:** 'S&P 500'과 '신용융자 잔고'만 켜두고 대조해 보면, 현재의 상승이 실물 경제에 기반한 것인지 아니면 과도한 레버리지에 의한 버블인지 직관적으로 파악할 수 있습니다.
        
        **2. 데이터 정밀 대조**
        - 차트 위에 마우스를 올리면 특정 시점의 모든 지표 수치가 동시에 표시됩니다.
        - 하단의 **원본 데이터 리포트**를 통해 차트에서 확인한 변곡점의 정확한 수치를 확정적으로 체크할 수 있습니다.
        """)

    # 1.5 통합 차트 (다중 Y축)
    st.divider()
    st.subheader("🌟 5대 핵심 지표 통합 추세 (Original Context)")
    st.markdown("지표별 고유 단위를 유지한 상태에서 다중 Y축을 통해 시장의 전반적인 에너지 흐름을 관찰합니다.")
    
    fig_integrated = go.Figure()
    # 세련된 지표명 정의
    colors = {'SP500': '#FFD700', 'Buffett_Indicator': '#00BFFF', 'Margin_Debt': '#FF8C00', 'Truck_Sales': '#00CC96', 'JPY_Rate': '#EF553B'}
    names = {
        'SP500': 'S&P 500', 
        'Buffett_Indicator': '버핏 지수', 
        'Margin_Debt': '신용융자 잔고', 
        'Truck_Sales': '트럭 판매량', 
        'JPY_Rate': '일본 금리'
    }
    
    fig_integrated.add_trace(go.Scatter(x=df.index, y=df['SP500'], name=names['SP500'], line=dict(color=colors['SP500'], width=3), yaxis="y1"))
    fig_integrated.add_trace(go.Scatter(x=df.index, y=df['Buffett_Indicator'], name=names['Buffett_Indicator'], line=dict(color=colors['Buffett_Indicator'], width=2), yaxis="y2"))
    fig_integrated.add_trace(go.Scatter(x=df.index, y=df['Margin_Debt'], name=names['Margin_Debt'], line=dict(color=colors['Margin_Debt'], width=2, dash='dot'), yaxis="y3"))
    fig_integrated.add_trace(go.Scatter(x=df.index, y=df['Truck_Sales'], name=names['Truck_Sales'], line=dict(color=colors['Truck_Sales'], width=2), yaxis="y4"))
    fig_integrated.add_trace(go.Scatter(x=df.index, y=df['JPY_Rate'], name=names['JPY_Rate'], line=dict(color=colors['JPY_Rate'], width=2, dash='dash'), yaxis="y5"))
    
    fig_integrated.update_layout(
        height=700,
        template="plotly_dark",
        hovermode="x unified",
        xaxis=dict(domain=[0.1, 0.8], title="Timeline"),
        yaxis=dict(title="S&P 500 (USD)", title_font=dict(color=colors['SP500']), tickfont=dict(color=colors['SP500']), side="left"),
        yaxis2=dict(title="Buffett Ratio", title_font=dict(color=colors['Buffett_Indicator']), tickfont=dict(color=colors['Buffett_Indicator']), anchor="free", overlaying="y", side="left", position=0.0),
        yaxis3=dict(title="Margin Debt ($M)", title_font=dict(color=colors['Margin_Debt']), tickfont=dict(color=colors['Margin_Debt']), anchor="x", overlaying="y", side="right"),
        yaxis4=dict(title="Truck Sales (K)", title_font=dict(color=colors['Truck_Sales']), tickfont=dict(color=colors['Truck_Sales']), anchor="free", overlaying="y", side="right", position=0.9),
        yaxis5=dict(title="JPY Rate (%)", title_font=dict(color=colors['JPY_Rate']), tickfont=dict(color=colors['JPY_Rate']), anchor="free", overlaying="y", side="right", position=1.0),
        legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="center", x=0.45)
    )
    st.plotly_chart(fig_integrated, use_container_width=True)

    # 2. 서브플롯 섹션
    st.divider()
    st.subheader("📐 영역별 수직 계층 분석 (Structural Subplots)")
    st.markdown("동일한 시간축 위에서 각 영역별 독립적 추세를 정밀 분석합니다.")

    fig_sub = make_subplots(
        rows=5, cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.03,
        subplot_titles=(names['SP500'], names['Buffett_Indicator'], names['Margin_Debt'], names['Truck_Sales'], names['JPY_Rate'])
    )

    fig_sub.add_trace(go.Scatter(x=df.index, y=df['SP500'], name="S&P 500", line=dict(color=colors['SP500'], width=2)), row=1, col=1)
    fig_sub.add_trace(go.Scatter(x=df.index, y=df['Buffett_Indicator'], name="버핏 지수", line=dict(color=colors['Buffett_Indicator'], width=2)), row=2, col=1)
    fig_sub.add_trace(go.Scatter(x=df.index, y=df['Margin_Debt'], name="신용융자 잔고", line=dict(color=colors['Margin_Debt'], width=2)), row=3, col=1)
    fig_sub.add_trace(go.Scatter(x=df.index, y=df['Truck_Sales'], name="트럭 판매량", line=dict(color=colors['Truck_Sales'], width=2)), row=4, col=1)
    fig_sub.add_trace(go.Scatter(x=df.index, y=df['JPY_Rate'], name="일본 금리", line=dict(color=colors['JPY_Rate'], width=2)), row=5, col=1)

    fig_sub.update_layout(height=1100, template="plotly_dark", hovermode="x unified", showlegend=False)
    
    # Y축 단위 표기
    fig_sub.update_yaxes(title_text="USD ($)", row=1, col=1)
    fig_sub.update_yaxes(title_text="Ratio", row=2, col=1)
    fig_sub.update_yaxes(title_text="Millions ($)", row=3, col=1)
    fig_sub.update_yaxes(title_text="K Units", row=4, col=1)
    fig_sub.update_yaxes(title_text="Percent (%)", row=5, col=1)

    st.plotly_chart(fig_sub, use_container_width=True)

    # 4. 데이터 요약 테이블
    st.divider()
    st.subheader("📋 정밀 데이터 리포트 (Raw Data Insight)")
    st.markdown("차트상의 추세를 실제 수치로 확정하기 위한 최근 상세 리포트입니다.")
    
    # 가독성을 위해 컬럼명 변경 및 반올림 처리
    display_df = df[['SP500', 'Buffett_Indicator', 'Margin_Debt', 'Truck_Sales', 'JPY_Rate']].tail(20).copy()
    display_df.columns = ['S&P 500 ($)', '버핏 지수 (Ratio)', '신용융자 잔고 ($M)', '트럭 판매량 (K)', '일본 금리 (%)']
    
    st.dataframe(
        display_df.sort_index(ascending=False).style.format("{:,.2f}"), 
        use_container_width=True
    )

else:
    st.warning("데이터 엔진 가동 중... 잠시만 기다려주세요.")