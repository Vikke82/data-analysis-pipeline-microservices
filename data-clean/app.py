#!/usr/bin/env python3
"""
Stock data cleaning and analysis service for microservices architecture.
Processes raw stock market data and calculates technical indicators.
Communicates with Redis service over the network.
"""

import os
import sys
import time
import logging
import json
import glob
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import redis

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class StockDataCleanService:
    def __init__(self):
        self.redis_host = os.getenv('REDIS_HOST', 'redis-service')
        self.redis_port = int(os.getenv('REDIS_PORT', 6379))
        self.shared_data_path = os.getenv('SHARED_DATA_PATH', '/shared/data')
        self.processing_interval = int(os.getenv('PROCESSING_INTERVAL', 30))
        
        # Initialize Redis connection
        self.redis_client = None
        self.pubsub = None
        self.connect_redis()
        
        # Create shared data directory if it doesn't exist
        os.makedirs(self.shared_data_path, exist_ok=True)
        
        logger.info(f"Stock Data Clean Service initialized")
        logger.info(f"Redis host: {self.redis_host}:{self.redis_port}")
        logger.info(f"Shared data path: {self.shared_data_path}")
        logger.info(f"Processing interval: {self.processing_interval}s")

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
                
                # Subscribe to data pipeline events
                self.pubsub = self.redis_client.pubsub()
                self.pubsub.subscribe('data_pipeline')
                
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
            self.redis_client.hset('data_clean_status', mapping=status_data)
            logger.debug(f"Status updated: {status_data}")
        except redis.RedisError as e:
            logger.error(f"Failed to update status in Redis: {e}")

    def find_raw_files(self):
        """Find raw CSV files in shared data directory."""
        raw_files = []
        patterns = [
            os.path.join(self.shared_data_path, "*.csv"),
            os.path.join(self.shared_data_path, "raw_*.csv"),
            os.path.join(self.shared_data_path, "*raw*.csv")
        ]
        
        for pattern in patterns:
            raw_files.extend(glob.glob(pattern))
        
        # Remove duplicates and sort
        raw_files = sorted(list(set(raw_files)))
    def find_unprocessed_files(self):
        """Find stock data files that need processing."""
        # Look for stock quote and historical files
        quote_files = glob.glob(os.path.join(self.shared_data_path, "stock_quotes_*.csv"))
        historical_files = glob.glob(os.path.join(self.shared_data_path, "stock_historical_*.csv"))
        
        # Filter out already processed files
        processed_files = glob.glob(os.path.join(self.shared_data_path, "processed_*.csv"))
        processed_names = set()
        
        for pf in processed_files:
            base_name = os.path.basename(pf).replace("processed_", "").replace(".csv", "")
            processed_names.add(base_name)
        
        unprocessed_files = []
        
        # Check quote files
        for quote_file in quote_files:
            base_name = os.path.basename(quote_file).replace("stock_quotes_", "").replace(".csv", "")
            if base_name not in processed_names:
                unprocessed_files.append(quote_file)
        
        # Check historical files  
        for hist_file in historical_files:
            base_name = os.path.basename(hist_file).replace("stock_historical_", "").replace(".csv", "")
            if base_name not in processed_names:
                unprocessed_files.append(hist_file)
        
        return unprocessed_files

    def calculate_technical_indicators(self, df):
        """Calculate technical indicators for stock data."""
        if 'close' not in df.columns:
            return df
        
        # Sort by date to ensure proper calculation
        if 'date' in df.columns:
            df = df.sort_values('date').reset_index(drop=True)
        
        # Simple Moving Averages
        df['sma_5'] = df['close'].rolling(window=5).mean()
        df['sma_20'] = df['close'].rolling(window=20).mean()
        
        # Exponential Moving Average
        df['ema_12'] = df['close'].ewm(span=12).mean()
        df['ema_26'] = df['close'].ewm(span=26).mean()
        
        # MACD
        df['macd'] = df['ema_12'] - df['ema_26']
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']
        
        # RSI (Relative Strength Index)
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Bollinger Bands
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
        
        # Daily returns
        df['daily_return'] = df['close'].pct_change()
        
        # Volatility (20-day rolling standard deviation of returns)
        df['volatility'] = df['daily_return'].rolling(window=20).std()
        
        return df

    def process_stock_data(self, file_path):
        """Process a single stock data file."""
        try:
            logger.info(f"Processing file: {file_path}")
            
            # Read the raw data
            df = pd.read_csv(file_path)
            original_rows = len(df)
            
            # Processing stats
            processing_stats = {
                'original_rows': original_rows,
                'file_type': 'quotes' if 'stock_quotes_' in file_path else 'historical',
                'steps': []
            }
            
            # Remove duplicates
            before_dedup = len(df)
            df = df.drop_duplicates()
            after_dedup = len(df)
            if before_dedup != after_dedup:
                processing_stats['steps'].append({
                    'step': 'remove_duplicates',
                    'rows_removed': before_dedup - after_dedup
                })
            
            # Handle missing values for numeric columns
            numeric_columns = df.select_dtypes(include=[np.number]).columns
            missing_before = df[numeric_columns].isnull().sum().sum()
            
            if missing_before > 0:
                for col in numeric_columns:
                    if col in ['current_price', 'high_price', 'low_price', 'open_price', 'close', 'high', 'low', 'open']:
                        # For price data, forward fill then backward fill
                        df[col] = df[col].fillna(method='ffill').fillna(method='bfill')
                    elif col == 'volume':
                        # For volume, use median
                        df[col] = df[col].fillna(df[col].median())
                    else:
                        # For other numeric columns, use median
                        df[col] = df[col].fillna(df[col].median())
                
                missing_after = df[numeric_columns].isnull().sum().sum()
                processing_stats['steps'].append({
                    'step': 'handle_missing_values',
                    'missing_before': int(missing_before),
                    'missing_after': int(missing_after)
                })
            
            # Calculate technical indicators for historical data
            if 'close' in df.columns and len(df) > 20:
                df = self.calculate_technical_indicators(df)
                processing_stats['steps'].append({
                    'step': 'technical_indicators',
                    'indicators_added': ['sma_5', 'sma_20', 'ema_12', 'ema_26', 'macd', 'rsi', 'bollinger_bands', 'volatility']
                })
            
            # Add market analysis for quotes
            if 'current_price' in df.columns:
                for idx, row in df.iterrows():
                    if pd.notnull(row['current_price']) and pd.notnull(row['previous_close']):
                        change_pct = ((row['current_price'] - row['previous_close']) / row['previous_close']) * 100
                        df.loc[idx, 'change_percent_calc'] = change_pct
                        
                        # Market sentiment based on change
                        if change_pct > 2:
                            df.loc[idx, 'sentiment'] = 'Strong Bullish'
                        elif change_pct > 0:
                            df.loc[idx, 'sentiment'] = 'Bullish'
                        elif change_pct > -2:
                            df.loc[idx, 'sentiment'] = 'Bearish'
                        else:
                            df.loc[idx, 'sentiment'] = 'Strong Bearish'
                
                processing_stats['steps'].append({
                    'step': 'market_analysis',
                    'analysis_added': ['change_percent_calc', 'sentiment']
                })
            
            # Data quality score
            final_rows = len(df)
            completeness = 1 - (df.isnull().sum().sum() / (len(df) * len(df.columns)))
            processing_stats['final_rows'] = final_rows
            processing_stats['data_quality_score'] = round(completeness * 100, 2)
            
            # Save processed data
            base_name = os.path.basename(file_path)
            timestamp = base_name.split('_')[-1].replace('.csv', '')
            file_type = 'quotes' if 'stock_quotes_' in file_path else 'historical'
            
            output_file = os.path.join(self.shared_data_path, f"processed_{file_type}_{timestamp}.csv")
            df.to_csv(output_file, index=False)
            
            # Save processing summary
            summary_file = os.path.join(self.shared_data_path, f"processing_summary_{file_type}_{timestamp}.json")
            with open(summary_file, 'w') as f:
                json.dump(processing_stats, f, indent=2)
            
            logger.info(f"Processed data saved to: {output_file}")
            logger.info(f"Data quality score: {processing_stats['data_quality_score']}%")
            
            return True, processing_stats
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            return False, {'error': str(e)}

    def process_all_files(self):
        """Process all unprocessed stock data files."""
        try:
            logger.info("Starting stock data processing")
            self.update_status({
                'status': 'processing',
                'timestamp': datetime.now().isoformat(),
                'message': 'Starting stock data processing'
            })
            
            unprocessed_files = self.find_unprocessed_files()
            
            if not unprocessed_files:
                logger.info("No unprocessed files found")
                self.update_status({
                    'status': 'idle',
                    'timestamp': datetime.now().isoformat(),
                    'message': 'No files to process'
                })
                return
            
            processed_files = []
            processing_results = []
            
            for file_path in unprocessed_files:
                success, stats = self.process_stock_data(file_path)
                if success:
                    processed_files.append({
                        'input_file': os.path.basename(file_path),
                        'file_type': stats['file_type'],
                        'stats': stats
                    })
                    processing_results.append(file_path)
                else:
                    logger.error(f"Failed to process {file_path}")
                    continue
            
            if processed_files:
                # Generate summary report
                summary = {
                    'timestamp': datetime.now().isoformat(),
                    'total_files_processed': len(processed_files),
                    'files': processed_files,
                    'average_quality_score': round(
                        sum([f['stats']['data_quality_score'] for f in processed_files]) / len(processed_files), 2
                    )
                }
                
                # Save summary report
                summary_path = os.path.join(self.shared_data_path, 'stock_processing_summary.json')
                with open(summary_path, 'w') as f:
                    json.dump(summary, f, indent=2)
                
                # Update status
                self.update_status({
                    'status': 'completed',
                    'timestamp': datetime.now().isoformat(),
                    'files_processed': len(processed_files),
                    'processed_files': json.dumps([f['input_file'] for f in processed_files]),
                    'average_quality_score': summary['average_quality_score'],
                    'message': f'Successfully processed {len(processed_files)} files'
                })
                
                # Signal visualization service
                self.redis_client.publish('data_pipeline', json.dumps({
                    'event': 'data_processed',
                    'timestamp': datetime.now().isoformat(),
                    'files_processed': len(processed_files),
                    'summary': summary
                }))
                
                logger.info(f"Stock data processing completed. Processed {len(processed_files)} files")
            else:
                self.update_status({
                    'status': 'error',
                    'timestamp': datetime.now().isoformat(),
                    'message': 'No files could be processed successfully'
                })
                
        except Exception as e:
            error_msg = f"Error during processing: {e}"
            logger.error(error_msg)
            self.update_status({
                'status': 'error',
                'timestamp': datetime.now().isoformat(),
                'message': error_msg
            })
            self.redis_client.publish('data_pipeline', json.dumps({
                'event': 'data_cleaned',
                'files': [f['output_file'] for f in processed_files],
                'summary': summary,
                'timestamp': datetime.now().isoformat()
            }))
            
            logger.info(f"Data cleaning completed. Processed {len(processed_files)} files")
            return True
            
        except Exception as e:
            error_msg = f"Data cleaning failed: {str(e)}"
            logger.error(error_msg)
            self.update_status({
                'status': 'error',
                'timestamp': datetime.now().isoformat(),
                'error': error_msg,
                'message': 'Data cleaning failed'
            })
            return False

    def listen_for_events(self):
        """Listen for Redis pub/sub events."""
        try:
            message = self.pubsub.get_message(timeout=1)
            if message and message['type'] == 'message':
                try:
                    event_data = json.loads(message['data'])
                    if event_data.get('event') == 'data_ingested':
                        logger.info("Received data ingested event, starting processing")
                        self.process_all_files()
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON in Redis message: {message['data']}")
        except redis.RedisError as e:
            logger.error(f"Redis pub/sub error: {e}")

    def health_check(self):
        """Perform health check."""
        try:
            # Check Redis connection
            self.redis_client.ping()
            
            # Check shared data directory
            if not os.path.exists(self.shared_data_path):
                return False
                
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    def run(self):
        """Main service loop."""
        logger.info("Starting Data Clean Service")
        
        # Set initial status
        self.update_status({
            'status': 'started',
            'timestamp': datetime.now().isoformat(),
            'message': 'Data clean service started'
        })
        
        # Process any existing files
        self.process_all_files()
        
        # Main loop - listen for events and periodic processing
        while True:
            try:
                # Listen for Redis events
                self.listen_for_events()
                
                # Periodic processing check
                time.sleep(self.processing_interval)
                
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
            'message': 'Data clean service stopped'
        })

if __name__ == "__main__":
    service = StockDataCleanService()
    service.run()