# a-share-dragon-head (A股沪深主板唯一真龙头战法 Skill)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-green.svg)](scripts/dragon_calc.py)
[![Agent Skill](https://img.shields.io/badge/Format-Agent%20SKILL.md-orange.svg)](SKILL.md)

一套面向 **A 股沪深主板(`60`/`00` 非 ST)** 的「只做市场唯一真龙头」全栈实战 AI Agent Skill。融合开源游资 Skill 架构、淘股吧与 23 位短线典籍心法（炒股养家、赵老哥、陈小群、退学炒股、北京炒家等），通过 **9 份结构化实战参考手册 + 7 合 1 纯 Python 确定性定量脚本**，实现从情绪周期定仓、三平台舆情交叉验证、筹码峰与指数共振、龙回头二波筛选到机械逃顶控回撤的完整闭环。

## 核心铁律

- **只看唯一真龙与最高位断板活口**：严格隔离「表A（实盘可买核心池，0-3只）」与「表B（纯情绪风向标，只看不买）」；铁血剔除中位 2 板低辨识度跟风补涨、量化平铺一日游首板与无换手缩量庄股。
- **三元共振 + 三平台交叉验证**：消息面催化定级（S/A/B/C） + **东方财富 / 同花顺 / 淘股吧**三平台股评人气核验（反向预警一致高潮） + K 线筹码峰（低位单峰突破/底峰锁仓，排雷上峰不移与假集中度）。
- **机械风控与量化反收割**：`09:25` 竞价低开超 `-5%` 熔断拉黑当日；严禁低开急拉 `+7%` 不封板追高；严禁盲目跌停翘板；单笔大面当日 0 仓冷却，连亏减半，单月回撤 10% 空仓复盘。

## 仓库目录结构

```text
a-share-dragon-head/
├── SKILL.md                                    # Agent 技能主入口与执行 SOP
├── README.md                                   # 项目总览与快速上手指南
├── LICENSE                                     # MIT 开源协议
├── scripts/
│   └── dragon_calc.py                          # 7 合 1 确定性量化计算与评分脚本
└── references/
    ├── second-wave-and-five-dim.md             # 龙回头二波五条硬筛、卡位博弈与五维15项评分
    ├── chip-and-index-resonance.md             # 筹码峰洗盘/派发、指数四维共振与大妖演化路径
    ├── quant-counter-and-sentiment.md          # 量化四大收割套路反制与0-100情绪温度计
    ├── sole-leader-and-buy-points.md           # 唯一真龙四维锁定、三平台舆情与六大经典买点
    ├── sell-and-drawdown.md                    # 六大硬核逃顶卖点、买入假设审计与回撤阶梯控仓
    ├── advanced-tape-and-cycle.md              # 09:15-09:25竞价暗门、封单比与同身位分离确认
    ├── youzi-classics.md                       # 23位游资典籍心法与散户反面清单
    ├── longhubang-and-yidong.md                # 龙虎榜首断板辨妖与沪深主板卡异动精确规则
    └── execution-playbook.md                   # 07:00-20:00全时段SOP与全仓/分仓防卖飞矩阵
```

## 7 合 1 量化脚本快速上手 (`scripts/dragon_calc.py`)

纯 Python 标准库零依赖，直接运行：

```bash
# 1. 情绪周期五维温度计 (0-100) 与仓位上限
python3 scripts/dragon_calc.py sentiment --lu 64 --ld 4 --bomb 53.96 --promo 30 --max-board 4

# 2. 唯一真龙客观分池 (表A核心 / 表A断板观察 / 表B风向标 / 淘汰)
python3 scripts/dragon_calc.py leader_score --symbol 九阳股份 --turnover 4.32 --buzz-level top --is-top-leader --inst-net-buy

# 3. 五维 15 项综合打分 (0-100 分与仓位建议)
python3 scripts/dragon_calc.py five_dim_score --symbol 九阳股份 --sentiment 24 --status 25 --tech 18 --chip 14 --fundamental 8

# 4. 沪深主板 10 日(+100%) / 30 日(+200%) 严重异常波动(卡异动)测算
python3 scripts/dragon_calc.py yidong --market sz --base10 5.82 --close 10.06 --idx10 -8.0

# 5. 次日涨跌停、-5% 熔断价、5/10 日均线与半仓降本测算
python3 scripts/dragon_calc.py levels --close 10.06 --cost 9.64 --closes5 8.75,8.11,8.92,9.30,10.06

# 6. 09:25 集合竞价爆量比与弱转强评级
python3 scripts/dragon_calc.py auction --prev-close 17.33 --open-price 17.75 --prev-amt 20.37 --auction-amt 1.15

# 7. 涨停封单成交比与次日溢价评估
python3 scripts/dragon_calc.py seal --seal-amt 3.17 --turnover-amt 11.43
```

## 在 AI Agent 中安装使用

本仓库遵循标准 `SKILL.md` 多文件技能规范，可直接导入支持 Skills 的 AI 助手（Gemini / Claude Code / Cursor / OpenClaw 等）：

1. 克隆或下载本仓库目录 `a-share-dragon-head/`。
2. 将整个目录放入你的 Agent Skills 目录，或在技能管理界面直接上传本仓库 ZIP 包。
3. 触发词示例：`找今天A股主板唯一真龙头`、`帮我做今晚20:00龙头战法复盘`、`09:25集合竞价点评表A`、`测算这只票的10日卡异动价格`。

## 免责声明

本项目仅供量化规则研究、交易纪律复盘与个人方法论整理，不构成任何证券投资建议或收益承诺。A 股短线交易波动极大，请独立判断并严格自控风险。
