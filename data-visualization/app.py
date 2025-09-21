#!/usr/bin/env python3
"""
Stock Market Data Visualization Service for microservices architecture.
Creates interactive stock market dashboards using Streamlit.
Communicates with Redis service over the network.
Displays real-time stock quotes, historical data, and technical indicators.
"""

import os
import sys
import time
import json
import glob
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import redis

# Configure Streamlit
st.set_page_config(
    page_title="Stock Market Analysis Pipeline - Microservices",
    page_icon="�",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration
REDIS_HOST = os.getenv('REDIS_HOST', 'redis-service')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
SHARED_DATA_PATH = os.getenv('SHARED_DATA_PATH', '/shared/data')

@st.cache_resource
def get_redis_connection():
    """Get Redis connection with caching."""
    try:
        client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5
        )
        client.ping()
        return client
    except redis.ConnectionError:
        st.error(f"Cannot connect to Redis at {REDIS_HOST}:{REDIS_PORT}")
        return None

@st.cache_data(ttl=30)  # Cache for 30 seconds
def get_service_status():
    """Get status of all services from Redis."""
    redis_client = get_redis_connection()
    if not redis_client:
        return {}
    
    try:
        statuses = {}
        
        # Get data ingest status
        ingest_status = redis_client.hgetall('data_ingest_status')
        if ingest_status:
            statuses['data_ingest'] = ingest_status
        
        # Get data clean status
        clean_status = redis_client.hgetall('data_clean_status')
        if clean_status:
            statuses['data_clean'] = clean_status
        
        return statuses
    except redis.RedisError as e:
        st.error(f"Redis error: {e}")
        return {}

@st.cache_data(ttl=60)  # Cache for 1 minute
def load_stock_data_files():
    """Load available stock data files from shared storage."""
    files_info = {
        'stock_quotes': [],
        'historical_data': [],
        'processed_quotes': [],
        'processed_historical': [],
        'summary_files': []
    }
    
    if not os.path.exists(SHARED_DATA_PATH):
        return files_info
    
    try:
        # Find raw stock quote files
        quote_files = glob.glob(os.path.join(SHARED_DATA_PATH, "stock_quotes_*.csv"))
        files_info['stock_quotes'] = sorted(quote_files, key=os.path.getmtime, reverse=True)
        
        # Find historical data files
        historical_files = glob.glob(os.path.join(SHARED_DATA_PATH, "stock_historical_*.csv"))
        files_info['historical_data'] = sorted(historical_files, key=os.path.getmtime, reverse=True)
        
        # Find processed quote files
        processed_quote_files = glob.glob(os.path.join(SHARED_DATA_PATH, "processed_quotes_*.csv"))
        files_info['processed_quotes'] = sorted(processed_quote_files, key=os.path.getmtime, reverse=True)
        
        # Find processed historical files
        processed_historical_files = glob.glob(os.path.join(SHARED_DATA_PATH, "processed_historical_*.csv"))
        files_info['processed_historical'] = sorted(processed_historical_files, key=os.path.getmtime, reverse=True)
        
        # Find summary files
        summary_files = glob.glob(os.path.join(SHARED_DATA_PATH, "*summary*.json"))
        files_info['summary_files'] = sorted(summary_files, key=os.path.getmtime, reverse=True)
        
    except Exception as e:
        st.error(f"Error loading files: {e}")
    
    return files_info

def load_dataframe(file_path):
    """Load a CSV file into a DataFrame."""
    try:
        return pd.read_csv(file_path)
    except Exception as e:
        st.error(f"Error loading {file_path}: {e}")
        return None

def load_json_file(file_path):
    """Load a JSON file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading {file_path}: {e}")
        return None

def create_stock_price_chart(df, symbol="Stock"):
    """Create a comprehensive stock price chart with technical indicators."""
    if df is None or df.empty:
        return None
    
    # Create subplots for price and volume
    fig = make_subplots(
        rows=3, cols=1,
        subplot_titles=(f'{symbol} Price Chart', 'Technical Indicators', 'Volume'),
        vertical_spacing=0.03,
        row_width=[0.6, 0.2, 0.2],
        specs=[[{"secondary_y": True}], [{"secondary_y": True}], [{}]]
    )
    
    # Main price chart
    if 'close' in df.columns and 'open' in df.columns and 'high' in df.columns and 'low' in df.columns:
        # Candlestick chart for historical data
        fig.add_trace(
            go.Candlestick(
                x=df.index if 'date' not in df.columns else pd.to_datetime(df['date']),
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'],
                name=f"{symbol} Price"
            ),
            row=1, col=1
        )
        
        # Add moving averages if available
        if 'sma_20' in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df.index if 'date' not in df.columns else pd.to_datetime(df['date']),
                    y=df['sma_20'],
                    mode='lines',
                    name='SMA 20',
                    line=dict(color='blue', width=2)
                ),
                row=1, col=1
            )
        
        if 'ema_12' in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df.index if 'date' not in df.columns else pd.to_datetime(df['date']),
                    y=df['ema_12'],
                    mode='lines',
                    name='EMA 12',
                    line=dict(color='red', width=2)
                ),
                row=1, col=1
            )
        
        # Bollinger Bands if available
        if 'bb_upper' in df.columns and 'bb_lower' in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df.index if 'date' not in df.columns else pd.to_datetime(df['date']),
                    y=df['bb_upper'],
                    mode='lines',
                    name='BB Upper',
                    line=dict(color='gray', width=1, dash='dash'),
                    showlegend=False
                ),
                row=1, col=1
            )
            fig.add_trace(
                go.Scatter(
                    x=df.index if 'date' not in df.columns else pd.to_datetime(df['date']),
                    y=df['bb_lower'],
                    mode='lines',
                    name='BB Lower',
                    line=dict(color='gray', width=1, dash='dash'),
                    fill='tonexty',
                    fillcolor='rgba(128,128,128,0.1)',
                    showlegend=False
                ),
                row=1, col=1
            )
        
        # Technical indicators subplot
        if 'rsi' in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df.index if 'date' not in df.columns else pd.to_datetime(df['date']),
                    y=df['rsi'],
                    mode='lines',
                    name='RSI',
                    line=dict(color='purple')
                ),
                row=2, col=1
            )
            # RSI overbought/oversold lines
            fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
        
        if 'macd' in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df.index if 'date' not in df.columns else pd.to_datetime(df['date']),
                    y=df['macd'],
                    mode='lines',
                    name='MACD',
                    line=dict(color='orange')
                ),
                row=2, col=1, secondary_y=True
            )
        
        # Volume chart
        if 'volume' in df.columns:
            fig.add_trace(
                go.Bar(
                    x=df.index if 'date' not in df.columns else pd.to_datetime(df['date']),
                    y=df['volume'],
                    name='Volume',
                    marker_color='lightblue'
                ),
                row=3, col=1
            )
    
    elif 'current_price' in df.columns:
        # For real-time quote data, show current prices
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df['current_price'],
                mode='lines+markers',
                name='Current Price',
                line=dict(color='blue', width=3)
            ),
            row=1, col=1
        )
    
    fig.update_layout(
        height=800,
        title=f"{symbol} Stock Analysis",
        xaxis_rangeslider_visible=False
    )
    
    return fig

def create_market_overview_dashboard(quotes_df, processed_df=None):
    """Create market overview dashboard with multiple stocks."""
    if quotes_df is None or quotes_df.empty:
        return None
    
    # Create market summary
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Market Sentiment', 'Price Changes', 'Volume Analysis', 'Performance Metrics'),
        specs=[[{"type": "pie"}, {"type": "bar"}],
               [{"type": "bar"}, {"type": "table"}]]
    )
    
    # Market sentiment pie chart
    if 'sentiment' in quotes_df.columns:
        sentiment_counts = quotes_df['sentiment'].value_counts()
        colors = {'Strong Bullish': 'darkgreen', 'Bullish': 'lightgreen', 
                 'Bearish': 'lightcoral', 'Strong Bearish': 'darkred'}
        fig.add_trace(
            go.Pie(
                labels=sentiment_counts.index,
                values=sentiment_counts.values,
                name="Sentiment",
                marker_colors=[colors.get(label, 'gray') for label in sentiment_counts.index]
            ),
            row=1, col=1
        )
    
    # Price changes bar chart
    if 'change_percent' in quotes_df.columns and 'symbol' in quotes_df.columns:
        fig.add_trace(
            go.Bar(
                x=quotes_df['symbol'],
                y=quotes_df['change_percent'],
                name="Change %",
                marker_color=quotes_df['change_percent'].apply(
                    lambda x: 'green' if x > 0 else 'red'
                )
            ),
            row=1, col=2
        )
    
    # Volume analysis
    if 'volume' in quotes_df.columns and 'symbol' in quotes_df.columns:
        fig.add_trace(
            go.Bar(
                x=quotes_df['symbol'],
                y=quotes_df['volume'],
                name="Volume",
                marker_color='lightblue'
            ),
            row=2, col=1
        )
    
    # Performance metrics table
    if 'symbol' in quotes_df.columns and 'current_price' in quotes_df.columns:
        metrics_cols = ['symbol', 'current_price', 'change_percent', 'volume']
        available_cols = [col for col in metrics_cols if col in quotes_df.columns]
        
        if available_cols:
            table_data = quotes_df[available_cols].round(2)
            fig.add_trace(
                go.Table(
                    header=dict(values=available_cols),
                    cells=dict(values=[table_data[col] for col in available_cols])
                ),
                row=2, col=2
            )
    
    fig.update_layout(height=800, showlegend=True)
    return fig

def main():
    """Main Streamlit application for stock market analysis."""
    st.title("� Stock Market Analysis Pipeline - Microservices Architecture")
    st.markdown("---")
    
    # Sidebar
    st.sidebar.title("🎛️ Stock Market Control Panel")
    
    # Service status
    st.sidebar.subheader("📊 Service Status")
    
    with st.spinner("Loading service status..."):
        statuses = get_service_status()
    
    if statuses:
        for service, status in statuses.items():
            status_color = "🟢" if status.get('status') == 'completed' else "🟡" if status.get('status') == 'processing' else "🔴"
            st.sidebar.markdown(f"{status_color} **{service.replace('_', ' ').title()}**")
            st.sidebar.markdown(f"Status: {status.get('status', 'Unknown')}")
            if 'message' in status:
                st.sidebar.markdown(f"Message: {status['message']}")
            st.sidebar.markdown("---")
    else:
        st.sidebar.warning("No service status available")
    
    # Data files section
    st.sidebar.subheader("📁 Stock Data Files")
    
    with st.spinner("Loading stock data files..."):
        files_info = load_stock_data_files()
    
    # Auto-refresh toggle
    auto_refresh = st.sidebar.checkbox("Auto-refresh (30s)", value=False)
    
    if auto_refresh:
        st.rerun()
        time.sleep(30)
    
    # Manual refresh button
    if st.sidebar.button("� Refresh Data"):
        st.cache_data.clear()
        st.rerun()
    
    # Main content area
    tab1, tab2, tab3, tab4 = st.tabs(["�📊 Market Overview", "📈 Individual Stocks", "🔍 Technical Analysis", "📋 Processing Summary"])
    
    with tab1:
        st.subheader("🌐 Stock Market Overview")
        
        if files_info['stock_quotes'] or files_info['processed_quotes']:
            # Load latest quotes data
            latest_quotes = None
            if files_info['processed_quotes']:
                latest_quotes_file = files_info['processed_quotes'][0]
                latest_quotes = load_dataframe(latest_quotes_file)
                st.info(f"📊 Showing processed data from: {os.path.basename(latest_quotes_file)}")
            elif files_info['stock_quotes']:
                latest_quotes_file = files_info['stock_quotes'][0]
                latest_quotes = load_dataframe(latest_quotes_file)
                st.info(f"📊 Showing raw data from: {os.path.basename(latest_quotes_file)}")
            
            if latest_quotes is not None and not latest_quotes.empty:
                # Market overview dashboard
                overview_fig = create_market_overview_dashboard(latest_quotes)
                if overview_fig:
                    st.plotly_chart(overview_fig, use_container_width=True)
                
                # Key metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    if 'current_price' in latest_quotes.columns:
                        avg_price = latest_quotes['current_price'].mean()
                        st.metric("Average Price", f"${avg_price:.2f}")
                
                with col2:
                    if 'change_percent' in latest_quotes.columns:
                        market_trend = latest_quotes['change_percent'].mean()
                        st.metric("Market Trend", f"{market_trend:.2f}%", delta=f"{market_trend:.2f}%")
                
                with col3:
                    if 'volume' in latest_quotes.columns:
                        total_volume = latest_quotes['volume'].sum()
                        st.metric("Total Volume", f"{total_volume:,.0f}")
                
                with col4:
                    active_stocks = len(latest_quotes)
                    st.metric("Active Stocks", active_stocks)
                
                # Recent data table
                st.subheader("📋 Recent Stock Data")
                display_columns = [col for col in ['symbol', 'current_price', 'change_percent', 'volume', 'sentiment'] 
                                 if col in latest_quotes.columns]
                if display_columns:
                    st.dataframe(latest_quotes[display_columns].round(2), use_container_width=True)
            else:
                st.warning("⚠️ No stock quotes data available")
        else:
            st.warning("⚠️ No stock data files found")
    
    with tab2:
        st.subheader("📈 Individual Stock Analysis")
        
        # Stock selection
        available_stocks = []
        stock_data = None
        
        if files_info['processed_historical'] or files_info['historical_data']:
            # Get available stocks from historical data
            historical_files = files_info['processed_historical'] or files_info['historical_data']
            for file_path in historical_files:
                try:
                    df = load_dataframe(file_path)
                    if df is not None and 'symbol' in df.columns:
                        stocks = df['symbol'].unique()
                        available_stocks.extend(stocks)
                except Exception as e:
                    st.error(f"Error loading {file_path}: {e}")
            
            available_stocks = list(set(available_stocks))
        
        if available_stocks:
            selected_stock = st.selectbox("Select a stock:", available_stocks)
            
            if selected_stock:
                # Load data for selected stock
                for file_path in (files_info['processed_historical'] or files_info['historical_data']):
                    try:
                        df = load_dataframe(file_path)
                        if df is not None and 'symbol' in df.columns:
                            stock_data = df[df['symbol'] == selected_stock].copy()
                            if not stock_data.empty:
                                break
                    except Exception:
                        continue
                
                if stock_data is not None and not stock_data.empty:
                    # Stock price chart
                    price_fig = create_stock_price_chart(stock_data, selected_stock)
                    if price_fig:
                        st.plotly_chart(price_fig, use_container_width=True)
                    
                    # Stock metrics
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        if 'close' in stock_data.columns:
                            current_price = stock_data['close'].iloc[-1]
                            st.metric("Current Price", f"${current_price:.2f}")
                    
                    with col2:
                        if 'volume' in stock_data.columns:
                            avg_volume = stock_data['volume'].mean()
                            st.metric("Avg Volume", f"{avg_volume:,.0f}")
                    
                    with col3:
                        if 'volatility' in stock_data.columns:
                            volatility = stock_data['volatility'].iloc[-1]
                            st.metric("Volatility", f"{volatility:.2f}%")
                    
                    with col4:
                        if 'rsi' in stock_data.columns:
                            rsi = stock_data['rsi'].iloc[-1]
                            st.metric("RSI", f"{rsi:.1f}")
                    
                    # Data table
                    st.subheader(f"📊 {selected_stock} Data")
                    st.dataframe(stock_data.round(2), use_container_width=True)
                else:
                    st.warning(f"⚠️ No data available for {selected_stock}")
        else:
            st.warning("⚠️ No historical stock data available")
    
    with tab3:
        st.subheader("🔍 Technical Analysis")
        
        if files_info['processed_historical']:
            processed_file = st.selectbox(
                "Select processed historical data file:",
                [os.path.basename(f) for f in files_info['processed_historical']]
            )
            
            if processed_file:
                file_path = next(f for f in files_info['processed_historical'] if os.path.basename(f) == processed_file)
                df = load_dataframe(file_path)
                
                if df is not None and not df.empty:
                    # Technical indicators summary
                    st.subheader("📊 Technical Indicators Summary")
                    
                    technical_columns = [col for col in df.columns if col in 
                                       ['sma_5', 'sma_20', 'ema_12', 'ema_26', 'macd', 'rsi', 'bb_upper', 'bb_lower', 'volatility']]
                    
                    if technical_columns:
                        # Show technical indicators for each stock
                        for symbol in df['symbol'].unique() if 'symbol' in df.columns else ['Stock']:
                            if 'symbol' in df.columns:
                                symbol_data = df[df['symbol'] == symbol].copy()
                            else:
                                symbol_data = df.copy()
                            
                            st.subheader(f"📈 {symbol} Technical Analysis")
                            
                            # Latest technical values
                            if not symbol_data.empty:
                                tech_metrics = {}
                                for col in technical_columns:
                                    if col in symbol_data.columns and not symbol_data[col].isna().all():
                                        tech_metrics[col.replace('_', ' ').title()] = symbol_data[col].iloc[-1]
                                
                                if tech_metrics:
                                    cols = st.columns(min(4, len(tech_metrics)))
                                    for i, (metric, value) in enumerate(tech_metrics.items()):
                                        with cols[i % 4]:
                                            st.metric(metric, f"{value:.2f}")
                            
                            # Technical chart
                            tech_fig = create_stock_price_chart(symbol_data, symbol)
                            if tech_fig:
                                st.plotly_chart(tech_fig, use_container_width=True)
                    else:
                        st.warning("⚠️ No technical indicators found in the data")
                else:
                    st.warning("⚠️ Unable to load the selected file")
        else:
            st.warning("⚠️ No processed historical data available")
    
    with tab4:
        st.subheader("📋 Processing Summary")
        
        if files_info['summary_files']:
            summary_file = st.selectbox(
                "Select summary file:",
                [os.path.basename(f) for f in files_info['summary_files']]
            )
            
            if summary_file:
                file_path = next(f for f in files_info['summary_files'] if os.path.basename(f) == summary_file)
                summary_data = load_json_file(file_path)
                
                if summary_data:
                    # Display processing summary
                    if 'timestamp' in summary_data:
                        st.info(f"📅 Processing Time: {summary_data['timestamp']}")
                    
                    if 'total_files_processed' in summary_data:
                        st.metric("Files Processed", summary_data['total_files_processed'])
                    
                    if 'average_quality_score' in summary_data:
                        st.metric("Average Data Quality", f"{summary_data['average_quality_score']}%")
                    
                    # Processing steps for each file
                    if 'files' in summary_data:
                        st.subheader("📁 File Processing Details")
                        
                        for file_info in summary_data['files']:
                            with st.expander(f"📄 {file_info.get('input_file', 'Unknown File')}"):
                                if 'stats' in file_info:
                                    stats = file_info['stats']
                                    
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        if 'original_rows' in stats:
                                            st.metric("Original Rows", stats['original_rows'])
                                    with col2:
                                        if 'final_rows' in stats:
                                            st.metric("Final Rows", stats['final_rows'])
                                    with col3:
                                        if 'data_quality_score' in stats:
                                            st.metric("Quality Score", f"{stats['data_quality_score']}%")
                                    
                                    # Processing steps
                                    if 'steps' in stats and stats['steps']:
                                        st.subheader("🔧 Processing Steps")
                                        for step in stats['steps']:
                                            st.write(f"✅ {step.get('step', 'Unknown step')}")
                                            for key, value in step.items():
                                                if key != 'step':
                                                    st.write(f"   - {key}: {value}")
                                
                                st.json(file_info)
                    
                    # Full summary
                    with st.expander("📊 Full Summary Data"):
                        st.json(summary_data)
                else:
                    st.warning("⚠️ Unable to load the selected summary file")
        else:
            st.warning("⚠️ No summary files available")
    
    # Footer
    st.markdown("---")
    st.markdown("**Stock Market Analysis Pipeline** | Microservices Architecture | Real-time Financial Data Processing")

if __name__ == "__main__":
    main()