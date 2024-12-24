from http.server import BaseHTTPRequestHandler
import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from update_daily_data import main as update_data

def handler(request, response):
    try:
        # Run the update
        update_data()
        
        # Return success response
        return {
            "statusCode": 200,
            "body": "Data update completed successfully"
        }
    except Exception as e:
        # Return error response
        return {
            "statusCode": 500,
            "body": f"Error updating data: {str(e)}"
        } 