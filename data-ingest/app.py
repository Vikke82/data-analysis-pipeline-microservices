#!/usr/bin/env python3
"""
Data ingestion service for microservices architecture.
Fetches real-time stock market data from Finnhub API.
Communicates with Redis service over the network.
"""

import os
import sys
import time
import logging
import json
import requests
import pandas as pd
from datetime import datetime, timedelta
import redis
import schedule

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class StockDataIngestService:
    def __init__(self):
        self.redis_host = os.getenv('REDIS_HOST', 'redis-service')
        self.redis_port = int(os.getenv('REDIS_PORT', 6379))
        self.shared_data_path = os.getenv('SHARED_DATA_PATH', '/shared/data')
        
        # Finnhub API configuration
        self.finnhub_api_key = os.getenv('FINNHUB_API_KEY', 'demo')  # Get from environment
        self.base_url = "https://finnhub.io/api/v1"
        
        # Stock symbols to track (configurable via environment)
        default_symbols = "AAPL,GOOGL,MSFT,TSLA,AMZN,NVDA,META"
        self.stock_symbols = os.getenv('STOCK_SYMBOLS', default_symbols).split(',')
        
        # Initialize Redis connection
        self.redis_client = None
        self.connect_redis()
        
        # Create shared data directory if it doesn't exist
        os.makedirs(self.shared_data_path, exist_ok=True)
        
        logger.info(f"Stock Data Ingest Service initialized")
        logger.info(f"Redis host: {self.redis_host}:{self.redis_port}")
        logger.info(f"Shared data path: {self.shared_data_path}")
        logger.info(f"Tracking symbols: {', '.join(self.stock_symbols)}")
        logger.info(f"Finnhub API: {'Demo mode' if self.finnhub_api_key == 'demo' else 'Live API key configured'}")

    def connect_redis(self):
        """Connect to Redis service with retry logic."""
        max_retries = 10
        retry_delay = 5
        
        for attempt in range(max_retries):
            try:
                self.redis_client = redis.Redis(
                    host=self.redis_host,
                    port=self.redis_port,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
                # Test connection
                self.redis_client.ping()
                logger.info(f"Successfully connected to Redis at {self.redis_host}:{self.redis_port}")
                return
            except redis.ConnectionError as e:
                logger.warning(f"Redis connection attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    logger.error("Failed to connect to Redis after all retries")
                    sys.exit(1)

    def update_status(self, status_data):
        """Update processing status in Redis."""
        try:
            self.redis_client.hset('data_ingest_status', mapping=status_data)
            logger.debug(f"Status updated: {status_data}")
        except redis.RedisError as e:
            logger.error(f"Failed to update status in Redis: {e}")

    def fetch_stock_quote(self, symbol):
        """Fetch real-time stock quote for a symbol."""
        url = f"{self.base_url}/quote"
        params = {
            'symbol': symbol,
            'token': self.finnhub_api_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'c' in data:  # 'c' is current price
                return {
                    'symbol': symbol,
                    'current_price': data.get('c'),
                    'high_price': data.get('h'),
                    'low_price': data.get('l'),
                    'open_price': data.get('o'),
                    'previous_close': data.get('pc'),
                    'change': data.get('d'),
                    'change_percent': data.get('dp'),
                    'timestamp': datetime.now().isoformat()
                }
            else:
                logger.warning(f"No data returned for symbol {symbol}")
                return None
        except requests.RequestException as e:
            logger.error(f"Failed to fetch data for {symbol}: {e}")
            return None

    def fetch_historical_data(self, symbol, days=30):
        """Fetch historical stock data (candles)."""
        end_time = int(datetime.now().timestamp())
        start_time = int((datetime.now() - timedelta(days=days)).timestamp())
        
        url = f"{self.base_url}/stock/candle"
        params = {
            'symbol': symbol,
            'resolution': 'D',  # Daily resolution
            'from': start_time,
            'to': end_time,
            'token': self.finnhub_api_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('s') == 'ok':  # Status OK
                return {
                    'symbol': symbol,
                    'timestamps': data.get('t', []),
                    'open': data.get('o', []),
                    'high': data.get('h', []),
                    'low': data.get('l', []),
                    'close': data.get('c', []),
                    'volume': data.get('v', [])
                }
            else:
                logger.warning(f"No historical data for symbol {symbol}")
                return None
        except requests.RequestException as e:
            logger.error(f"Failed to fetch historical data for {symbol}: {e}")
            return None

    def fetch_company_profile(self, symbol):
        """Fetch company profile data."""
        url = f"{self.base_url}/stock/profile2"
        params = {'symbol': symbol, 'token': self.finnhub_api_key}
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data and 'name' in data:
                return {
                    'symbol': symbol,
                    'name': data.get('name'),
                    'country': data.get('country'),
                    'currency': data.get('currency'),
                    'exchange': data.get('exchange'),
                    'industry': data.get('finnhubIndustry'),
                    'ipo': data.get('ipo'),
                    'market_cap': data.get('marketCapitalization'),
                    'shares_outstanding': data.get('shareOutstanding'),
                    'logo': data.get('logo'),
                    'weburl': data.get('weburl'),
                    'phone': data.get('phone'),
                    'timestamp': datetime.now().isoformat()
                }
            else:
                logger.warning(f"No company profile for symbol {symbol}")
                return None
        except requests.RequestException as e:
            logger.error(f"Failed to fetch company profile for {symbol}: {e}")
            return None

    def fetch_company_news(self, symbol, days=7):
        """Fetch company news."""
        from_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        to_date = datetime.now().strftime('%Y-%m-%d')
        
        url = f"{self.base_url}/company-news"
        params = {
            'symbol': symbol,
            'from': from_date,
            'to': to_date,
            'token': self.finnhub_api_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data and isinstance(data, list):
                news_items = []
                for item in data[:10]:  # Limit to 10 most recent
                    news_items.append({
                        'symbol': symbol,
                        'headline': item.get('headline'),
                        'summary': item.get('summary'),
                        'url': item.get('url'),
                        'datetime': datetime.fromtimestamp(item.get('datetime', 0)).isoformat() if item.get('datetime') else None,
                        'source': item.get('source'),
                        'category': item.get('category'),
                        'image': item.get('image'),
                        'sentiment': item.get('sentiment')
                    })
                return news_items
            else:
                logger.warning(f"No news for symbol {symbol}")
                return []
        except requests.RequestException as e:
            logger.error(f"Failed to fetch news for {symbol}: {e}")
            return []

    def fetch_earnings(self, symbol):
        """Fetch earnings data."""
        url = f"{self.base_url}/stock/earnings"
        params = {'symbol': symbol, 'token': self.finnhub_api_key}
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data and isinstance(data, list):
                earnings_data = []
                for earning in data:
                    earnings_data.append({
                        'symbol': symbol,
                        'actual': earning.get('actual'),
                        'estimate': earning.get('estimate'),
                        'period': earning.get('period'),
                        'quarter': earning.get('quarter'),
                        'year': earning.get('year'),
                        'timestamp': datetime.now().isoformat()
                    })
                return earnings_data
            else:
                logger.warning(f"No earnings data for symbol {symbol}")
                return []
        except requests.RequestException as e:
            logger.error(f"Failed to fetch earnings for {symbol}: {e}")
            return []

    def fetch_financials(self, symbol, freq='annual'):
        """Fetch financial statements."""
        url = f"{self.base_url}/stock/financials-reported"
        params = {
            'symbol': symbol,
            'freq': freq,
            'token': self.finnhub_api_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data and 'data' in data and data['data']:
                return {
                    'symbol': symbol,
                    'frequency': freq,
                    'data': data['data'][:5],  # Limit to 5 most recent
                    'timestamp': datetime.now().isoformat()
                }
            else:
                logger.warning(f"No financial data for symbol {symbol}")
                return None
        except requests.RequestException as e:
            logger.error(f"Failed to fetch financials for {symbol}: {e}")
            return None

    def fetch_insider_transactions(self, symbol):
        """Fetch insider trading data."""
        from_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
        to_date = datetime.now().strftime('%Y-%m-%d')
        
        url = f"{self.base_url}/stock/insider-transactions"
        params = {
            'symbol': symbol,
            'from': from_date,
            'to': to_date,
            'token': self.finnhub_api_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data and 'data' in data and data['data']:
                insider_data = []
                for transaction in data['data'][:20]:  # Limit to 20 most recent
                    insider_data.append({
                        'symbol': symbol,
                        'person_name': transaction.get('name'),
                        'share': transaction.get('share'),
                        'change': transaction.get('change'),
                        'filing_date': transaction.get('filingDate'),
                        'transaction_date': transaction.get('transactionDate'),
                        'transaction_code': transaction.get('transactionCode')
                    })
                return insider_data
            else:
                logger.warning(f"No insider transaction data for symbol {symbol}")
                return []
        except requests.RequestException as e:
            logger.error(f"Failed to fetch insider transactions for {symbol}: {e}")
            return []

    def fetch_analyst_recommendations(self, symbol):
        """Fetch analyst recommendations."""
        url = f"{self.base_url}/stock/recommendation"
        params = {'symbol': symbol, 'token': self.finnhub_api_key}
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data and isinstance(data, list):
                recommendations = []
                for rec in data[:12]:  # Last 12 months
                    recommendations.append({
                        'symbol': symbol,
                        'buy': rec.get('buy'),
                        'hold': rec.get('hold'),
                        'sell': rec.get('sell'),
                        'strong_buy': rec.get('strongBuy'),
                        'strong_sell': rec.get('strongSell'),
                        'period': rec.get('period')
                    })
                return recommendations
            else:
                logger.warning(f"No analyst recommendations for symbol {symbol}")
                return []
        except requests.RequestException as e:
            logger.error(f"Failed to fetch analyst recommendations for {symbol}: {e}")
            return []

    def fetch_social_sentiment(self, symbol):
        """Fetch social sentiment data."""
        url = f"{self.base_url}/stock/social-sentiment"
        params = {'symbol': symbol, 'token': self.finnhub_api_key}
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data and 'reddit' in data and 'twitter' in data:
                return {
                    'symbol': symbol,
                    'reddit_mention': data['reddit'][0].get('mention') if data['reddit'] else 0,
                    'reddit_positive_mention': data['reddit'][0].get('positiveMention') if data['reddit'] else 0,
                    'reddit_negative_mention': data['reddit'][0].get('negativeMention') if data['reddit'] else 0,
                    'reddit_score': data['reddit'][0].get('score') if data['reddit'] else 0,
                    'twitter_mention': data['twitter'][0].get('mention') if data['twitter'] else 0,
                    'twitter_positive_mention': data['twitter'][0].get('positiveMention') if data['twitter'] else 0,
                    'twitter_negative_mention': data['twitter'][0].get('negativeMention') if data['twitter'] else 0,
                    'twitter_score': data['twitter'][0].get('score') if data['twitter'] else 0,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                logger.warning(f"No social sentiment data for symbol {symbol}")
                return None
        except requests.RequestException as e:
            logger.error(f"Failed to fetch social sentiment for {symbol}: {e}")
            return None

    def fetch_dividends(self, symbol, years=5):
        """Fetch dividend data."""
        from_date = (datetime.now() - timedelta(days=years*365)).strftime('%Y-%m-%d')
        to_date = datetime.now().strftime('%Y-%m-%d')
        
        url = f"{self.base_url}/stock/dividend"
        params = {
            'symbol': symbol,
            'from': from_date,
            'to': to_date,
            'token': self.finnhub_api_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data and isinstance(data, list):
                dividends = []
                for div in data:
                    dividends.append({
                        'symbol': symbol,
                        'amount': div.get('amount'),
                        'adjusted_amount': div.get('adjustedAmount'),
                        'declaration_date': div.get('declarationDate'),
                        'ex_dividend_date': div.get('exDate'),
                        'payment_date': div.get('payDate'),
                        'record_date': div.get('recordDate'),
                        'frequency': div.get('frequency')
                    })
                return dividends
            else:
                logger.warning(f"No dividend data for symbol {symbol}")
                return []
        except requests.RequestException as e:
            logger.error(f"Failed to fetch dividends for {symbol}: {e}")
            return []

    def fetch_market_news(self, category='general'):
        """Fetch general market news."""
        url = f"{self.base_url}/news"
        params = {
            'category': category,
            'token': self.finnhub_api_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data and isinstance(data, list):
                news_items = []
                for item in data[:20]:  # Limit to 20 items
                    news_items.append({
                        'headline': item.get('headline'),
                        'summary': item.get('summary'),
                        'url': item.get('url'),
                        'datetime': datetime.fromtimestamp(item.get('datetime', 0)).isoformat() if item.get('datetime') else None,
                        'source': item.get('source'),
                        'category': item.get('category'),
                        'image': item.get('image'),
                        'related': item.get('related')
                    })
                return news_items
            else:
                logger.warning(f"No market news for category {category}")
                return []
        except requests.RequestException as e:
            logger.error(f"Failed to fetch market news: {e}")
            return []

    def fetch_ipo_calendar(self, days=30):
        """Fetch IPO calendar."""
        from_date = datetime.now().strftime('%Y-%m-%d')
        to_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
        
        url = f"{self.base_url}/calendar/ipo"
        params = {
            'from': from_date,
            'to': to_date,
            'token': self.finnhub_api_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data and 'ipoCalendar' in data:
                ipo_data = []
                for ipo in data['ipoCalendar']:
                    ipo_data.append({
                        'date': ipo.get('date'),
                        'exchange': ipo.get('exchange'),
                        'name': ipo.get('name'),
                        'number_of_shares': ipo.get('numberOfShares'),
                        'price': ipo.get('price'),
                        'status': ipo.get('status'),
                        'symbol': ipo.get('symbol'),
                        'total_shares_value': ipo.get('totalSharesValue')
                    })
                return ipo_data
            else:
                logger.warning("No IPO calendar data")
                return []
        except requests.RequestException as e:
            logger.error(f"Failed to fetch IPO calendar: {e}")
            return []

    def fetch_stock_data(self):
        """Fetch comprehensive stock market data from Finnhub API."""
        try:
            logger.info("Starting comprehensive stock data fetch from Finnhub API")
            self.update_status({
                'status': 'fetching',
                'timestamp': datetime.now().isoformat(),
                'message': 'Fetching comprehensive stock data from Finnhub API'
            })
            
            # Data containers
            all_quotes = []
            all_historical = []
            all_profiles = []
            all_news = []
            all_earnings = []
            all_financials = []
            all_insider = []
            all_recommendations = []
            all_sentiment = []
            all_dividends = []
            fetched_symbols = []
            
            for symbol in self.stock_symbols:
                symbol = symbol.strip()
                logger.info(f"Fetching comprehensive data for {symbol}")
                
                # Fetch real-time quote
                quote_data = self.fetch_stock_quote(symbol)
                if quote_data:
                    all_quotes.append(quote_data)
                    fetched_symbols.append(symbol)
                
                # Fetch historical data
                historical_data = self.fetch_historical_data(symbol, days=30)
                if historical_data:
                    all_historical.append(historical_data)
                
                # Fetch company profile
                profile_data = self.fetch_company_profile(symbol)
                if profile_data:
                    all_profiles.append(profile_data)
                
                # Fetch company news
                news_data = self.fetch_company_news(symbol, days=7)
                if news_data:
                    all_news.extend(news_data)
                
                # Fetch earnings
                earnings_data = self.fetch_earnings(symbol)
                if earnings_data:
                    all_earnings.extend(earnings_data)
                
                # Fetch financials
                financials_data = self.fetch_financials(symbol)
                if financials_data:
                    all_financials.append(financials_data)
                
                # Fetch insider transactions
                insider_data = self.fetch_insider_transactions(symbol)
                if insider_data:
                    all_insider.extend(insider_data)
                
                # Fetch analyst recommendations
                recommendations_data = self.fetch_analyst_recommendations(symbol)
                if recommendations_data:
                    all_recommendations.extend(recommendations_data)
                
                # Fetch social sentiment
                sentiment_data = self.fetch_social_sentiment(symbol)
                if sentiment_data:
                    all_sentiment.append(sentiment_data)
                
                # Fetch dividends
                dividends_data = self.fetch_dividends(symbol)
                if dividends_data:
                    all_dividends.extend(dividends_data)
                
                # Rate limiting - wait between API calls
                time.sleep(1.2)  # Increased delay for more API calls
            
            # Fetch market-wide data
            logger.info("Fetching market-wide data")
            market_news = self.fetch_market_news('general')
            ipo_calendar = self.fetch_ipo_calendar()
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Save all data types to separate CSV files
            files_created = []
            
            # Real-time quotes
            if all_quotes:
                quotes_df = pd.DataFrame(all_quotes)
                quotes_file = os.path.join(self.shared_data_path, f"stock_quotes_{timestamp}.csv")
                quotes_df.to_csv(quotes_file, index=False)
                files_created.append(quotes_file)
                logger.info(f"Saved {len(all_quotes)} real-time quotes")
            
            # Historical data
            if all_historical:
                historical_records = []
                for hist_data in all_historical:
                    symbol = hist_data['symbol']
                    for i in range(len(hist_data['timestamps'])):
                        historical_records.append({
                            'symbol': symbol,
                            'date': datetime.fromtimestamp(hist_data['timestamps'][i]).strftime('%Y-%m-%d'),
                            'open': hist_data['open'][i],
                            'high': hist_data['high'][i],
                            'low': hist_data['low'][i],
                            'close': hist_data['close'][i],
                            'volume': hist_data['volume'][i]
                        })
                
                if historical_records:
                    hist_df = pd.DataFrame(historical_records)
                    hist_file = os.path.join(self.shared_data_path, f"stock_historical_{timestamp}.csv")
                    hist_df.to_csv(hist_file, index=False)
                    files_created.append(hist_file)
                    logger.info(f"Saved {len(historical_records)} historical records")
            
            # Company profiles
            if all_profiles:
                profiles_df = pd.DataFrame(all_profiles)
                profiles_file = os.path.join(self.shared_data_path, f"company_profiles_{timestamp}.csv")
                profiles_df.to_csv(profiles_file, index=False)
                files_created.append(profiles_file)
                logger.info(f"Saved {len(all_profiles)} company profiles")
            
            # Company news
            if all_news:
                news_df = pd.DataFrame(all_news)
                news_file = os.path.join(self.shared_data_path, f"company_news_{timestamp}.csv")
                news_df.to_csv(news_file, index=False)
                files_created.append(news_file)
                logger.info(f"Saved {len(all_news)} news items")
            
            # Earnings
            if all_earnings:
                earnings_df = pd.DataFrame(all_earnings)
                earnings_file = os.path.join(self.shared_data_path, f"earnings_{timestamp}.csv")
                earnings_df.to_csv(earnings_file, index=False)
                files_created.append(earnings_file)
                logger.info(f"Saved {len(all_earnings)} earnings records")
            
            # Financials (need to handle nested structure)
            if all_financials:
                financials_flat = []
                for fin_data in all_financials:
                    symbol = fin_data['symbol']
                    for report in fin_data['data']:
                        financials_flat.append({
                            'symbol': symbol,
                            'frequency': fin_data['frequency'],
                            'year': report.get('year'),
                            'quarter': report.get('quarter'),
                            'form': report.get('form'),
                            'start_date': report.get('startDate'),
                            'end_date': report.get('endDate'),
                            'filed_date': report.get('filedDate'),
                            'accepted_date': report.get('acceptedDate')
                        })
                
                if financials_flat:
                    financials_df = pd.DataFrame(financials_flat)
                    financials_file = os.path.join(self.shared_data_path, f"financials_{timestamp}.csv")
                    financials_df.to_csv(financials_file, index=False)
                    files_created.append(financials_file)
                    logger.info(f"Saved {len(financials_flat)} financial records")
            
            # Insider transactions
            if all_insider:
                insider_df = pd.DataFrame(all_insider)
                insider_file = os.path.join(self.shared_data_path, f"insider_transactions_{timestamp}.csv")
                insider_df.to_csv(insider_file, index=False)
                files_created.append(insider_file)
                logger.info(f"Saved {len(all_insider)} insider transactions")
            
            # Analyst recommendations
            if all_recommendations:
                recommendations_df = pd.DataFrame(all_recommendations)
                recommendations_file = os.path.join(self.shared_data_path, f"analyst_recommendations_{timestamp}.csv")
                recommendations_df.to_csv(recommendations_file, index=False)
                files_created.append(recommendations_file)
                logger.info(f"Saved {len(all_recommendations)} analyst recommendations")
            
            # Social sentiment
            if all_sentiment:
                sentiment_df = pd.DataFrame(all_sentiment)
                sentiment_file = os.path.join(self.shared_data_path, f"social_sentiment_{timestamp}.csv")
                sentiment_df.to_csv(sentiment_file, index=False)
                files_created.append(sentiment_file)
                logger.info(f"Saved {len(all_sentiment)} social sentiment records")
            
            # Dividends
            if all_dividends:
                dividends_df = pd.DataFrame(all_dividends)
                dividends_file = os.path.join(self.shared_data_path, f"dividends_{timestamp}.csv")
                dividends_df.to_csv(dividends_file, index=False)
                files_created.append(dividends_file)
                logger.info(f"Saved {len(all_dividends)} dividend records")
            
            # Market news
            if market_news:
                market_news_df = pd.DataFrame(market_news)
                market_news_file = os.path.join(self.shared_data_path, f"market_news_{timestamp}.csv")
                market_news_df.to_csv(market_news_file, index=False)
                files_created.append(market_news_file)
                logger.info(f"Saved {len(market_news)} market news items")
            
            # IPO calendar
            if ipo_calendar:
                ipo_df = pd.DataFrame(ipo_calendar)
                ipo_file = os.path.join(self.shared_data_path, f"ipo_calendar_{timestamp}.csv")
                ipo_df.to_csv(ipo_file, index=False)
                files_created.append(ipo_file)
                logger.info(f"Saved {len(ipo_calendar)} IPO records")
            
            # Update status with success
            self.update_status({
                'status': 'completed',
                'timestamp': datetime.now().isoformat(),
                'message': f'Successfully fetched comprehensive data for {len(fetched_symbols)} symbols',
                'symbols_fetched': json.dumps(fetched_symbols),
                'files_created': len(files_created),
                'data_types': json.dumps(['quotes', 'historical', 'profiles', 'news', 'earnings', 'financials', 'insider', 'recommendations', 'sentiment', 'dividends', 'market_news', 'ipo_calendar'])
            })
            
            # Publish event to Redis for other services
            self.redis_client.publish('data_pipeline', json.dumps({
                'event': 'comprehensive_data_ingested',
                'timestamp': datetime.now().isoformat(),
                'symbols': fetched_symbols,
                'files_created': len(files_created),
                'data_summary': {
                    'quotes': len(all_quotes),
                    'historical': len(all_historical),
                    'profiles': len(all_profiles),
                    'news': len(all_news),
                    'earnings': len(all_earnings),
                    'financials': len(all_financials),
                    'insider': len(all_insider),
                    'recommendations': len(all_recommendations),
                    'sentiment': len(all_sentiment),
                    'dividends': len(all_dividends),
                    'market_news': len(market_news) if market_news else 0,
                    'ipo_calendar': len(ipo_calendar) if ipo_calendar else 0
                }
            }))
            
            logger.info(f"Comprehensive stock data ingestion completed. Created {len(files_created)} data files for {len(fetched_symbols)} symbols")
            return True
            
        except Exception as e:
            error_msg = f"Error during comprehensive stock data fetch: {e}"
            logger.error(error_msg)
            self.update_status({
                'status': 'error',
                'timestamp': datetime.now().isoformat(),
                'message': error_msg
            })
            return False

    def health_check(self):
        """Perform health check."""
        try:
            # Check Redis connection
            self.redis_client.ping()
            
            # Check Finnhub API connection
            url = f"{self.base_url}/quote"
            params = {'symbol': 'AAPL', 'token': self.finnhub_api_key}
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    def run(self):
        """Main service loop."""
        logger.info("Starting Stock Data Ingest Service")
        
        # Set initial status
        self.update_status({
            'status': 'started',
            'timestamp': datetime.now().isoformat(),
            'message': 'Stock data ingest service started'
        })
        
        # Schedule periodic data ingestion (every 15 minutes for stock data)
        schedule.every(15).minutes.do(self.fetch_stock_data)
        
        # Run initial data fetch
        self.fetch_stock_data()
        
        # Main loop
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except KeyboardInterrupt:
                logger.info("Service interrupted by user")
                break
            except Exception as e:
                logger.error(f"Unexpected error in main loop: {e}")
                time.sleep(5)
        
        # Update final status
        self.update_status({
            'status': 'stopped',
            'timestamp': datetime.now().isoformat(),
            'message': 'Stock data ingest service stopped'
        })

if __name__ == "__main__":
    service = StockDataIngestService()
    service.run()