"""
数据存储管理
"""
from datetime import datetime
from pathlib import Path
from typing import Optional, Union

import polars as pl


class Storage:
    """数据存储管理"""
    
    def __init__(self, data_dir: Union[str, Path]):
        self.data_dir = Path(data_dir)
        
    def get_path(self, broker: str, market: str, data_type: str, 
                 symbol: str, freq: Optional[str] = None, date: Optional[datetime] = None) -> Path:
        """获取数据文件路径"""
        if freq:
            filename = f"{symbol}_{freq}_{date.strftime('%Y%m%d')}.parquet"
        else:
            filename = f"{symbol}_{date.strftime('%Y%m%d')}.parquet"
            
        return self.data_dir / broker / market / data_type / filename
    
    async def save_data(self, df: pl.DataFrame, path: Path):
        """保存数据"""
        path.parent.mkdir(parents=True, exist_ok=True)
        df.write_parquet(path)
        
    async def load_data(self, path: Path) -> pl.DataFrame:
        """加载数据"""
        if not path.exists():
            return pl.DataFrame()
        return pl.read_parquet(path)
