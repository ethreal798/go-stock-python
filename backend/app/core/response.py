"""统一响应格式模块。

提供标准的 API 响应包装类，确保所有接口返回统一的格式：
{
    "code": 1,      # 1 表示成功，0 表示失败
    "msg": "",      # 成功时为空字符串，失败时为错误提示信息
    "data": None    # 成功时为业务数据，失败时为 None
}
"""

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class ApiResponse(BaseModel):
    """统一 API 响应包装。"""

    code: int = 1
    msg: str = ""
    data: Optional[Any] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @classmethod
    def success(cls, data: Any = None, msg: str = "") -> "ApiResponse":
        """创建成功响应。"""
        return cls(code=1, msg=msg, data=data)

    @classmethod
    def error(cls, msg: str = "请求失败", code: int = 0) -> "ApiResponse":
        """创建错误响应。"""
        return cls(code=code, msg=msg, data={})
