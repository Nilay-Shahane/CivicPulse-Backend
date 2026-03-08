import time
from database.supabase import supabase

from routers.search import run_sentiment_pipeline

POLICY_MAP = {
    'pm-kisan': 'PM KISAN scheme',
    'ayushman-bharat': 'Ayushman Bharat health insurance',
    'nep-2020': 'National Education Policy 2020',
    'atmanirbhar-bharat': 'Atmanirbhar Bharat self reliant India',
    'digital-india': 'Digital India initiative',
    'make-in-india': 'Make in India manufacturing',
    'swachh-bharat': 'Swachh Bharat Clean India Mission',
    'smart-cities': 'Smart Cities Mission India',
    'beti-bachao-beti-padhao': 'Beti Bachao Beti Padhao scheme',
    'jal-jeevan-mission': 'Jal Jeevan Mission water supply',
    'ujjwala-yojana': 'Ujjwala Yojana LPG scheme',
    'skill-india': 'Skill India training program',
    'aadhaar': 'Aadhaar UIDAI card',
    'upi': 'UPI unified payments interface',
    'pm-awas-yojana': 'PM Awas Yojana housing scheme',
    'mudra-yojana': 'MUDRA Yojana loan scheme',
    'jan-dhan-yojana': 'Jan Dhan Yojana bank account',
    'startup-india': 'Startup India initiative',
    'national-solar-mission': 'National Solar Mission India',
    'plastic-ban': 'India plastic ban policy',
    'mid-day-meal': 'Mid Day Meal Scheme India',
    'msp-reforms': 'MSP minimum support price reforms',
    'digilocker': 'DigiLocker digital documents',
    'stand-up-india': 'Stand Up India loan scheme',
    'poshan-abhiyaan': 'POSHAN Abhiyaan nutrition mission',
}

def run_scheduled_sentiment_analysis():
    print("Running scheduled sentiment analysis...")
    try:
        response = supabase.table("tracked_policies").select("policy_id").execute()
        if not response.data:
            return

        unique_ids = set([item['policy_id'] for item in response.data])

        for p_id in unique_ids:
            # Look up the search query using the map
            query = POLICY_MAP.get(p_id)
            
            if not query:
                print(f"Skipping {p_id}: No search query found in map.")
                continue

            print(f"Processing: {p_id} with query: {query}")
            
            try:
                full_result = run_sentiment_pipeline(query) 
                storage_data = {
                    "query": full_result.get("query"),
                    "stats": full_result.get("stats")
                }

                supabase.table("policy_sentiment_history").insert({
                    "policy_id": p_id,
                    "analysis_data": storage_data
                }).execute()
                
                print(f"Successfully saved stats for {p_id}")
                time.sleep(10)
                
            except Exception as e:
                print(f"Error analyzing {p_id}: {e}")

    except Exception as e:
        print(f"Cronjob failed: {e}")