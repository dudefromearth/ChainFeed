#!/usr/bin/env python3
"""
Expiration Inspector CLI
Usage examples:
  python tools/expiration_cli.py --symbol SPX --check-date 2025-10-17
  python tools/expiration_cli.py --symbol ES --next
  python tools/expiration_cli.py --symbol SPX --list
  python tools/expiration_cli.py --symbol SPX --summary
"""

import argparse
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils.expiration_utils import (
    is_valid_expiration,
    get_next_valid_expiration,
    list_valid_expirations,
    summarize_expiration_status,
)

def main():
    parser = argparse.ArgumentParser(description="Inspect valid option expiration dates for a symbol.")
    parser.add_argument("--symbol", required=True, help="Underlying symbol (e.g. SPX, ES)")
    parser.add_argument("--check-date", help="Check if a specific expiration date is valid (YYYY-MM-DD)")
    parser.add_argument("--next", action="store_true", help="Get the next available expiration date")
    parser.add_argument("--list", action="store_true", help="List all valid expirations up to 10 DTE")
    parser.add_argument("--summary", action="store_true", help="Show expiration status summary")
    parser.add_argument("--max-dte", type=int, default=10, help="Max DTE range (default: 10)")

    args = parser.parse_args()
    symbol = args.symbol.upper()

    # Validation
    if not (args.check_date or args.next or args.list or args.summary):
        parser.print_help()
        sys.exit(1)

    if args.check_date:
        valid = is_valid_expiration(symbol, args.check_date)
        print(f"✅ {args.check_date} is a valid expiration for {symbol}" if valid else f"❌ {args.check_date} is NOT valid for {symbol}")

    if args.next:
        next_exp = get_next_valid_expiration(symbol, from_date=args.check_date)
        if next_exp:
            print(f"➡️ Next valid expiration after {args.check_date or 'today'}: {next_exp}")
        else:
            print("⚠️ No valid future expiration found.")

    if args.list:
        exps = list_valid_expirations(symbol, limit_dte=args.max_dte)
        print(f"📆 Valid expirations for {symbol} (up to {args.max_dte} DTE):\n" + "\n".join(exps))

    if args.summary:
        summary = summarize_expiration_status(symbol, max_dte=args.max_dte)
        print("🔎 Expiration Summary:")
        for k, v in summary.items():
            print(f"  {k}: {v}")

if __name__ == "__main__":
    main()