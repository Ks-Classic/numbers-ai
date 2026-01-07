"""
極CUBE並び型判定スクリプトの単体テスト

各型の判定ロジックをテストし、定義書に記載されている全パターンが正しく判定されることを確認する。
"""

import sys
import unittest
import importlib.util
from pathlib import Path

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent

# パスを先に追加（pattern_classifier.pyがインポートする前に設定する必要がある）
# pattern_classifier.pyがインポートするモジュールのパスを設定
if str(PROJECT_ROOT / 'core') not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / 'core'))
if str(PROJECT_ROOT / 'scripts' / 'production') not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / 'scripts' / 'production'))
if str(Path(__file__).parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent))

# pattern_classifier.pyを動的にインポート（パスが設定された後）
# パスを設定してからモジュールを読み込む
pattern_classifier_path = Path(__file__).parent / "pattern_classifier.py"

# モジュールの読み込み前に、pattern_classifier.pyが使用するパスを確実に設定
# pattern_classifier.py内でパスを設定しているが、その前にインポートが実行される可能性があるため
# ここで再度パスを確認・設定
if str(PROJECT_ROOT / 'core') not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / 'core'))
if str(PROJECT_ROOT / 'scripts' / 'production') not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / 'scripts' / 'production'))

spec = importlib.util.spec_from_file_location("pattern_classifier", pattern_classifier_path)
pattern_classifier = importlib.util.module_from_spec(spec)

# モジュールを実行する前に、パスが設定されていることを確認
# pattern_classifier.py内でパスを設定しているが、念のためここでも設定
spec.loader.exec_module(pattern_classifier)

# 関数を取得
is_connected = pattern_classifier.is_connected
are_all_connected = pattern_classifier.are_all_connected
is_horizontal_straight = pattern_classifier.is_horizontal_straight
is_vertical_straight = pattern_classifier.is_vertical_straight
is_v_shape = pattern_classifier.is_v_shape
is_inverted_v_shape = pattern_classifier.is_inverted_v_shape
check_diagonal_patterns = pattern_classifier.check_diagonal_patterns
is_l_shape_bottom_left = pattern_classifier.is_l_shape_bottom_left
is_l_shape_bottom_right = pattern_classifier.is_l_shape_bottom_right
is_l_shape_top_left = pattern_classifier.is_l_shape_top_left
is_l_shape_top_right = pattern_classifier.is_l_shape_top_right
is_zigzag_right = pattern_classifier.is_zigzag_right
is_zigzag_left = pattern_classifier.is_zigzag_left
is_corner_horizontal_left_up = pattern_classifier.is_corner_horizontal_left_up
is_corner_horizontal_right_up = pattern_classifier.is_corner_horizontal_right_up
is_corner_horizontal_left_down = pattern_classifier.is_corner_horizontal_left_down
is_corner_horizontal_right_down = pattern_classifier.is_corner_horizontal_right_down
is_corner_vertical_left_up = pattern_classifier.is_corner_vertical_left_up
is_corner_vertical_right_up = pattern_classifier.is_corner_vertical_right_up
is_corner_vertical_left_down = pattern_classifier.is_corner_vertical_left_down
is_corner_vertical_right_down = pattern_classifier.is_corner_vertical_right_down
classify_pattern = pattern_classifier.classify_pattern


class TestConnectionFunctions(unittest.TestCase):
    """つながりの判定関数のテスト"""
    
    def test_is_connected_horizontal(self):
        """横方向のつながり"""
        self.assertTrue(is_connected((2, 2), (2, 3)))
        self.assertTrue(is_connected((2, 3), (2, 2)))
        self.assertFalse(is_connected((2, 2), (2, 4)))  # 1列を挟んでいる
    
    def test_is_connected_vertical(self):
        """縦方向のつながり"""
        self.assertTrue(is_connected((2, 3), (3, 3)))
        self.assertTrue(is_connected((3, 3), (4, 3)))
        self.assertFalse(is_connected((2, 3), (4, 3)))  # 3行目を飛ばしている
    
    def test_is_connected_diagonal(self):
        """斜め方向のつながり"""
        self.assertTrue(is_connected((2, 2), (3, 3)))  # 右下
        self.assertTrue(is_connected((2, 4), (3, 3)))  # 左下
        self.assertTrue(is_connected((3, 3), (4, 2)))  # 左上
        self.assertTrue(is_connected((3, 3), (4, 4)))  # 右下
        self.assertFalse(is_connected((2, 2), (4, 4)))  # 2列離れている
    
    def test_are_all_connected(self):
        """3つの位置がすべてつながっているか"""
        # 連結しているケース
        self.assertTrue(are_all_connected([(2, 2), (2, 3), (2, 4)]))  # 横一文字
        self.assertTrue(are_all_connected([(2, 3), (3, 3), (4, 3)]))  # 縦一文字
        self.assertTrue(are_all_connected([(2, 2), (3, 3), (4, 4)]))  # 斜め
        
        # 連結していないケース（孤立した位置がある）
        self.assertFalse(are_all_connected([(2, 2), (2, 3), (4, 4)]))  # 4,4が孤立


class TestBasicPatterns(unittest.TestCase):
    """基本型（横一文字型、縦一文字型、V字型、逆V字型）のテスト"""
    
    def test_horizontal_straight(self):
        """横一文字型のテスト"""
        # 2行目のパターン
        self.assertTrue(is_horizontal_straight([(2, 1), (2, 2), (2, 3)]))
        self.assertTrue(is_horizontal_straight([(2, 2), (2, 3), (2, 4)]))
        self.assertTrue(is_horizontal_straight([(2, 6), (2, 7), (2, 8)]))
        
        # 3行目のパターン
        self.assertTrue(is_horizontal_straight([(3, 1), (3, 2), (3, 3)]))
        
        # 4行目のパターン
        self.assertTrue(is_horizontal_straight([(4, 1), (4, 2), (4, 3)]))
        
        # 連続していないケース
        self.assertFalse(is_horizontal_straight([(2, 1), (2, 2), (2, 4)]))  # 1列を挟んでいる
        self.assertFalse(is_horizontal_straight([(2, 1), (3, 2), (2, 3)]))  # 異なる行
    
    def test_vertical_straight(self):
        """縦一文字型のテスト"""
        # 各列のパターン
        for col in range(1, 9):
            self.assertTrue(is_vertical_straight([(2, col), (3, col), (4, col)]))
        
        # 連続していないケース
        self.assertFalse(is_vertical_straight([(2, 3), (3, 3), (5, 3)]))  # 4行目を飛ばしている
        self.assertFalse(is_vertical_straight([(2, 2), (2, 3), (4, 2)]))  # 異なる列
    
    def test_v_shape(self):
        """V字型のテスト"""
        # パターン1: 2行目2列(A) - 3行目3列(B) - 2行目4列(C)
        self.assertTrue(is_v_shape([(2, 2), (3, 3), (2, 4)]))
        
        # パターン2: 2行目2列(A) - 3行目3列(B) - 2行目6列(C)
        self.assertTrue(is_v_shape([(2, 2), (3, 3), (2, 6)]))
        
        # パターン7: 3行目2列(A) - 4行目3列(B) - 3行目4列(C)
        self.assertTrue(is_v_shape([(3, 2), (4, 3), (3, 4)]))
        
        # V字型ではないケース
        self.assertFalse(is_v_shape([(2, 2), (3, 3), (2, 3)]))  # 列の差が1
    
    def test_inverted_v_shape(self):
        """逆V字型のテスト"""
        # パターン1: 3行目1列(A) - 2行目2列(B) - 3行目3列(C)
        self.assertTrue(is_inverted_v_shape([(3, 1), (2, 2), (3, 3)]))
        
        # パターン2: 3行目2列(A) - 2行目3列(B) - 3行目4列(C)
        self.assertTrue(is_inverted_v_shape([(3, 2), (2, 3), (3, 4)]))
        
        # パターン7: 4行目1列(A) - 3行目2列(B) - 4行目3列(C)
        self.assertTrue(is_inverted_v_shape([(4, 1), (3, 2), (4, 3)]))
        
        # 逆V字型ではないケース
        self.assertFalse(is_inverted_v_shape([(2, 2), (3, 3), (2, 4)]))  # V字型


class TestDiagonalPatterns(unittest.TestCase):
    """斜め型（4種類）のテスト"""
    
    def test_diagonal_bottom_right(self):
        """斜め右下型のテスト"""
        # パターン1: 2行目1列、3行目2列、4行目3列
        result = check_diagonal_patterns([(2, 1), (3, 2), (4, 3)])
        self.assertEqual(result, "斜め右下型")
        
        # パターン6: 2行目6列、3行目7列、4行目8列
        result = check_diagonal_patterns([(2, 6), (3, 7), (4, 8)])
        self.assertEqual(result, "斜め右下型")
    
    def test_diagonal_bottom_left(self):
        """斜め左下型のテスト"""
        # パターン1: 2行目3列、3行目2列、4行目1列
        result = check_diagonal_patterns([(2, 3), (3, 2), (4, 1)])
        self.assertEqual(result, "斜め左下型")
        
        # パターン6: 2行目8列、3行目7列、4行目6列
        result = check_diagonal_patterns([(2, 8), (3, 7), (4, 6)])
        self.assertEqual(result, "斜め左下型")
    
    def test_diagonal_top_right(self):
        """斜め右上型のテスト"""
        # パターン1: 4行目1列、3行目2列、2行目3列
        result = check_diagonal_patterns([(4, 1), (3, 2), (2, 3)])
        self.assertEqual(result, "斜め右上型")
        
        # パターン6: 4行目6列、3行目7列、2行目8列
        result = check_diagonal_patterns([(4, 6), (3, 7), (2, 8)])
        self.assertEqual(result, "斜め右上型")
    
    def test_diagonal_top_left(self):
        """斜め左上型のテスト"""
        # パターン1: 4行目3列、3行目2列、2行目1列
        result = check_diagonal_patterns([(4, 3), (3, 2), (2, 1)])
        self.assertEqual(result, "斜め左上型")
        
        # パターン6: 4行目8列、3行目7列、2行目6列
        result = check_diagonal_patterns([(4, 8), (3, 7), (2, 6)])
        self.assertEqual(result, "斜め左上型")


class TestLShapePatterns(unittest.TestCase):
    """L字型（4種類）のテスト"""
    
    def test_l_shape_bottom_left(self):
        """└字型（左下L字）のテスト"""
        # パターン1: 2行目1列、3行目1列・2列（角: 3行目1列）
        self.assertTrue(is_l_shape_bottom_left([(2, 1), (3, 1), (3, 2)]))
        
        # パターン7: 3行目1列、4行目1列・2列（角: 4行目1列）
        self.assertTrue(is_l_shape_bottom_left([(3, 1), (4, 1), (4, 2)]))
    
    def test_l_shape_bottom_right(self):
        """┘字型（右下L字）のテスト"""
        # パターン1: 2行目2列、3行目1列・2列（角: 3行目2列）
        self.assertTrue(is_l_shape_bottom_right([(2, 2), (3, 1), (3, 2)]))
        
        # パターン7: 3行目2列、4行目1列・2列（角: 4行目2列）
        self.assertTrue(is_l_shape_bottom_right([(3, 2), (4, 1), (4, 2)]))
    
    def test_l_shape_top_left(self):
        """┌字型（左上L字）のテスト"""
        # パターン1: 2行目1列・2列、3行目1列（角: 2行目1列）
        self.assertTrue(is_l_shape_top_left([(2, 1), (2, 2), (3, 1)]))
        
        # パターン7: 3行目1列・2列、4行目1列（角: 3行目1列）
        self.assertTrue(is_l_shape_top_left([(3, 1), (3, 2), (4, 1)]))
    
    def test_l_shape_top_right(self):
        """┐字型（右上L字）のテスト"""
        # パターン1: 2行目1列・2列、3行目2列（角: 2行目2列）
        self.assertTrue(is_l_shape_top_right([(2, 1), (2, 2), (3, 2)]))
        
        # パターン7: 3行目1列・2列、4行目2列（角: 3行目2列）
        self.assertTrue(is_l_shape_top_right([(3, 1), (3, 2), (4, 2)]))


class TestZigzagPatterns(unittest.TestCase):
    """ジグザグ型（2種類）のテスト"""
    
    def test_zigzag_right(self):
        """ジグザグ型（右斜め）のテスト"""
        # パターン1: 2行目1列 → 3行目2列 → 4行目1列
        self.assertTrue(is_zigzag_right([(2, 1), (3, 2), (4, 1)]))
        
        # パターン7: 2行目7列 → 3行目8列 → 4行目7列
        self.assertTrue(is_zigzag_right([(2, 7), (3, 8), (4, 7)]))
    
    def test_zigzag_left(self):
        """ジグザグ型（左斜め）のテスト"""
        # パターン1: 2行目2列 → 3行目1列 → 4行目2列
        self.assertTrue(is_zigzag_left([(2, 2), (3, 1), (4, 2)]))
        
        # パターン7: 2行目8列 → 3行目7列 → 4行目8列
        self.assertTrue(is_zigzag_left([(2, 8), (3, 7), (4, 8)]))


class TestCornerPatterns(unittest.TestCase):
    """コーナー型（8種類）のテスト"""
    
    def test_corner_horizontal_left_up(self):
        """コーナー型（横長・左斜め上）のテスト"""
        # パターン1: 2行目1列 → 3行目2列、3行目3列
        self.assertTrue(is_corner_horizontal_left_up([(2, 1), (3, 2), (3, 3)]))
        
        # パターン7: 3行目1列 → 4行目2列、4行目3列
        self.assertTrue(is_corner_horizontal_left_up([(3, 1), (4, 2), (4, 3)]))
    
    def test_corner_horizontal_right_up(self):
        """コーナー型（横長・右斜め上）のテスト"""
        # パターン1: 3行目1列・2列 → 2行目3列
        self.assertTrue(is_corner_horizontal_right_up([(3, 1), (3, 2), (2, 3)]))
        
        # パターン7: 4行目1列・2列 → 3行目3列
        self.assertTrue(is_corner_horizontal_right_up([(4, 1), (4, 2), (3, 3)]))
    
    def test_corner_horizontal_left_down(self):
        """コーナー型（横長・左斜め下）のテスト"""
        # パターン1: 3行目1列 → 2行目2列、2行目3列
        self.assertTrue(is_corner_horizontal_left_down([(3, 1), (2, 2), (2, 3)]))
        
        # パターン7: 4行目1列 → 3行目2列、3行目3列
        self.assertTrue(is_corner_horizontal_left_down([(4, 1), (3, 2), (3, 3)]))
    
    def test_corner_horizontal_right_down(self):
        """コーナー型（横長・右斜め下）のテスト"""
        # パターン1: 2行目1列・2列 → 3行目3列
        self.assertTrue(is_corner_horizontal_right_down([(2, 1), (2, 2), (3, 3)]))
        
        # パターン7: 3行目1列・2列 → 4行目3列
        self.assertTrue(is_corner_horizontal_right_down([(3, 1), (3, 2), (4, 3)]))
    
    def test_corner_vertical_left_up(self):
        """コーナー型（縦長・左斜め上）のテスト"""
        # パターン1: 2行目1列 → 3行目2列 → 4行目2列
        self.assertTrue(is_corner_vertical_left_up([(2, 1), (3, 2), (4, 2)]))
        
        # パターン7: 2行目7列 → 3行目8列 → 4行目8列
        self.assertTrue(is_corner_vertical_left_up([(2, 7), (3, 8), (4, 8)]))
    
    def test_corner_vertical_right_up(self):
        """コーナー型（縦長・右斜め上）のテスト"""
        # パターン1: 2行目2列 → 3行目1列 → 4行目1列
        self.assertTrue(is_corner_vertical_right_up([(2, 2), (3, 1), (4, 1)]))
        
        # パターン7: 2行目8列 → 3行目7列 → 4行目7列
        self.assertTrue(is_corner_vertical_right_up([(2, 8), (3, 7), (4, 7)]))
    
    def test_corner_vertical_left_down(self):
        """コーナー型（縦長・左斜め下）のテスト"""
        # パターン1: 2行目2列 → 3行目2列 → 4行目1列
        self.assertTrue(is_corner_vertical_left_down([(2, 2), (3, 2), (4, 1)]))
        
        # パターン7: 2行目8列 → 3行目8列 → 4行目7列
        self.assertTrue(is_corner_vertical_left_down([(2, 8), (3, 8), (4, 7)]))
    
    def test_corner_vertical_right_down(self):
        """コーナー型（縦長・右斜め下）のテスト"""
        # パターン1: 2行目1列 → 3行目1列 → 4行目2列
        self.assertTrue(is_corner_vertical_right_down([(2, 1), (3, 1), (4, 2)]))
        
        # パターン7: 2行目7列 → 3行目7列 → 4行目8列
        self.assertTrue(is_corner_vertical_right_down([(2, 7), (3, 7), (4, 8)]))


class TestClassifyPattern(unittest.TestCase):
    """classify_pattern関数の統合テスト"""
    
    def test_classify_all_patterns(self):
        """全22種類の型が正しく判定されることを確認"""
        test_cases = [
            # 基本型
            ([(2, 1), (2, 2), (2, 3)], "横一文字型"),
            ([(2, 3), (3, 3), (4, 3)], "縦一文字型"),
            ([(2, 2), (3, 3), (2, 4)], "V字型"),
            ([(3, 2), (2, 3), (3, 4)], "逆V字型"),
            
            # 斜め型
            ([(2, 1), (3, 2), (4, 3)], "斜め右下型"),
            ([(2, 3), (3, 2), (4, 1)], "斜め左下型"),
            ([(4, 1), (3, 2), (2, 3)], "斜め右上型"),
            ([(4, 3), (3, 2), (2, 1)], "斜め左上型"),
            
            # L字型
            ([(2, 1), (3, 1), (3, 2)], "└字型（左下L字）"),
            ([(2, 2), (3, 1), (3, 2)], "┘字型（右下L字）"),
            ([(2, 1), (2, 2), (3, 1)], "┌字型（左上L字）"),
            ([(2, 1), (2, 2), (3, 2)], "┐字型（右上L字）"),
            
            # ジグザグ型
            ([(2, 1), (3, 2), (4, 1)], "ジグザグ型（右斜め）"),
            ([(2, 2), (3, 1), (4, 2)], "ジグザグ型（左斜め）"),
            
            # コーナー型（横長）
            ([(2, 1), (3, 2), (3, 3)], "コーナー型（横長・左斜め上）"),
            ([(3, 1), (3, 2), (2, 3)], "コーナー型（横長・右斜め上）"),
            ([(3, 1), (2, 2), (2, 3)], "コーナー型（横長・左斜め下）"),
            ([(2, 1), (2, 2), (3, 3)], "コーナー型（横長・右斜め下）"),
            
            # コーナー型（縦長）
            ([(2, 1), (3, 2), (4, 2)], "コーナー型（縦長・左斜め上）"),
            ([(2, 2), (3, 1), (4, 1)], "コーナー型（縦長・右斜め上）"),
            ([(2, 2), (3, 2), (4, 1)], "コーナー型（縦長・左斜め下）"),
            ([(2, 1), (3, 1), (4, 2)], "コーナー型（縦長・右斜め下）"),
        ]
        
        for positions, expected_pattern in test_cases:
            with self.subTest(positions=positions, expected=expected_pattern):
                result = classify_pattern(positions)
                self.assertEqual(result, expected_pattern, 
                               f"位置 {positions} は {expected_pattern} と判定されるべきですが、{result} と判定されました")


if __name__ == '__main__':
    # unittest.main()を実行
    # プロジェクトルートから実行する場合:
    # python -m unittest scripts.base_statistics.02_extreme_cube.02-02_並び型分析.test_pattern_classifier -v
    # または、このファイルを直接実行:
    # python test_pattern_classifier.py
    unittest.main(verbosity=2)

