# Importing libraries required
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from pycoingecko import CoinGeckoAPI
import os
import time
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class CryptoAdvisor:
    def __init__(self):
        # Initialize CoinGecko API client
        self.cg = CoinGeckoAPI()
        
        # Initialize cache for crypto data
        self.cache = {}
        self.cache_expiry = {}
        self.cache_duration = 300  # Cache duration in seconds (5 minutes)
        
        # Define system message for better conversation quality
        self.system_message = """
        You are CrypGene, a crypto-savvy friend.
        Keep your advice under 80 words—warm, relatable, and natural. You should also have the knowledge of prices of crypto currencies.
        Explain blockchain, trends, risks, and analysis like you're chatting over coffee.
        Use phrases like "you know" and fun analogies.
        Ask thoughtful questions, share both pros and cons, and never guarantee returns.
        Mention risks clearly and adjust your advice based on the user's vibe.
        """
        
        # Set up the LLM with optimized settings for faster responses
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0.4,  # Lower temperature for faster, more deterministic responses
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            max_output_tokens=150,  # Limit output size for faster generation
        )
        
        # Setup conversation memory
        self.memory = ConversationBufferMemory(return_messages=True)
        
        # Setup the conversation prompt
        self.prompt = PromptTemplate(
            input_variables=["history", "input"],
            template=f"{self.system_message}\n\nConversation History:\n{{history}}\nHuman: {{input}}\nAI: "
        )
        
        # Create the conversation chain
        self.conversation = ConversationChain(
            llm=self.llm,
            memory=self.memory,
            prompt=self.prompt,
            verbose=False
        )
    
    # Add a new method to reset conversation memory
    def reset_conversation(self):
        """Reset the conversation memory to start a fresh chat"""
        self.memory = ConversationBufferMemory(return_messages=True)
        self.conversation = ConversationChain(
            llm=self.llm,
            memory=self.memory,
            prompt=self.prompt,
            verbose=False
        )
        
        # Return a flag indicating this is a fresh conversation
        # This will be used by the app to clear speech-related state
        return True
    
    def get_crypto_data(self, crypto_name=None):
        """Get cryptocurrency data from CoinGecko with caching for faster responses"""
        try:
            current_time = time.time()
            cache_key = f"crypto_{crypto_name if crypto_name else 'global'}"
            
            # Check if we have cached data that hasn't expired
            if cache_key in self.cache and current_time < self.cache_expiry.get(cache_key, 0):
                return self.cache[cache_key]
            
            if crypto_name:
                # Search for specific crypto
                search_result = self.cg.search(crypto_name)
                if search_result and 'coins' in search_result and search_result['coins']:
                    coin_id = search_result['coins'][0]['id']
                    
                    # Check if we have coin_id in cache
                    coin_cache_key = f"coin_{coin_id}"
                    if coin_cache_key in self.cache and current_time < self.cache_expiry.get(coin_cache_key, 0):
                        return self.cache[coin_cache_key]
                    
                    coin_data = self.cg.get_coin_by_id(coin_id, localization=False, market_data=True)
                    
                    result = {
                        'name': coin_data['name'],
                        'symbol': coin_data['symbol'].upper(),
                        'current_price': coin_data['market_data']['current_price']['usd'],
                        'market_cap': coin_data['market_data']['market_cap']['usd'],
                        'price_change_24h': coin_data['market_data']['price_change_percentage_24h'],
                        'price_change_7d': coin_data['market_data']['price_change_percentage_7d'],
                        'price_change_30d': coin_data['market_data']['price_change_percentage_30d'],
                    }
                    
                    # Cache the result with both keys
                    self.cache[cache_key] = result
                    self.cache[coin_cache_key] = result
                    self.cache_expiry[cache_key] = current_time + self.cache_duration
                    self.cache_expiry[coin_cache_key] = current_time + self.cache_duration
                    
                    return result
            
            # If no specific crypto or not found, return global market data
            global_data = self.cg.get_global()
            
            result = {
                'total_market_cap': global_data['total_market_cap']['usd'],
                'total_volume': global_data['total_volume']['usd'],
                'market_cap_change_percentage_24h_usd': global_data['market_cap_change_percentage_24h_usd'],
                'active_cryptocurrencies': global_data['active_cryptocurrencies'],
                'markets': global_data['markets'],
            }
            
            # Cache the global data
            self.cache[cache_key] = result
            self.cache_expiry[cache_key] = current_time + self.cache_duration
            
            return result
        
        except Exception as e:
            print(f"Error fetching crypto data: {str(e)}")
            return None
    
    def get_response(self, query):
        """Generate a response to the user's query with optimized processing"""
        try:
            import time
            start_time = time.time()
            
            # Optimized keyword detection for cryptocurrency queries
            crypto_keywords = ["price of", "how is", "what about", "data on", "information on", "stats for", "how much is", "what's the price", "what is the price", "current price", "price for", "value of", "cost of", "worth of"]
            market_keywords = ["market", "overall", "general", "trending", "crypto market", "cryptocurrency market"]
            
            # Fast check if this is a crypto-related query
            query_lower = query.lower()
            is_crypto_query = any(keyword in query_lower for keyword in crypto_keywords) or any(keyword in query_lower for keyword in market_keywords)
            
            # Only process crypto data if it's a relevant query
            crypto_data = None
            if is_crypto_query:
                specific_crypto = None
                
                # Check for specific crypto mentions
                # First, check for common cryptocurrency names directly in the query
                common_cryptos = ["bitcoin", "btc", "ethereum", "eth", "dogecoin", "doge", "ripple", "xrp", "cardano", "ada", 
                                 "solana", "sol", "polkadot", "dot", "litecoin", "ltc", "chainlink", "link", "stellar", "xlm", 
                                 "tether", "usdt", "binance", "bnb"]
                
                for crypto in common_cryptos:
                    if crypto in query_lower.split():
                        specific_crypto = crypto
                        break
                
                # If no common crypto found, try to extract from keywords
                if not specific_crypto:
                    for keyword in crypto_keywords:
                        if keyword in query_lower:
                            # Extract potential crypto name after the keyword
                            keyword_index = query_lower.find(keyword)
                            remaining_text = query[keyword_index + len(keyword):].strip()
                            if remaining_text:
                                potential_crypto = remaining_text.split()[0]
                                if potential_crypto and len(potential_crypto) > 1:
                                    specific_crypto = potential_crypto
                                    break
                
                # Get crypto data if needed
                if specific_crypto:
                    crypto_data = self.get_crypto_data(specific_crypto)
                elif any(keyword in query_lower for keyword in market_keywords):
                    crypto_data = self.get_crypto_data()
            
            # Enhance the query with crypto data if available
            enhanced_query = query
            if crypto_data:
                # Format price data in a more readable way for the LLM
                formatted_data = ""
                if 'name' in crypto_data and 'current_price' in crypto_data:
                    # Format for specific cryptocurrency
                    formatted_data = f"\n\nLatest data for {crypto_data['name']} ({crypto_data['symbol']}):\n"
                    formatted_data += f"Current Price: ${crypto_data['current_price']:,.2f} USD\n"
                    
                    if 'price_change_24h' in crypto_data:
                        change_24h = crypto_data['price_change_24h']
                        direction = "up" if change_24h > 0 else "down"
                        formatted_data += f"24h Change: {direction} {abs(change_24h):.2f}%\n"
                    
                    if 'market_cap' in crypto_data:
                        formatted_data += f"Market Cap: ${crypto_data['market_cap']:,.0f} USD\n"
                else:
                    # Format for global market data
                    formatted_data = "\n\nLatest Global Crypto Market Data:\n"
                    if 'total_market_cap' in crypto_data:
                        formatted_data += f"Total Market Cap: ${crypto_data['total_market_cap']:,.0f} USD\n"
                    if 'market_cap_change_percentage_24h_usd' in crypto_data:
                        formatted_data += f"24h Market Change: {crypto_data['market_cap_change_percentage_24h_usd']:.2f}%\n"
                    if 'active_cryptocurrencies' in crypto_data:
                        formatted_data += f"Active Cryptocurrencies: {crypto_data['active_cryptocurrencies']}\n"
                
                enhanced_query = f"{query}{formatted_data}"
            
            # Get response from conversation chain
            response = self.conversation.predict(input=enhanced_query)
            
            # Log performance metrics
            processing_time = time.time() - start_time
            print(f"Response generated in {processing_time:.2f} seconds")
            
            return response
        
        except Exception as e:
            print(f"Error generating response: {str(e)}")
            return f"I'm sorry, but I encountered an error while processing your request. Please try again later. (Error: {str(e)})"