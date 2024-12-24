import yfinance as yf
from supabase import create_client, Client
from datetime import datetime, timedelta
import pandas as pd
import time

# Initialize Supabase client with service role key
SUPABASE_URL = "https://joeyaqjjtnhoapgacazd.supabase.co"
SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpvZXlhcWpqdG5ob2FwZ2FjYXpkIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczNTA2MDEzMywiZXhwIjoyMDUwNjM2MTMzfQ.gfBxmeDLQaAEOv47MbkYtin_wXlTvjRDr6sp6m7Wy-k"

# Initialize Supabase client with service role key for admin access
supabase = create_client(SUPABASE_URL, SERVICE_KEY)

# List of BIST30 stock symbols (with .IS suffix for Yahoo Finance)
BIST30_STOCKS = [
    "AKBNK.IS", "ARCLK.IS", "ASELS.IS", "BIMAS.IS", "DOHOL.IS", 
    "EKGYO.IS", "ENKAI.IS", "EREGL.IS", "FROTO.IS", "GARAN.IS", 
    "HALKB.IS", "ISCTR.IS", "KCHOL.IS", "KOZAA.IS", "KOZAL.IS", 
    "KRDMD.IS", "PETKM.IS", "PGSUS.IS", "SAHOL.IS", "SASA.IS", 
    "SISE.IS", "TAVHL.IS", "TCELL.IS", "THYAO.IS", "TKFEN.IS", 
    "TOASO.IS", "TTKOM.IS", "TUPRS.IS", "VAKBN.IS", "YKBNK.IS"
]

def fetch_stock_data(symbol: str):
    """Fetch historical data for a given stock symbol using yfinance"""
    try:
        stock = yf.Ticker(symbol)
        # Get data for the last 5 years
        df = stock.history(period="5y")
        
        # Reset index to make date a column
        df = df.reset_index()
        
        # Convert date to string format
        df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')
        
        # Rename columns to match table schema
        df = df.rename(columns={
            'Date': 'date',
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume',
            'Dividends': 'dividends',
            'Stock Splits': 'stock_splits'
        })
        
        # Convert DataFrame to list of dictionaries
        records = df.to_dict('records')
        return records
    except Exception as e:
        print(f"Error fetching data for {symbol}: {str(e)}")
        return None

def insert_stock_data(symbol: str, data: list):
    """Insert historical data into the stock's table"""
    if not data:
        return False
    
    try:
        # Remove .IS suffix and convert to lowercase for table name
        table_name = symbol.replace('.IS', '').lower()
        
        # Insert data in batches of 100 records
        batch_size = 100
        total_batches = (len(data) + batch_size - 1) // batch_size
        
        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]
            try:
                response = supabase.table(table_name).insert(batch).execute()
                print(f"Inserted batch {i//batch_size + 1} of {total_batches} for {symbol}")
            except Exception as e:
                if "duplicate key value violates unique constraint" in str(e):
                    print(f"Skipping duplicate records in batch {i//batch_size + 1} for {symbol}")
                else:
                    raise e
            
            # Add a small delay between batches to avoid rate limiting
            time.sleep(0.5)
            
        return True
    except Exception as e:
        print(f"Error inserting data for {symbol}: {str(e)}")
        return False

def main():
    """Main function to fetch and insert data for all BIST30 stocks"""
    for symbol in BIST30_STOCKS:
        print(f"\nProcessing {symbol}...")
        
        # Fetch data
        print(f"Fetching data for {symbol}...")
        data = fetch_stock_data(symbol)
        
        if data:
            # Insert data
            print(f"Inserting data for {symbol}...")
            if insert_stock_data(symbol, data):
                print(f"Successfully processed {symbol}")
            else:
                print(f"Failed to insert data for {symbol}")
        else:
            print(f"No data fetched for {symbol}")
            
        # Add a small delay between stocks to avoid rate limiting
        time.sleep(2)

if __name__ == "__main__":
    main() 