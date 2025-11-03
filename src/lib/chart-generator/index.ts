/**
 * 予測表生成アルゴリズム
 * 
 * 中国罫線理論に基づく予測表を生成する。
 * 仕様は docs/元ネタ/表作成ルール.,md を参照。
 */

import type { Target, Pattern } from '@/types/prediction';
import type { ChartData, ChartGrid, MainRow } from '@/types/chart';
import { ChartGenerationError } from '@/types/chart';
import { 
  getPreviousResult, 
  getPreviousPreviousResult,
  getPredictedDigits,
  type ColumnName,
  DataLoadError 
} from '@/lib/data-loader';

/**
 * 予測表を生成する
 * 
 * @param roundNumber 回号
 * @param pattern パターン（'A' = 0なし、'B' = 0あり）
 * @param target 対象（'n3' または 'n4'）
 * @returns 予測表データ
 * @throws ChartGenerationError 生成エラー
 */
export async function generateChart(
  roundNumber: number,
  pattern: Pattern,
  target: Target
): Promise<ChartData> {
  try {
    // ステップ1: 予測出目の抽出
    const sourceList = await extractPredictedDigits(roundNumber, target);
    
    // ステップ2: パターン別の元数字リスト作成
    const nums = applyPatternExpansion(sourceList, pattern);
    
    // ステップ3: メイン行の組み立て
    const mainRows = buildMainRows(nums);
    
    // ステップ4: グリッド初期配置
    const rows = mainRows.length * 2;
    const cols = 8;
    const grid = initializeGrid(rows, cols, mainRows);
    
    // ステップ5: パターンB中心0配置
    if (pattern === 'B') {
      placeCenterZero(grid, rows, cols);
    }
    
    // ステップ6-8: 裏数字・余りマスルール
    applyVerticalInverse(grid, rows, cols);
    applyHorizontalInverse(grid, rows, cols);
    applyRemainingCopy(grid, rows, cols);
    
    return {
      grid,
      rows,
      cols,
      pattern,
      target,
      sourceDigits: sourceList
    };
  } catch (error) {
    if (error instanceof ChartGenerationError) {
      throw error;
    }
    
    if (error instanceof DataLoadError) {
      throw new ChartGenerationError(
        `データ読み込みエラー: ${error.message}`,
        error
      );
    }
    
    throw new ChartGenerationError(
      `予測表生成エラー: ${(error as Error).message}`,
      error
    );
  }
}

/**
 * 予測出目を抽出する
 * 
 * 前回（round_number-1）と前々回（round_number-2）の当選番号から、
 * keisen_master.jsonを参照して各桁の予測出目を取得し、結合する。
 * 
 * @param roundNumber 回号
 * @param target 対象（'n3' または 'n4'）
 * @returns 予測出目の配列（source_list）
 */
async function extractPredictedDigits(
  roundNumber: number,
  target: Target
): Promise<number[]> {
  // 前回と前々回のデータを取得
  const previousResult = await getPreviousResult(roundNumber);
  const previousPreviousResult = await getPreviousPreviousResult(roundNumber);
  
  if (!previousResult) {
    throw new ChartGenerationError(
      `前回の当選番号が見つかりません（回号: ${roundNumber - 1}）`
    );
  }
  
  if (!previousPreviousResult) {
    throw new ChartGenerationError(
      `前々回の当選番号が見つかりません（回号: ${roundNumber - 2}）`
    );
  }
  
  // 対象に応じた桁名と当選番号を取得
  const columnNames: ColumnName[] = target === 'n3' 
    ? ['百の位', '十の位', '一の位']
    : ['千の位', '百の位', '十の位', '一の位'];
  
  const previousWinning = target === 'n3' 
    ? previousResult.n3Winning 
    : previousResult.n4Winning;
  
  const previousPreviousWinning = target === 'n3'
    ? previousPreviousResult.n3Winning
    : previousPreviousResult.n4Winning;
  
  // 各桁の予測出目を取得して結合
  const sourceList: number[] = [];
  
  for (const columnName of columnNames) {
    // 前回・前々回の該当桁の数字を取得
    const digitIndex = columnNames.indexOf(columnName);
    const previousDigit = parseInt(previousWinning[digitIndex], 10);
    const previousPreviousDigit = parseInt(previousPreviousWinning[digitIndex], 10);
    
    // 予測出目を取得
    const predictedDigits = await getPredictedDigits(
      target,
      columnName,
      previousDigit,
      previousPreviousDigit
    );
    
    // source_listに追加
    sourceList.push(...predictedDigits);
  }
  
  // 昇順ソート
  sourceList.sort((a, b) => a - b);
  
  return sourceList;
}

/**
 * パターン別の元数字リストを作成する
 * 
 * @param sourceList 予測出目の配列
 * @param pattern パターン（'A' = 0なし、'B' = 0あり）
 * @returns 拡張後の元数字リスト
 */
function applyPatternExpansion(
  sourceList: number[],
  pattern: Pattern
): number[] {
  const nums = [...sourceList];
  
  if (pattern === 'A') {
    // パターンA（0なし）: 0〜9の欠番をすべて追加
    for (let digit = 0; digit <= 9; digit++) {
      if (!nums.includes(digit)) {
        nums.push(digit);
      }
    }
  } else {
    // パターンB（0あり）: 0が含まれていなければ0を1つ追加
    if (!nums.includes(0)) {
      nums.push(0);
    }
  }
  
  // 昇順ソート（重複は許容）
  nums.sort((a, b) => a - b);
  
  return nums;
}

/**
 * メイン行を組み立てる
 * 
 * 仕様: docs/元ネタ/表作成ルール.,md の「4. メイン行の組み立て（vFinal 3.0）」
 * 
 * @param nums 元数字リスト
 * @returns メイン行の配列
 */
function buildMainRows(nums: number[]): MainRow[] {
  const mainRows: MainRow[] = [];
  let tempList = [...nums];
  let rowIndex = 0;
  
  while (tempList.length > 0) {
    // ユニーク値を昇順で取得
    const uniqueDigits = [...new Set(tempList)].sort((a, b) => a - b);
    
    if (uniqueDigits.length >= 4) {
      // 4種類以上の場合: 最初の4種類を構成メンバーとして使用
      const members = uniqueDigits.slice(0, 4);
      const newRow: [number, number, number, number] = [0, 0, 0, 0];
      
      // tempListから順に取り出してnewRowに格納
      for (let i = 0; i < 4; i++) {
        const idx = tempList.indexOf(members[i]);
        if (idx === -1) {
          throw new ChartGenerationError(
            `メイン行組み立てエラー: 数字${members[i]}が見つかりません`
          );
        }
        newRow[i] = tempList[idx];
        tempList.splice(idx, 1);
      }
      
      mainRows.push({ elements: newRow, rowIndex: rowIndex++ });
    } else {
      // 4種類未満の場合: ユニーク値をベースに最大値を繰り返し追加
      const maxValue = Math.max(...uniqueDigits);
      const newRow: [number, number, number, number] = [
        ...uniqueDigits,
        ...Array(4 - uniqueDigits.length).fill(maxValue)
      ] as [number, number, number, number];
      
      // tempListから使用した数字を削除
      // 各数字を1個ずつ削除（重複を考慮）
      for (const digit of newRow) {
        const idx = tempList.indexOf(digit);
        if (idx !== -1) {
          tempList.splice(idx, 1);
        }
      }
      
      mainRows.push({ elements: newRow, rowIndex: rowIndex++ });
    }
  }
  
  if (mainRows.length === 0) {
    throw new ChartGenerationError('メイン行が1本も生成されませんでした');
  }
  
  return mainRows;
}

/**
 * グリッドを初期化し、メイン行を配置する
 * 
 * @param rows 行数
 * @param cols 列数（常に8）
 * @param mainRows メイン行の配列
 * @returns 初期化されたグリッド
 */
function initializeGrid(
  rows: number,
  cols: number,
  mainRows: MainRow[]
): ChartGrid {
  // 2次元配列を初期化（初期値null）
  const grid: ChartGrid = Array(rows)
    .fill(null)
    .map(() => Array(cols).fill(null));
  
  // メイン行を配置（行・列ともに偶数インデックス）
  for (let i = 0; i < mainRows.length; i++) {
    const rowIndex = i * 2;
    const mainRow = mainRows[i];
    
    for (let j = 0; j < 4; j++) {
      const colIndex = j * 2;
      grid[rowIndex][colIndex] = mainRow.elements[j];
    }
  }
  
  return grid;
}

/**
 * パターンBの中心0配置
 * 
 * 中心マス群を (row昇順, col昇順) で走査し、
 * 最初に見つかる空白マスに0を1つ配置する。
 * 
 * @param grid グリッド
 * @param rows 行数
 * @param cols 列数
 */
function placeCenterZero(grid: ChartGrid, rows: number, cols: number): void {
  const centerRows = [
    Math.floor((rows - 1) / 2),
    Math.ceil((rows - 1) / 2)
  ];
  const centerCols = [
    Math.floor((cols - 1) / 2),
    Math.ceil((cols - 1) / 2)
  ];
  
  // 中心マス群を走査
  for (const r of centerRows) {
    for (const c of centerCols) {
      if (grid[r][c] === null) {
        grid[r][c] = 0;
        return; // 1つ配置したら終了
      }
    }
  }
}

/**
 * 裏数字を計算する
 * 
 * @param n 数字（0-9）
 * @returns 裏数字（(n + 5) % 10）
 */
function inverse(n: number): number {
  return (n + 5) % 10;
}

/**
 * 裏数字ルール（縦パス）を適用する
 * 
 * 上から下へ順に処理し、nullかつ上に値がある場合に裏数字を配置する。
 * 更新がなくなるまで繰り返す。
 * 
 * @param grid グリッド
 * @param rows 行数
 * @param cols 列数
 */
function applyVerticalInverse(grid: ChartGrid, rows: number, cols: number): void {
  let updated = true;
  
  while (updated) {
    updated = false;
    
    for (let y = 0; y < rows; y++) {
      for (let x = 0; x < cols; x++) {
        if (grid[y][x] === null && y > 0 && grid[y - 1][x] !== null) {
          grid[y][x] = inverse(grid[y - 1][x]!);
          updated = true;
        }
      }
    }
  }
}

/**
 * 裏数字ルール（横パス）を適用する
 * 
 * 左から右へ順に処理し、nullかつ左に値がある場合に裏数字を配置する。
 * 更新がなくなるまで繰り返す。
 * 
 * @param grid グリッド
 * @param rows 行数
 * @param cols 列数
 */
function applyHorizontalInverse(grid: ChartGrid, rows: number, cols: number): void {
  let updated = true;
  
  while (updated) {
    updated = false;
    
    for (let y = 0; y < rows; y++) {
      for (let x = 0; x < cols; x++) {
        if (grid[y][x] === null && x > 0 && grid[y][x - 1] !== null) {
          grid[y][x] = inverse(grid[y][x - 1]!);
          updated = true;
        }
      }
    }
  }
}

/**
 * 余りマスルールを適用する
 * 
 * nullかつ上に値がある場合に、上から値をコピーする。
 * 更新がなくなるまで繰り返す。
 * 
 * @param grid グリッド
 * @param rows 行数
 * @param cols 列数
 */
function applyRemainingCopy(grid: ChartGrid, rows: number, cols: number): void {
  let updated = true;
  
  while (updated) {
    updated = false;
    
    for (let y = 0; y < rows; y++) {
      for (let x = 0; x < cols; x++) {
        if (grid[y][x] === null && y > 0 && grid[y - 1][x] !== null) {
          grid[y][x] = grid[y - 1][x];
          updated = true;
        }
      }
    }
  }
}

