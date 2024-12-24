from fastapi import FastAPI, HTTPException
from supabase import create_client, Client
import os
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel

app = FastAPI()

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://joeyaqjjtnhoapgacazd.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class ExchangeRate(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: Optional[float] = None

@app.get("/")
def read_root():
    return {"message": "Welcome to the USD/TRY Exchange Rate API"}

@app.get("/api/usdtry/latest")
def get_latest_rate():
    try:
        response = supabase.table("usdtry").select("*").order("date", desc=True).limit(1).execute()
        if response.data:
            return response.data[0]
        raise HTTPException(status_code=404, detail="No exchange rate data found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/usdtry/history")
def get_historical_rates(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 100
):
    try:
        query = supabase.table("usdtry").select("*")
        
        if start_date:
            query = query.gte("date", start_date)
        if end_date:
            query = query.lte("date", end_date)
            
        response = query.order("date", desc=True).limit(limit).execute()
        
        if response.data:
            return response.data
        return []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/usdtry/stats")
def get_exchange_rate_stats():
    try:
        # Get latest rate
        latest = supabase.table("usdtry").select("*").order("date", desc=True).limit(1).execute()
        
        # Get stats for the last 30 days
        thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        monthly_stats = supabase.table("usdtry").select("*").gte("date", thirty_days_ago).execute()
        
        if latest.data and monthly_stats.data:
            latest_rate = latest.data[0]
            monthly_data = monthly_stats.data
            
            # Calculate monthly stats
            monthly_high = max(rate["high"] for rate in monthly_data)
            monthly_low = min(rate["low"] for rate in monthly_data)
            monthly_avg = sum(rate["close"] for rate in monthly_data) / len(monthly_data)
            
            return {
                "latest_rate": latest_rate["close"],
                "latest_date": latest_rate["date"],
                "monthly_high": monthly_high,
                "monthly_low": monthly_low,
                "monthly_avg": monthly_avg,
                "monthly_change_percent": ((latest_rate["close"] - monthly_data[-1]["close"]) / monthly_data[-1]["close"]) * 100
            }
        
        raise HTTPException(status_code=404, detail="No exchange rate data found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 