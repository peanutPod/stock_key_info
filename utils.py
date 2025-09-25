import akshare as ak
import matplotlib.pyplot as plt
import pandas as pd



def plot_stock_data(stock_id, start_date: str = "19700101", end_date: str = "20500101"):
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
    ax1.plot(stock_zh_a_hist_df["日期"], stock_zh_a_hist_df["收盘"], color="blue", label="收盘价")
    ax1.set_xlabel("data")
    ax1.set_ylabel("close_price", color="blue")
    ax1.tick_params(axis="y", labelcolor="blue")

    # 成交量柱状图
    ax2 = ax1.twinx()
    ax2.bar(stock_zh_a_hist_df["日期"], stock_zh_a_hist_df["成交量"], color="gray", alpha=0.3, label="成交量")
    ax2.set_ylabel("volume", color="gray")
    ax2.tick_params(axis="y", labelcolor="gray")

    fig.tight_layout()
    plt.title(f"{stock_id} clost_price&&volume")
    plt.savefig(f"{stock_id}_close_price_volum.png")  # 保存为图片文件


def get_key_indicator_ths(stock_id: str, start_time, end_time,debug=False):
    """
    关键指标-同花顺-数据准确
    获取年度和最新报告期数据，并合并保存
    只保留报告期在 start_time 和 end_time 之间的数据
    """
    # 年度数据
    annual_df = ak.stock_financial_abstract_ths(symbol=stock_id, indicator="按年度")
    if debug:
        print("get_key_indicator_ths 的字段名:", annual_df.columns.tolist())
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
    annual_df = annual_df[annual_df["报告期"].astype(int).between(int(start_time), int(end_time))]
    annual_df = annual_df.sort_values("报告期", ascending=False)

    # 按报告期数据，只取最新一期
    report_df = ak.stock_financial_abstract_ths(symbol=stock_id, indicator="按报告期")
    report_df = report_df[selected_columns]
    report_df = report_df.sort_values("报告期", ascending=False)
    latest_report = report_df.head(1)

    # 合并年度和最新报告期数据
    merged_df = pd.concat([latest_report, annual_df], ignore_index=True)
    return merged_df


def plot_close_price_trend(stock_id, start_time, end_time):
    # 东方财富网-数据中心-估值分析-股票估值-股票估值
    stock_zh_a_hist_df = ak.stock_zh_a_hist(
        symbol=stock_id, period="monthly", start_date=start_time, end_date=end_time, adjust="qfq"
    )
    # 绘制收盘价和日期图表
    plt.figure(figsize=(10, 5))
    plt.plot(stock_zh_a_hist_df["日期"], stock_zh_a_hist_df["收盘"], marker="o")
    plt.xlabel("data")
    plt.ylabel("close_price")
    plt.title(f"{stock_id} close_price_trend")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f"{stock_id}_close_price_trend.png")  # 保存为图片文件
    plt.show()



def get_gdqy(stock_id, start_year, end_year,debug=False):
    """
    同发顺数据-数据准确
    :param stock_id: 股票代码
    :param start_year: 起始年份
    :param end_year: 结束年份
    :return: 合并后的 DataFrame
    """
    columns_to_keep = ["报告期", "*所有者权益（或股东权益）合计", "存货", "总现金", "未分配利润"]

    # 年度数据
    annual_df = ak.stock_financial_debt_ths(symbol=stock_id, indicator="按年度")

    # 仅保留存在的列
    existing_columns = [col for col in columns_to_keep if col in annual_df.columns]
    annual_df = annual_df[existing_columns]

    if debug:
        print("get_gdqy 的字段名:", annual_df.columns.tolist())

    annual_df = annual_df[annual_df["报告期"].astype(int).between(int(start_year), int(end_year))]
    annual_df = annual_df.sort_values("报告期", ascending=False)

    # 按报告期数据，只取最新一期
    report_df = ak.stock_financial_debt_ths(symbol=stock_id, indicator="按报告期")
    report_df = report_df[existing_columns]
    report_df = report_df.sort_values("报告期", ascending=False)
    latest_report = report_df.head(1)

    # 合并年度和最新报告期数据
    merged_df = pd.concat([latest_report, annual_df], ignore_index=True)
    return merged_df



def get_year_gj(stock_id, start_year="2020", end_year="2025"):
    # 获取股票历史数据
    stock_zh_a_hist_df = ak.stock_zh_a_hist(
        symbol=stock_id, period="daily", start_date=f"{start_year}0101", end_date=f"{end_year}1231", adjust="qfq"
    )

    # 将日期列转换为日期时间格式
    stock_zh_a_hist_df["日期"] = pd.to_datetime(stock_zh_a_hist_df["日期"])

    # 按年份分组并获取每年的最后一个交易日数据
    last_trading_days = (
        stock_zh_a_hist_df.sort_values("日期").groupby(stock_zh_a_hist_df["日期"].dt.year, as_index=False).last()
    )

    selected_columns = [
        "日期",
        "收盘",
    ]
    last_trading_days = last_trading_days[selected_columns].sort_values("日期", ascending=False)

    # 打印结果
    # print(last_trading_days)
    return last_trading_days


def get_sxl(stock_id, start_date: str = "19700101", end_date: str = "20500101"):
    """查询股东户数，按日期区间筛选，并保存为csv"""

    # 尝试获取股票详细信息
    # df = ak.stock_value_em(symbol=stock_id)
    try:
        # 尝试获取数据
        df = ak.stock_value_em(symbol=stock_id)
    except Exception as e:
        # 捕获所有可能的异常并打印信息
        return None



    df["数据日期"] = pd.to_datetime(df["数据日期"])
    # 按日期区间筛选
    start_dt = pd.to_datetime(start_date, format="%Y%m%d")
    end_dt = pd.to_datetime(end_date, format="%Y%m%d")
    df = df[df["数据日期"].between(start_dt, end_dt)]
    # 只保留需要的字段
    df = df[["数据日期", "总股本"]]
    # df = df[["数据日期", "总股本", "PEG值"]]
    # 户均持股市值换算成万元，保留两位有效数字
    df["总股本"] = (df["总股本"] / 1e8).round(4)
    # 增减比例换算成百分比,这里本身得到的数据就是百分比
    # 按年份分组，取每组最后一条
    df = df.sort_values("数据日期", ascending=False).groupby(df["数据日期"].dt.year).head(1)

    return df
