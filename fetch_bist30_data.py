import os
import time
import pandas as pd
import yfinance as yf
from datetime import datetime
from supabase import create_client

# Supabase configuration
SUPABASE_URL = 'https://joeyaqjjtnhoapgacazd.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpvZXlhcWpqdG5ob2FwZ2FjYXpkIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczNTA2MDEzMywiZXhwIjoyMDUwNjM2MTMzfQ.gfBxmeDLQaAEOv47MbkYtin_wXlTvjRDr6sp6m7Wy-k'

# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# BIST30 stocks with their company names
BIST30_STOCKS = {
    'AKBNK': 'Akbank',
    'ARCLK': 'Arcelik',
    'ASELS': 'Aselsan',
    'BIMAS': 'BIM Magazalar',
    'EKGYO': 'Emlak Konut GMYO',
    'EREGL': 'Eregli Demir Celik',
    'FROTO': 'Ford Otosan',
    'GARAN': 'Garanti BBVA',
    'KCHOL': 'Koc Holding',
    'KOZAA': 'Koza Anadolu Metal',
    'KOZAL': 'Koza Altin',
    'KRDMD': 'Kardemir',
    'PETKM': 'Petkim',
    'PGSUS': 'Pegasus',
    'SAHOL': 'Sabanci Holding',
    'SASA': 'Sasa Polyester',
    'SISE': 'Sisecam',
    'TAVHL': 'TAV Havalimanlari',
    'TCELL': 'Turkcell',
    'THYAO': 'Turkish Airlines',
    'TOASO': 'Tofas Oto',
    'TUPRS': 'Tupras',
    'VAKBN': 'Vakifbank',
    'YKBNK': 'Yapi Kredi'
}

def verify_table_exists(stock_code):
    """Verify that the table exists in Supabase"""
    try:
        table_name = stock_code.lower()
        supabase.table(table_name).select("*").limit(1).execute()
        return True
    except Exception as e:
        print(f"Table {table_name} does not exist or is not accessible")
        return False

def fetch_stock_data(stock_code):
    """Fetch historical data for a stock from Yahoo Finance"""
    try:
        print(f"\nFetching data for {stock_code}...")
        
        # Add .IS suffix for Istanbul Stock Exchange
        ticker = yf.Ticker(f"{stock_code}.IS")
        
        # Get maximum available historical data
        df = ticker.history(period="max", auto_adjust=True)
        
        if df.empty:
            print(f"No data available for {stock_code}")
            return None
        
        # Reset index to make Date a column
        df = df.reset_index()
        
        # Format the data
        df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')
        
        # Rename columns to match our schema
        df = df.rename(columns={
            'Date': 'date',
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume'
        })
        
        # Ensure volume is integer and handle NaN values
        df['volume'] = df['volume'].fillna(0).astype(int)
        
        # Remove any rows with NaN values in price columns
        df = df.dropna(subset=['open', 'high', 'low', 'close'])
        
        print(f"Fetched {len(df)} records from {df['date'].min()} to {df['date'].max()}")
        return df[['date', 'open', 'high', 'low', 'close', 'volume']]
    
    except Exception as e:
        print(f"Error fetching {stock_code} data: {str(e)}")
        return None

def upload_to_supabase(df, stock_code):
    """Upload data to Supabase, avoiding duplicates"""
    try:
        table_name = stock_code.lower()
        
        # Get existing dates from Supabase
        response = supabase.table(table_name)\
            .select('date')\
            .execute()
        
        existing_dates = set(row['date'] for row in response.data)
        
        # Filter out existing dates
        new_data = df[~df['date'].isin(existing_dates)]
        
        if len(new_data) > 0:
            print(f"\nUploading {len(new_data)} new records for {stock_code}...")
            print(f"Date range: {new_data['date'].min()} to {new_data['date'].max()}")
            
            # Convert DataFrame to list of dictionaries
            records = new_data.to_dict('records')
            
            # Upload in batches to avoid request size limits
            batch_size = 500
            total_uploaded = 0
            
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                try:
                    supabase.table(table_name).insert(batch).execute()
                    total_uploaded += len(batch)
                    print(f"Uploaded {total_uploaded}/{len(new_data)} records...")
                except Exception as e:
                    print(f"Error uploading batch for {stock_code}: {str(e)}")
                    continue
            
            print(f"Successfully processed {total_uploaded} new records for {stock_code}")
            return True
        else:
            print(f"No new data to add for {stock_code}")
            return True
            
    except Exception as e:
        print(f"Error uploading {stock_code} data: {str(e)}")
        return False

def process_stock(stock_code, company_name):
    """Process a single stock"""
    print(f"\nProcessing {company_name} ({stock_code})...")
    
    # Verify table exists
    if not verify_table_exists(stock_code):
        print(f"Please create table for {stock_code} first")
        return False
    
    # Fetch data
    df = fetch_stock_data(stock_code)
    if df is not None and not df.empty:
        print(f"Fetched {len(df)} records from {df['date'].min()} to {df['date'].max()}")
        
        # Upload data
        if upload_to_supabase(df, stock_code):
            return True
    
    return False

def main():
    successful_stocks = []
    failed_stocks = []
    
    total_stocks = len(BIST30_STOCKS)
    current_stock = 0
    
    for stock_code, company_name in BIST30_STOCKS.items():
        current_stock += 1
        print(f"\nProcessing stock {current_stock}/{total_stocks}")
        
        try:
            if process_stock(stock_code, company_name):
                successful_stocks.append(stock_code)
            else:
                failed_stocks.append(stock_code)
            
            # Add a delay between stocks to avoid rate limiting
            time.sleep(2)
            
        except Exception as e:
            print(f"Error processing {stock_code}: {str(e)}")
            failed_stocks.append(stock_code)
    
    # Print summary
    print("\nProcessing complete!")
    print(f"Successfully processed {len(successful_stocks)} stocks: {', '.join(successful_stocks)}")
    if failed_stocks:
        print(f"Failed to process {len(failed_stocks)} stocks: {', '.join(failed_stocks)}")

if __name__ == "__main__":
    main() 