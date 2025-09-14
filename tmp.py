import akshare as ak
import pandas as pd

import pandas as pd
import akshare as ak

import pandas as pd
import akshare as ak
import pandas as pd
import akshare as ak


# import akshare as ak

# stock_financial_benefit_ths_df = ak.stock_financial_benefit_ths(symbol="000063", indicator="按年度")

# print(stock_financial_benefit_ths_df)

# stock_financial_benefit_ths_df.to_csv(f"tt.csv", index=False, encoding="utf-8-sig")

import akshare as ak

# stock_value_em_df = ak.stock_value_em(symbol="000028")
# print(stock_value_em_df)


def get_sxl(stock_id="000028", start_date: str = "19700101", end_date: str = "20500101"):
    """查询股东户数，按日期区间筛选，并保存为csv"""

    # 尝试获取股票详细信息
    df = ak.stock_value_em(symbol=stock_id)

    df["数据日期"] = pd.to_datetime(df["数据日期"])
    # 按日期区间筛选
    start_dt = pd.to_datetime(start_date, format="%Y%m%d")
    end_dt = pd.to_datetime(end_date, format="%Y%m%d")
    df = df[df["数据日期"].between(start_dt, end_dt)]
    # 只保留需要的字段
    df = df[["数据日期", "总市值", "总股本", "市销率", "PEG值"]]
    # 户均持股市值换算成万元，保留两位有效数字
    df["总股本"] = (df["总股本"] / 1e8).round(2)
    # 增减比例换算成百分比,这里本身得到的数据就是百分比
    # 按年份分组，取每组最后一条
    df = df.sort_values("数据日期", ascending=False).groupby(df["数据日期"].dt.year).head(1)
    print(df)

    return df


get_sxl()
