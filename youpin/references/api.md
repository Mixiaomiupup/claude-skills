# 悠悠有品 API 参考

来源: mitmproxy 抓包 iOS APP v5.42.0

## 认证配置

### 公共 Headers

```python
HEADERS = {
    "Authorization": "Bearer <jwt_token>",
    "Content-Type": "application/json",
    "AppType": "3",
    "platform": "ios",
    "version": "5.42.0",
    "app-version": "5.42.0",
    "api-version": "1.0",
    "Gameid": "730",
    "uk": "<用户密钥>",
    "deviceUk": "<设备密钥>",
    "DeviceToken": "<设备ID>",
    "User-Agent": "iOS/26.3 AppleStore com.uu898.uusteam/5.42.0 Alamofire/5.2.2",
    "package-type": "uuyp",
}
```

### 公共 Body 参数

```python
CB = {
    "AppType": "3",
    "Platform": "ios",
    "SessionId": "<设备ID>",
    "Version": "5.42.0"
}
```

## 只读 API 完整列表

### 交易查询

| 接口 | 路径 | 参数 |
|------|------|------|
| 出售订单列表 | `POST /api/youpin/bff/trade/sale/v1/sell/list` | `orderStatus:0, pageIndex, pageSize(≤20)` |
| 购买订单列表 | `POST /api/youpin/bff/trade/sale/v1/buy/list` | `pageIndex, pageSize(≤20)` |
| 订单详情 | `POST /api/youpin/bff/trade/v1/order/query/detail` | `orderNo: "订单号"` |
| 待发货列表 | `POST /api/youpin/bff/trade/sell/page/v1/waitDeliver/waitDeliverList` | - |
| 未读消息 | `POST /api/youpin/bff/trade/v1/order/counter/userHasUnreadMsg` | - |
| 订单待办 | `POST /api/youpin/bff/trade/todo/v1/orderTodo/topList` | - |

### 求购查询（只读）

| 接口 | 路径 | 参数 |
|------|------|------|
| 求购列表 | `POST .../purchase/order/getTemplatePurchaseOrderPageList` | - |
| 求购搜索 | `POST .../purchase/order/searchPurchaseOrderListV2` | `status:10, pageSize, pageIndex` |
| 求购筛选配置 | `POST .../purchase/order/getTemplateFilterConfigV2` | - |

### 商品市场行情（按 templateId 查询）

| 接口 | 路径 | 参数 |
|------|------|------|
| 在售列表 | `POST /api/homepage/v3/detail/commodity/list/sell` | `templateId(str), pageIndex, pageSize` |
| 求购列表 | `POST /api/youpin/bff/trade/purchase/order/getTemplatePurchaseOrderPageList` | `templateId(str), pageIndex, pageSize` |
| 求购筛选配置 | `POST /api/youpin/bff/trade/purchase/order/getTemplateFilterConfigV2` | `templateId` |

**在售列表响应**: `data.commodityList[]` — price(元,字符串), abrade, stickers, userId, commodityName, templateId

**求购列表响应**: `data.responseList[]` — purchasePrice(元,浮点), surplusQuantity, userName, autoReceived, abradeText

### 库存与商品

| 接口 | 路径 |
|------|------|
| 我的库存 | `POST /api/youpin/commodity-agg/inventory/list/pull` |
| 在售商品 | `POST /api/youpin/bff/new/commodity/v1/commodity/list/sell` |
| 出租商品 | `POST /api/youpin/bff/new/commodity/v1/commodity/list/lease` |
| 预售商品 | `POST /api/youpin/bff/new/commodity/v1/commodity/list/presale` |
| 商品详情 | `GET /api/commodity/Commodity/Detail?Id=<id>` |
| 资产标签 | `GET .../inventoryTagInfo/getUserAssetTagList` |

### 钱包与用户

| 接口 | 路径 |
|------|------|
| 账户信息 | `POST /api/youpin/bff/payment/v1/user/account/info` |
| 钱包类型 | `POST /api/youpin/bff/payment/v1/user/account/wallet/type` |
| 银行卡 | `POST /api/youpin/bff/payment/query/user/bank/card/show` |
| 店铺配置 | `GET /api/user/Store/GetUserStoreConfig` |

### 市场行情

| 接口 | 路径 |
|------|------|
| 首页在售 | `POST /api/homepage/v4/template/querySellPagedList` |
| 详情页在售 | `POST /api/homepage/v3/detail/commodity/list/sell` |
| 游戏列表 | `GET /api/youpin/commodity/adapter/public/game/queryAllList` |

## 响应格式

两种响应风格共存:

```json
// 交易类 API（小写 key）
{"code": 0, "msg": "success", "data": { ... }}

// 首页/市场类 API（大写 key）
{"Code": 0, "Msg": "success", "Data": { ... }, "TotalCount": 30966}
```

订单列表: `data.orderList` 为数组。

## 商品搜索与 templateId 查找

**搜索 API 现状**: 已测试的搜索端点均不支持关键词过滤:
- `/api/homepage/search/match` — 返回 `Code: -1`
- `/api/homepage/search/list` — 忽略 keyword，返回全量 30966 条
- `/api/homepage/v4/template/querySellPagedList` — 忽略 keyword，返回热门商品

**templateId 获取方案**:
1. 从交易历史（买卖订单）的 `productDetailList[].commodityTemplateId` 提取
2. 桥接工具 `/tmp/youpin_bridge.py` 自动构建 name→templateId 缓存

**search/list 响应字段**（大写 key，仅供参考，不支持过滤）:
- `Data.commodityTemplateList[]`: Id, CommodityName, CommodityHashName, Price, OnSaleCount, SteamPrice, TypeName, Exterior, Quality, Rarity

## 已知限制

- `pageSize` 超过 20~30 返回空数据
- 部分接口需要 `sign-token` + `sign-timestamp`（交易查询接口不需要）
- 搜索接口疑似需要额外签名参数，当前无法按关键词过滤
- Response 通常 gzip 压缩
- Cookie `acw_tc` 由服务端设置，后续请求需携带
- JWT Token 有效期约 35 天
- csfilter `goods_id` ≠ youpin `templateId`，需通过商品名称桥接

## 禁止接口清单（绝不调用）

以下接口涉及资金操作或商品状态变更，**永远不要调用**：

- 任何含 `create`、`submit`、`confirm` 的交易接口
- 任何含 `buy`、`purchase/create` 的下单接口
- 任何含 `sell`、`commodity/create`、`onShelf`、`offShelf` 的上下架接口
- 任何含 `deliver`、`delivery` 的发货接口
- 任何含 `pay`、`payment/create`、`withdraw` 的支付/提现接口
- 任何含 `cancel`、`refund` 的退款接口
- `/api/youpin/bff/trade/v1/order/sell/deliveryStrategy` — 发货策略（写入操作）
