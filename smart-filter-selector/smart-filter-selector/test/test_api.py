import requests
import json
import logging
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint."""
    logger.info("\n" + "="*60)
    logger.info("🏥 Testing Health Endpoint")
    logger.info("="*60)

    response = requests.get(f"{BASE_URL}/health")
    logger.info(f"Status Code: {response.status_code}")
    logger.info(f"Response: {json.dumps(response.json(), indent=2)}")

    return response.status_code == 200

def test_query(query_text, max_filters=10, min_confidence=0.6):
    """Test query analysis endpoint."""
    # logger already imported and initialized at top
    logger.info("\n" + "="*60)
    logger.info(f"🔍 Testing Query: '{query_text}'")
    logger.info("="*60)

    payload = {
        "query": query_text,
        "options": {
            "maxFiltersPerCategory": max_filters,
            "minConfidence": min_confidence
        }
    }

    response = requests.post(
        f"{BASE_URL}/api/filter/analyze-query",
        json=payload,
        headers={"Content-Type": "application/json"}
    )

    logger.info(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        logger.info(f"\n📊 Results:")
        logger.info(f"   Query: {result.get('query')}")
        logger.info(f"   Processing Time: {result.get('processingTime')}")

        if 'stages' in result:
            logger.info(f"   Embedding Search: {result['stages'].get('embedding_search')}")
            logger.info(f"   LLM Refinement: {result['stages'].get('llm_refinement')}")

        logger.info(f"\n🎯 Reduced Filters:")
        for category, values in result.get('reducedFilters', {}).items():
            confidence = result.get('confidence', {}).get(category, 0)
            logger.info(f"\n   {category} (confidence: {confidence:.2f}):")
            if isinstance(values, list):
                for v in values[:5]:  # Show first 5
                    if isinstance(v, dict):
                        logger.info(f"      - {v.get('name', v)}")
                    else:
                        logger.info(f"      - {v}")
            elif isinstance(values, dict):
                for subcat, subvalues in values.items():
                    logger.info(f"      {subcat}:")
                    for v in subvalues[:3]:  # Show first 3
                        if isinstance(v, dict):
                            logger.info(f"         - {v.get('name', v)}")
                        else:
                            logger.info(f"         - {v}")

        logger.info(f"\n💡 Reasoning:")
        for category, reason in result.get('reasoning', {}).items():
            logger.info(f"   {category}: {reason}")
    else:
        logger.error(f"❌ Error: {response.text}")

    return response.status_code == 200

def run_all_tests():
    """Run all test queries."""
    # logger already imported and initialized at top
    logger.info("\n" + "🚀" * 30)
    logger.info("STARTING API TESTS")
    logger.info("🚀" * 30)

    # Test 1: Health check
    if not test_health():
        logger.error("\n❌ Health check failed! Make sure the service is running.")
        return

    # Test queries
    test_queries = [
        "railway signaling expert with ERTMS and SCADE experience",
        "nuclear power plant instrumentation engineer",
        "metro automation CBTC specialist",
        "Python developer for smart grid energy systems",
        "civil engineer for tunnel infrastructure",
        "cybersecurity expert for railway systems"
    ]

    for query in test_queries:
        test_query(query)

    logger.info("\n" + "="*60)
    logger.info("✅ All Tests Completed!")
    logger.info("="*60 + "\n")

if __name__ == '__main__':
    run_all_tests()