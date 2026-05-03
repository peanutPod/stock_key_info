import argparse
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import akshare as ak
import numpy as np
import pandas as pd
from tqdm import tqdm

import utils


ROOT_DIR = Path("/home/peanut/stock_key_info/all_stocks_20260505")
TEMPLATE_ROOT = Path("/home/peanut/stock_key_info/all_stocks_copy")
DONE_FILE_NAME = "scrape_done.csv"
START_YEAR = "2010" 
END_YEAR = "2026"
END_DATE = f"{END_YEAR}0331"
DEFAULT_WORKERS = 4

OUTPUT_COLUMNS = [
    "报告期",
    "总市值",
    "总股本",
    "收盘",
    "市销率",
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

EXPLICIT_INDUSTRY_MAP = {
    "IT服务": "软件开发",
    "一般零售": "商业百货",
    "专业工程": "工程建设",
    "专业连锁": "商业百货",
    "个护用品": "美容护理",
    "乘用车": "汽车整车",
    "互联网电商": "互联网服务",
    "休闲食品": "食品饮料",
    "体育": "文化传媒",
    "元件": "电子元件",
    "其他家电": "家电行业",
    "其他电子": "消费电子",
    "其他电源设备": "电源设备",
    "养殖业": "农牧饲渔",
    "军工电子": "航天航空",
    "农业综合": "农牧饲渔",
    "农产品加工": "农牧饲渔",
    "农化制品": "农药兽药",
    "冶钢原料": "钢铁行业",
    "出版": "文化传媒",
    "动物保健": "农药兽药",
    "包装印刷": "造纸印刷",
    "化妆品": "美容护理",
    "化学纤维": "化纤行业",
    "医疗美容": "美容护理",
    "厨卫电器": "家电行业",
    "商用车": "汽车整车",
    "地面兵装": "航天航空",
    "基础建设": "工程建设",
    "塑料": "塑料制品",
    "家居用品": "家用轻工",
    "家电零部件": "家电行业",
    "小家电": "家电行业",
    "工业金属": "有色金属",
    "广告营销": "文化传媒",
    "影视院线": "文化传媒",
    "房屋建设": "工程建设",
    "摩托车及其他": "汽车整车",
    "数字媒体": "文化传媒",
    "文娱用品": "家用轻工",
    "旅游及景区": "旅游酒店",
    "旅游及酒店": "旅游酒店",
    "旅游零售": "旅游酒店",
    "普钢": "钢铁行业",
    "服装家纺": "纺织服装",
    "林业": "农牧饲渔",
    "橡胶": "橡胶制品",
    "水泥": "水泥建材",
    "油服工程": "石油行业",
    "油气开采": "石油行业",
    "游戏": "游戏",
    "炼化及贸易": "石油行业",
    "焦炭": "煤炭行业",
    "煤炭开采": "煤炭行业",
    "照明设备": "光学光电子",
    "燃气": "燃气",
    "物流": "物流行业",
    "特钢": "钢铁行业",
    "环保设备": "环保行业",
    "环境治理": "环保行业",
    "电力": "电力行业",
    "电视广播": "文化传媒",
    "白色家电": "家电行业",
    "白酒": "酿酒行业",
    "非白酒": "酿酒行业",
    "种植业": "农牧饲渔",
    "纺织制造": "纺织服装",
    "综合": "综合行业",
    "自动化设备": "专用设备",
    "航天装备": "航天航空",
    "航海装备": "船舶制造",
    "航空装备": "航天航空",
    "证券": "证券",
    "调味发酵品": "食品饮料",
    "贸易": "贸易行业",
    "轨交设备": "交运设备",
    "造纸": "造纸印刷",
    "酒店餐饮": "旅游酒店",
    "金属新材料": "小金属",
    "银行": "银行",
    "食品加工": "食品饮料",
    "饮料乳品": "食品饮料",
    "饰品": "珠宝首饰",
    "饲料": "农牧饲渔",
    "黑色家电": "家电行业",
    "房地产": "房地产开发",
    "渔业": "农牧饲渔",
    "钢铁": "钢铁行业",
}


def normalize_text(value):
    if pd.isna(value):
        return ""
    return str(value).replace(" ", "").strip()


def build_category_maps(root_dir: Path):
    top_level_dirs = {path.name for path in root_dir.iterdir() if path.is_dir()}
    second_level_parent = {}

    for parent in root_dir.iterdir():
        if not parent.is_dir():
            continue
        child_dirs = [child for child in parent.iterdir() if child.is_dir()]
        if not child_dirs:
            second_level_parent[parent.name] = parent.name
            continue
        for child in child_dirs:
            second_level_parent[child.name] = parent.name

    return top_level_dirs, second_level_parent


TOP_LEVEL_DIRS = set()
SECOND_LEVEL_PARENT = {}


def _create_industry_dirs_from_template(target_root: Path, template_root: Path):
    if not template_root.exists():
        raise FileNotFoundError(f"模板目录不存在: {template_root}")
    for path in template_root.rglob("*"):
        if path.is_dir():
            rel = path.relative_to(template_root)
            (target_root / rel).mkdir(parents=True, exist_ok=True)


def set_root_dir(root_dir: Path, template_root: Path = TEMPLATE_ROOT):
    global ROOT_DIR, TOP_LEVEL_DIRS, SECOND_LEVEL_PARENT

    if not root_dir.exists():
        root_dir.mkdir(parents=True, exist_ok=True)
        _create_industry_dirs_from_template(root_dir, template_root)

    ROOT_DIR = root_dir
    TOP_LEVEL_DIRS, SECOND_LEVEL_PARENT = build_category_maps(ROOT_DIR)


def load_done_codes(root_dir: Path) -> set[str]:
    done_path = root_dir / DONE_FILE_NAME
    if not done_path.exists():
        return set()
    df = pd.read_csv(done_path, dtype={"股票代码": str})
    return set(df["股票代码"].astype(str).str.zfill(6).tolist())


def append_done_record(record: dict, root_dir: Path):
    done_path = root_dir / DONE_FILE_NAME
    df = pd.DataFrame([record])
    if not done_path.exists():
        df.to_csv(done_path, index=False, encoding="utf-8-sig")
    else:
        df.to_csv(done_path, index=False, encoding="utf-8-sig", mode="a", header=False)


def normalize_industry(raw_industry: str):
    raw = normalize_text(raw_industry)
    if not raw:
        return None

    stripped = raw.rstrip("ⅠⅡⅢⅣV")
    if stripped in SECOND_LEVEL_PARENT or stripped in TOP_LEVEL_DIRS:
        return stripped
    if raw in SECOND_LEVEL_PARENT or raw in TOP_LEVEL_DIRS:
        return raw
    return EXPLICIT_INDUSTRY_MAP.get(stripped) or EXPLICIT_INDUSTRY_MAP.get(raw)


def resolve_output_path(stock_name: str, raw_industry: str):
    if not TOP_LEVEL_DIRS and not SECOND_LEVEL_PARENT:
        set_root_dir(ROOT_DIR)
    target_industry = normalize_industry(raw_industry)
    if not target_industry:
        return None, None

    if target_industry in SECOND_LEVEL_PARENT:
        parent = SECOND_LEVEL_PARENT[target_industry]
        if parent == target_industry:
            output_dir = ROOT_DIR / parent
        else:
            output_dir = ROOT_DIR / parent / target_industry
        return output_dir / f"{sanitize_filename(stock_name)}.csv", target_industry

    if target_industry in TOP_LEVEL_DIRS:
        return ROOT_DIR / target_industry / f"{sanitize_filename(stock_name)}.csv", target_industry

    return None, None


def sanitize_filename(stock_name: str):
    name = normalize_text(stock_name)
    for old, new in [("/", "_"), ("\\", "_"), (":", "_"), ("*", "_"), ('"', "_")]:
        name = name.replace(old, new)
    return name


def parse_amount_to_yi(value):
    if pd.isna(value):
        return None
    text = normalize_text(value)
    if not text or text == "False":
        return None
    try:
        if "万亿" in text:
            return round(float(text.replace("万亿", "")) * 10000, 3)
        if "亿" in text:
            return round(float(text.replace("亿", "")), 3)
        if "万" in text:
            return round(float(text.replace("万", "")) / 10000, 6)
        return round(float(text), 3)
    except ValueError:
        return None


def annualized_ps_ratio(report_period: str):
    period = str(report_period)
    if period.endswith("03-31"):
        return 0.25
    if period.endswith("06-30"):
        return 0.5
    if period.endswith("09-30"):
        return 0.75
    return 1.0


def fetch_current_universe():
    df = utils._call_with_retry(ak.stock_info_a_code_name)
    df = df.rename(columns={"code": "股票代码", "name": "股票简称"}).copy()
    df["股票简称"] = df["股票简称"].apply(normalize_text)

    filtered_df = df[
        ~df["股票简称"].str.upper().str.contains("ST", na=False)
        & ~df["股票简称"].str.contains("退", na=False)
        & ~df["股票代码"].astype(str).str.startswith(("200", "900"))
    ].copy()
    filtered_df.drop_duplicates(subset=["股票代码"], inplace=True)
    return filtered_df


def fetch_batch_industry_map():
    df = utils._call_with_retry(ak.stock_yjbb_em, date="20251231")
    df = df[["股票代码", "股票简称", "所处行业"]].copy()
    df["股票代码"] = df["股票代码"].astype(str)
    df["股票简称"] = df["股票简称"].apply(normalize_text)
    df["所处行业"] = df["所处行业"].apply(normalize_text)
    return dict(zip(df["股票代码"], df["所处行业"]))


def fetch_stock_industry(code: str):
    info_df = utils._call_with_retry(ak.stock_individual_info_em, symbol=code)
    info_map = dict(zip(info_df["item"], info_df["value"]))
    return normalize_text(info_map.get("行业", ""))


def build_empty_year_df(column_name: str):
    return pd.DataFrame(columns=[column_name, "年份"])


def ensure_year_column(df: pd.DataFrame, date_column: str):
    if df is None:
        return build_empty_year_df(date_column)
    result = df.copy()
    if "年份" not in result.columns:
        result["年份"] = pd.Series(dtype="Int64")
    if date_column in result.columns and not result.empty:
        result["年份"] = pd.to_datetime(result[date_column], errors="coerce").dt.year
    return result


def merge_stock_frames(stock_code: str):
    key_indicator_df = utils.get_key_indicator_ths(stock_code, START_YEAR, END_YEAR)
    gdqy_df = utils.get_gdqy(stock_code, START_YEAR, END_YEAR)
    sxl_df = utils.get_sxl(stock_code, start_date=f"{START_YEAR}0101", end_date=END_DATE)
    price_df = utils.get_year_gj_dfcf(stock_code, START_YEAR, END_YEAR)

    if key_indicator_df is None or key_indicator_df.empty:
        raise ValueError("关键指标为空")
    if gdqy_df is None or gdqy_df.empty:
        raise ValueError("资产负债指标为空")

    key_indicator_df = key_indicator_df.copy()
    gdqy_df = gdqy_df.copy()
    sxl_df = ensure_year_column(sxl_df, "数据日期")
    price_df = ensure_year_column(price_df, "日期")

    key_indicator_df["年份"] = key_indicator_df["报告期"].astype(str).str[:4].astype(int)
    gdqy_df["年份"] = gdqy_df["报告期"].astype(str).str[:4].astype(int)

    merged_df = key_indicator_df.copy()
    merged_df = pd.merge(merged_df, sxl_df, on="年份", how="left")
    merged_df = pd.merge(merged_df, gdqy_df, on="年份", how="left")
    merged_df = pd.merge(merged_df, price_df, on="年份", how="left")

    merged_df.drop(
        columns=[
            "报告期_y",
            "年份",
            "股票代码",
            "日期",
            "数据日期",
            "扣非净利润",
            "扣非净利润同比增长率",
            "每股经营现金流",
        ],
        errors="ignore",
        inplace=True,
    )
    merged_df.rename(
        columns={
            "报告期_x": "报告期",
            "*所有者权益（或股东权益）合计": "股东权益",
            "营业总收入": "营业总收入(亿)",
            "净利润": "净利润(亿)",
        },
        inplace=True,
    )

    merged_df["报告期"] = merged_df["报告期"].astype(str)
    merged_df.sort_values(by=["报告期"], ascending=[False], inplace=True)
    merged_df["营业总收入(亿)"] = merged_df["营业总收入(亿)"].apply(parse_amount_to_yi)

    merged_df["总股本"] = pd.to_numeric(merged_df["总股本"], errors="coerce")
    merged_df["收盘"] = pd.to_numeric(merged_df["收盘"], errors="coerce")

    merged_df["总市值"] = (merged_df["总股本"] * merged_df["收盘"]).round(3)
    revenue_series = pd.to_numeric(merged_df["营业总收入(亿)"], errors="coerce")
    market_cap_series = pd.to_numeric(merged_df["总市值"], errors="coerce")
    annualized_factor = pd.to_numeric(merged_df["报告期"].apply(annualized_ps_ratio), errors="coerce")
    ps_ratio = np.where(revenue_series > 0, market_cap_series / revenue_series * annualized_factor, np.nan)
    merged_df["市销率"] = pd.Series(ps_ratio, index=merged_df.index, dtype="float64").round(4)

    return merged_df[[column for column in OUTPUT_COLUMNS if column in merged_df.columns]]


def process_stock(stock_row, batch_industry_map, dry_run=False):
    stock_code = stock_row["股票代码"]
    stock_name = stock_row["股票简称"]
    raw_industry = batch_industry_map.get(stock_code)
    if not raw_industry:
        raw_industry = fetch_stock_industry(stock_code)

    output_path, mapped_industry = resolve_output_path(stock_name, raw_industry)
    if output_path is None:
        raise ValueError(f"无法映射行业: {raw_industry}")

    merged_df = merge_stock_frames(stock_code)
    if merged_df.empty:
        raise ValueError("合并结果为空")

    if not dry_run:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        merged_df.to_csv(output_path, index=False, encoding="utf-8-sig")

    return {
        "股票代码": stock_code,
        "股票简称": stock_name,
        "原始行业": raw_industry,
        "映射行业": mapped_industry,
        "输出路径": str(output_path),
    }


def cleanup_stale_files(expected_paths: set[str], dry_run=False):
    removed = []
    for csv_path in ROOT_DIR.rglob("*.csv"):
        path_str = str(csv_path)
        if path_str in expected_paths:
            continue
        removed.append(path_str)
        if not dry_run:
            csv_path.unlink()
    return removed


def output_exists_for_stock(stock_row, batch_industry_map) -> bool:
    raw_industry = batch_industry_map.get(stock_row["股票代码"])
    if not raw_industry:
        return False
    output_path, _ = resolve_output_path(stock_row["股票简称"], raw_industry)
    return output_path is not None and output_path.exists()


def run(
    limit=None,
    stock_code=None,
    workers=DEFAULT_WORKERS,
    clean_stale=False,
    dry_run=False,
    root_dir: str | None = None,
    resume=True,
):
    set_root_dir(Path(root_dir) if root_dir else ROOT_DIR)
    current_universe_df = fetch_current_universe()
    batch_industry_map = fetch_batch_industry_map()

    if stock_code:
        current_universe_df = current_universe_df[current_universe_df["股票代码"] == stock_code]

    skipped = 0
    if resume:
        done_codes = load_done_codes(ROOT_DIR)
        if done_codes:
            current_universe_df = current_universe_df[~current_universe_df["股票代码"].astype(str).isin(done_codes)]
        if not current_universe_df.empty:
            skipped_mask = current_universe_df.apply(
                lambda row: output_exists_for_stock(row, batch_industry_map), axis=1
            )
            skipped = int(skipped_mask.sum())
            current_universe_df = current_universe_df[~skipped_mask]

    if limit:
        current_universe_df = current_universe_df.head(limit)

    stocks = current_universe_df.to_dict("records")
    expected_paths = set()
    results = []
    failures = []

    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_map = {
            executor.submit(process_stock, stock, batch_industry_map, dry_run): stock
            for stock in stocks
        }
        for future in tqdm(as_completed(future_map), total=len(future_map), desc="抓取进度"):
            stock = future_map[future]
            try:
                result = future.result()
                results.append(result)
                expected_paths.add(result["输出路径"])
                if not dry_run:
                    append_done_record(result, ROOT_DIR)
            except Exception as exc:
                failures.append(
                    {
                        "股票代码": stock["股票代码"],
                        "股票简称": stock["股票简称"],
                        "错误": str(exc),
                    }
                )

    removed_files = cleanup_stale_files(expected_paths, dry_run=dry_run) if clean_stale else []

    summary = {
        "总股票数": len(stocks),
        "成功": len(results),
        "失败": len(failures),
        "删除旧文件": len(removed_files),
        "已跳过": skipped,
    }

    summary_path = ROOT_DIR / "scrape_summary.json"
    failures_path = ROOT_DIR / "scrape_failures.csv"
    if not dry_run:
        summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        pd.DataFrame(failures).to_csv(failures_path, index=False, encoding="utf-8-sig")

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if failures:
        print(f"失败明细已写入: {failures_path}")
    if clean_stale:
        print(f"清理旧文件数量: {len(removed_files)}")


def run_from_failure_file(failure_file: str, workers=1, dry_run=False, root_dir: str | None = None):
    set_root_dir(Path(root_dir) if root_dir else ROOT_DIR)
    current_universe_df = fetch_current_universe()
    batch_industry_map = fetch_batch_industry_map()
    failure_df = pd.read_csv(failure_file, dtype={"股票代码": str})
    failure_df["股票代码"] = failure_df["股票代码"].astype(str).str.zfill(6)

    retry_df = current_universe_df[current_universe_df["股票代码"].isin(failure_df["股票代码"])].copy()
    stocks = retry_df.to_dict("records")
    results = []
    failures = []

    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_map = {
            executor.submit(process_stock, stock, batch_industry_map, dry_run): stock
            for stock in stocks
        }
        for future in tqdm(as_completed(future_map), total=len(future_map), desc="补抓进度"):
            stock = future_map[future]
            try:
                result = future.result()
                results.append(result)
                if not dry_run:
                    append_done_record(result, ROOT_DIR)
            except Exception as exc:
                failures.append(
                    {
                        "股票代码": stock["股票代码"],
                        "股票简称": stock["股票简称"],
                        "错误": str(exc),
                    }
                )

    retry_failures_path = ROOT_DIR / "scrape_failures_retry.csv"
    if not dry_run:
        pd.DataFrame(failures).to_csv(retry_failures_path, index=False, encoding="utf-8-sig")

    summary = {
        "重试股票数": len(stocks),
        "重试成功": len(results),
        "重试失败": len(failures),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if failures:
        print(f"重试失败明细已写入: {retry_failures_path}")


def parse_args():
    parser = argparse.ArgumentParser(description="抓取当前国内上市股票并按模板格式落盘")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--stock-code", type=str, default=None)
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
    parser.add_argument("--clean-stale", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--failure-file", type=str, default=None)
    parser.add_argument("--root-dir", type=str, default=str(ROOT_DIR))
    parser.add_argument("--no-resume", dest="resume", action="store_false", help="不使用断点续抓，重新抓取所有股票")
    parser.set_defaults(resume=True)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.failure_file:
        run_from_failure_file(
            failure_file=args.failure_file,
            workers=args.workers,
            dry_run=args.dry_run,
            root_dir=args.root_dir,
        )
    else:
        run(
            limit=args.limit,
            stock_code=args.stock_code,
            workers=args.workers,
            clean_stale=args.clean_stale,
            dry_run=args.dry_run,
            root_dir=args.root_dir,
            resume=args.resume,
        )