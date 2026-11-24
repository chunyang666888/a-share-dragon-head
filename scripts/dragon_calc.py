#!/usr/bin/env python3
"""Deterministic 7-in-1 calculator for A-share mainboard dragon-head trading.

Subcommands:
  sentiment       5-factor market sentiment thermometer (0-100) & position cap
  leader_score    Objective Table A / Table B / Veto classifier for sole leaders
  five_dim_score  5-dimension 100-point quantitative dragon-head scorer
  yidong          SH/SZ mainboard 10-day (+100%) & 30-day (+200%) severe abnormal movement
  levels          Next-day limit-up/down, -5% auction circuit breaker, MA5/MA10, cost math
  auction         09:25 call auction volume ratio & weak-to-strong grader
  seal            Limit-up sealing amount / daily turnover ratio grader
"""

import argparse
import json
import sys


def round_price(val: float) -> float:
    return round(val + 1e-9, 2)


def calc_sentiment(args: argparse.Namespace) -> dict:
    # 1. Limit-up count (0-25)
    if args.lu < 30:
        s_lu = 5
    elif args.lu < 45:
        s_lu = 12
    elif args.lu <= 95:
        s_lu = 22
    elif args.lu <= 130:
        s_lu = 25
    else:
        s_lu = 25

    # 2. Limit-down count (0-25, lower is better)
    if args.ld <= 3:
        s_ld = 25
    elif args.ld <= 8:
        s_ld = 20
    elif args.ld <= 15:
        s_ld = 12
    elif args.ld < 30:
        s_ld = 5
    else:
        s_ld = 0

    # 3. Bomb rate (0-20, lower is stronger)
    if args.bomb < 20:
        s_bomb = 20
    elif args.bomb < 30:
        s_bomb = 16
    elif args.bomb < 45:
        s_bomb = 10
    else:
        s_bomb = 4

    # 4. Promotion rate (0-15)
    if args.promo < 20:
        s_promo = 3
    elif args.promo < 35:
        s_promo = 8
    elif args.promo <= 65:
        s_promo = 13
    else:
        s_promo = 15

    # 5. Max consecutive board height (0-15)
    if args.max_board <= 2:
        s_board = 3
    elif args.max_board == 3:
        s_board = 7
    elif args.max_board <= 5:
        s_board = 12
    else:
        s_board = 15

    total = s_lu + s_ld + s_bomb + s_promo + s_board

    if total < 25 or args.ld >= 30:
        stage = "退潮 / 极度冰点期"
        pos_cap = "0% - 20%"
        advice = "空仓防守为主, 仅盯1只逆势抗跌穿越活口, 严禁接力中位股"
    elif total > 85 or (args.lu >= 130 and args.promo >= 80):
        stage = "情绪一致高潮预警期"
        pos_cap = "40% - 60% (只卖不追一致)"
        advice = "严防次日高开低走兑现, 持仓逢一致加速锁利"
    elif total >= 70 and args.bomb >= 45:
        stage = "高潮次日强分歧期"
        pos_cap = "30% - 50%"
        advice = "去弱留强, 严禁追高开后排, 只做唯一总龙承接或最高位断板弱转强"
    elif total >= 45 and args.bomb < 45:
        stage = "主升 / 良性换手期"
        pos_cap = "50% - 70%"
        advice = "最佳赚钱窗口, 聚焦表A唯一真龙与最高身位换手龙"
    else:
        stage = "弱势分歧 / 筑底试错期"
        pos_cap = "20% - 30%"
        advice = "轻仓只做唯一真龙首阴5日线低吸或冰点后首只弱转强"

    return {
        "temperature_score": total,
        "stage": stage,
        "position_cap": pos_cap,
        "advice": advice,
        "breakdown": {
            "limit_up_score": s_lu,
            "limit_down_score": s_ld,
            "bomb_rate_score": s_bomb,
            "promotion_score": s_promo,
            "max_board_score": s_board,
        },
    }


def calc_leader_score(args: argparse.Namespace) -> dict:
    veto_reasons = []
    if args.reg_warning:
        veto_reasons.append("存在监管工作函/ST/立案/重大证伪澄清")
    if args.lhasa_dominated:
        veto_reasons.append("龙虎榜拉萨散户席位霸榜派发")
    if veto_reasons:
        return {
            "symbol": args.symbol,
            "bucket": "直接淘汰(一票否决)",
            "score": 0,
            "reasons": veto_reasons,
        }

    if args.one_word or args.severe_yidong:
        reasons = []
        if args.one_word:
            reasons.append("连续缩量一字无换手(假集中度风险)")
        if args.severe_yidong:
            reasons.append("已触发或逼近严重异常波动红线")
        return {
            "symbol": args.symbol,
            "bucket": "表B: 纯情绪风向标(只看不买)",
            "score": 40,
            "reasons": reasons,
        }

    if args.mid_tier_follow and not args.is_top_leader and not args.top_board_break:
        return {
            "symbol": args.symbol,
            "bucket": "直接淘汰(中位跟风板)",
            "score": 20,
            "reasons": ["属于梯队中位跟风补涨, 非全场唯一真龙或最高身位"],
        }

    score = 0
    notes = []

    if args.is_top_leader:
        score += 35
        notes.append("全场人气总龙或最高连板身位(+35)")
    elif args.top_board_break:
        score += 25
        notes.append("最高位首次断板活口(+25)")
    else:
        score += 10
        notes.append("普通前排标的(+10)")

    # Turnover health
    if 15.0 <= args.turnover <= 45.0:
        score += 20
        notes.append(f"健康充分换手 {args.turnover:.2f}%(+20)")
    elif 3.0 <= args.turnover < 15.0:
        score += 15
        notes.append(f"缩量锁筹换手 {args.turnover:.2f}%(+15)")
    else:
        score += 5
        notes.append(f"换手率 {args.turnover:.2f}% 偏极端的过热或无量(+5)")

    # Three-platform buzz
    buzz_map = {
        "top": (20, "东财/同花顺/淘股吧三平台顶流辨识度(+20)"),
        "medium": (10, "三平台中等讨论度(+10)"),
        "low": (0, "三平台辨识度偏低(+0)"),
    }
    b_pts, b_note = buzz_map[args.buzz_level]
    score += b_pts
    notes.append(b_note)

    # Capital resonance
    if args.inst_net_buy:
        score += 25
        notes.append("龙虎榜获机构/北向/顶级游资共振净买入(+25)")
    else:
        score += 8
        notes.append("纯游资或无显著大资金共振(+8)")

    if args.top_board_break and not args.is_top_leader:
        bucket = "表A末位: 最高位断板观察(次日仅看竞价弱转强)"
    elif score >= 75:
        bucket = "表A核心: 实盘唯一真龙(★★★★★/★★★★☆)"
    elif score >= 60:
        bucket = "表A备选: 强分歧承接核心(★★★☆☆)"
    else:
        bucket = "直接淘汰(综合辨识度与合力不足)"

    return {
        "symbol": args.symbol,
        "bucket": bucket,
        "score": score,
        "notes": notes,
    }


def calc_five_dim_score(args: argparse.Namespace) -> dict:
    # Clamp inputs to max weights: sentiment(30), status(25), tech(20), chip(15), fund(10)
    s_sent = max(0, min(30, args.sentiment))
    s_stat = max(0, min(25, args.status))
    s_tech = max(0, min(20, args.tech))
    s_chip = max(0, min(15, args.chip))
    s_fund = max(0, min(10, args.fundamental))
    total = s_sent + s_stat + s_tech + s_chip + s_fund

    if total >= 80:
        rating = "强关注(A级核心)"
        pos_advice = "强周期最高可至 60%-80% 仓位, 严守标准买点与 3%-5% 硬止损"
    elif total >= 60:
        rating = "一般关注(B级观察)"
        pos_advice = "仓位上限不超过 30%-50%, 必须结合盘中量价与分时承接确认"
    else:
        rating = "不建议操作(放弃)"
        pos_advice = "风险大于机会, 直接放弃"

    return {
        "symbol": args.symbol,
        "total_score": total,
        "rating": rating,
        "position_advice": pos_advice,
        "dimensions": {
            "market_sentiment_30": s_sent,
            "dragon_status_25": s_stat,
            "technical_pattern_20": s_tech,
            "chip_and_capital_15": s_chip,
            "catalyst_and_cap_10": s_fund,
        },
    }


def calc_yidong(args: argparse.Namespace) -> dict:
    market_name = "深市主板(基准: 深证A指 399107)" if args.market == "sz" else "沪市主板(基准: 上证指数 000001)"
    limit_up = round_price(args.close * 1.10)

    out = {
        "market": market_name,
        "current_close": args.close,
        "next_limit_up": limit_up,
    }

    if args.base10 is not None:
        trigger_10d = round_price(args.base10 * (2.00 + args.idx10 / 100.0))
        frontrun_10d = round_price(trigger_10d * 0.98)
        cur_dev_10d = round(((args.close / args.base10 - 1.0) * 100.0) - args.idx10, 2)
        lu_dev_10d = round(((limit_up / args.base10 - 1.0) * 100.0) - args.idx10, 2)
        out["window_10d_100pct"] = {
            "base_close": args.base10,
            "index_change_pct": args.idx10,
            "current_deviation_pct": cur_dev_10d,
            "if_limit_up_deviation_pct": lu_dev_10d,
            "trigger_price": trigger_10d,
            "frontrun_warning_price": frontrun_10d,
            "limit_up_triggers_severe": lu_dev_10d >= 100.0,
        }

    if args.base30 is not None:
        trigger_30d = round_price(args.base30 * (3.00 + args.idx30 / 100.0))
        frontrun_30d = round_price(trigger_30d * 0.98)
        cur_dev_30d = round(((args.close / args.base30 - 1.0) * 100.0) - args.idx30, 2)
        lu_dev_30d = round(((limit_up / args.base30 - 1.0) * 100.0) - args.idx30, 2)
        out["window_30d_200pct"] = {
            "base_close": args.base30,
            "index_change_pct": args.idx30,
            "current_deviation_pct": cur_dev_30d,
            "if_limit_up_deviation_pct": lu_dev_30d,
            "trigger_price": trigger_30d,
            "frontrun_warning_price": frontrun_30d,
            "limit_up_triggers_severe": lu_dev_30d >= 200.0,
        }

    return out


def calc_levels(args: argparse.Namespace) -> dict:
    close = args.close
    limit_up = round_price(close * 1.10)
    limit_down = round_price(close * 0.90)
    circuit_breaker_neg5 = round_price(close * 0.95)
    mild_dip_neg3 = round_price(close * 0.97)
    spike_plus5 = round_price(close * 1.05)
    spike_plus7 = round_price(close * 1.07)

    out = {
        "current_close": close,
        "next_limit_up_10pct": limit_up,
        "next_limit_down_neg10pct": limit_down,
        "auction_circuit_breaker_neg5pct": circuit_breaker_neg5,
        "mild_dip_neg3pct": mild_dip_neg3,
        "intraday_plus5pct": spike_plus5,
        "intraday_plus7pct": spike_plus7,
    }

    if args.closes5:
        vals = [float(x.strip()) for x in args.closes5.split(",") if x.strip()]
        if len(vals) >= 5:
            last5 = vals[-5:]
            out["ma5"] = {
                "today": round_price(sum(last5) / 5.0),
                "next_day_if_flat": round_price((sum(last5[1:]) + close) / 5.0),
            }
        if len(vals) >= 10:
            last10 = vals[-10:]
            out["ma10"] = {
                "today": round_price(sum(last10) / 10.0),
                "next_day_if_flat": round_price((sum(last10[1:]) + close) / 10.0),
            }

    if args.cost is not None:
        pnl_pct = round((close / args.cost - 1.0) * 100.0, 2)
        cost_vs_close_pct = round((args.cost / close - 1.0) * 100.0, 2)
        out["position"] = {
            "cost_basis": args.cost,
            "current_pnl_pct": pnl_pct,
            "drop_to_breakeven_pct": cost_vs_close_pct,
            "remaining_cost_if_sell_half_at_plus5pct": round_price(2 * args.cost - spike_plus5),
            "remaining_cost_if_sell_half_at_limit_up": round_price(2 * args.cost - limit_up),
        }

    return out


def calc_auction(args: argparse.Namespace) -> dict:
    open_pct = round((args.open_price / args.prev_close - 1.0) * 100.0, 2)
    vol_ratio_pct = round((args.auction_amt / args.prev_amt) * 100.0, 2) if args.prev_amt > 0 else 0.0

    if open_pct <= -5.0:
        verdict = "触发 -5% 竞价熔断, 直接拉黑当日, 严禁抄底或翘板"
    elif open_pct >= 2.0 and vol_ratio_pct >= 3.0:
        verdict = "标准竞价爆量弱转强(达标), 关注 09:30-09:45 承接与半路/回封"
    elif open_pct >= 2.0 and vol_ratio_pct < 3.0:
        verdict = "缩量虚高开(防量化次日高开秒砸), 绝不盲目追高, 等换手确认"
    elif -5.0 < open_pct < 2.0:
        verdict = "正常分歧开盘, 纳入 09:45-10:30 回踩5日/10日均线缩量企稳观察"
    else:
        verdict = "中性观察"

    return {
        "open_change_pct": open_pct,
        "auction_to_prev_turnover_pct": vol_ratio_pct,
        "verdict": verdict,
    }


def calc_seal(args: argparse.Namespace) -> dict:
    ratio = round(args.seal_amt / args.turnover_amt, 2) if args.turnover_amt > 0 else 0.0
    if ratio >= 3.0:
        grade = "极强封单(高溢价预期 +4%~+8%+)"
    elif ratio >= 1.0:
        grade = "健康强封(次日高开溢价概率大 +2%~+5%)"
    elif ratio >= 0.5:
        grade = "中性偏弱封单(次日看竞价强弱决定去留)"
    else:
        grade = "极弱封单/偷袭板警报(次日防平开低走或量化砸盘)"

    return {
        "seal_to_turnover_ratio": ratio,
        "grade": grade,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="A-share mainboard dragon-head 7-in-1 calculator")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_st = sub.add_parser("sentiment", help="Calculate 0-100 market sentiment score")
    p_st.add_argument("--lu", type=int, required=True, help="Limit-up stock count")
    p_st.add_argument("--ld", type=int, required=True, help="Limit-down stock count")
    p_st.add_argument("--bomb", type=float, required=True, help="Bomb rate in percent")
    p_st.add_argument("--promo", type=float, required=True, help="Consecutive board promotion rate in percent")
    p_st.add_argument("--max-board", type=int, required=True, help="Highest consecutive board count")

    p_ls = sub.add_parser("leader_score", help="Classify candidate into Table A / Table B / Veto")
    p_ls.add_argument("--symbol", type=str, required=True, help="Stock name or code")
    p_ls.add_argument("--turnover", type=float, required=True, help="Latest daily turnover rate in percent")
    p_ls.add_argument("--buzz-level", choices=["top", "medium", "low"], default="medium", help="Three-platform buzz level")
    p_ls.add_argument("--is-top-leader", action="store_true", help="Market sole leader or highest board leader")
    p_ls.add_argument("--top-board-break", action="store_true", help="Highest-tier first board-break survivor")
    p_ls.add_argument("--inst-net-buy", action="store_true", help="Institutional/northbound/top-youzi net buy")
    p_ls.add_argument("--one-word", action="store_true", help="Continuous volume-less one-word limit-up")
    p_ls.add_argument("--severe-yidong", action="store_true", help="Triggered severe abnormal movement")
    p_ls.add_argument("--mid-tier-follow", action="store_true", help="Mid-tier low-recognition follow-on board")
    p_ls.add_argument("--reg-warning", action="store_true", help="Regulatory warning letter, ST, or falsified logic")
    p_ls.add_argument("--lhasa-dominated", action="store_true", help="Retail Lhasa seats dominating buy side")

    p_5d = sub.add_parser("five_dim_score", help="5-dimension 100-point dragon-head scorer")
    p_5d.add_argument("--symbol", type=str, required=True, help="Stock name or code")
    p_5d.add_argument("--sentiment", type=int, required=True, help="Market sentiment & cycle score (0-30)")
    p_5d.add_argument("--status", type=int, required=True, help="Dragon status & recognition score (0-25)")
    p_5d.add_argument("--tech", type=int, required=True, help="Technical pattern & volume score (0-20)")
    p_5d.add_argument("--chip", type=int, required=True, help="Chip & capital structure score (0-15)")
    p_5d.add_argument("--fundamental", type=int, required=True, help="Catalyst & market cap score (0-10)")

    p_yd = sub.add_parser("yidong", help="Calculate severe abnormal movement thresholds")
    p_yd.add_argument("--market", choices=["sh", "sz"], required=True, help="sh or sz mainboard")
    p_yd.add_argument("--close", type=float, required=True, help="Latest closing price")
    p_yd.add_argument("--base10", type=float, default=None, help="Closing price prior to 10-day window")
    p_yd.add_argument("--idx10", type=float, default=0.0, help="Benchmark index 10-day change in percent")
    p_yd.add_argument("--base30", type=float, default=None, help="Closing price prior to 30-day window")
    p_yd.add_argument("--idx30", type=float, default=0.0, help="Benchmark index 30-day change in percent")

    p_lv = sub.add_parser("levels", help="Calculate key price levels, MAs, and position math")
    p_lv.add_argument("--close", type=float, required=True, help="Latest closing price")
    p_lv.add_argument("--cost", type=float, default=None, help="User holding cost basis")
    p_lv.add_argument("--closes5", type=str, default=None, help="Comma-separated recent 5 or 10 closes (oldest to newest)")

    p_au = sub.add_parser("auction", help="Evaluate 09:25 call auction volume and weak-to-strong")
    p_au.add_argument("--prev-close", type=float, required=True, help="Previous closing price")
    p_au.add_argument("--open-price", type=float, required=True, help="09:25 opening price")
    p_au.add_argument("--prev-amt", type=float, required=True, help="Previous full-day turnover amount")
    p_au.add_argument("--auction-amt", type=float, required=True, help="09:25 call auction turnover amount")

    p_sl = sub.add_parser("seal", help="Evaluate limit-up seal-to-turnover ratio")
    p_sl.add_argument("--seal-amt", type=float, required=True, help="Closing bid-1 sealing amount")
    p_sl.add_argument("--turnover-amt", type=float, required=True, help="Full-day turnover amount")

    args = parser.parse_args()
    handlers = {
        "sentiment": calc_sentiment,
        "leader_score": calc_leader_score,
        "five_dim_score": calc_five_dim_score,
        "yidong": calc_yidong,
        "levels": calc_levels,
        "auction": calc_auction,
        "seal": calc_seal,
    }
    result = handlers[args.cmd](args)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
