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

def fetch_usdtry_data():
    """Fetch historical USD/TRY exchange rate data using yfinance"""
    try:
        # Yahoo Finance symbol for USD/TRY
        symbol = "USDTRY=X"
        ticker = yf.Ticker(symbol)
        
        # Get data from 2000-01-01 to present
        start_date = "2000-01-01"
        df = ticker.history(start=start_date, end=None)
        
        # Reset index to make date a column
        df = df.reset_index()
        
        # Convert date to string format
        df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')
        
        # Select and rename only the columns we need
        df = df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]
        df = df.rename(columns={
            'Date': 'date',
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume'
        })
        
        # Convert DataFrame to list of dictionaries
        records = df.to_dict('records')
        return records
    except Exception as e:
        print(f"Error fetching USD/TRY data: {str(e)}")
        return None

def insert_usdtry_data(data: list):
    """Insert historical data into the USD/TRY table"""
    if not data:
        return False
    
    try:
        table_name = 'usdtry'
        
        # Insert data in batches of 100 records
        batch_size = 100
        total_batches = (len(data) + batch_size - 1) // batch_size
        
        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]
            try:
                response = supabase.table(table_name).insert(batch).execute()
                print(f"Inserted batch {i//batch_size + 1} of {total_batches}")
            except Exception as e:
                if "duplicate key value violates unique constraint" in str(e):
                    print(f"Skipping duplicate records in batch {i//batch_size + 1}")
                else:
                    raise e
            
            # Add a small delay between batches to avoid rate limiting
            time.sleep(0.5)
            
        return True
    except Exception as e:
        print(f"Error inserting USD/TRY data: {str(e)}")
        return False

def main():
    """Main function to fetch and insert USD/TRY historical data"""
    print("Fetching USD/TRY historical data...")
    data = fetch_usdtry_data()
    
    if data:
        print(f"Found {len(data)} records. Inserting data...")
        if insert_usdtry_data(data):
            print("Successfully processed USD/TRY data")
        else:
            print("Failed to insert USD/TRY data")
    else:
        print("No data fetched for USD/TRY")

if __name__ == "__main__":
    main() 