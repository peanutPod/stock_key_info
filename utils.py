import akshare as ak
import matplotlib.pyplot as plt
import pandas as pd


def get_stock_info(stock_id):
    """
    获取股票的上市时间，总股本，总市值
    """
    stock_individual_info_em_df = ak.stock_individual_info_em(symbol=stock_id)
    ipo_time = stock_individual_info_em_df._values[8][1]
    total_issue = round(stock_individual_info_em_df._values[3][1] / 100000000, 2)
    total_value = round(stock_individual_info_em_df._values[5][1] / 100000000, 2)

    # print("上市时间：", ipo_time)
    # print("总股本（单位：亿）：", total_issue)
    # print("总市值（单位：亿）：", total_value)

    df = pd.DataFrame([{
        "股票代码": stock_id,
        "上市时间": ipo_time,
        "总股本(亿)": total_issue,
        "总市值(亿)": total_value
    }])
    # df.to_csv(f"{stock_id}_info.csv", index=False, encoding="utf-8-sig")

    return df


def plot_stock_data(stock_id,start_date: str = "19700101",end_date: str = "20500101"):
    """
    绘制股票的收盘价和成交量图表
    """
    # 获取股票历史数据
    stock_zh_a_hist_df = ak.stock_zh_a_hist(
        symbol=stock_id, period="monthly", start_date=start_date, end_date=end_date, adjust="qfq"
    )

    # 仅保留start_date到end_date的数据
    stock_zh_a_hist_df["日期"] = pd.to_datetime(stock_zh_a_hist_df["日期"], errors="coerce").dt.date
    # start_year = int(start_date[:4])
    # end_year = int(end_date[:4])
    start_date = pd.to_datetime(start_date, format="%Y%m%d").date()
    end_date = pd.to_datetime(end_date, format="%Y%m%d").date()
    stock_zh_a_hist_df = stock_zh_a_hist_df[stock_zh_a_hist_df["日期"].between(start_date, end_date)]

    # 绘图
    fig, ax1 = plt.subplots(figsize=(12, 6))

    # 收盘价折线
    ax1.plot(stock_zh_a_hist_df["日期"], stock_zh_a_hist_df["收盘"], color='blue', label='收盘价')
    ax1.set_xlabel('data')
    ax1.set_ylabel('close_price', color='blue')
    ax1.tick_params(axis='y', labelcolor='blue')

    # 成交量柱状图
    ax2 = ax1.twinx()
    ax2.bar(stock_zh_a_hist_df["日期"], stock_zh_a_hist_df["成交量"], color='gray', alpha=0.3, label='成交量')
    ax2.set_ylabel('volume', color='gray')
    ax2.tick_params(axis='y', labelcolor='gray')

    fig.tight_layout()
    plt.title(f"{stock_id} clost_price&&volume")
    plt.savefig(f"{stock_id}_close_price_volum.png")  # 保存为图片文件



def get_key_indicator_ths(stock_id: str, start_time, end_time):
    """
    关键指标-同花顺
    获取年度和最新报告期数据，并合并保存
    只保留报告期在 start_time 和 end_time 之间的数据
    """
    # 年度数据
    annual_df = ak.stock_financial_abstract_ths(symbol=stock_id, indicator="按年度")
    selected_columns = [
        "报告期",
        "营业总收入",
        "营业总收入同比增长率",
        "净利润",
        "净利润同比增长率",
        "扣非净利润",
        "扣非净利润同比增长率",
        "每股净资产",
        "每股经营现金流",
        "销售净利率",
    ]
    annual_df = annual_df[selected_columns]
    # 只保留报告期在 start_time 和 end_time 之间的数据
    annual_df = annual_df[
        annual_df["报告期"].astype(int).between(int(start_time), int(end_time))
    ]
    annual_df = annual_df.sort_values("报告期", ascending=False)

    # 按报告期数据，只取最新一期
    report_df = ak.stock_financial_abstract_ths(symbol=stock_id, indicator="按报告期")
    report_df = report_df[selected_columns]
    report_df = report_df.sort_values("报告期", ascending=False)
    latest_report = report_df.head(1)

    # 合并年度和最新报告期数据
    merged_df = pd.concat([latest_report, annual_df], ignore_index=True)
    # merged_df.to_csv(f"{stock_id}_key_indicator_ths.csv", index=False, encoding="utf-8-sig")
    return merged_df


def get_gdhs(stock_id, start_date: str = "19700101", end_date: str = "20500101"):
    """查询股东户数，按日期区间筛选，并保存为csv"""
    # df = ak.stock_zh_a_gdhs_detail_em(symbol=stock_id)

    try:
        # 尝试获取股票详细信息
        df = ak.stock_zh_a_gdhs_detail_em(symbol=stock_id)
        
        # 如果获取的数据为空，抛出异常
        if df.empty:
            raise ValueError("获取的数据为空，请检查股票代码或数据源。")
        # 转换日期为datetime类型
        df["股东户数统计截止日"] = pd.to_datetime(df["股东户数统计截止日"])
        # 按日期区间筛选
        start_dt = pd.to_datetime(start_date, format="%Y%m%d")
        end_dt = pd.to_datetime(end_date, format="%Y%m%d")
        df = df[df["股东户数统计截止日"].between(start_dt, end_dt)]
        # 只保留需要的字段
        df = df[["股东户数统计截止日", "股东户数-本次", "户均持股市值", "股东户数-增减比例"]]
        # 户均持股市值换算成万元，保留两位有效数字
        df["户均持股市值"] = (df["户均持股市值"] / 10000).round(2)
        # 增减比例换算成百分比,这里本身得到的数据就是百分比
        df["股东户数-增减比例"] = df["股东户数-增减比例"]
        # 按年份分组，取每组最后一条
        df = df.sort_values("股东户数统计截止日",ascending=False).groupby(df["股东户数统计截止日"].dt.year).head(1)
        # 保存为csv文件
        # df.to_csv(f"{stock_id}_gdhs.csv", index=False, encoding="utf-8-sig")
        # print(df)
        return df
    except ValueError as ve:
        print(f"ValueError: {ve}")

def plot_close_price_trend(stock_id, start_time, end_time):
    # 东方财富网-数据中心-估值分析-股票估值-股票估值
    stock_zh_a_hist_df = ak.stock_zh_a_hist(symbol=stock_id, period="monthly", start_date=start_time, end_date=end_time, adjust="qfq")
    # 绘制收盘价和日期图表
    plt.figure(figsize=(10, 5))
    plt.plot(stock_zh_a_hist_df["日期"], stock_zh_a_hist_df["收盘"], marker='o')
    plt.xlabel("data")
    plt.ylabel("close_price")
    plt.title(f"{stock_id} close_price_trend")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f"{stock_id}_close_price_trend.png")  # 保存为图片文件
    plt.show()


def get_zysrxx(stock_id_with_market, start_year, end_year):

    stock_zygc_em_df = ak.stock_zygc_em(symbol=stock_id_with_market)
    # 报告日期转换为datetime类型
    stock_zygc_em_df["报告日期"] = pd.to_datetime(stock_zygc_em_df["报告日期"], errors="coerce")
    # 筛选2018-2025年数据
    mask = stock_zygc_em_df["报告日期"].dt.year.between(int(start_year),int(end_year) )
    filtered_df = stock_zygc_em_df[mask]

    # 仅保留地区为“境内”和“境外”的数据
    filtered_df = filtered_df[filtered_df["主营构成"].isin(["境内", "境外"])]

    # 去掉“分类类型”和“股票代码”两列
    filtered_df = filtered_df.drop(columns=["分类类型", "股票代码"])

    # 主营收入、主营成本、主营利润单位换算为亿元，保留两位小数
    for col in ["主营收入", "主营成本", "主营利润"]:
        if col in filtered_df.columns:
            filtered_df[col] = (filtered_df[col] / 1e8).round(2)

    # 去掉一年内若存在12月31日，则去掉本年内6月30日的信息
    def remove_june_if_december_exists(df):
        result = []
        for year, group in df.groupby(df["报告日期"].dt.year):
            dates = group["报告日期"].dt.strftime("%m-%d")
            if "12-31" in dates.values:
                group = group[group["报告日期"].dt.strftime("%m-%d") != "06-30"]
            result.append(group)
        return pd.concat(result)

    filtered_df = remove_june_if_december_exists(filtered_df)

    # 报告日期降序排列
    filtered_df = filtered_df.sort_values("报告日期", ascending=False)

    # 保存为 CSV 文件
    # filtered_df.to_csv(f"{stock_id_with_market}_zyxx.csv", index=False, encoding="utf-8-sig")

    # print(filtered_df)
    return filtered_df



def get_gdqy(stock_id, start_year, end_year):
    """
    获取股票股东权益数据，合并最新报告期和年度数据
    :param stock_id: 股票代码
    :param start_year: 起始年份
    :param end_year: 结束年份
    :return: 合并后的 DataFrame
    """
    columns_to_keep = [
        "报告期",
        "*所有者权益（或股东权益）合计",
        "存货",
        "总现金",
        "未分配利润"
    ]

    # 年度数据
    annual_df = ak.stock_financial_debt_ths(symbol=stock_id, indicator="按年度")
    # 仅保留存在的列
    existing_columns = [col for col in columns_to_keep if col in annual_df.columns]
    annual_df = annual_df[existing_columns]


    annual_df = annual_df[annual_df["报告期"].astype(int).between(int(start_year), int(end_year))]
    annual_df = annual_df.sort_values("报告期", ascending=False)

    # 按报告期数据，只取最新一期
    report_df = ak.stock_financial_debt_ths(symbol=stock_id, indicator="按报告期")
    report_df = report_df[existing_columns]
    report_df = report_df.sort_values("报告期", ascending=False)
    latest_report = report_df.head(1)

    # 合并年度和最新报告期数据
    merged_df = pd.concat([latest_report, annual_df], ignore_index=True)
    # merged_df.to_csv(f"{stock_id}_gdqy.csv", index=False, encoding="utf-8-sig")
    # print(merged_df)
    return merged_df


def get_every_zgb(stock_id_with_market_end,start_year="2020", end_year="2025"):
    """
    获取每年年末的总股本数据
    """
    # 获取股票数据
    stock_zh_a_gbjg_em_df = ak.stock_zh_a_gbjg_em(symbol=stock_id_with_market_end)
    # 选择保留的列
    filtered_df = stock_zh_a_gbjg_em_df[["变更日期", "总股本"]].copy()
    # 将变更日期转换为日期格式
    filtered_df["变更日期"] = pd.to_datetime(filtered_df["变更日期"], errors='coerce')
    # 筛选出2020年到2025年之间的数据
    filtered_df = filtered_df[
    (filtered_df["变更日期"] >= pd.to_datetime(f"{start_year}-01-01", errors='coerce')) &
    (filtered_df["变更日期"] <= pd.to_datetime(f"{end_year}-12-31", errors='coerce'))
]
    # 提取年份
    filtered_df["年份"] = filtered_df["变更日期"].dt.year
    # 按年份分组并取每个年份中最新的总股本
    annual_total_shares = filtered_df.sort_values("变更日期").groupby("年份").last().reset_index()
    annual_total_shares["总股本"] = round(annual_total_shares["总股本"]/1e8,2)

    # 生成缺失年份的列表
    all_years = pd.DataFrame({"年份": range(int(start_year), int(end_year)+1)})
    annual_total_shares = pd.merge(all_years, annual_total_shares, on="年份", how="left")

    # 用前一年的股本数填充缺失值
    annual_total_shares["总股本"] =  annual_total_shares["总股本"].ffill()

    drop_field=["变更日期"]
    annual_total_shares = annual_total_shares.drop(columns=drop_field, errors='ignore').sort_values(by=["年份"], ascending=[False])
    # 设置显示选项，确保以浮点数格式显示
    pd.set_option('display.float_format', '{:.6f}'.format)
    # 打印结果
    return annual_total_shares

def get_year_gj(stock_id,start_year="2020", end_year="2025"):
    # 获取股票历史数据
    stock_zh_a_hist_df = ak.stock_zh_a_hist(symbol=stock_id, period="daily", start_date=f"{start_year}0101", end_date=f'{end_year}1231', adjust="qfq")

    # 将日期列转换为日期时间格式
    stock_zh_a_hist_df["日期"] = pd.to_datetime(stock_zh_a_hist_df["日期"])

    # 按年份分组并获取每年的最后一个交易日数据
    last_trading_days = (stock_zh_a_hist_df
                        .sort_values("日期")
                        .groupby(stock_zh_a_hist_df["日期"].dt.year, as_index=False)
                        .last())

    selected_columns = [
        "日期",
        "收盘",
    ]
    last_trading_days = last_trading_days[selected_columns].sort_values("日期", ascending=False)


    # 打印结果
    # print(last_trading_days)
    return last_trading_days