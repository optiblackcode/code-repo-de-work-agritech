import os
import json
from datetime import datetime, timedelta
from google.ads.googleads.client import GoogleAdsClient
from google.oauth2 import service_account


CONFIG = {
    "developer_token": "UfwukMYOFwQLFsCXVjjtzw",
    "login_customer_id": "6385295998", 
    "customer_id": "1849790507", 
    "service_account_file": "service-account-key.json", 
    "scopes": ["https://www.googleapis.com/auth/adwords"],
}

def get_service_account_credentials():
    """Creates credentials from service account JSON file."""
    try:
        credentials = service_account.Credentials.from_service_account_file(
            CONFIG["service_account_file"],
            scopes=CONFIG["scopes"]
        )
        return credentials
    except FileNotFoundError:
        print(f"❌ Service account file '{CONFIG['service_account_file']}' not found!")
        print("Please download your service account JSON file from Google Cloud Console")
        return None
    except Exception as e:
        print(f"❌ Error loading service account: {e}")
        return None

def get_google_ads_client():
    """Initializes Google Ads client with service account credentials."""
    credentials = get_service_account_credentials()
    if not credentials:
        return None
    
    # Create client configuration
    client_config = {
        "developer_token": CONFIG["developer_token"],
        "login_customer_id": CONFIG["login_customer_id"],
        "use_proto_plus": True,
    }
    
    # Initialize client with service account credentials
    client = GoogleAdsClient(
        credentials=credentials,
        developer_token=CONFIG["developer_token"],
        login_customer_id=CONFIG["login_customer_id"],
        use_proto_plus=True
    )
    
    return client

def test_google_ads_connection():
    """Tests if the API connection works with service account."""
    try:
        client = get_google_ads_client()
        if not client:
            return False
            
        service = client.get_service("GoogleAdsService")
        
        query = "SELECT customer.id, customer.descriptive_name FROM customer"
        request = client.get_type("SearchGoogleAdsRequest")
        request.customer_id = CONFIG["customer_id"]
        request.query = query
        
        response = service.search(request=request)
        for row in response:
            print(f"✅ Success! Connected to account: {row.customer.descriptive_name} (ID: {row.customer.id})")
            return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nPossible fixes:")
        print("- Ensure service account has Google Ads API access")
        print("- Check if service account is linked to your Google Ads account")
        print("- Verify the service account JSON file is correct")
        return False

def get_campaigns():
    """Example function to fetch campaigns."""
    try:
        client = get_google_ads_client()
        if not client:
            return []
            
        service = client.get_service("GoogleAdsService")
        
        query = """
            SELECT 
                campaign.id,
                campaign.name,
                campaign.status,
                campaign.advertising_channel_type
            FROM campaign
            WHERE campaign.status != 'REMOVED'
        """
        
        request = client.get_type("SearchGoogleAdsRequest")
        request.customer_id = CONFIG["customer_id"]
        request.query = query
        
        response = service.search(request=request)
        campaigns = []
        
        for row in response:
            campaign_data = {
                "id": row.campaign.id,
                "name": row.campaign.name,
                "status": row.campaign.status.name,
                "type": row.campaign.advertising_channel_type.name
            }
            campaigns.append(campaign_data)
            print(f"📊 Campaign: {campaign_data['name']} (ID: {campaign_data['id']}) - Status: {campaign_data['status']}")
        
        return campaigns
        
    except Exception as e:
        print(f"❌ Error fetching campaigns: {e}")
        return []

def get_account_performance(days_back=7):
    """Gets account performance metrics for the last N days."""
    try:
        client = get_google_ads_client()
        if not client:
            return None
            
        service = client.get_service("GoogleAdsService")
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        query = f"""
            SELECT 
                metrics.impressions,
                metrics.clicks,
                metrics.cost_micros,
                metrics.conversions,
                segments.date
            FROM customer
            WHERE segments.date >= '{start_date.strftime('%Y-%m-%d')}'
            AND segments.date <= '{end_date.strftime('%Y-%m-%d')}'
        """
        
        request = client.get_type("SearchGoogleAdsRequest")
        request.customer_id = CONFIG["customer_id"]
        request.query = query
        
        response = service.search(request=request)
        
        total_impressions = 0
        total_clicks = 0
        total_cost = 0
        total_conversions = 0
        
        for row in response:
            total_impressions += row.metrics.impressions
            total_clicks += row.metrics.clicks
            total_cost += row.metrics.cost_micros
            total_conversions += row.metrics.conversions
        
        # Convert cost from micros to currency
        total_cost_currency = total_cost / 1_000_000
        
        performance = {
            "date_range": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
            "impressions": total_impressions,
            "clicks": total_clicks,
            "cost": round(total_cost_currency, 2),
            "conversions": total_conversions,
            "ctr": round((total_clicks / total_impressions * 100), 2) if total_impressions > 0 else 0,
            "cpc": round((total_cost_currency / total_clicks), 2) if total_clicks > 0 else 0
        }
        
        print(f"\n📈 Account Performance ({performance['date_range']}):")
        print(f"   Impressions: {performance['impressions']:,}")
        print(f"   Clicks: {performance['clicks']:,}")
        print(f"   Cost: ${performance['cost']:,}")
        print(f"   Conversions: {performance['conversions']}")
        print(f"   CTR: {performance['ctr']}%")
        print(f"   CPC: ${performance['cpc']}")
        
        return performance
        
    except Exception as e:
        print(f"❌ Error fetching performance data: {e}")
        return None

if __name__ == "__main__":
    print("🔍 Testing Google Ads API connection with Service Account...")
    
    if test_google_ads_connection():
        print("\n📋 Fetching campaigns...")
        campaigns = get_campaigns()
        
        print(f"\n📊 Found {len(campaigns)} campaigns")
        
        print("\n📈 Fetching account performance...")
        performance = get_account_performance(days_back=7)
    else:
        print("\n❌ Connection failed. Please check your service account setup.")