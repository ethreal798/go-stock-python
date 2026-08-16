# """雪球基金档案与风险指标外部来源适配。"""
#
# from __future__ import annotations
#
# from typing import Any
#
#
# class FundMetadataSourceError(RuntimeError):
#     """雪球基金档案或风险接口请求异常。"""
#
#
# def fetch_fund_profile_frame(symbol: str, *, timeout: float = 20) -> Any:
#     """获取单只基金基本信息；雪球明确未收录时返回空 DataFrame。"""
#     try:
#         import akshare as ak
#         import pandas as pd
#     except ImportError as exc:  # pragma: no cover
#         raise FundMetadataSourceError("缺少 akshare，请先安装后端 requirements.txt") from exc
#     try:
#         return ak.fund_individual_basic_info_xq(symbol=symbol, timeout=timeout)
#     except KeyError as exc:
#         # 场内 ETF 等未收录代码返回 result_code=600001 且没有 data 字段。
#         if exc.args == ("data",):
#             return pd.DataFrame(columns=["item", "value"])
#         raise FundMetadataSourceError(f"基金 {symbol} 雪球基本信息返回格式异常") from exc
#     except Exception as exc:
#         raise FundMetadataSourceError(f"基金 {symbol} 雪球基本信息请求失败") from exc
#
#
# def fetch_fund_risk_frame(symbol: str, *, timeout: float = 20) -> Any:
#     """获取单只基金按周期风险指标；明确无风险数据时返回空 DataFrame。"""
#     try:
#         import akshare as ak
#         import pandas as pd
#     except ImportError as exc:  # pragma: no cover
#         raise FundMetadataSourceError("缺少 akshare/pandas，请先安装后端 requirements.txt") from exc
#     try:
#         return ak.fund_individual_analysis_xq(symbol=symbol, timeout=timeout)
#     except KeyError as exc:
#         if exc.args == ("index_data_list",):
#             return pd.DataFrame()
#         raise FundMetadataSourceError(f"基金 {symbol} 雪球风险指标返回格式异常") from exc
#     except Exception as exc:
#         raise FundMetadataSourceError(f"基金 {symbol} 雪球风险指标请求失败") from exc
