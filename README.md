# CrypGene - AI Cryptocurrency Advisor 💰

CrypGene is an intelligent conversational AI agent that serves as your personal financial advisor specializing in cryptocurrency investments. Powered by Google's Gemini model for natural language processing and integrated with the CoinGecko API for real-time market data, CrypGene provides informed insights to help guide your crypto investment decisions.

## ✨ Features

- **Interactive Market Dashboard**: View comprehensive, real-time data on top cryptocurrencies including prices, market caps, and performance metrics
- **AI-Powered Conversations**: Engage in natural, human-like discussions about cryptocurrency investments with personalized insights
- **Real-time Market Data**: Access up-to-date information on cryptocurrency prices, market caps, trading volumes, and trends
- **Trending Coins Tracker**: Monitor the top trending cryptocurrencies in a convenient sidebar display
- **Price Charts**: Visualize cryptocurrency price movements with interactive 7-day price charts
- **Chat Management**: Easily start new conversations or clear chat history with intuitive controls

## 🔧 Requirements

- Python 3.9+
- Google API key for Gemini LLM
- Internet connection for real-time cryptocurrency data

## 🚀 Setup and Installation

1. Clone this repository:
   ```
   git clone <repository-url>
   cd crypgene
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up your API keys:
   - update new Google API key in the .env file    

4. Run the application:
   ```
   streamlit run app.py
   ```

## How to Use

### Left Sidebar
- **New Chat**: Start a fresh conversation with CrypGene
- **Save Chat**: Save your current conversation to history
- **Trending Coins**: View the latest trending cryptocurrencies at a glance
- **Chat History**: Access, load, or delete your previous conversations with CrypGene

### Market Overview Tab
- Browse real-time data on the top 50 cryptocurrencies by market cap
- View global market statistics including total market cap and 24h trading volume
- Click on any cryptocurrency to see detailed information and 7-day price charts

### AI Advisor Tab
- Ask CrypGene questions about cryptocurrency investments, such as:
   - "Should I invest in Bitcoin right now?"
   - "What's the current price of Ethereum?"
   - "Can you explain blockchain technology in simple terms?"
   - "What are the most promising altcoins to watch in 2024?"
   - "How should I diversify my crypto portfolio?"
   - "What factors are affecting the crypto market today?"

## 🛠️ Technical Details

- **Google Gemini Model**: Utilizes Google's advanced Gemini 2.0 Flash model for natural language understanding and generation
- **CoinGecko API**: Sources real-time and historical cryptocurrency data
- **Plotly**: Creates responsive and interactive data visualizations

## ⚠️ Disclaimer

CrypGene provides information and suggestions based on available market data but does not guarantee investment returns. The advice given is for educational purposes only. Always conduct your own research (DYOR) and consider consulting with a professional financial advisor before making any investment decisions. Cryptocurrency investments involve significant risk and volatility.
