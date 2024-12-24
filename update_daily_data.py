import os
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import requests
import urllib3
from concurrent.futures import ThreadPoolExecutor

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.NotOpenSSLWarning)

# Get Supabase credentials from environment variables
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://joeyaqjjtnhoapgacazd.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpvZXlhcWpqdG5ob2FwZ2FjYXpkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzUwNjAxMzMsImV4cCI6MjA1MDYzNjEzM30.NGf0s9yYGlG-qK-eVVv0HL4sak0UrMO26Kjs3YxnC4o')

# BIST30 stocks
BIST30_STOCKS = [
    'akbnk', 'arclk', 'asels', 'bimas', 'ekgyo', 'eregl', 'froto',
    'garan', 'kchol', 'kozaa', 'kozal', 'krdmd', 'petkm', 'pgsus',
    'sahol', 'sasa', 'sise', 'tavhl', 'tcell', 'thyao', 'toaso',
    'tuprs', 'vakbn', 'ykbnk'
]

def get_latest_date(table_name):
    """Get the latest date in a table."""
    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/{table_name}",
            params={
                "select": "date",
                "order": "date.desc",
                "limit": 1
            },
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}"
            },
            verify=False
        )
        response.raise_for_status()
        data = response.json()
        return data[0]['date'].split('T')[0] if data else None
    except Exception as e:
        print(f"Error getting latest date for {table_name}: {str(e)}")
        return None

def fetch_stock_data(stock_code):
    """Fetch latest stock data from Yahoo Finance."""
    try:
        print(f"Fetching data for {stock_code.upper()}.IS...")
        
        # Get the latest date in the database
        latest_db_date = get_latest_date(stock_code)
        if not latest_db_date:
            print(f"No existing data found for {stock_code.upper()}")
            return None
        
        # Convert to datetime and add one day to get new data
        start_date = (datetime.strptime(latest_db_date, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        if start_date >= end_date:
            print(f"No new data needed for {stock_code.upper()}")
            return None
        
        # Fetch data from Yahoo Finance
        ticker = yf.Ticker(f"{stock_code.upper()}.IS")
        df = ticker.history(start=start_date, end=end_date)
        
        if df.empty:
            print(f"No new data available for {stock_code.upper()}")
            return None
        
        # Prepare data for upload
        df = df.reset_index()
        df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')
        df = df.rename(columns={
            'Date': 'date',
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume'
        })
        
        records = df.to_dict('records')
        print(f"Fetched {len(records)} new records for {stock_code.upper()}")
        return records
        
    except Exception as e:
        print(f"Error fetching data for {stock_code.upper()}: {str(e)}")
        return None

def fetch_exchange_rate():
    """Fetch latest USD/TRY exchange rate data."""
    try:
        print("Fetching USD/TRY exchange rate data...")
        
        # Get the latest date in the database
        latest_db_date = get_latest_date('usdtry')
        if not latest_db_date:
            print("No existing exchange rate data found")
            return None
        
        # Convert to datetime and add one day to get new data
        start_date = (datetime.strptime(latest_db_date, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        if start_date >= end_date:
            print("No new exchange rate data needed")
            return None
        
        # Fetch data from Yahoo Finance
        ticker = yf.Ticker("TRY=X")
        df = ticker.history(start=start_date, end=end_date)
        
        if df.empty:
            print("No new exchange rate data available")
            return None
        
        # Prepare data for upload
        df = df.reset_index()
        df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')
        df = df.rename(columns={
            'Date': 'date',
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume'
        })
        
        records = df.to_dict('records')
        print(f"Fetched {len(records)} new exchange rate records")
        return records
        
    except Exception as e:
        print(f"Error fetching exchange rate data: {str(e)}")
        return None

def upload_to_supabase(table_name, records):
    """Upload records to Supabase table."""
    if not records:
        return
    
    try:
        print(f"Uploading {len(records)} records to {table_name}...")
        
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/{table_name}",
            json=records,
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "resolution=merge-duplicates"
            },
            verify=False
        )
        response.raise_for_status()
        print(f"Successfully uploaded data to {table_name}")
        
    except Exception as e:
        print(f"Error uploading to {table_name}: {str(e)}")
        raise  # Re-raise the exception to mark the update as failed

def update_stock(stock_code):
    """Update data for a single stock."""
    try:
        records = fetch_stock_data(stock_code)
        if records:
            upload_to_supabase(stock_code, records)
        return True
    except Exception as e:
        print(f"Failed to update {stock_code}: {str(e)}")
        return False

def main():
    print(f"Starting daily data update at {datetime.now()}")
    
    try:
        # Update exchange rate data first
        exchange_records = fetch_exchange_rate()
        if exchange_records:
            upload_to_supabase('usdtry', exchange_records)
        
        # Update stock data in parallel
        failed_stocks = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            results = list(executor.map(update_stock, BIST30_STOCKS))
            failed_stocks = [stock for stock, success in zip(BIST30_STOCKS, results) if not success]
        
        if failed_stocks:
            raise Exception(f"Failed to update some stocks: {', '.join(failed_stocks)}")
        
        print(f"Completed daily data update at {datetime.now()}")
        return True
        
    except Exception as e:
        print(f"Daily update failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    # Exit with appropriate status code
    exit(0 if success else 1) 