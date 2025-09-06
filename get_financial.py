import akshare as ak

#使用东财的借口
stock_id="300999"
stock_id_with_market =  "SZ" +stock_id




#百度股市通-财经日历-股息红利
# news_trade_notify_dividend_baidu_df = ak.news_trade_notify_dividend_baidu(date="20241107")
# print(news_trade_notify_dividend_baidu_df)



#新浪财经-财务分析-财务指标
"""
    输入参数

名称	类型	描述
symbol	str	symbol="600004"; 股票代码
start_year	str	start_year="2020"; 开始查询的时间

"""
# stock_financial_analysis_indicator_df = ak.stock_financial_analysis_indicator(symbol="600004", start_year="2020")
# print(stock_financial_analysis_indicator_df)

#东方财富网-股东人数
stock_zh_a_gdhs_detail_em_df = ak.stock_zh_a_gdhs_detail_em(symbol=stock_id)
print(stock_zh_a_gdhs_detail_em_df)


#东方财富网-数据中心-估值分析-每日互动-每日互动-估值分析
stock_value_em_df = ak.stock_value_em(symbol=stock_id)
print(stock_value_em_df)

