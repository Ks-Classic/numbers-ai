#!/usr/bin/env python3
"""
モデル精度確認スクリプト

修正前のデータで学習したモデルが、修正後のデータでどの程度正確か確認します。
"""

import sys
from pathlib import Path
import csv

# プロジェクトルート
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'core'))

DATA_DIR = PROJECT_ROOT / 'data'
MODELS_DIR = DATA_DIR / 'models'

def load_past_results():
    """過去の結果を読み込む"""
    csv_path = DATA_DIR / 'past_results.csv'
    data = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                round_num = int(row['round_number'])
                n3_winning = row.get('n3_winning', 'NULL')
                n4_winning = row.get('n4_winning', 'NULL')
                
                # NULLでない回号のみ保存
                if n3_winning != 'NULL' and n4_winning != 'NULL':
                    data.append({
                        'round_number': round_num,
                        'n3_winning': n3_winning,
                        'n4_winning': n4_winning,
                        'n3_rehearsal': row.get('n3_rehearsal', 'NULL'),
                        'n4_rehearsal': row.get('n4_rehearsal', 'NULL'),
                        'draw_date': row.get('draw_date', 'NULL')
                    })
            except:
                continue
    
    return data

def analyze_data_quality(data):
    """データの品質を分析"""
    print("=" * 80)
    print("データ品質分析")
    print("=" * 80)
    
    # 6847以前と以降に分ける
    before_fix = [d for d in data if d['round_number'] <= 6847]
    after_fix = [d for d in data if d['round_number'] > 6847]
    
    print(f"\n📊 データ分布:")
    print(f"  総データ数: {len(data)} 回号")
    print(f"  回号6847以前（修正されたデータ）: {len(before_fix)} 回号")
    print(f"  回号6848以降（元々正しいデータ）: {len(after_fix)} 回号")
    
    # サンプルデータを表示
    print(f"\n📌 回号6847付近のサンプル:")
    sample_rounds = [6845, 6846, 6847, 6848, 6849, 6850]
    for round_num in sample_rounds:
        sample = next((d for d in data if d['round_number'] == round_num), None)
        if sample:
            print(f"  {round_num}: N3_rehearsal={sample['n3_rehearsal']}, "
                  f"N3_winning={sample['n3_winning']}, "
                  f"N4_rehearsal={sample['n4_rehearsal']}, "
                  f"N4_winning={sample['n4_winning']}")
    
    return before_fix, after_fix

def check_model_existence():
    """モデルファイルの存在確認"""
    print("\n" + "=" * 80)
    print("モデルファイル確認")
    print("=" * 80)
    
    models_found = {
        'combination_batches': False,
        'axis_batches': False,
        'checkpoint': False
    }
    
    # Combinationバッチモデル
    comb_dir = MODELS_DIR / 'combination_batches'
    if comb_dir.exists():
        pkl_files = list(comb_dir.glob('*.pkl'))
        if pkl_files:
            models_found['combination_batches'] = True
            print(f"\n✓ Combination Batches: {len(pkl_files)} ファイル")
            # 最新ファイルのタイムスタンプ
            import os
            latest = max(pkl_files, key=os.path.getmtime)
            import datetime
            mtime = os.path.getmtime(latest)
            timestamp = datetime.datetime.fromtimestamp(mtime)
            print(f"  最終更新: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Axisバッチモデル
    axis_dir = MODELS_DIR / 'axis_batches'
    if axis_dir.exists():
        pkl_files = list(axis_dir.glob('*.pkl'))
        if pkl_files:
            models_found['axis_batches'] = True
            print(f"\n✓ Axis Batches: {len(pkl_files)} ファイル")
    
    # チェックポイント
    checkpoint_file = MODELS_DIR / 'combination_checkpoint.pkl'
    if checkpoint_file.exists():
        models_found['checkpoint'] = True
        print(f"\n✓ Checkpoint: {checkpoint_file.name}")
    
    if not any(models_found.values()):
        print("\n❌ モデルファイルが見つかりません")
    
    return models_found

def analyze_learning_impact(before_fix, after_fix):
    """学習データへの影響を分析"""
    print("\n" + "=" * 80)
    print("モデル学習への影響分析")
    print("=" * 80)
    
    print(f"\n⚠️  問題の概要:")
    print(f"  モデル生成日: 2025年11月18日")
    print(f"  その時点でのデータ状態:")
    print(f"    - 回号6847以前: リハーサルと本番が逆（間違い）")
    print(f"    - 回号6848以降: 正しいデータ")
    
    total_data = len(before_fix) + len(after_fix)
    wrong_data_percentage = (len(before_fix) / total_data * 100) if total_data > 0 else 0
    
    print(f"\n📊 学習データの構成（2025年11月18日時点）:")
    print(f"  総データ: {total_data} 回号")
    print(f"  間違ったデータ: {len(before_fix)} 回号 ({wrong_data_percentage:.1f}%)")
    print(f"  正しいデータ: {len(after_fix)} 回号 ({100-wrong_data_percentage:.1f}%)")
    
    print(f"\n🎯 影響評価:")
    if wrong_data_percentage > 90:
        print(f"  ❌ 極めて深刻: 学習データの{wrong_data_percentage:.1f}%が間違っていた")
        print(f"     → モデルは主にリハーサル番号を学習していた可能性が高い")
        print(f"     → 予測精度に重大な影響がある")
    elif wrong_data_percentage > 50:
        print(f"  ⚠️  深刻: 学習データの{wrong_data_percentage:.1f}%が間違っていた")
        print(f"     → モデルの信頼性に疑問がある")
    elif wrong_data_percentage > 10:
        print(f"  ⚠️  影響あり: 学習データの{wrong_data_percentage:.1f}%が間違っていた")
        print(f"     → 一部の予測に影響がある可能性")
    else:
        print(f"  ✓ 影響軽微: 学習データの{wrong_data_percentage:.1f}%のみが間違っていた")
    
def main():
    print("\n")
    print("█" * 80)
    print("  Numbers-AI モデル精度確認")
    print("█" * 80)
    
    # 1. データ読み込み
    print("\n📂 データ読み込み中...")
    data = load_past_results()
    print(f"✓ {len(data)} 回号分のデータを読み込みました")
    
    # 2. データ品質分析
    before_fix, after_fix = analyze_data_quality(data)
    
    # 3. モデルファイル確認
    models_found = check_model_existence()
    
    # 4. 学習への影響分析
    analyze_learning_impact(before_fix, after_fix)
    
    # 5. 推奨アクション
    print("\n" + "=" * 80)
    print("推奨アクション")
    print("=" * 80)
    
    if any(models_found.values()):
        print("\n現在のモデルは間違ったデータで学習されています。")
        print("\n【選択肢】")
        print("  1. モデルを削除して統計ベースの予測のみを使用（暫定対応）")
        print("     → 安全だが、予測の幅が狭くなる")
        print("  2. 新しいデータでモデルを再学習（推奨、時間がかかる）")
        print("     → 最も正確だが、モデル生成環境の再構築が必要")
        print("  3. そのまま使用して精度をモニタリング")
        print("     → リスクあり、予測結果の検証が必要")
    else:
        print("\n✓ モデルファイルが見つからないため、影響はありません")
        print("  現在は統計ベースの予測のみを使用しています")
    
    print("\n" + "=" * 80)
    print("完了")
    print("=" * 80)
    print()

if __name__ == "__main__":
    main()
