import streamlit as st
import os
from agent import CryptoAdvisor
import pycoingecko
from pycoingecko import CoinGeckoAPI
import pandas as pd
import numpy as np
import time
import copy
# Add import for text-to-speech functionality
from gtts import gTTS
from io import BytesIO
import base64
# Add import for plotly
import plotly.graph_objects as go
from datetime import datetime, timedelta
# We'll use only SpeechRecognition for microphone input

# Initialize the CoinGecko API client
cg = CoinGeckoAPI()

# Set up the Streamlit page
st.set_page_config(
    page_title="CrypGene - AI Crypto Advisor",
    page_icon="💰",
    layout="wide"
)

# Initialize session state variables if they don't exist
if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "crypto_advisor" not in st.session_state:
    st.session_state.crypto_advisor = CryptoAdvisor()
    
# Add session state for selected coin and page view
if "selected_coin" not in st.session_state:
    st.session_state.selected_coin = None
    
# Add session state for page view (main or coin_detail)
if "page_view" not in st.session_state:
    st.session_state.page_view = "main"

# Add text-to-speech function
def text_to_speech(text):
    tts = gTTS(text=text, lang='en', slow=False)
    fp = BytesIO()
    tts.write_to_fp(fp)
    fp.seek(0)
    audio_bytes = fp.read()
    b64 = base64.b64encode(audio_bytes).decode()
    
    # Include a unique ID for the audio element so it can be controlled with JavaScript
    audio_id = f"audio_{int(time.time())}"
    
    # Create HTML with audio player and a stop button
    html = f'''
    <audio id="{audio_id}" autoplay="true" src="data:audio/mp3;base64,{b64}">
    <script>
        // Register a function to stop the audio
        window.stopAudio = function() {{
            const audioElement = document.getElementById("{audio_id}");
            if (audioElement) {{
                audioElement.pause();
                audioElement.currentTime = 0;
            }}
        }}
    </script>
    '''
    return html

# Sidebar title
st.sidebar.title("🔥 Trending Cryptos")

# Function to get historical price data for a coin
def get_coin_historical_data(coin_id):
    try:
        # Calculate dates for 7-day period
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        # Format dates as required by CoinGecko API (Unix timestamps)
        from_timestamp = int(start_date.timestamp())
        to_timestamp = int(end_date.timestamp())
        
        # Get market chart data
        chart_data = cg.get_coin_market_chart_range_by_id(
            id=coin_id,
            vs_currency='usd',
            from_timestamp=from_timestamp,
            to_timestamp=to_timestamp
        )
        
        # Extract price data
        price_data = chart_data['prices']
        dates = [datetime.fromtimestamp(price[0]/1000) for price in price_data]
        prices = [price[1] for price in price_data]
        
        return dates, prices
    except Exception as e:
        st.error(f"Error fetching historical data: {str(e)}")
        return [], []

# Function to display coin details on a dedicated page
def show_coin_details(coin_id, coin_symbol, market_cap_rank):
    try:
        # Get detailed coin data
        coin_data = cg.get_coin_by_id(coin_id, localization=False, market_data=True)
        
        # Extract relevant information
        name = coin_data['name']
        symbol = coin_data['symbol'].upper()
        current_price = coin_data['market_data']['current_price']['usd']
        market_cap = coin_data['market_data']['market_cap']['usd']
        price_change_24h = coin_data['market_data']['price_change_percentage_24h']
        
        # Create a header with back button
        col1, col2 = st.columns([1, 5])
        with col1:
            if st.button("← Back", key="back_to_main"):
                st.session_state.selected_coin = None
                st.session_state.page_view = "main"
                st.rerun()
        with col2:
            st.title(f"{name} ({symbol}) Details")
        
        # Create a container for coin details
        st.subheader("Key Metrics")
        
        # Display basic metrics in columns
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Current Price", f"${current_price:,.2f}", f"{price_change_24h:+.2f}%")
        with col2:
            st.metric("Market Cap", f"${market_cap:,.0f}")
        with col3:
            st.metric("Rank", f"#{market_cap_rank}")
        
        # Get historical data for chart
        st.subheader("7-Day Price Chart")
        dates, prices = get_coin_historical_data(coin_id)
        
        if dates and prices:
            # Create a line chart with Plotly
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=dates,
                y=prices,
                mode='lines',
                name=f'{symbol} Price',
                line=dict(color='#1f77b4', width=2)
            ))
            
            # Customize the layout
            fig.update_layout(
                xaxis_title="Date",
                yaxis_title="Price (USD)",
                height=400,
                margin=dict(l=0, r=0, t=10, b=0),
                hovermode="x unified"
            )
            
            # Display the chart
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Could not load historical price data for chart")
            
        # Add additional information
        if 'description' in coin_data and 'en' in coin_data['description'] and coin_data['description']['en']:
            with st.expander("About " + name):
                st.markdown(coin_data['description']['en'])
                
    except Exception as e:
        st.error(f"Error loading coin details: {str(e)}")

# Get trending coins data in the sidebar (more compact)
try:
    trending_data = cg.get_search_trending()
    trending_coins = trending_data['coins'][:5]  # Get top 5 trending coins
    
    # Create an even more compact display for trending coins with clickable names
    for coin in trending_coins:
        coin_info = coin['item']
        cols = st.sidebar.columns([1, 4])
        with cols[0]:
            st.image(coin_info['thumb'], width=25)
        with cols[1]:
            # Make the coin name clickable instead of having a separate button
            coin_name = f"**{coin_info['name']}** ({coin_info['symbol'].upper()}) #{coin_info['market_cap_rank']}"
            if st.button(coin_name, key=f"view_{coin_info['id']}", use_container_width=True):
                st.session_state.selected_coin = coin_info['id']
                st.session_state.page_view = "coin_detail"
                st.rerun()
except Exception as e:
    st.sidebar.error(f"Could not fetch trending coins: {str(e)}")

# New Chat and Save Chat buttons (moved below trending coins)
st.sidebar.markdown("---")
st.sidebar.subheader("💬 Chat Controls")
col1, col2 = st.sidebar.columns(2)
with col1:
    # In your "New Chat" button handler
    if st.button("New Chat", use_container_width=True):
        # Save current conversation to history if not empty
        if st.session_state.messages:
            # Get timestamp for chat identification
            timestamp = time.strftime("%Y-%m-%d %H:%M")
            
            # Extract first user message for title (or use default)
            first_user_message = next((msg["content"] for msg in st.session_state.messages if msg["role"] == "user"), "New Conversation")
            chat_title = first_user_message[:20] + "..." if len(first_user_message) > 20 else first_user_message
            
            # Create a chat record with title and messages
            chat_record = {
                "title": chat_title,
                "timestamp": timestamp,
                "messages": copy.deepcopy(st.session_state.messages)
            }
            
            # Add to chat history
            st.session_state.chat_history.append(chat_record)
        
        # Clear current messages for new chat
        st.session_state.messages = []
        
        # Reset the conversation memory in the advisor
        st.session_state.crypto_advisor.reset_conversation()
        
        # Clear speech-related session state
        if "speech_html" in st.session_state:
            del st.session_state.speech_html
        
        st.rerun()
with col2:
    if st.button("Save Chat", use_container_width=True):
        if st.session_state.messages:
            # Get timestamp for chat identification
            timestamp = time.strftime("%Y-%m-%d %H:%M")
            
            # Extract first user message for title (or use default)
            first_user_message = next((msg["content"] for msg in st.session_state.messages if msg["role"] == "user"), "New Conversation")
            chat_title = first_user_message[:20] + "..." if len(first_user_message) > 20 else first_user_message
            
            # Create a chat record with title and messages
            chat_record = {
                "title": chat_title,
                "timestamp": timestamp,
                "messages": copy.deepcopy(st.session_state.messages)
            }
            
            # Add to chat history
            st.session_state.chat_history.append(chat_record)
            st.sidebar.success("Chat saved to history!")
            time.sleep(1)
            st.rerun()

# Display conversation history in the sidebar
st.sidebar.markdown("---")
st.sidebar.subheader("💬 Chat History")

# Display past conversations with ability to load them
if st.session_state.chat_history:
    for idx, chat in enumerate(st.session_state.chat_history):
        # Create an expander for each past conversation
        with st.sidebar.expander(f"{chat['title']} ({chat['timestamp']})"):
            # Show a preview of the conversation
            for i, msg in enumerate(chat["messages"][:3]):  # Show first 3 messages as preview
                role_icon = "👤" if msg["role"] == "user" else "🤖"
                content_preview = msg["content"][:30] + "..." if len(msg["content"]) > 30 else msg["content"]
                st.markdown(f"{role_icon} {content_preview}")
            
            # Show load and delete buttons for this chat
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Load", key=f"load_{idx}", use_container_width=True):
                    st.session_state.messages = copy.deepcopy(chat["messages"])
                    st.rerun()
            with col2:
                if st.button("Delete", key=f"delete_{idx}", use_container_width=True):
                    st.session_state.chat_history.pop(idx)
                    st.rerun()
else:
    st.sidebar.info("No saved conversations yet. Start chatting and save your conversations!")

# Main content area - conditionally show main page or coin detail page
if st.session_state.page_view == "coin_detail" and st.session_state.selected_coin:
    # Find the selected coin info
    try:
        # Try to find in trending coins first
        trending_data = cg.get_search_trending()
        trending_coins = trending_data['coins'][:5]
        selected_coin_info = next((coin['item'] for coin in trending_coins if coin['item']['id'] == st.session_state.selected_coin), None)
        
        # If not found in trending, get the coin data directly
        if not selected_coin_info:
            coin_data = cg.get_coin_by_id(st.session_state.selected_coin)
            selected_coin_info = {
                'id': coin_data['id'],
                'symbol': coin_data['symbol'],
                'market_cap_rank': coin_data.get('market_cap_rank', 'N/A')
            }
        
        # Show the coin details page
        show_coin_details(selected_coin_info['id'], selected_coin_info['symbol'], selected_coin_info['market_cap_rank'])
    except Exception as e:
        st.error(f"Error loading coin details: {str(e)}")
        if st.button("← Back to Main Page"):
            st.session_state.selected_coin = None
            st.session_state.page_view = "main"
            st.rerun()
else:
    # Main app layout
    st.title("CrypGene - Your AI Crypto Advisor 👨🏽‍💼")

    # Create tabs
    tab1, tab2 = st.tabs(["📊 Market Overview", "🤖 AI Advisor"])

    # Tab 1: Market Overview
    with tab1:
        st.header("Cryptocurrency Market Overview")
        
        # Simple progress indicator for coin data
        with st.spinner("Loading market data..."):
            try:
                # Fetch the top 50 coins by market cap
                coins_data = cg.get_coins_markets(
                    vs_currency='usd',
                    order='market_cap_desc',
                    per_page=50,
                    page=1,
                    sparkline=False
                )
                
                # Check if we received valid data
                if not coins_data or len(coins_data) == 0:
                    st.error("No data received from CoinGecko API. Please try again later.")
                else:
                    # Create a simple table with basic data
                    data = []
                    for coin in coins_data:
                        # Extract only necessary data with safe defaults
                        rank = coin.get('market_cap_rank', 'N/A')
                        name = coin.get('name', 'Unknown')
                        symbol = coin.get('symbol', '').upper()
                        price = coin.get('current_price', 0)
                        price_change = coin.get('price_change_percentage_24h', 0)
                        market_cap = coin.get('market_cap', 0)
                        volume = coin.get('total_volume', 0)
                        
                        data.append({
                            'Rank': rank,
                            'Name': name,
                            'Symbol': symbol,
                            'Price (USD)': f"${price:,.2f}" if price else "$0.00",
                            '24h Change (%)': f"{price_change:+.2f}%" if price_change else "0.00%",
                            'Market Cap (USD)': f"${market_cap:,.0f}" if market_cap else "$0",
                            'Volume (24h)': f"${volume:,.0f}" if volume else "$0"
                        })
                    
                    # Create DataFrame and display
                    df = pd.DataFrame(data)
                    
                    # Display the dataframe without selection functionality
                    st.dataframe(df, use_container_width=True, height=500)
                    
                    # Note: Coin details can still be accessed through the trending coins sidebar
                    
            except Exception as e:
                st.error(f"Error loading market data: {str(e)}")
                
        # Display global market statistics at the bottom with a more prominent design
        st.subheader("🌎 Global Market Statistics")
        
        with st.spinner("Loading global market data..."):
            try:
                # Get global market data
                global_data = cg.get_global()
                
                # Extract statistics with robust error handling
                # Total Market Cap
                total_market_cap = 0
                if global_data and 'total_market_cap' in global_data:
                    market_cap_data = global_data['total_market_cap']
                    if isinstance(market_cap_data, dict) and 'usd' in market_cap_data:
                        total_market_cap = market_cap_data['usd']
                
                # Total Volume
                total_volume = 0
                if global_data and 'total_volume' in global_data:
                    volume_data = global_data['total_volume']
                    if isinstance(volume_data, dict) and 'usd' in volume_data:
                        total_volume = volume_data['usd']
                
                # Market Cap Change
                market_cap_change = 0
                if global_data and 'market_cap_change_percentage_24h_usd' in global_data:
                    market_cap_change = global_data['market_cap_change_percentage_24h_usd']
                                
                # row - Market Cap, Volume and 24h market change
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("💰 Total Market Cap", f"${total_market_cap:,.0f}")
                with col2:
                    st.metric("📊 24h Trading Volume", f"${total_volume:,.0f}")
                with col3:
                    st.metric("📈 Market Cap Change (24h)", f"{market_cap_change:+.2f}%", 
                             delta_color="normal")
                                                
            except Exception as e:
                st.error(f"Could not fetch global market data: {str(e)}")

    # Tab 2: AI Advisor
    with tab2:
        # Chat section
        st.header("Chat and Talk with CrypGene")
        
        # Create a container for chat messages
        chat_container = st.container()
        
        # Create a container for the input box, which will stay at the bottom
        input_container = st.container()
        
        # Add speech input option
        with input_container:
            # Regular text input - now using full width
            prompt = st.chat_input("Ask me anything about crypto investments or any other investments...", key="chat_input")
            
            if prompt:
                # Clear any currently playing speech
                if "speech_html" in st.session_state:
                    del st.session_state.speech_html
                
                # Add user message to chat history
                st.session_state.messages.append({"role": "user", "content": prompt})
                
                # Get response from the advisor agent
                response = st.session_state.crypto_advisor.get_response(prompt)
                
                # Add assistant response to chat history
                st.session_state.messages.append({"role": "assistant", "content": response})
                
                # Convert response to speech
                speech_html = text_to_speech(response)
                st.session_state.speech_html = speech_html
                
                # Force a rerun to update the UI
                st.rerun()
        
        # Display current chat messages in the chat container
        with chat_container:
            if not st.session_state.messages:
                # Show welcome message if no messages
                st.info("👋 Welcome! Ask me anything about cryptocurrency investments.")
            
            # Display all messages
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
            
            # Play speech if available and add a stop button
            if "speech_html" in st.session_state:
                # Add a stop button to control audio playback
                if st.button("🔇 Stop Audio", key="stop_audio"):
                    # Use JavaScript to stop the audio
                    st.components.v1.html('''
                    <script>
                        if (window.stopAudio) {
                            window.stopAudio();
                        }
                    </script>
                    ''', height=0)
                    # Remove the speech HTML from session state
                    del st.session_state.speech_html
                    st.rerun()
                
                # Add the audio component
                st.components.v1.html(st.session_state.speech_html, height=0)

# Add disclaimer at the bottom of the application
st.markdown("---")
with st.container():
    st.caption("**⚠️DISCLAIMER:**")
    st.caption("""
    CrypGene provides AI-generated insights for educational use only. 
    Not financial advice—invest at your own risk.
    """)