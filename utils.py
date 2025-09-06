import akshare as ak
import matplotlib.pyplot as plt


def get_stock_info(stock_id,debug=False):
    """
    获取股票的上市时间，总股本，总市值
    """
    stock_individual_info_em_df = ak.stock_individual_info_em(symbol=stock_id)
    ipo_time=stock_individual_info_em_df._values[8][1]

    total_issue=round(stock_individual_info_em_df._values[3][1]/100000000,2)   

    total_value=round(stock_individual_info_em_df._values[5][1]/100000000,2) 

    if debug:
        print("上市时间：",ipo_time)
        print("总股本（单位：亿）：",total_issue)
        print("总市值（单位：亿）：",total_value) 

    return ipo_time,total_issue,total_value



def plot_stock_data(stock_id, start_date="20201001", end_date='20250906'):
    """
    绘制股票的收盘价和成交量图表
    """
    # 获取股票历史数据
    stock_zh_a_hist_df = ak.stock_zh_a_hist(
        symbol=stock_id, period="monthly", start_date=start_date, end_date=end_date, adjust="qfq"
    )

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
    plt.savefig("stock_chart.png")  # 保存为图片文件



def get_key_indicator_ths(stock_id: str):
    """
    关键指标-同花顺
    """
    stock_financial_abstract_ths_df = ak.stock_financial_abstract_ths(symbol=stock_id, indicator="按年度")
    # 按指定顺序筛选列
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
        "销售净利率"
    ]
    result_df = stock_financial_abstract_ths_df[selected_columns]
    print(result_df)
    # 保存为csv文件
    result_df.to_csv("key_indicator_ths.csv", index=False)
    return result_df
