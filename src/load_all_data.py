"""Should contain the main function that combines all the data loading"""
from textual_data import gather_market_report_content_from_ids, gather_market_report_ids, gather_news_content_from_ids, gather_news_ids


def load_personal_text_for_user(user_id):
    """Load all the data for a specific user"""
    
    # Load the personal news and market reports
    market_report_ids = gather_market_report_ids(user_id, number=5, days_threshold=7)
    market_report_content = gather_market_report_content_from_ids(market_report_ids)
    
    news_ids = gather_news_ids(user_id, number=5, days_threshold=7)
    news_content = gather_news_content_from_ids(news_ids)
    
    return