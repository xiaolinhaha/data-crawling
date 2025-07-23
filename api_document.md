# 金融信息爬虫API接口文档
## 简介
本文档描述了金融信息爬虫系统的API接口，这些接口可用于获取多个金融新闻网站的最新文章内容。

## 基本信息

- **基础URL**: `http://127.0.0.1:5005/api/crawlers`
- **请求方法**: GET
- **响应格式**: JSON

## 爬虫列表

可通过以下接口查看所有可用的爬虫：

```
GET /api/crawlers/
```

**响应示例**:

```json
{
  "status": "success",
  "message": "成功获取爬虫列表",
  "data": [
    {
      "name": "中国金融新闻网",
      "endpoint": "/api/crawlers/financial_news/financial_news",
      "description": "爬取中国金融新闻网的最新新闻"
    },
    {
      "name": "中国金融信息网",
      "endpoint": "/api/crawlers/cnfin/cnfin_news",
      "description": "爬取中国金融信息网的最新新闻"
    },
    {
      "name": "东方财富网评论精华",
      "endpoint": "/api/crawlers/east_money/east_money_news",
      "description": "爬取东方财富网评论精华栏目的最新文章"
    },
    {
      "name": "东方财富网焦点",
      "endpoint": "/api/crawlers/east_money_focus/east_money_focus",
      "description": "爬取东方财富网焦点页面的重要文章"
    },
    {
      "name": "东方财富网理财资讯",
      "endpoint": "/api/crawlers/east_money_lczx/east_money_lczx_news",
      "description": "爬取东方财富网理财资讯栏目的最新文章"
    },
    {
      "name": "新浪财经基金",
      "endpoint": "/api/crawlers/sina_finance/sina_finance_news",
      "description": "爬取新浪财经基金首页顶部新闻"
    },
    {
      "name": "新浪财经股票",
      "endpoint": "/api/crawlers/sina_stock/sina_stock_news",
      "description": "爬取新浪财经股票页面顶部新闻"
    },
    {
      "name": "深蓝保保险攻略",
      "endpoint": "/api/crawlers/shenlanbao/shenlanbao_article",
      "description": "爬取深蓝保保险攻略页面的最新文章"
    },
    {
      "name": "中证网公司要闻",
      "endpoint": "/api/crawlers/cs_company/cs_company_article",
      "description": "爬取中证网公司要闻页面的最新两条文章"
    },
    {
      "name": "搜狐政策搜索",
      "endpoint": "/api/crawlers/sohu_policy/sohu_policy_news",
      "description": "获取搜狐政策搜索的24小时内最新两条新闻"
    },
    {
      "name": "东方财富网防骗文章",
      "endpoint": "/api/crawlers/eastmoney_antifraud/eastmoney_antifraud_article",
      "description": "获取东方财富网关于防骗的最新文章"
    },
    {
      "name": "中国金融网风险揭示",
      "endpoint": "/api/crawlers/cnfin_risk/cnfin_risk_news",
      "description": "获取中国金融网风险揭示栏目的最新文章"
    },
    {
      "name": "搜狐财经",
      "endpoint": "/api/crawlers/sohu_finance/sohu_finance_news",
      "description": "获取搜狐财经栏目的最新文章"
    },
    {
      "name": "东方财富网国际经济",
      "endpoint": "/api/crawlers/eastmoney_international/eastmoney_international",
      "description": "获取东方财富网国际经济栏目的最新文章"
    }
  ]
}
```

## 详细API接口

### 1. 中国金融新闻网

获取中国金融新闻网的最新新闻。

- **接口URL**: `/api/crawlers/financial_news/financial_news`
- **网站链接**: [https://www.financialnews.com.cn/](https://www.financialnews.com.cn/)

**响应示例**:

```json
{
  "status": "success",
  "message": "成功获取中国金融新闻网最新新闻",
  "data": {
    "title": "引导金融支持专精特新企业发展（金观平）",
    "url": "http://www.financialnews.com.cn/jigou/chuangtou/202304/t20230425_260638.html",
    "date": "2023-04-25 07:44:00"
  }
}
```

### 2. 中国金融信息网

获取中国金融信息网的最新新闻。

- **接口URL**: `/api/crawlers/cnfin/cnfin_news`
- **网站链接**: [https://www.cnfin.com/](https://www.cnfin.com/)

**响应示例**:

```json
{
  "status": "success",
  "message": "成功获取中国金融信息网最新新闻",
  "data": {
    "title": "2022年金融机构对外金融资产负债统计数据报告",
    "url": "https://www.cnfin.com/ll-1/detail/1682257437_261854.html",
    "date": "2023-04-24"
  }
}
```

### 3. 东方财富网评论精华

获取东方财富网评论精华栏目的最新文章。

- **接口URL**: `/api/crawlers/east_money/east_money_news`
- **网站链接**: [https://finance.eastmoney.com/a/cpljh.html](https://finance.eastmoney.com/a/cpljh.html)

**响应示例**:

```json
{
  "status": "success",
  "message": "成功获取东方财富网评论精华的最新文章",
  "data": {
    "title": "交易"鬼才"频频亏损，黄金却在暴涨，什么在发生",
    "url": "http://finance.eastmoney.com/a/202304242754099895.html",
    "date": "2023-04-24 15:52:00"
  }
}
```

### 4. 东方财富网焦点

获取东方财富网焦点页面的重要文章。

- **接口URL**: `/api/crawlers/east_money_focus/east_money_focus`
- **网站链接**: [https://finance.eastmoney.com/yaowen.html](https://finance.eastmoney.com/yaowen.html)

**响应示例**:

```json
{
  "status": "success",
  "message": "成功获取东方财富网焦点页面的重要文章",
  "data": {
    "title": "多地再出发 国企并购重组加速度",
    "url": "http://finance.eastmoney.com/a/202304242753954761.html",
    "date": "2023-04-24 15:17:00",
    "content": "本报记者 鲍立 近期，国企并购重组再提速。\n4月19日，徐工机械与柳工集团签署了战略重组协议，徐工集团旗下的徐工机械将通过向柳工集团及建信金融资产投资有限公司、广西国同盛投资有限公司定向发行股份及支付现金相结合方式，购买柳工集团及建信投资、国同盛投资持有的柳工股份77.33%的股权......（更多内容省略）"
  }
}
```

### 5. 东方财富网理财资讯

获取东方财富网理财资讯栏目的最新文章。

- **接口URL**: `/api/crawlers/east_money_lczx/east_money_lczx_news`
- **网站链接**: [https://money.eastmoney.com/a/clczx.html](https://money.eastmoney.com/a/clczx.html)

**响应示例**:

```json
{
  "status": "success",
  "message": "成功获取东方财富网理财资讯的最新文章",
  "data": {
    "title": "证监会正式出台证券基金专项产品投资"新三板"相关规则，投资者范围及投资条件全面拓展",
    "url": "http://finance.eastmoney.com/a/202304242754123411.html",
    "date": "2023-04-24 16:05:00"
  }
}
```

### 6. 新浪财经基金

获取新浪财经基金首页顶部新闻。

- **接口URL**: `/api/crawlers/sina_finance/sina_finance_news`
- **网站链接**: [https://finance.sina.com.cn/fund/](https://finance.sina.com.cn/fund/)

**响应示例**:

```json
{
  "status": "success",
  "message": "成功获取新浪财经基金最新新闻",
  "data": {
    "title": "公募机构卧薪尝胆，核心制造业优质上市公司望成布局重点",
    "url": "https://finance.sina.com.cn/roll/2023-04-24/doc-imyprrvq3133903.shtml",
    "date": "2023-04-24 07:56:05"
  }
}
```

### 7. 新浪财经股票

获取新浪财经股票页面顶部新闻。

- **接口URL**: `/api/crawlers/sina_stock/sina_stock_news`
- **网站链接**: [https://finance.sina.com.cn/stock/](https://finance.sina.com.cn/stock/)

**响应示例**:

```json
{
  "status": "success",
  "message": "成功获取新浪财经股票最新新闻",
  "data": {
    "title": "历史收益已达600%，嘉实远见精选今买是否值得？",
    "url": "https://finance.sina.com.cn/money/fund/fundzmt/2023-04-24/doc-imyprrvq3137359.shtml",
    "date": "2023-04-24 10:35:10"
  }
}
```

### 8. 深蓝保保险攻略

获取深蓝保保险攻略页面的最新文章。

- **接口URL**: `/api/crawlers/shenlanbao/shenlanbao_article`
- **网站链接**: [https://www.shenlanbao.com/](https://www.shenlanbao.com/)

**响应示例**:

```json
{
  "status": "success",
  "message": "成功获取深蓝保保险攻略的最新文章",
  "data": {
    "title": "大家保险亏损严重、偿付能力下降？保单会有风险吗？",
    "url": "https://www.shenlanbao.com/baoxian/article_0_1050_18066.html",
    "date": "2023-04-24"
  }
}
```

### 9. 中证网公司要闻

获取中证网公司要闻页面的最新两条文章。

- **接口URL**: `/api/crawlers/cs_company/cs_company_article`
- **网站链接**: [https://www.cs.com.cn/ssgs/gsxw/](https://www.cs.com.cn/ssgs/gsxw/)

**响应示例**:

```json
{
  "status": "success",
  "message": "成功获取中证网公司要闻最新两条文章",
  "data": [
    {
      "title": "大象起舞活力迸发 今年上市险企股价大涨",
      "url": "https://www.cs.com.cn/ssgs/gsxw/202304/t20230424_6332456.html",
      "date": "2023-04-24"
    },
    {
      "title": "传化智联去年净利微降",
      "url": "https://www.cs.com.cn/ssgs/gsxw/202304/t20230424_6332455.html",
      "date": "2023-04-24"
    }
  ]
}
```

### 10. 搜狐政策搜索

获取搜狐政策搜索的24小时内最新两条新闻。

- **接口URL**: `/api/crawlers/sohu_policy/sohu_policy_news`
- **网站链接**: [https://www.sohu.com/](https://www.sohu.com/)

**响应示例**:

```json
{
  "status": "success",
  "message": "成功获取搜狐政策搜索的最新两条新闻",
  "data": [
    {
      "title": "个人养老金保险账户资金收支有了"紧箍咒"",
      "url": "https://www.sohu.com/a/676219071_121124378",
      "date": "2023-04-24 10:29:00",
      "source": "中国银行保险报"
    },
    {
      "title": "重庆下发实施细则，个人养老金投资种类新增商业养老保险",
      "url": "https://www.sohu.com/a/676213553_161795",
      "date": "2023-04-24 10:19:00",
      "source": "券商中国"
    }
  ]
}
```

### 11. 中国金融网风险揭示

获取中国金融网风险揭示栏目的最新文章。

- **接口URL**: `/api/crawlers/cnfin_risk/cnfin_risk_news`
- **网站链接**: [https://www.cnfin.com/](https://www.cnfin.com/)

**响应示例**:

```json
{
  "status": "success", 
  "message": "成功获取中国金融网风险揭示栏目最新文章", 
  "data": {
    "title": "警惕非法"看盘"App骗局，养老钱易"入坑"难"出坑"", 
    "url": "https://www.cnfin.com/fxjs/detail/1681870384_260987.html", 
    "date": "2023-04-19", 
    "source": "中国金融信息网", 
    "content": "近年来，非法"看盘"App层出不穷，作案手法不断翻新。随着年龄的增长..."
  }
}
```

### 12. 东方财富网防骗文章

获取东方财富网关于防骗的最新文章。

- **接口URL**: `/api/crawlers/eastmoney_antifraud/eastmoney_antifraud_article`
- **网站链接**: [https://www.eastmoney.com/](https://www.eastmoney.com/)

**响应示例**:

```json
{
  "status": "success",
  "message": "成功获取东方财富网防骗文章",
  "data": {
    "title": "重磅发布！2023年第一季度十大典型证券期货违法犯罪案例",
    "url": "https://finance.eastmoney.com/a/202304211649384828.html",
    "date": "2023-04-21 08:50:49",
    "source": "证监会",
    "content": "证监会今日通报2023年第一季度证券期货违法犯罪十大典型案例...(内容省略)"
  }
}
```

### 13. 搜狐财经

获取搜狐财经栏目的最新文章。

- **接口URL**: `/api/crawlers/sohu_finance/sohu_finance_news`
- **网站链接**: [https://business.sohu.com/](https://business.sohu.com/)

**响应示例**:

```json
{
  "status": "success",
  "message": "成功获取搜狐财经最新文章",
  "data": {
    "title": "一季度GDP增速超预期，多重积极因素支撑中国经济恢复向好",
    "url": "https://www.sohu.com/a/676456781_121123594",
    "date": "2023-04-25 08:20:00",
    "source": "搜狐财经",
    "content": "一季度国内生产总值同比增长4.5%，比上年四季度加快2.2个百分点，超出市场预期。消费物价温和上涨，居民消费价格指数(CPI)同比上涨1.3%，比上年四季度有所回落。就业形势总体向好，一季度全国城镇调查失业率平均值为5.3%，比上年四季度下降0.2个百分点。"
  }
}
```

### 14. 东方财富网国际经济

获取东方财富网国际经济栏目的最新文章。

- **接口URL**: `/api/crawlers/eastmoney_international/eastmoney_international`
- **网站链接**: [https://finance.eastmoney.com/a/cgjjj.html](https://finance.eastmoney.com/a/cgjjj.html)

**响应示例**:

```json
{
  "status": "success",
  "message": "成功获取东方财富网国际经济最新文章",
  "data": {
    "title": "美国国务卿布林肯访华前夕 美对华释放强烈政经分离信号 中方持续释放善意",
    "url": "https://finance.eastmoney.com/a/202306152814671795.html",
    "date": "2023-06-15 18:33:25",
    "source": "东方财富网",
    "content": "据环球时报，中国商务部6月15日公布的数据显示，今年前5个月，中国吸收外资超过5000亿元人民币，同比下降0.5%，降幅较前4个月收窄0.7个百分点，其中5月当月利用外资同比增长19.6%。中国－欧盟商会15日发布《商业信心调查2023》报告称，欧洲企业在华业务面临挑战，但近七成受访企业仍表示计划在中国扩大业务规模。"
  }
}
```

### 15. 环球网国际新闻

获取环球网国际新闻栏目24小时内的最新文章。

- **接口URL**: `/api/crawlers/huanqiu_world/huanqiu_world_news`
- **网站链接**: [https://world.huanqiu.com/roll](https://world.huanqiu.com/roll)

**响应示例**:

```json
{
  "status": "success",
  "message": "成功获取环球网国际新闻最新文章",
  "data": [
    {
      "title": "诺贝尔文学奖得主略萨去世，享年89岁",
      "url": "https://world.huanqiu.com/article/4MGpQ8wEZhZ",
      "date": "2025-04-14 02:45:39",
      "source": "澎湃新闻",
      "summary": "澎湃新闻记者获悉，2010年诺贝尔文学奖得主马里奥·巴尔加斯·略萨（Mario Vargas Llosa）于当地时间4月13日在秘鲁利马逝世，享年89岁。",
      "content": "澎湃新闻记者获悉，2010年诺贝尔文学奖得主马里奥·巴尔加斯·略萨（Mario Vargas Llosa）于当地时间4月13日在秘鲁利马逝世，享年89岁。\n\n略萨代表作有《绿房子》《酒吧长谈》《公羊的节日》和《世界末日之战》等。\n\n略萨的儿子阿尔瓦罗·巴尔加斯·略萨在社交媒体X上宣布了这个消息\n\n略萨的儿子阿尔瓦罗·巴尔加斯·略萨在社交媒体X上分享的家庭声明中表示："我们怀着沉重的心情宣布，我们的父亲马里奥·巴尔加斯·略萨今天在利马安详去世，身边陪伴着家人。"这位作家的三个孩子补充说，不会举行公众仪式，但他们将进行家庭告别。"
    },
    {
      "title": "德媒：接替默克尔后，朔尔茨执政联盟正在分崩离析",
      "url": "https://world.huanqiu.com/article/4MGpSj0DQmK",
      "date": "2025-04-14 01:34:22",
      "source": "环球时报",
      "summary": "德国总理朔尔茨领导的"交通灯"执政联盟分崩离析，三党领导层正不断疏远，联盟内部对立越来越尖锐。一些分析认为，这个脆弱的执政联盟已无法持续太久。",
      "content": "德国总理朔尔茨领导的"交通灯"执政联盟分崩离析，三党领导层正不断疏远，联盟内部对立越来越尖锐。\n\n据德国《商报》报道，德国联邦议院副议长戈林-埃卡特日前指出，"交通灯"联盟三党间的不和令人震惊。她虽然仍然相信执政联盟会坚持到2025年的正常选举，但也警告说，德国不能再这样继续下去了。\n\n早在2022年，戈林-埃卡特就曾称朔尔茨的领导方式"太被动"了。按照她的看法，朔尔茨做事应当更加果断。"联邦总理作为政府首脑有责任表明方向。他是牵头人，必须提醒其他人拿出解决方案，而不是与问题共存"。"
    }
  ]
}
```

### 16. 人民网健康

获取人民网健康首页大标题。

- **接口URL**: `/api/crawlers/people_health/people_health_topic`
- **网站链接**: [http://health.people.com.cn/](http://health.people.com.cn/)

**响应示例**:

```json
{
  "status": "success",
  "message": "成功获取人民网健康首页大标题",
  "data": {
    "title": "春日这些常见的花草，原来都是中药",
    "url": "http://health.people.com.cn/n1/2023/0413/c14739-32657423.html",
    "date": "2023-04-13",
    "source": "人民网-生命时报",
    "content": "春暖花开，各种鲜花绽放。不少赏心悦目的花草，也是功效不凡的中药材，如丁香、茉莉、月季、玫瑰等。\n\n丁香\n\n丁香可作为中药材，具有温中降逆、补肾助阳的功效，多用于脾胃虚寒、呃逆、呕吐的治疗；还可用于肾阳不足所导致的小便频数、阳痿等症状。正常人群泡茶喝则可暖胃健脾、理气止痛。\n\n茉莉\n\n茉莉花可清热化痰、疏肝解郁、利咽止痛、健脾开胃。用茉莉花煮水洗脸，可防止皮肤干燥。需要注意的是，胃炎、胃溃疡和糖尿病患者应慎用。\n\n月季\n\n月季花药用主要用于调解气血，治疗肝郁气滞、跌打损伤、妇女月经不调、风湿痹痛、瘀滞肿痛等病症。月季花泡水需先洗净，过沸水然后加到沸水中，或者加到保温杯里泡开。女性月经期间不建议喝月季花茶。\n\n玫瑰\n\n玫瑰花入药可行气解郁、和血止痛，常用于月经不调、产后瘀血腹痛等症状。玫瑰花性温，常喝有助于女性调经养颜，改善体寒，也有助于改善皮肤暗沉、细纹多等问题。"
  }
}
```

### 17. 人民网社会

获取人民网社会版块首页大标题。

- **接口URL**: `/api/crawlers/people_society/people_society_headline`
- **网站链接**: [http://society.people.com.cn/](http://society.people.com.cn/)

**响应示例**:

```json
{
  "status": "success",
  "message": "成功获取人民网社会版块首页大标题",
  "data": {
    "title": "中央气象台发布大风黄色预警 各地全力应对大风天气",
    "url": "http://society.people.com.cn/n1/2025/0414/c1008-40458926.html",
    "date": "2025-04-14",
    "source": "人民网",
    "content": "据中央气象台消息，4月14日，新疆南疆盆地、内蒙古中西部、华北西部和北部、辽宁西部等地有沙尘天气。受冷空气和低涡切变影响，14日08时至15日08时，新疆西部山区和南疆盆地、内蒙古中西部、华北、东北地区中南部、黄淮、江淮等地有4~6级偏北风，阵风7~9级，其中，新疆南疆盆地局地风力可达10~12级；东部和南部海区有6~8级大风，阵风9~10级。\n\n中央气象台4月14日06时继续发布大风黄色预警。\n\n天津、河北、北京等多地气象台发布大风蓝色预警信号，提醒市民关注天气预报，注意防范。目前，各地均在积极采取措施应对大风天气。"
  }
}
```

### 18. 人民网科普

获取人民网科普版块首页大标题。

- **接口URL**: `/api/crawlers/people_science/people_science_headline`
- **网站链接**: [http://kpzg.people.com.cn/](http://kpzg.people.com.cn/)

**响应示例**:

```json
{
  "status": "success",
  "message": "成功获取人民网科普版块首页大标题",
  "data": {
    "title": "智慧交通标准化试点项目推出",
    "url": "http://kpzg.people.com.cn/n1/2025/0414/c404843-40458875.html",
    "date": "2025-04-14",
    "source": "人民网",
    "content": "试点项目聚焦智慧物流、智慧出行及相关新型基础设施三大方向，以建立健全智慧交通标准体系、持续推动成套标准验证与先进标准研制、提升标准化基础能力、强化标准实施应用等为目标。\n\n近日，由北京市海淀区政府、市场监管总局和交通运输部联合推出的智慧交通标准化试点项目正式启动，这是国家级标准化示范项目，意味着北京市海淀区将进一步创新智慧交通应用场景，通过标准引领，推动海淀区成为智慧交通标准应用与创新示范区。"
  }
}
```

## 响应参数说明

所有API接口的响应均遵循以下格式：

| 参数名 | 类型 | 说明 |
|--------|------|------|
| status | string | 请求状态，成功为"success"，失败为"error" |
| message | string | 状态描述消息 |
| source | string | 数据来源网站名称 |
| data | array | 文章数据数组 |

`data`数组中每个文章对象包含以下字段：

| 参数名 | 类型 | 说明 |
|--------|------|------|
| title | string | 文章标题 |
| url | string | 文章原始链接 |
| date | string | 文章发布日期 (YYYY-MM-DD格式) |
| content | string | 文章正文内容 |
| summary | string | 文章摘要 (仅东方财富网评论精华接口提供) |

## 错误处理

当API请求失败时，会返回如下格式的错误信息：

```json
{
  "status": "error",
  "message": "错误信息描述",
  "data": []
}
```

常见错误包括：

- 获取列表页失败
- 解析列表页失败
- 获取文章详情失败

## 注意事项

1. 本API仅供学习和研究使用，请勿用于商业目的
2. 建议控制请求频率，避免对目标网站造成压力
3. 接口返回的内容可能随目标网站结构变化而需要更新
4. 爬虫返回的内容已去除反斜杠，保证了数据的可读性

## 使用示例

### 使用curl获取中国金融新闻网的最新新闻

```bash
curl -X GET "http://127.0.0.1:5005/api/crawlers/financial_news/financial_news"
```

### 使用Python请求接口

```python
import requests

# 获取所有爬虫列表
response = requests.get("http://127.0.0.1:5005/api/crawlers/")
print(response.json())

# 获取中国金融信息网的最新新闻
response = requests.get("http://127.0.0.1:5005/api/crawlers/cnfin/cnfin_news")
print(response.json())
```

## 部署说明

1. 安装依赖：`pip install -r requirements.txt`
2. 设置环境变量：
   ```bash
   export APP_HOST="0.0.0.0"
   export APP_PORT=5005
   export DEBUG_MODEL="True"
   ```
3. 启动服务：`python app.py` 