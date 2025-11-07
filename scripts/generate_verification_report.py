#!/usr/bin/env python3
"""
keisen_master.json検証レポート生成スクリプト
"""

import json
import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
OUTPUT_DIR = Path(__file__).parent.parent / "docs" / "report"

def generate_report():
    """検証レポートを生成"""
    
    # 検証結果を読み込む
    with open(DATA_DIR / "keisen_master_verification.json", 'r', encoding='utf-8') as f:
        verification = json.load(f)
    
    # keisen_master.jsonを読み込む
    with open(DATA_DIR / "keisen_master.json", 'r', encoding='utf-8') as f:
        keisen_master = json.load(f)
    
    # 統計を計算
    total_patterns = len(verification)
    match_patterns = [r for r in verification if r['status'] == 'MATCH']
    partial_match_patterns = [r for r in verification if r['status'] == 'PARTIAL_MATCH']
    mismatch_patterns = [r for r in verification if r['status'] == 'MISMATCH']
    empty_patterns = [r for r in verification if r['status'] == 'EMPTY']
    
    match_rate = len(match_patterns) / total_patterns * 100
    partial_rate = len(partial_match_patterns) / total_patterns * 100
    mismatch_rate = len(mismatch_patterns) / total_patterns * 100
    
    avg_match_rate = sum([r['match_rate'] for r in verification if r['status'] != 'NO_DATA' and r['status'] != 'EMPTY']) / len([r for r in verification if r['status'] != 'NO_DATA' and r['status'] != 'EMPTY']) * 100
    
    # レポートを生成
    report_lines = []
    report_lines.append("# keisen_master.json検証レポート")
    report_lines.append("")
    report_lines.append("## 概要")
    report_lines.append("")
    report_lines.append("本レポートは、`keisen_master.json`の予測出目が、1340-6391回の実データと一致しているかを検証した結果です。")
    report_lines.append("")
    report_lines.append("### 検証方法")
    report_lines.append("")
    report_lines.append("1. **データ範囲**: 1340-6391回（週5回制開始以降）")
    report_lines.append("2. **検証ロジック**:")
    report_lines.append("   - 前々回の当選番号の該当桁（例：百の位）")
    report_lines.append("   - 前回の当選番号の該当桁（例：百の位）")
    report_lines.append("   - その組み合わせのときに、実際に当選した数字（その桁）の出現回数を集計")
    report_lines.append("   - 出現回数の降順でソート（同率は昇順）")
    report_lines.append("   - `keisen_master.json`の予測出目が実データの上位に含まれているかを確認")
    report_lines.append("")
    report_lines.append("### 検証結果サマリー")
    report_lines.append("")
    report_lines.append(f"- **総パターン数**: {total_patterns}パターン")
    report_lines.append(f"- **完全一致**: {len(match_patterns)}パターン ({match_rate:.1f}%)")
    report_lines.append(f"- **部分一致**: {len(partial_match_patterns)}パターン ({partial_rate:.1f}%)")
    report_lines.append(f"- **不一致**: {len(mismatch_patterns)}パターン ({mismatch_rate:.1f}%)")
    report_lines.append(f"- **空パターン**: {len(empty_patterns)}パターン")
    report_lines.append(f"- **平均一致率**: {avg_match_rate:.2f}%")
    report_lines.append("")
    report_lines.append("## 判断基準")
    report_lines.append("")
    report_lines.append("### 完全一致（MATCH）")
    report_lines.append("")
    report_lines.append("`keisen_master.json`の予測出目が、実データの上位（予測出目の数だけ）に**全て含まれている**場合。")
    report_lines.append("")
    report_lines.append("**例**:")
    report_lines.append("- keisen_master.jsonの予測出目: `[3, 9, 5]`")
    report_lines.append("- 実データの上位3位: `[3, 9, 5]`")
    report_lines.append("- → **完全一致** ✅")
    report_lines.append("")
    report_lines.append("### 部分一致（PARTIAL_MATCH）")
    report_lines.append("")
    report_lines.append("`keisen_master.json`の予測出目の**一部**が実データの上位に含まれている場合。")
    report_lines.append("")
    report_lines.append("**例**:")
    report_lines.append("- keisen_master.jsonの予測出目: `[5, 4, 3, 8, 9]`")
    report_lines.append("- 実データの上位5位: `[2, 1, 5, 6, 0]`")
    report_lines.append("- 一致している数字: `5`のみ（1つ）")
    report_lines.append("- → **部分一致** ⚠️")
    report_lines.append("")
    report_lines.append("### 不一致（MISMATCH）")
    report_lines.append("")
    report_lines.append("`keisen_master.json`の予測出目が、実データの上位に**全く含まれていない**場合。")
    report_lines.append("")
    report_lines.append("**例**:")
    report_lines.append("- keisen_master.jsonの予測出目: `[3, 9, 5]`")
    report_lines.append("- 実データの上位3位: `[4, 2, 6]`")
    report_lines.append("- 一致している数字: なし")
    report_lines.append("- → **不一致** ❌")
    report_lines.append("")
    report_lines.append("## 具体例")
    report_lines.append("")
    
    # 完全一致の例（サンプル数が多いもの）
    match_examples = sorted([r for r in match_patterns if r['total_samples'] >= 20], 
                           key=lambda x: x['total_samples'], reverse=True)[:3]
    
    if match_examples:
        report_lines.append("### 完全一致の例")
        report_lines.append("")
        for i, example in enumerate(match_examples, 1):
            report_lines.append(f"#### 例{i}: {example['n_type'].upper()} {example['column']} - 前々回={example['prev2']}, 前回={example['prev']}")
            report_lines.append("")
            report_lines.append(f"- **サンプル数**: {example['total_samples']}回")
            report_lines.append(f"- **keisen_master.jsonの予測出目**: `{example['keisen_predictions']}`")
            report_lines.append(f"- **実データの上位{len(example['keisen_predictions'])}位**: `{example['actual_top_n']}`")
            report_lines.append(f"- **一致数**: {example['match_count']}/{example['keisen_count']} ({example['match_rate']*100:.0f}%)")
            report_lines.append("")
            report_lines.append("**各数字の出現回数**:")
            for digit in sorted([int(k) for k in example['actual_counts'].keys()]):
                count = example['actual_counts'][str(digit)]
                mark = "✅" if digit in example['keisen_predictions'] else ""
                report_lines.append(f"  - 数字{digit}: {count}回 {mark}")
            report_lines.append("")
            report_lines.append("**判断**: 完全一致 ✅")
            report_lines.append("")
            report_lines.append("---")
            report_lines.append("")
    
    # 部分一致の例
    partial_examples = sorted([r for r in partial_match_patterns if r['total_samples'] >= 20], 
                             key=lambda x: x['match_rate'])[:3]
    
    if partial_examples:
        report_lines.append("### 部分一致の例")
        report_lines.append("")
        for i, example in enumerate(partial_examples, 1):
            report_lines.append(f"#### 例{i}: {example['n_type'].upper()} {example['column']} - 前々回={example['prev2']}, 前回={example['prev']}")
            report_lines.append("")
            report_lines.append(f"- **サンプル数**: {example['total_samples']}回")
            report_lines.append(f"- **keisen_master.jsonの予測出目**: `{example['keisen_predictions']}`")
            report_lines.append(f"- **実データの上位{len(example['keisen_predictions'])}位**: `{example['actual_top_n']}`")
            report_lines.append(f"- **一致数**: {example['match_count']}/{example['keisen_count']} ({example['match_rate']*100:.0f}%)")
            report_lines.append("")
            report_lines.append("**各数字の出現回数**:")
            for digit in sorted([int(k) for k in example['actual_counts'].keys()]):
                count = example['actual_counts'][str(digit)]
                mark = "✅" if digit in example['keisen_predictions'] else ""
                report_lines.append(f"  - 数字{digit}: {count}回 {mark}")
            report_lines.append("")
            report_lines.append("**判断**: 部分一致 ⚠️")
            report_lines.append("")
            report_lines.append("---")
            report_lines.append("")
    
    # 不一致の例
    if mismatch_patterns:
        mismatch_examples = sorted([r for r in mismatch_patterns if r['total_samples'] >= 20], 
                                  key=lambda x: x['total_samples'], reverse=True)[:3]
        
        if mismatch_examples:
            report_lines.append("### 不一致の例")
            report_lines.append("")
            for i, example in enumerate(mismatch_examples, 1):
                report_lines.append(f"#### 例{i}: {example['n_type'].upper()} {example['column']} - 前々回={example['prev2']}, 前回={example['prev']}")
                report_lines.append("")
                report_lines.append(f"- **サンプル数**: {example['total_samples']}回")
                report_lines.append(f"- **keisen_master.jsonの予測出目**: `{example['keisen_predictions']}`")
                report_lines.append(f"- **実データの上位{len(example['keisen_predictions'])}位**: `{example['actual_top_n']}`")
                report_lines.append(f"- **一致数**: {example['match_count']}/{example['keisen_count']} ({example['match_rate']*100:.0f}%)")
                report_lines.append("")
                report_lines.append("**各数字の出現回数**:")
                for digit in sorted([int(k) for k in example['actual_counts'].keys()]):
                    count = example['actual_counts'][str(digit)]
                    mark = "❌" if digit in example['keisen_predictions'] else ""
                    report_lines.append(f"  - 数字{digit}: {count}回 {mark}")
                report_lines.append("")
                report_lines.append("**判断**: 不一致 ❌")
                report_lines.append("")
                report_lines.append("---")
                report_lines.append("")
    
    # 結論
    report_lines.append("## 結論")
    report_lines.append("")
    report_lines.append(f"`keisen_master.json`の予測出目は、1340-6391回の実データと**{match_rate:.1f}%が完全一致**しています。")
    report_lines.append("")
    report_lines.append("### 推奨事項")
    report_lines.append("")
    if match_rate >= 90:
        report_lines.append("- ✅ **高精度**: 90%以上の完全一致率は非常に良好です。")
        report_lines.append("- `keisen_master.json`は実データに基づいて正確に作成されていると判断できます。")
    elif match_rate >= 70:
        report_lines.append("- ⚠️ **中程度の精度**: 70%以上の完全一致率は良好ですが、改善の余地があります。")
        report_lines.append("- 部分一致や不一致のパターンを確認し、必要に応じて`keisen_master.json`を更新することを検討してください。")
    else:
        report_lines.append("- ❌ **低精度**: 完全一致率が70%未満です。")
        report_lines.append("- `keisen_master.json`の見直しを強く推奨します。")
    report_lines.append("")
    report_lines.append("### 注意事項")
    report_lines.append("")
    report_lines.append("- サンプル数が少ないパターン（20回未満）は、統計的に信頼性が低い可能性があります。")
    report_lines.append("- 部分一致や不一致のパターンでも、実データの上位10位以内に含まれている場合は、予測として有効な可能性があります。")
    report_lines.append("- 本検証は1340-6391回のデータに基づいています。より新しいデータで再検証することで、予測精度の変化を確認できます。")
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")
    report_lines.append("*レポート生成日: 2025-01-XX*")
    report_lines.append("*検証データ範囲: 1340-6391回*")
    
    # レポートを保存
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = OUTPUT_DIR / "keisen_master_verification_report.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))
    
    print(f"レポート生成完了: {report_path}")
    return report_path

if __name__ == "__main__":
    generate_report()

