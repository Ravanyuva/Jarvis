from jarvis_advanced import WebResearcher
import time

def test_research():
    print("Initializing Researcher...")
    researcher = WebResearcher()
    
    query = "Who is the CEO of Google?"
    print(f"Testing search for: {query}")
    
    try:
        result = researcher.search_and_scrape(query)
        print("\n--- Result extracted ---")
        print(result[:500] + "...")
        print("------------------------")
        
        if "Sundar Pichai" in result or "CEO" in result:
            print("[SUCCESS] Found relevant keywords.")
        else:
            print("[WARNING] Might not have found relevant info, check output.")
            
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")

if __name__ == "__main__":
    test_research()
