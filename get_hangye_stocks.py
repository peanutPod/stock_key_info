import utils
import pandas as pd
import os
import akshare as ak
from datetime import datetime

# 更新提示
# pip install akshare --upgrade -i https://pypi.org/simple

# 全局参数
g_start_year = "2015"
g_start_md = "0101"
g_end_year = "2025"
g_end_md = "0906"
cur_ratio = 0.5
MIN_NET_PROFIT = 1  # 最低净利润(亿)
MIN_REVENUE = 3     # 最低营业收入(亿) - 新增参数
CHECK_YEARS = 4     # 检查最近4年

# 提前创建主目录
output_dir = "all_stocks"
os.makedirs(output_dir, exist_ok=True)

# 获取业绩报表数据
stock_yjbb_em_df = ak.stock_yjbb_em(date="20250630")

# 过滤掉不符合条件的股票
filtered_df = stock_yjbb_em_df[
    ~stock_yjbb_em_df["股票代码"].str.startswith(('2','4', '8','9')) &
    ~stock_yjbb_em_df["股票简称"].str.contains('ST', case=False)
]

# 按行业分组
industry_groups = filtered_df.groupby("所处行业")

# 预定义转换函数（放在循环外，避免重复定义）
def convert_revenue(value):
    if pd.isna(value):
        return None
    value_str = str(value).strip()
    if "万亿" in value_str:
        return round(float(value_str.replace("万亿", "")) * 10000,3)
    elif "亿" in value_str:
        return round(float(value_str.replace("亿", "")),3)
    elif "万" in value_str:
        return round(float(value_str.replace("万", "")) / 10000,3)
    else:
        try:
            return round(float(value_str),3)
        except ValueError:
            return None

# 预定义要选择的列和要删除的列
drop_fields = [
    "报告期_y", "年份", "股票代码", "股东户数统计截止日",
    "股东户数-本次", "扣非净利润", "扣非净利润同比增长率",
    "上市时间", "日期", "数据日期"
]

rename_fields = {
    "报告期_x": "报告期",
    "*所有者权益（或股东权益）合计": "股东权益",
    "营业总收入": "营业总收入(亿)",
    "净利润": "净利润(亿)"
}

selected_columns = [
    "报告期", "总市值", "总股本", "收盘", "市销率", "PEG值",
    "营业总收入(亿)", "营业总收入同比增长率", "净利润(亿)",
    "净利润同比增长率", "每股净资产", "总现金", "未分配利润",
    "销售净利率", "股东权益", "存货"
]

# need_industry=['中药','互联网服务',"化学制药",'医疗器械',"半导体","小金属","有色金属","消费电子","生物制品",'电子元件','计算机设备','软件开发','通信服务','通信设备',"通用设备"]


# 遍历每个行业分组
for industry, group in industry_groups:
    # if industry not in need_industry:
    #     continue
    # 为每个行业创建目录
    industry_dir = os.path.join(output_dir, industry)
    os.makedirs(industry_dir, exist_ok=True)
    
    # 整理股票信息
    stocks_items = [
        {"stock_name": name, "stock_id": code.replace(".", "").replace(" ", "")}
        for code, name in zip(group["股票代码"], group["股票简称"])
    ]
    
    print(f"\n处理行业: {industry}，共 {len(stocks_items)} 只股票")
    # 批量处理行业内的股票
    for i, stock in enumerate(stocks_items, 1):
        stock_id = stock["stock_id"]
        stock_name = stock["stock_name"]
        print(f"({i}/{len(stocks_items)}) 处理股票: {stock_name} ({stock_id})")

        try:
            # 获取各数据
            key_indicator_ths = utils.get_key_indicator_ths(stock_id, g_start_year, g_end_year)
            gdqy = utils.get_gdqy(stock_id, g_start_year, g_end_year)

            sxl = utils.get_sxl(stock_id, 
                               start_date=g_start_year + g_start_md, 
                               end_date=g_end_year + g_end_md)
            if sxl is None:
                continue
                
            year_price = utils.get_year_gj(stock_id, g_start_year, g_end_year)

            # 提取年份
            key_indicator_ths["年份"] = key_indicator_ths["报告期"].astype(str).str[:4].astype(int)
            sxl["年份"] = sxl["数据日期"].dt.year
            gdqy["年份"] = gdqy["报告期"].astype(str).str[:4].astype(int)
            year_price["年份"] = year_price["日期"].dt.year

            # 按年份合并
            merged_df = key_indicator_ths.copy()
            merged_df = pd.merge(merged_df, sxl, on="年份", how="left")
            merged_df = pd.merge(merged_df, gdqy, on="年份", how="left")
            merged_df = pd.merge(merged_df, year_price, on="年份", how="left")

            # 移除不需要的列
            merged_df.drop(columns=drop_fields, errors="ignore", inplace=True)

            # 重命名列
            merged_df.rename(columns=rename_fields, inplace=True)

            # 确保报告期为字符串
            merged_df["报告期"] = merged_df["报告期"].astype(str)

            # 按报告期排序
            merged_df.sort_values(by=["报告期"], ascending=[False], inplace=True)

            # 处理营业总收入
            if "营业总收入(亿)" in merged_df.columns:
                merged_df["营业总收入(亿)"] = merged_df["营业总收入(亿)"].apply(convert_revenue)

            if "净利润(亿)" in merged_df.columns:
                merged_df["净利润(亿)"] = merged_df["净利润(亿)"].apply(convert_revenue)


            # 计算总市值和市销率
            if "总股本" in merged_df.columns and "收盘" in merged_df.columns:
                merged_df["总市值"] = round(merged_df["总股本"] * merged_df["收盘"], 3)
                
                if "营业总收入(亿)" in merged_df.columns:
                    merged_df["市销率"] = round(merged_df["总市值"] / merged_df["营业总收入(亿)"].replace(0, pd.NA), 4)
                    
                    if not merged_df.empty:
                        merged_df.iloc[0, merged_df.columns.get_loc("市销率")] *= cur_ratio

            # 筛选存在的列
            existing_columns = [col for col in selected_columns if col in merged_df.columns]
            merged_df = merged_df[existing_columns]

            # 保存到csv
            csv_path = os.path.join(industry_dir, f"{stock_name}.csv")
            merged_df.to_csv(csv_path, index=False, encoding="utf-8-sig")

        except Exception as e:
            continue

print("\n所有处理完成")
