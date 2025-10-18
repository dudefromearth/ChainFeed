# test_fetch.py
from core.chain_fetcher import fetch_option_chain

data = fetch_option_chain("SPX", "2025-10-17")
print(f"Contracts fetched: {len(data)}")