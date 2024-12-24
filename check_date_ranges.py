import os
from supabase import create_client

# Supabase configuration
SUPABASE_URL = 'https://joeyaqjjtnhoapgacazd.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpvZXlhcWpqdG5ob2FwZ2FjYXpkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzUwNjAxMzMsImV4cCI6MjA1MDYzNjEzM30.NGf0s9yYGlG-qK-eVVv0HL4sak0UrMO26Kjs3YxnC4o'

# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# BIST30 Stock List
BIST30_STOCKS = [
    'akbnk', 'arclk', 'asels', 'bimas', 'ekgyo', 'eregl', 'froto', 
    'garan', 'hekts', 'isgyo', 'kchol', 'kozaa', 'kozal', 'krdmd', 
    'odas', 'oyakc', 'petkm', 'pgsus', 'sahol', 'sasa', 'sise', 
    'tavhl', 'tcell', 'thyao', 'toaso', 'tuprs', 'ulker', 'vakbn', 
    'vestl', 'ykbnk'
]

def check_date_range(stock):
    try:
        # Get earliest date
        earliest = supabase.table(stock).select('date').order('date', desc=False).limit(1).execute()
        # Get latest date
        latest = supabase.table(stock).select('date').order('date', desc=True).limit(1).execute()
        # Get total count
        count = supabase.table(stock).select('*', count='exact').execute()
        
        if earliest.data and latest.data and count.count is not None:
            return {
                'stock': stock.upper(),
                'earliest': earliest.data[0]['date'].split('T')[0],
                'latest': latest.data[0]['date'].split('T')[0],
                'total_records': count.count
            }
        else:
            return {
                'stock': stock.upper(),
                'error': 'No data found'
            }
    except Exception as e:
        return {
            'stock': stock.upper(),
            'error': str(e)
        }

def main():
    print("\nChecking date ranges for BIST30 stocks...")
    print("-" * 80)
    print(f"{'Stock':<10} {'Earliest Date':<15} {'Latest Date':<15} {'Total Records':<15}")
    print("-" * 80)
    
    for stock in BIST30_STOCKS:
        result = check_date_range(stock)
        if 'error' in result:
            print(f"{result['stock']:<10} Error: {result['error']}")
        else:
            print(f"{result['stock']:<10} {result['earliest']:<15} {result['latest']:<15} {result['total_records']:<15}")
    
    # Also check USD/TRY exchange rates
    result = check_date_range('usdtry')
    print("\nUSD/TRY Exchange Rate Range:")
    if 'error' in result:
        print(f"Error: {result['error']}")
    else:
        print(f"Earliest: {result['earliest']}")
        print(f"Latest: {result['latest']}")
        print(f"Total Records: {result['total_records']}")

if __name__ == "__main__":
    main() 