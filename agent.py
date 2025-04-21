# Importing libraries required
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from pycoingecko import CoinGeckoAPI
import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class CryptoAdvisor:
    def __init__(self):
        # Initialize CoinGecko API client
        self.cg = CoinGeckoAPI()
        
        # Define system message for better conversation quality
        self.system_message = """
        You are CrypGene, a crypto-savvy friend.
        Keep your advice under 80 words—warm, relatable, and natural.
        Explain blockchain, trends, risks, and analysis like you're chatting over coffee.
        Use phrases like "you know" and fun analogies.
        Ask thoughtful questions, share both pros and cons, and never guarantee returns.
        Mention risks clearly and adjust your advice based on the user's vibe.
        
        """
        
        # Set up the LLM
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0.7,
            google_api_key=os.getenv("GOOGLE_API_KEY"),
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
        """Get cryptocurrency data from CoinGecko"""
        try:
            if crypto_name:
                # Search for specific crypto
                search_result = self.cg.search(crypto_name)
                if search_result and 'coins' in search_result and search_result['coins']:
                    coin_id = search_result['coins'][0]['id']
                    coin_data = self.cg.get_coin_by_id(coin_id, localization=False, market_data=True)
                    
                    return {
                        'name': coin_data['name'],
                        'symbol': coin_data['symbol'].upper(),
                        'current_price': coin_data['market_data']['current_price']['usd'],
                        'market_cap': coin_data['market_data']['market_cap']['usd'],
                        'price_change_24h': coin_data['market_data']['price_change_percentage_24h'],
                        'price_change_7d': coin_data['market_data']['price_change_percentage_7d'],
                        'price_change_30d': coin_data['market_data']['price_change_percentage_30d'],
                    }
            
            # If no specific crypto or not found, return global market data
            global_data = self.cg.get_global()
            
            return {
                'total_market_cap': global_data['total_market_cap']['usd'],
                'total_volume': global_data['total_volume']['usd'],
                'market_cap_change_percentage_24h_usd': global_data['market_cap_change_percentage_24h_usd'],
                'active_cryptocurrencies': global_data['active_cryptocurrencies'],
                'markets': global_data['markets'],
            }
        
        except Exception as e:
            print(f"Error fetching crypto data: {str(e)}")
            return None
    
    def get_response(self, query):
        """Generate a response to the user's query"""
        try:
            # Check if the query is about a specific cryptocurrency
            crypto_keywords = ["price of", "how is", "what about", "data on", "information on", "stats for"]
            
            specific_crypto = None
            for keyword in crypto_keywords:
                if keyword in query.lower():
                    # Extract potential crypto name after the keyword
                    keyword_index = query.lower().find(keyword)
                    potential_crypto = query[keyword_index + len(keyword):].strip().split()[0]
                    if potential_crypto and len(potential_crypto) > 1:
                        specific_crypto = potential_crypto
                        break
            
            # Get crypto data if needed
            crypto_data = None
            if specific_crypto:
                crypto_data = self.get_crypto_data(specific_crypto)
            elif any(keyword in query.lower() for keyword in ["market", "overall", "general", "trending"]):
                crypto_data = self.get_crypto_data()
            
            # Enhance the query with crypto data if available
            enhanced_query = query
            if crypto_data:
                enhanced_query = f"{query}\n\nHere's the latest data: {crypto_data}"
            
            # Get response from conversation chain
            response = self.conversation.predict(input=enhanced_query)
            
            return response
        
        except Exception as e:
            print(f"Error generating response: {str(e)}")
            return f"I'm sorry, but I encountered an error while processing your request. Please try again later. (Error: {str(e)})"