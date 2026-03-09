# 收益统计分析参考

## 完整流程

### 1. 拉取订单

```python
def fetch_orders(order_type, min_timestamp=None):
    """拉取出售或购买订单列表。

    Args:
        order_type: "sell" 或 "buy"
        min_timestamp: 最早时间戳(毫秒)，None=不限
    """
    if order_type == "sell":
        url = "https://api.youpin898.com/api/youpin/bff/trade/sale/v1/sell/list"
    else:
        url = "https://api.youpin898.com/api/youpin/bff/trade/sale/v1/buy/list"

    all_orders = []
    page = 1
    while True:
        body = {**CB, "pageIndex": page, "pageSize": 20}
        if order_type == "sell":
            body["orderStatus"] = 0
        resp = requests.post(url, headers=HEADERS, json=body, timeout=15)
        data = resp.json()
        if data.get("code") != 0:
            break
        orders = data.get("data", {}).get("orderList")
        if not orders:
            break
        for o in orders:
            ct = o.get("createOrderTime", 0)
            if min_timestamp and ct < min_timestamp:
                continue
            all_orders.append(o)
        last_time = orders[-1].get("createOrderTime", 0)
        if min_timestamp and last_time < min_timestamp:
            break
        if len(orders) < 20:
            break
        page += 1
        time.sleep(0.3)
    return all_orders
```

### 2. 展开多件订单

关键：一个订单可能包含多件商品。`productDetail` 只有第一件，必须用 `productDetailList`。

```python
def expand_order(o):
    """把一个订单展开成单品列表。"""
    ct = o.get("createOrderTime", 0)
    order_no = o.get("orderNo", "")
    status = o.get("orderStatus")
    commodity_num = o.get("commodityNum", 1) or 1
    pdl = o.get("productDetailList") or []
    pd = o.get("productDetail", {})
    items = []

    if len(pdl) > 1:
        # 多件订单：每个子品有独立 abrade 和 price
        for sub in pdl:
            items.append({
                "order_no": order_no,
                "status": sub.get("orderStatus") or status,
                "name": sub.get("commodityName", pd.get("commodityName", "未知")),
                "template_id": sub.get("commodityTemplateId", pd.get("commodityTemplateId")),
                "abrade": sub.get("abrade") or sub.get("commodityAbrade"),
                "price": sub.get("price", 0),  # 单品价格（分）
                "create_time": ...,
                "create_ts": ct,
            })
    elif commodity_num > 1 and not pdl:
        # 无 productDetailList 但多件：均分 totalAmount
        per_price = o.get("totalAmount", 0) // commodity_num
        for i in range(commodity_num):
            items.append({...price: per_price...})
    else:
        # 单件订单
        items.append({...price: o.get("totalAmount", 0)...})

    return items
```

### 3. 匹配逻辑

```
对每个出售单品 s：
  如果 s 有磨损值(abrade)：
    1. 在购买中找 template_id 相同 + abrade 相同 + 买入时间 ≤ 卖出时间 的
    2. 找不到则放宽时间限制（可能先卖后买的情况）
  如果 s 无磨损值(N/A)：
    FIFO: 找 template_id 相同 + 无磨损 + 买入时间 ≤ 卖出时间 的第一个
  未匹配的出售 → unmatched_sells
  未匹配的购买 → unmatched_buys（持仓）
```

### 4. 统计指标

| 指标 | 计算 |
|------|------|
| 毛收益 | Σ(卖出价 - 买入价) |
| 毛收益率 | 毛收益 / 总买入 |
| 平台手续费 | 总卖出 × 2.5% |
| 净收益 | 毛收益 - 手续费 |
| 胜率 | 盈利笔数 / 总匹配笔数 |

### 5. 品类分类

```python
if "手套" in name or "（★）" in name:
    cat = "手套/刀"
elif "挂件" in name:
    cat = "挂件"
elif "印花" in name:
    cat = "印花"
elif any(x in name for x in ["捕兽者", "德拉戈米尔", "马尔库斯", ...]):
    cat = "探员"
elif "武器箱" in name:
    cat = "武器箱"
else:
    cat = "枪皮"
```

## Excel 导出结构

3 个 Sheet：

1. **交易明细**: 序号、商品名称、磨损值、买入价、卖出价、收益、收益率、买入日期、卖出日期、持仓天数、匹配状态、订单号
2. **汇总统计**: 总体统计 + 已匹配交易收益 + 分品类收益表
3. **持仓中(未出售)**: 序号、商品名称、磨损值、买入价、买入日期

依赖: `openpyxl`

## 典型输出数据量

- 出售订单 ~700+（原始），展开后 ~1200 单品
- 购买订单 ~3100+（原始），展开后 ~4100 单品
- 匹配率 ~90%+
