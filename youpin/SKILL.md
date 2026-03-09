---
name: youpin
description: >
  悠悠有品(youpin898) CS2 饰品交易平台 API 交互工具。只读查询，严禁买卖操作。
  支持：查询买卖订单、订单详情、库存查看、钱包余额、商品在售列表、商品求购列表、收益统计分析、Excel导出。
  当用户提到悠悠有品、youpin、交易记录、收益统计、持仓分析、订单查询、在售数、求购价、市场行情时使用。
  CRITICAL: 绝对禁止调用任何购买、出售、上架、下架、求购、发货相关接口。
---

# 悠悠有品 API 交互 (只读)

## CRITICAL SAFETY RULE

**严禁调用任何写入/交易接口。** 本 skill 仅用于数据查询和分析。

### 禁止的操作（永远不要调用）

- 购买商品、下单
- 上架/下架商品
- 发起求购
- 发货/确认收货
- 修改价格
- 任何 PUT/DELETE 操作
- 任何含 `create`、`buy`、`sell`、`deliver`、`purchase/create`、`order/create` 的接口

如果用户要求执行买卖操作，**拒绝并解释此 skill 仅支持只读查询**。

---

## 认证

JWT Bearer Token，有效期约 35 天。Token 存储位置由用户指定（通常在脚本中硬编码或环境变量）。

公共 Headers 和 Body 参数详见 [references/api.md](references/api.md)。

## 允许的查询能力

### 1. 订单查询

| 功能 | API | 方法 |
|------|-----|------|
| 出售订单列表 | `/api/youpin/bff/trade/sale/v1/sell/list` | POST |
| 购买订单列表 | `/api/youpin/bff/trade/sale/v1/buy/list` | POST |
| 订单详情 | `/api/youpin/bff/trade/v1/order/query/detail` | POST |

**分页**: `pageSize` 最大 20（超过返回空），使用 `pageIndex` 翻页。

**订单详情参数**: 使用 `{"orderNo": "订单号"}` （不是 orderId）。

**订单状态**: `orderStatus: 340` = 已完成。

### 2. 商品市场行情（按 templateId 查询）

| 功能 | API | 方法 |
|------|-----|------|
| 在售列表 | `/api/homepage/v3/detail/commodity/list/sell` | POST |
| 求购列表 | `/api/youpin/bff/trade/purchase/order/getTemplatePurchaseOrderPageList` | POST |

**在售列表参数**: `{"templateId": "44360", "pageIndex": 1, "pageSize": 10}`
- 返回 `data.commodityList` — 每件在售商品: price(元,字符串), abrade, stickers, userId 等
- price 单位是**元**（不是分），字符串类型

**求购列表参数**: `{"templateId": "44360", "pageIndex": 1, "pageSize": 10}`
- 返回 `data.responseList` — 每个求购单:
  - `purchasePrice`: 求购单价（元，浮点数）
  - `surplusQuantity`: 剩余求购数量
  - `userName`: 求购者名称
  - `autoReceived`: 是否自动收货
  - `abradeText`: 磨损要求（如 "0.09-0.1"，可为 null）
- 按价格从高到低排列

**templateId 查找**: 悠悠有品的搜索 API 不对外暴露关键词过滤。通过以下方式获取 templateId：
1. **交易历史桥接**（推荐）: 从买卖订单的 `productDetailList[].commodityTemplateId` 提取，按商品名称匹配
2. **桥接工具**: PC 上 `/tmp/youpin_bridge.py`，用法:
   - `python3 youpin_bridge.py --build` — 从交易历史构建 name→templateId 映射缓存
   - `python3 youpin_bridge.py "红线"` — 按名称搜索并显示市场数据
   - `python3 youpin_bridge.py "红线" 1` — 搜索并查询第1条的在售+求购
3. **手动**: 用户在 APP 中找到商品页，从 URL 或页面信息获取

**注意**: csfilter 的 `goods_id` 与悠悠有品的 `templateId` 是不同 ID 体系，需通过商品名称桥接

### 3. 库存与商品查询

| 功能 | API |
|------|-----|
| 我的库存 | `/api/youpin/commodity-agg/inventory/list/pull` |
| 在售商品（我的） | `/api/youpin/bff/new/commodity/v1/commodity/list/sell` |
| 商品详情 | `GET /api/commodity/Commodity/Detail?Id=<id>` |

### 4. 钱包余额

| 功能 | API |
|------|-----|
| 账户信息 | `/api/youpin/bff/payment/v1/user/account/info` |
| 钱包类型 | `/api/youpin/bff/payment/v1/user/account/wallet/type` |

### 5. 收益统计分析

核心分析流程：

1. **拉取订单**: 出售订单（指定时间段）+ 购买订单（全量历史）
2. **展开多件订单**: 使用 `productDetailList` 字段拆分，每个子品有独立 abrade/price
3. **匹配买卖**: 有磨损值用 template_id + abrade 精确匹配；无磨损用 template_id FIFO
4. **统计输出**: 匹配收益、未匹配出售、持仓（未出售购买）
5. **Excel 导出**: 交易明细 + 汇总统计 + 持仓列表

详细实现参考 [references/profit-analysis.md](references/profit-analysis.md)。

## 关键数据结构

### 订单列表项

```
orderNo          订单号（字符串）
orderId          订单ID（数字）
orderStatus      340=已完成
totalAmount      总金额（分）
commodityNum     商品数量
createOrderTime  创建时间（毫秒时间戳）
productDetail    单品信息（仅第一件）
productDetailList 全部商品列表（多件订单必须用这个）
```

### productDetailList 子项

```
commodityName       商品名称
commodityTemplateId 模板ID（同款商品共享）
abrade / commodityAbrade  磨损值
price               单品价格（分）
assertId            资产ID
commodityId         商品ID
orderStatus         子品状态
```

## 执行环境

脚本在**个人 PC**（工作站）上运行，通过 frp 穿透访问：

```bash
# SCP 脚本到 PC
scp -P 6000 /tmp/script.py mixiaomi@106.15.125.84:/tmp/script.py

# 远程执行
ssh -p 6000 mixiaomi@106.15.125.84 "python3 /tmp/script.py"

# 下载结果
scp -P 6000 mixiaomi@106.15.125.84:/tmp/result.xlsx ~/Desktop/
```

## 注意事项

- 价格单位是**分**，显示时除以 100
- `Gameid: 730` = CS2
- 多件订单必须用 `productDetailList` 展开，`productDetail` 只有第一件
- Token 过期后需用户重新提供（从 APP 抓包获取）
- 手机需开代理才能抓包，**用完提醒用户关闭代理**
