#!/usr/bin/env python3
"""
画像ファイルから文字を抽出するスクリプト（OCR対応・表構造認識）

画像ファイルからOCRでテキストを抽出します。
表データの抽出に最適化されたOCR設定を使用し、表の構造情報を活用して精度を向上させます。

使い方:
    python extract_text.py <画像ファイルパス>
    python extract_text.py <フォルダパス>

出力:
    - コンソールにOCR結果を表示
    - GPTなどに渡す際のプロンプト形式でも出力
"""

import sys
import re
from pathlib import Path
from typing import Optional, Dict, List, Tuple

try:
    from PIL import Image
    import pytesseract
    HAS_OCR = True
except ImportError:
    HAS_OCR = False
    print("エラー: 必要なパッケージがインストールされていません。")
    print("以下のコマンドを実行してください:")
    print("  cd scripts && source venv/bin/activate && pip install -r requirements.txt")
    sys.exit(1)

try:
    import cv2
    import numpy as np
    HAS_CV = True
except ImportError:
    HAS_CV = False
    print("⚠ OpenCVがインストールされていません。表構造認識機能は無効です。")
    print("基本的なOCRは実行できますが、精度向上のためOpenCVのインストールを推奨します。")


def detect_table_structure(img_array: np.ndarray) -> Optional[Dict]:
    """
    画像から表の構造を検出
    
    表の構造:
    - 一番左の列: 「前々回」「前回」「予測出目」（固定）
    - 「前々回」の隣のセル: 0～9のどれか
    - 「前回」の行: 0～9で固定（列ヘッダー）
    - 「予測出目」のセル: 前回行の0～9ごとの列の下に3～7ケタくらいの数字
    
    Returns:
        表の構造情報（行・列の境界線など）またはNone
    """
    if not HAS_CV:
        return None
    
    try:
        # グレースケール化
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY) if len(img_array.shape) == 3 else img_array
        
        # 二値化
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # 横線検出
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
        detected_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)
        h_lines = cv2.HoughLinesP(detected_lines, 1, np.pi/180, 100, minLineLength=100, maxLineGap=10)
        
        # 縦線検出
        vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
        detected_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, vertical_kernel, iterations=2)
        v_lines = cv2.HoughLinesP(detected_lines, 1, np.pi/180, 100, minLineLength=100, maxLineGap=10)
        
        # 行・列の境界線を推定
        if h_lines is not None and v_lines is not None:
            h_positions = sorted(set([int(line[0][1]) for line in h_lines if abs(line[0][1] - line[0][3]) < 5]))
            v_positions = sorted(set([int(line[0][0]) for line in v_lines if abs(line[0][0] - line[0][2]) < 5]))
            
            return {
                'horizontal_lines': h_positions,
                'vertical_lines': v_positions,
                'rows': len(h_positions) - 1 if len(h_positions) > 1 else 0,
                'cols': len(v_positions) - 1 if len(v_positions) > 1 else 0
            }
    except Exception as e:
        print(f"    ⚠ 表構造検出エラー: {e}")
    
    return None


def extract_cell_text(img_array: np.ndarray, x1: int, y1: int, x2: int, y2: int) -> str:
    """
    指定されたセル領域からテキストを抽出
    """
    if not HAS_OCR:
        return ""
    
    try:
        # セル領域を切り出し
        cell_img = img_array[y1:y2, x1:x2]
        
        # セル領域が小さすぎる場合はスキップ
        if cell_img.size == 0 or cell_img.shape[0] < 10 or cell_img.shape[1] < 10:
            return ""
        
        # PIL Imageに変換
        if len(cell_img.shape) == 3:
            cell_pil = Image.fromarray(cv2.cvtColor(cell_img, cv2.COLOR_BGR2RGB))
        else:
            cell_pil = Image.fromarray(cell_img)
        
        # 数字のみ抽出する設定（予測出目のセル用）
        config_digits = r'--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789'
        text = pytesseract.image_to_string(cell_pil, config=config_digits)
        
        # 数字のみ抽出
        digits = re.sub(r'[^0-9]', '', text)
        
        return digits
    except Exception as e:
        return ""


def extract_text_with_structure(image_path: Path) -> Dict[str, any]:
    """
    表構造を活用してOCRを実行
    
    Returns:
        抽出結果の辞書（zenzenkai, column_data, raw_ocr）
    """
    result = {
        'zenzenkai': None,
        'column_data': {str(i): [] for i in range(10)},
        'raw_ocr': '',
        'structure_detected': False
    }
    
    if not HAS_OCR:
        return result
    
    try:
        # 画像を読み込み
        img = Image.open(image_path)
        img_array = np.array(img)
        
        # OpenCV形式に変換
        if HAS_CV:
            if len(img_array.shape) == 3:
                img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            else:
                img_cv = img_array.copy()
        else:
            img_cv = None
        
        # まず全体のOCRを実行（フォールバック用）
        custom_config = r'--oem 3 --psm 3 -l jpn+eng'
        raw_ocr = pytesseract.image_to_string(img, config=custom_config)
        result['raw_ocr'] = raw_ocr
        
        # 表構造を検出
        structure = None
        if HAS_CV and img_cv is not None:
            structure = detect_table_structure(img_cv)
            if structure:
                result['structure_detected'] = True
        
        # 構造情報がない場合は従来のOCR結果から抽出
        if not structure:
            # OCR結果から「前々回」の値を抽出
            zenzenkai_match = re.search(r'前々回\s*[:：]?\s*(\d)', raw_ocr)
            if zenzenkai_match:
                result['zenzenkai'] = int(zenzenkai_match.group(1))
            
            # 「予測出目」セクションから数字を抽出
            lines = raw_ocr.split('\n')
            in_prediction = False
            for line in lines:
                if '予測出目' in line or 'yosoku' in line.lower():
                    in_prediction = True
                    continue
                
                if in_prediction:
                    # 数字を抽出（3～7ケタ）
                    numbers = re.findall(r'\d{3,7}', line)
                    for num in numbers:
                        # 列位置を推定（簡易版）
                        for digit in num:
                            if digit.isdigit():
                                col = int(digit)
                                if col not in result['column_data'][str(col)]:
                                    result['column_data'][str(col)].append(col)
            
            return result
        
        # 構造情報がある場合、セル単位でOCR
        h_lines = structure.get('horizontal_lines', [])
        v_lines = structure.get('vertical_lines', [])
        
        if len(h_lines) < 3 or len(v_lines) < 2:
            return result
        
        # 一番左の列で「前々回」「前回」「予測出目」を探す
        left_col_end = v_lines[1] if len(v_lines) > 1 else img_array.shape[1] // 4
        
        # 各行を処理
        for i in range(len(h_lines) - 1):
            y1 = h_lines[i]
            y2 = h_lines[i + 1]
            
            # 左列のテキストを抽出
            left_cell = img_array[y1:y2, 0:left_col_end]
            if len(left_cell.shape) == 3:
                left_pil = Image.fromarray(cv2.cvtColor(left_cell, cv2.COLOR_BGR2RGB))
            else:
                left_pil = Image.fromarray(left_cell)
            
            left_text = pytesseract.image_to_string(left_pil, config=r'--oem 3 --psm 7 -l jpn+eng')
            
            # 「前々回」の行を検出
            if '前々回' in left_text or 'zenzenkai' in left_text.lower():
                # 隣のセルから0～9の値を抽出
                if len(v_lines) > 1:
                    x1 = left_col_end
                    x2 = v_lines[2] if len(v_lines) > 2 else left_col_end + 100
                    zenzenkai_text = extract_cell_text(img_cv, x1, y1, x2, y2)
                    if zenzenkai_text:
                        result['zenzenkai'] = int(zenzenkai_text[0]) if zenzenkai_text[0].isdigit() else None
            
            # 「前回」の行を検出（列ヘッダー0～9）
            elif '前回' in left_text or 'zenkai' in left_text.lower():
                # 各列のヘッダー（0～9）を抽出
                for j in range(len(v_lines) - 1):
                    if j == 0:
                        continue  # 左列はスキップ
                    x1 = v_lines[j]
                    x2 = v_lines[j + 1] if j + 1 < len(v_lines) else img_array.shape[1]
                    header_text = extract_cell_text(img_cv, x1, y1, x2, y2)
                    if header_text and header_text[0].isdigit():
                        col = int(header_text[0])
                        if 0 <= col <= 9:
                            result['column_data'][str(col)] = []
            
            # 「予測出目」の行を検出
            elif '予測出目' in left_text or 'yosoku' in left_text.lower() or 'demoku' in left_text.lower():
                # 各列の予測出目を抽出
                for j in range(len(v_lines) - 1):
                    if j == 0:
                        continue  # 左列はスキップ
                    x1 = v_lines[j]
                    x2 = v_lines[j + 1] if j + 1 < len(v_lines) else img_array.shape[1]
                    prediction_text = extract_cell_text(img_cv, x1, y1, x2, y2)
                    
                    # 3～7ケタの数字を抽出
                    if prediction_text:
                        # 数字を個別に抽出（各数字が0～9）
                        digits = [int(d) for d in prediction_text if d.isdigit() and 0 <= int(d) <= 9]
                        if digits:
                            # 列位置を推定（簡易版：列インデックスから）
                            col_idx = j - 1
                            if 0 <= col_idx <= 9:
                                result['column_data'][str(col_idx)].extend(digits)
                                result['column_data'][str(col_idx)] = list(set(result['column_data'][str(col_idx)]))
        
        # 予測出目の行以降も処理（複数行ある場合）
        prediction_row_idx = None
        for i in range(len(h_lines) - 1):
            y1 = h_lines[i]
            y2 = h_lines[i + 1]
            left_cell = img_array[y1:y2, 0:left_col_end]
            if len(left_cell.shape) == 3:
                left_pil = Image.fromarray(cv2.cvtColor(left_cell, cv2.COLOR_BGR2RGB))
            else:
                left_pil = Image.fromarray(left_cell)
            left_text = pytesseract.image_to_string(left_pil, config=r'--oem 3 --psm 7 -l jpn+eng')
            
            if '予測出目' in left_text:
                prediction_row_idx = i
                break
        
        if prediction_row_idx is not None:
            # 予測出目の行以降を処理
            for i in range(prediction_row_idx + 1, len(h_lines) - 1):
                y1 = h_lines[i]
                y2 = h_lines[i + 1]
                
                # 各列の数字を抽出
                for j in range(len(v_lines) - 1):
                    if j == 0:
                        continue
                    x1 = v_lines[j]
                    x2 = v_lines[j + 1] if j + 1 < len(v_lines) else img_array.shape[1]
                    cell_text = extract_cell_text(img_cv, x1, y1, x2, y2)
                    
                    if cell_text:
                        digits = [int(d) for d in cell_text if d.isdigit() and 0 <= int(d) <= 9]
                        if digits:
                            col_idx = j - 1
                            if 0 <= col_idx <= 9:
                                result['column_data'][str(col_idx)].extend(digits)
                                result['column_data'][str(col_idx)] = list(set(result['column_data'][str(col_idx)]))
        
        # 重複を除去してソート
        for col in result['column_data']:
            result['column_data'][col] = sorted(list(set(result['column_data'][col])))
        
    except Exception as e:
        print(f"✗ 構造認識OCRエラー: {e}")
        import traceback
        traceback.print_exc()
    
    return result


def extract_text_from_image(image_path: Path) -> str:
    """
    画像からOCRでテキストを抽出（従来の方法）
    """
    if not HAS_OCR:
        return ""
    
    try:
        img = Image.open(image_path)
        custom_config = r'--oem 3 --psm 3 -l jpn+eng'
        text = pytesseract.image_to_string(img, config=custom_config)
        return text
    except Exception as e:
        print(f"✗ OCRエラー: {e}")
        return ""


def format_for_gpt(image_path: Path, ocr_text: str, structure_result: Optional[Dict] = None) -> str:
    """
    GPTなどに渡す際のプロンプト形式でフォーマット
    """
    result = []
    result.append("=" * 80)
    result.append("画像から抽出したテキスト（表データ用）")
    result.append("=" * 80)
    result.append(f"\n画像ファイル: {image_path.name}\n")
    
    if structure_result and structure_result.get('structure_detected'):
        result.append("【表構造認識結果】")
        result.append("-" * 80)
        zenzenkai = structure_result.get('zenzenkai')
        column_data = structure_result.get('column_data', {})
        
        if zenzenkai is not None:
            result.append(f"前々回の値: {zenzenkai}")
        else:
            result.append("前々回の値: （検出できませんでした）")
        
        result.append("\n予測出目（列ごと）:")
        has_data = False
        for col in range(10):
            col_str = str(col)
            if column_data.get(col_str):
                result.append(f"  前回={col}: {column_data[col_str]}")
                has_data = True
        
        if not has_data:
            result.append("  （予測出目が見つかりませんでした）")
        
        result.append("")
    
    result.append("【OCR結果】")
    result.append("-" * 80)
    if ocr_text:
        result.append(ocr_text)
    else:
        result.append("（OCR結果が空です）")
    
    result.append("\n" + "=" * 80)
    return "\n".join(result)


def process_image(image_path: Path):
    """
    1つの画像ファイルを処理
    """
    print(f"\n{'='*80}")
    print(f"処理中: {image_path.name}")
    print(f"{'='*80}\n")
    
    # 表構造を活用したOCRを実行
    print("📷 OCR実行中（表構造認識モード）...")
    structure_result = extract_text_with_structure(image_path)
    
    # 従来のOCRも実行（フォールバック用）
    raw_ocr = extract_text_from_image(image_path)
    
    if structure_result.get('structure_detected'):
        print("✓ 表構造を検出しました")
        zenzenkai = structure_result.get('zenzenkai')
        if zenzenkai is not None:
            print(f"✓ 前々回の値: {zenzenkai}")
        
        column_data = structure_result.get('column_data', {})
        data_count = sum(len(column_data.get(str(i), [])) for i in range(10))
        print(f"✓ 予測出目データ: {data_count}個の数値候補を抽出")
    else:
        print("⚠ 表構造を検出できませんでした（従来のOCRを使用）")
    
    if raw_ocr:
        print(f"✓ OCR完了 ({len(raw_ocr)}文字)")
    else:
        print("⚠ OCR結果が空です")
    
    # 結果を表示
    print(f"\n{'='*80}")
    print("【抽出結果】")
    print(f"{'='*80}\n")
    
    if structure_result.get('structure_detected'):
        zenzenkai = structure_result.get('zenzenkai')
        column_data = structure_result.get('column_data', {})
        
        if zenzenkai is not None:
            print(f"前々回の値: {zenzenkai}")
        
        print("\n予測出目（列ごと）:")
        has_data = False
        for col in range(10):
            col_str = str(col)
            if column_data.get(col_str):
                print(f"  前回={col}: {column_data[col_str]}")
                has_data = True
        
        if not has_data:
            print("  （予測出目が見つかりませんでした）")
        
        print("\n【生のOCR結果】")
        print("-" * 80)
    
    if raw_ocr:
        print(raw_ocr)
    else:
        print("（OCR結果が空です）")
    
    # GPTなどに渡す形式で出力
    print("\n" + "=" * 80)
    print("【GPTなどに渡す際のプロンプト形式】")
    print("=" * 80)
    print(format_for_gpt(image_path, raw_ocr, structure_result))
    
    print("\n" + "=" * 80)
    print("✓ 処理完了")
    print("=" * 80)


def process_folder(folder_path: Path):
    """
    フォルダ内の全画像ファイルを処理
    """
    # 画像ファイルを探す
    image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff']
    image_files = []
    for ext in image_extensions:
        image_files.extend(folder_path.glob(f"*{ext}"))
        image_files.extend(folder_path.glob(f"*{ext.upper()}"))
    
    if not image_files:
        print(f"✗ 画像ファイルが見つかりません: {folder_path}")
        return
    
    print(f"📁 フォルダ: {folder_path}")
    print(f"画像ファイル数: {len(image_files)}\n")
    
    # 画像ファイルを処理
    for image_file in sorted(image_files):
        process_image(image_file)
    
    print(f"\n✓ 完了: {len(image_files)}枚の画像を処理しました")


def main():
    if len(sys.argv) < 2:
        print("使い方:")
        print("  python extract_text.py <画像ファイルパス>")
        print("  python extract_text.py <フォルダパス>")
        print("\n例:")
        print("  python extract_text.py ../docs/images/4-4-一の位/N4-一の位-0.png")
        print("  python extract_text.py ../docs/images/4-4-一の位/")
        sys.exit(1)
    
    target_path = Path(sys.argv[1])
    
    if not target_path.exists():
        print(f"✗ ファイル/フォルダが見つかりません: {target_path}")
        sys.exit(1)
    
    if target_path.is_file():
        # 単一ファイル
        suffix = target_path.suffix.lower()
        if suffix in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff']:
            process_image(target_path)
        else:
            print(f"✗ サポートされていないファイル形式: {suffix}")
            print("  画像ファイル（.png, .jpg, .jpeg等）のみ処理できます。")
            sys.exit(1)
    else:
        # フォルダ
        process_folder(target_path)


if __name__ == "__main__":
    main()
