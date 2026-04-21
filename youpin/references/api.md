# 悠悠有品 API 参考

来源: mitmproxy 抓包 iOS APP v5.43.0

## 认证配置

### 公共 Headers

```python
HEADERS = {
    "Authorization": "Bearer <jwt_token>",
    "Content-Type": "application/json",
    "AppType": "3",
    "platform": "ios",
    "version": "5.43.0",
    "app-version": "5.43.0",
    "api-version": "1.0",
    "Gameid": "730",
    "uk": "<用户密钥>",
    "deviceUk": "<设备密钥>",
    "DeviceToken": "<设备ID>",
    "User-Agent": "iOS/26.3.1 AppleStore com.uu898.uusteam/5.43.0 Alamofire/5.2.2",
    "package-type": "uuyp",
}
```

### 公共 Body 参数

```python
CB = {
    "AppType": "3",
    "Platform": "ios",
    "SessionId": "<设备ID>",
    "Version": "5.43.0"
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

### 价格走势

| 接口 | 路径 | 参数 |
|------|------|------|
| 趋势筛选配置 | `POST /api/youpin/price/trend/filter/info` | `{"templateId": 782}` |
| 趋势数据 | `POST /api/youpin/price/trend/data` | `{"orderType": 1, "day": 30, "templateId": 782}` |
| 有效日期范围 | `POST /api/youpin/price/trend/getValidDateTime` | `{"templateId": 782, "type": 14}` |

**orderType 值**:
- `1` = 成交价格（UU平台）
- `11` = 在售数量
- `12` = 在租数量
- `14` = 在售价格
- `13` = Steam 价格

**day 值**: `7`(近7天), `15`(近15天), `30`(近30天) — 最大30天

**趋势数据响应**: `data.tradeDataList[]`
- `time`: 毫秒时间戳
- `price`: 值（字符串）— 成交价时为元，在售数量时为件数
- `localDate`: 日期 "2026-04-03"
- `proportion`: 比例值
- 每天约5-6个采样点，需按 `localDate` 聚合

## 响应格式

两种响应风格共存:

```json
// 交易类 API（小写 key）
{"code": 0, "msg": "success", "data": { ... }}

// 首页/市场类 API（大写 key）
{"Code": 0, "Msg": "success", "Data": { ... }, "TotalCount": 30966}
```

订单列表: `data.orderList` 为数组。

## 商品搜索

### 搜索联想 (autocomplete)

`POST /api/homepage/search/match`

```json
{"keyWords": "红线", "userId": "14095698", "listType": "10", "gameId": 730,
 "AppType": "3", "Platform": "ios", "Version": "5.43.0", "SessionId": "..."}
```

- **关键参数**: `keyWords`（大写W）、`userId`（必须）、`gameId`（整数730）
- 返回 `Data.dataList[]`: `commodityName`, `templateId`, `haveTemplateToggleList`
- 最多 10 条，用于自动补全

### 搜索结果列表 (完整搜索)

`POST /api/homepage/search/new/list`

```json
{"keyWords": "红线", "listType": 10, "gameId": 730, "pageIndex": 1, "pageSize": 20,
 "listSortType": 0, "filterMap": {}, "minPrice": "", "maxPrice": "",
 "userId": "14095698", "AppType": "3", "Platform": "ios", "Version": "5.43.0", "SessionId": "..."}
```

- 返回 `Data.commodityTemplateList[]`: `Id`(=templateId), `CommodityName`, `Price`, `OnSaleCount`, `SteamPrice`, `CommodityHashName`, `TypeName`, `Exterior`, `Quality`, `Rarity`
- 大写字段名，支持分页

### 搜索 API 注意事项

- 参数名 `keyWords` 大写 W，`gameId` 小写（整数），`listType` 整数或字符串均可
- 必须包含 `userId`，否则返回空结果
- 响应使用大写 key（`Code`, `Data`）

## 已知限制

- `pageSize` 超过 20~30 返回空数据
- 部分接口需要 `sign-token` + `sign-timestamp`（交易查询接口不需要）
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
