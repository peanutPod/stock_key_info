import akshare as ak
import matplotlib.pyplot as plt

#使用东财的借口
stock_id="300999"
stock_id_with_market =  "SZ" +stock_id
start_time="20250101"
end_time="20250906"

stock_zh_ah_spot_em_df = ak.stock_zh_ah_spot_em()
print(stock_zh_ah_spot_em_df)

# 保存为 CSV 文件
stock_zh_ah_spot_em_df.to_csv("stock_zh_ah_spot_em.csv", index=False, encoding="utf-8-sig")