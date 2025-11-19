#!/usr/bin/env python3
"""tempList生成ルールの具体例テスト"""

def build_temp_list(nums):
    """tempListを「4桁単位で最小値から順に重複せずに選択」のルールで生成"""
    temp_list = []
    remaining = nums.copy()
    
    # 4桁単位で処理
    while len(remaining) > 0:
        chunk = []
        # 重複しない最小値から順に選ぶ
        unique_elements = sorted(list(set(remaining)))
        for digit in unique_elements:
            if len(chunk) < 4 and digit in remaining:
                chunk.append(digit)
                remaining.remove(digit)
        
        # 4桁に満たない場合、残りから最小値から順に埋める（重複してもOK）
        # 「最小値から順に」は0～9まで重複せずに順番に埋めていく（連続していなくてもOK）
        if len(chunk) < 4 and len(remaining) > 0:
            while len(chunk) < 4 and len(remaining) > 0:
                # chunkの最後の数字を取得（なければ-1）
                last_digit = chunk[-1] if chunk else -1
                # 最後の数字の次の最小値（0～9の順序で）を残りから選ぶ
                candidates = [d for d in remaining if d > last_digit]
                if candidates:
                    next_digit = min(candidates)
                else:
                    # last_digitより大きい数字がない場合は、残りから最小値を選ぶ
                    next_digit = min(remaining)
                chunk.append(next_digit)
                remaining.remove(next_digit)
        
        temp_list.extend(chunk)
        print(f"  チャンク: {chunk}, 残り: {remaining}")
    
    return temp_list

# 例1: [1, 1, 2, 2, 3, 3]
print("例1: nums = [1, 1, 2, 2, 3, 3]")
result1 = build_temp_list([1, 1, 2, 2, 3, 3])
print(f"  結果: tempList = {result1}\n")

# 例2: [0, 0, 1, 1, 2, 2, 3]
print("例2: nums = [0, 0, 1, 1, 2, 2, 3]")
result2 = build_temp_list([0, 0, 1, 1, 2, 2, 3])
print(f"  結果: tempList = {result2}\n")

# 例3: [5, 5, 6, 6, 7, 7, 8]
print("例3: nums = [5, 5, 6, 6, 7, 7, 8]")
result3 = build_temp_list([5, 5, 6, 6, 7, 7, 8])
print(f"  結果: tempList = {result3}\n")

# 例4: [2, 2, 4, 4, 6, 6]
print("例4: nums = [2, 2, 4, 4, 6, 6]")
result4 = build_temp_list([2, 2, 4, 4, 6, 6])
print(f"  結果: tempList = {result4}\n")

# 例5: [3, 3, 3, 4, 4] (既知の例)
print("例5: nums = [3, 3, 3, 4, 4]")
result5 = build_temp_list([3, 3, 3, 4, 4])
print(f"  結果: tempList = {result5}\n")

# 例6: [0, 1, 1, 2, 2, 5, 7, 8, 8, 9, 9] (ユーザーが最初に提示した例)
print("例6: nums = [0, 1, 1, 2, 2, 5, 7, 8, 8, 9, 9]")
result6 = build_temp_list([0, 1, 1, 2, 2, 5, 7, 8, 8, 9, 9])
print(f"  結果: tempList = {result6}\n")

# 例7: [1, 1, 3, 3, 5, 5, 7]
print("例7: nums = [1, 1, 3, 3, 5, 5, 7]")
result7 = build_temp_list([1, 1, 3, 3, 5, 5, 7])
print(f"  結果: tempList = {result7}\n")

