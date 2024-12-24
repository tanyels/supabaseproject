import os
import requests
import urllib3
from datetime import datetime

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.NotOpenSSLWarning)

# Supabase credentials
SUPABASE_URL = 'https://joeyaqjjtnhoapgacazd.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpvZXlhcWpqdG5ob2FwZ2FjYXpkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzUwNjAxMzMsImV4cCI6MjA1MDYzNjEzM30.NGf0s9yYGlG-qK-eVVv0HL4sak0UrMO26Kjs3YxnC4o'

# BIST30 stocks
BIST30_STOCKS = [
    'akbnk', 'arclk', 'asels', 'bimas', 'ekgyo', 'eregl', 'froto',
    'garan', 'kchol', 'kozaa', 'kozal', 'krdmd', 'petkm', 'pgsus',
    'sahol', 'sasa', 'sise', 'tavhl', 'tcell', 'thyao', 'toaso',
    'tuprs', 'vakbn', 'ykbnk'
]

def fetch_all_data(stock_symbol):
    all_data = []
    offset = 0
    page_size = 1000
    
    while True:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/{stock_symbol}",
            params={
                "select": "date",
                "order": "date.asc",
                "offset": offset,
                "limit": page_size
            },
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}"
            },
            verify=False
        )
        response.raise_for_status()
        data = response.json()
        
        if not data:
            break
            
        all_data.extend(data)
        if len(data) < page_size:
            break
            
        offset += page_size
        print(f"   Fetched {len(all_data)} records so far...")
    
    return all_data

def check_stock_data(stock_symbol):
    print(f"\nChecking {stock_symbol.upper()}...")
    
    try:
        data = fetch_all_data(stock_symbol)
        
        if not data:
            print(f"❌ {stock_symbol.upper()}: No data found")
            return False
        
        earliest_date = data[0]['date'].split('T')[0]
        latest_date = data[-1]['date'].split('T')[0]
        total_count = len(data)
        
        print(f"✅ {stock_symbol.upper()}")
        print(f"   First record: {earliest_date}")
        print(f"   Last record:  {latest_date}")
        print(f"   Total records: {total_count}")
        
        # Check for gaps in data
        dates = [datetime.strptime(record['date'].split('T')[0], '%Y-%m-%d') for record in data]
        date_gaps = []
        for i in range(1, len(dates)):
            gap = (dates[i] - dates[i-1]).days
            if gap > 5:  # More than 5 days gap (accounting for weekends)
                date_gaps.append((dates[i-1].strftime('%Y-%m-%d'), dates[i].strftime('%Y-%m-%d'), gap))
        
        if date_gaps:
            print("   ⚠️ Found data gaps:")
            for start, end, days in date_gaps[:3]:  # Show only first 3 gaps
                print(f"      {start} to {end} ({days} days)")
            if len(date_gaps) > 3:
                print(f"      ... and {len(date_gaps) - 3} more gaps")
        
        return True
        
    except Exception as e:
        print(f"❌ {stock_symbol.upper()}: Error - {str(e)}")
        return False

def main():
    print("Checking BIST30 stock data in Supabase...")
    print("=" * 50)
    
    successful_stocks = []
    failed_stocks = []
    
    for stock in BIST30_STOCKS:
        if check_stock_data(stock):
            successful_stocks.append(stock)
        else:
            failed_stocks.append(stock)
    
    print("\nSummary")
    print("=" * 50)
    print(f"Total stocks checked: {len(BIST30_STOCKS)}")
    print(f"Successful: {len(successful_stocks)}")
    print(f"Failed: {len(failed_stocks)}")
    
    if failed_stocks:
        print("\nFailed stocks:")
        for stock in failed_stocks:
            print(f"- {stock.upper()}")

if __name__ == "__main__":
    main() 