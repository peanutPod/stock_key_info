import utils
import pandas as pd
import os
from yi_shi_zhu_xing import stocks
dir_name = "衣食住行"

# update
# pip install akshare --upgrade -i https://pypi.org/simple

g_start_year = "2015"
g_start_md = "0101"
g_end_year = "2025"
g_end_md = "0906"
cur_ratio = 0.5


if __name__ == "__main__":

    for stock in stocks:
        print(f"Processing stock: {stock['stock_id']}")
        stock_id = stock["stock_id"]
        start_year = g_start_year
        start_md = g_start_md
        end_year = g_end_year
        end_md = g_end_md
        cur_ratio = cur_ratio
        stock_name = stock["stock_name"]

        # 获取各数据
        key_indicator_ths = utils.get_key_indicator_ths(stock_id, start_year, end_year)
        gdqy = utils.get_gdqy(stock_id, start_year, end_year)

        sxl = utils.get_sxl(stock_id, start_date=start_year + start_md, end_date=end_year + end_md)
        year_price = utils.get_year_gj(stock_id, start_year, end_year)

        # 提取年份
        key_indicator_ths["年份"] = key_indicator_ths["报告期"].astype(str).str[:4].astype(int)
        sxl["年份"] = sxl["数据日期"].dt.year
        gdqy["年份"] = gdqy["报告期"].astype(str).str[:4].astype(int)
        year_price["年份"] = year_price["日期"].dt.year

        # 按年份合并
        merged_df = key_indicator_ths.copy()
        merged_df = pd.merge(merged_df, sxl, on="年份", how="left")
        merged_df = pd.merge(merged_df, gdqy, on="年份", how="left")
        # merged_df = pd.merge(merged_df, zgb, on="年份", how="left")
        merged_df = pd.merge(merged_df, year_price, on="年份", how="left")

        drop_field = [
            "报告期_y",
            "年份",
            "股票代码",
            "股东户数统计截止日",
            "股东户数-本次",
            "扣非净利润",
            "扣非净利润同比增长率",
            "上市时间",
            "日期",
            "数据日期",
        ]
        merged_df = merged_df.drop(columns=drop_field, errors="ignore")

        # 修改报告期_x 列名为 报告期
        rename_field = {
            "报告期_x": "报告期",
            "*所有者权益（或股东权益）合计": "股东权益",
            "营业总收入": "营业总收入(亿)",
            "净利润": "净利润(亿)",
        }
        merged_df = merged_df.rename(columns=rename_field)

        # 确保报告期为字符串
        merged_df["报告期"] = merged_df["报告期"].astype(str)
        # 打印 merged_df 的字段名
        # print("merged_df 的字段名:", merged_df.columns.tolist())
        merged_df = merged_df.sort_values(by=["报告期"], ascending=[False])

        # 处理营业总收入，将“亿”转换为浮点数并支持“万”
        def convert_revenue(value):
            if "亿" in value:
                if "万亿" in value:
                    return float(value.replace("万亿", "").strip()) * 10000  # 去掉“万亿”并转换为浮点数，同时转换为亿
                else:
                    return float(value.replace("亿", "").strip())  # 去掉“亿”并转换为浮点数
            elif "万" in value:
                return float(value.replace("万", "").strip()) / 10000  # 去掉“万”并转换为浮点数，同时转换为亿
            else:
                return float(value)

        # 应用转换函数
        # print(merged_df["营业总收入(亿)"])
        merged_df["营业总收入(亿)"] = merged_df["营业总收入(亿)"].apply(convert_revenue)

        merged_df["总市值"]=round(merged_df["总股本"] * merged_df["收盘"],3) 

        merged_df["市销率"]=round(merged_df["总市值"]*1.0 / (merged_df["营业总收入(亿)"]*1.0),4)

        # 将第一个数据乘以0.5
        if not merged_df.empty:  # 确保DataFrame不为空
            merged_df.iloc[0, merged_df.columns.get_loc("市销率")] *= cur_ratio

        selected_columns = [
            "报告期",
            "总市值",
            "总股本",
            "收盘",
            "市销率",
            "PEG值",
            "营业总收入(亿)",
            "营业总收入同比增长率",
            "净利润(亿)",
            "净利润同比增长率",
            "每股净资产",
            "总现金",
            "未分配利润",
            "销售净利率",
            "股东权益",
            "存货",
        ]

        # 筛选出实际存在于DataFrame中的列
        existing_columns = [col for col in selected_columns if col in merged_df.columns]

        # 只选择存在的列
        merged_df = merged_df[existing_columns]

        os.makedirs(dir_name, exist_ok=True)
        # 保存到csv
        merged_df.to_csv(f"{dir_name}/{stock_name}.csv", index=False, encoding="utf-8-sig")
