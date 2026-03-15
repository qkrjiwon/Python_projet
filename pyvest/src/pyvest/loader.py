from pathlib import Path
import logging
import pickle
from datetime import datetime
from typing import Sequence

import pandas as pd
import yfinance as yf

from priceseries import PriceSeries

class DataLoader:
    
    def __init__(self, cache_dir: str =".cache") -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
    
    def _get_cache_path(
            self,
            ticker: str,
            price_col: str,
            dates: tuple[str, str]

    ):
        file_name = f"{ticker}_{price_col}_{dates[0]}_{dates[1]}"
        return self.cache_dir / file_name
    
    
    def _save_to_cache(
            self,
            cache_path: Path,
            ticker: str,
            prices: list[float],
            price_col: str,
            dates: list,
            start: str,
            end: str,
            )-> None: 
    
        data = {
            "ticker": ticker,
            "start": start,
            "end": end,
            "fetched_at": datetime.now().isoformat(),
            "n_prices": len(prices),
            "prices": prices,
            "dates": dates,
            "price_col": price_col,
        }
        with open(cache_path, 'wb') as f:
            pickle.dump(data, f)

    def _check_dates_overlab(self,
                             cached_start: pd.Timestamp,
                             cached_end: pd.Timestamp,
                             req_start: pd.Timestamp,
                             req_end : pd.Timestamp):
        pass
    

    def _load_from_cache(
            self,
            ticker: str,
            price_col: str,
            start_date: pd.Timestamp,
            end_date: pd.Timestamp
    ):
        if not self.cache_dir.exists():
            print("le dossier de cache n'existe pas")
            return (None, "miss", None)
        
        for file_path in self.cache_dir.iterdir():
            if not file_path.is_file() or file_path.suffix != ".pkl":
                continue

            name_parts = file_path.stem.split('_')
            if len(name_parts) < 4:
                    continue

            cached_ticker = name_parts[0]
            cached_col = name_parts[1]
            cached_start = pd.Timestamp(name_parts[2])
            cached_end = pd.Timestamp(name_parts[3])

            if cached_ticker != ticker or cached_col != price_col:
                continue
            
            cached_start = pd.to_datetime(cached_start)
            cached_end = pd.to_datetime(cached_end)

            status, gap_start, gap_end = self._check_date_overlap(
                    cached_start, cached_end, start_date, end_date
                )
            if status != "miss":
                    with open(file_path, 'rb') as f:
                        data = pickle.load(f)

                    # Reconstruire le DataFrame avec les dates
                    prices_list = data['prices']
                    dates_list = data.get('dates') # méthode pandas sur dataframe
                    
                    df = pd.DataFrame({price_col: prices_list})
                    
                    if dates_list is not None:
                        # Utiliser les dates réelles stockées
                        df.index = pd.to_datetime(dates_list)
                    else:
                        # Fallback: utiliser les jours ouvrés
                        date_range = pd.bdate_range(
                            start=cached_start, 
                            periods=len(df)
                        )
                        df.index = date_range

                    if status == "exact":
                        return (df, "exact", None)
                    elif status == "contains":
                        return (df, "contains", None)
                    elif status.startswith("overlap"):
                        return (df, status, (gap_start, gap_end))

        return (None, "miss", None)

        pass

    def fetch_single_ticker(
        self, 
        ticker: str, 
        price_col: str, 
        dates: tuple[str, str]
    ) -> PriceSeries:

        start_date = pd.Timestamp(dates[0])
        end_date = pd.Timestamp(dates[1])
        ticker_instance = yf.Ticker(ticker)
        df = ticker_instance.history(start = start_date, end = end_date)

        if df.empty:
            print(f"DataFrame vide pour {ticker}")
            return None

        if price_col not in df.columns:
            print(f"{price_col} n'est pas dans le DataFrame du ticker {ticker}")
            raise KeyError(f"{price_col} n'est pas dans le DataFrame du ticker {ticker}")
        prices = df.loc[:, price_col]
        date_list = df.index.tolist()

        if prices.empty : 
            print(f"Colonne {price_col} vide pour {ticker}")
            return None
        
        return PriceSeries(values=prices, name= price_col)
    pass


if __name__ == "__main__":
    dataloader = DataLoader()
    result = dataloader.fetch_single_ticker('AAPL', 'Close', ("2024-01-01", "2024-01-10"))
    print(result)
    pass
