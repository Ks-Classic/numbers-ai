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
 * @param pattern パターン（'A1' | 'A2' | 'B1' | 'B2'）
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
    // メイン行数に応じて、必要な行数を計算
    // メイン行は奇数行（1, 3, 5, 7行目）に配置し、
    // その下の偶数行（2, 4, 6, 8行目）に裏数字を配置
    // したがって、メイン行がN本の場合：
    //   - 最後のメイン行は行(2*N-1)に配置される
    //   - その下の行(2*N)に裏数字を配置する必要がある
    //   - つまり、行数は 2*N（メイン行1本→2行、2本→4行、3本→6行、4本→8行）
    // 注意: 実装・表示・配列すべて1-indexedで統一（配列のインデックス1から使用、grid[0]は未使用）
    // 例: メイン行3本の場合、最後のメイン行は行5、その下の行6に裏数字
    let rows = mainRows.length * 2; // メイン行N本の場合、2*N行必要
    const cols = 8;
    let grid = initializeGrid(rows, cols, mainRows);
    
    // ステップ5: メイン行配置後の余りマスルール（裏数字適用前）
    // 奇数行の奇数列・偶数列の空マスに対して、
    // その上のメイン行（奇数行）の同じ列の数字をコピー
    applyMainRowRemainingCopy(grid, rows, cols);
    
    // ステップ5.5: パターンA2/B2中心0配置
    // メイン行配置後の余りマスルールの後に実行することで、
    // 余りマスルールで補完された数字が中心0配置で上書きされないようにする
    let centerZeroPos: [number, number] | null = null;
    let centerZeroPlaced = false;
    if (pattern === ('A2' as Pattern) || pattern === ('B2' as Pattern)) {
      centerZeroPos = placeCenterZero(grid, rows, cols);
      centerZeroPlaced = centerZeroPos !== null;
    }
    
    // ステップ6-7: 裏数字ルール
    // ステップ6: 縦パス（上から下へ裏数字を配置）
    applyVerticalInverse(grid, rows, cols, centerZeroPos);
    // ステップ7: 横パス（左から右へ裏数字を配置）
    applyHorizontalInverse(grid, rows, cols);
    
    // ステップ8: 8行を超える場合は9行以降を削除して8行にする
    if (rows > 8 && cols === 8) {
      // 9行目以降を削除（grid[0]は未使用、grid[1]からgrid[8]までを保持）
      grid = grid.slice(0, 9); // grid[0]からgrid[8]まで（1-8行目）
      rows = 8;
    }
    
    // ステップ9: 8列×8行の場合の最終調整（0配置パターンのみ）
    if (rows === 8 && cols === 8 && (pattern === 'A2' || pattern === 'B2')) {
      // 5列5行目を0に強制置き換え
      grid[5][5] = 0;
      // 5列4行目を5に強制置き換え
      grid[4][5] = 5;
    }
    
    return {
      grid,
      rows,
      cols,
      pattern,
      target,
      sourceDigits: sourceList,
      expandedDigits: nums, // 拡張後の数字（欠番補足後）
      centerZeroPlaced
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
  
  // ソートしない（桁順を保持：百の位→十の位→一の位の順）
  
  return sourceList;
}

/**
 * パターン別の元数字リストを作成する
 * 
 * @param sourceList 予測出目の配列
 * @param pattern パターン（'A1' | 'A2' | 'B1' | 'B2'）
 * @returns 拡張後の元数字リスト
 */
function applyPatternExpansion(
  sourceList: number[],
  pattern: Pattern
): number[] {
  const nums = [...sourceList];
  
  // A1/A2: 欠番補足あり（0〜9全追加）
  // B1/B2: 欠番補足なし（0も含めて、すべて欠番補足しない）
  if (pattern === ('A1' as Pattern) || pattern === ('A2' as Pattern)) {
    // パターンA1/A2: 0〜9の欠番をすべて追加
    for (let digit = 0; digit <= 9; digit++) {
      if (!nums.includes(digit)) {
        nums.push(digit);
      }
    }
  }
  // B1/B2の場合は何も追加しない（sourceListをそのまま使用）
  
  // 昇順ソート（重複は許容）
  nums.sort((a, b) => a - b);
  
  return nums;
}

/**
 * メイン行を組み立てる
 * 
 * 仕様: 各メイン行に必ず4つまで数字を入れる
 * - 最後のメイン行以外は必ず4つ
 * - 最後のメイン行だけは残りの数字をすべて入れる（4つ未満でもOK）
 * - tempListは最小値順にソート済み（4桁単位で最小値から順に選択するため）
 * - 4桁単位で最小値から順に重複せずに選択（連続していなくても良い、例：0,1,2,5）
 * - 4桁埋めたら次の最小値から繰り返し
 * - 4桁埋まらなかったら、次の未消費の最小値から埋めていく
 * - tempListは事前に並べ替え済みなので、メイン行作成時は先頭から順に取るだけ
 * - 行をまたぐ連続は許容（前の行の最後と次の行の最初が同じでもOK）
 * - 元数字リストに存在する数分だけ使用可能（同じ数字が複数回出現する場合は、その分だけ使用）
 * 
 * @param nums 元数字リスト（ソート済み）
 * @returns メイン行の配列
 */
function buildMainRows(nums: number[]): MainRow[] {
  const mainRows: MainRow[] = [];
  // tempListを「4桁単位で最小値から順に重複せずに選択」のルールで並べ替え
  let tempList: number[] = [];
  let remaining = [...nums];
  
  // 4桁単位で処理
  while (remaining.length > 0) {
    const chunk: number[] = [];
    // 重複しない最小値から順に選ぶ
    const uniqueElements = [...new Set(remaining)].sort((a, b) => a - b);
    for (const digit of uniqueElements) {
      if (chunk.length < 4) {
        const index = remaining.indexOf(digit);
        if (index !== -1) {
          chunk.push(digit);
          remaining.splice(index, 1);
        }
      }
    }
    
    // 4桁に満たない場合、残りから最小値から順に埋める（重複してもOK）
    // 「最小値から順に」は0～9まで重複せずに順番に埋めていく（連続していなくてもOK）
    if (chunk.length < 4 && remaining.length > 0) {
      while (chunk.length < 4 && remaining.length > 0) {
        // chunkの最後の数字を取得（なければ-1）
        const lastDigit = chunk.length > 0 ? chunk[chunk.length - 1] : -1;
        // 最後の数字の次の最小値（0～9の順序で）を残りから選ぶ
        // 残りにlastDigitより大きい数字がある場合は、その中から最小値を選ぶ
        // 残りにlastDigitより大きい数字がない場合は、残りから最小値を選ぶ
        const candidates = remaining.filter(d => d > lastDigit);
        let nextDigit: number;
        if (candidates.length > 0) {
          nextDigit = Math.min(...candidates);
        } else {
          // lastDigitより大きい数字がない場合は、残りから最小値を選ぶ
          nextDigit = Math.min(...remaining);
        }
        const index = remaining.indexOf(nextDigit);
        chunk.push(nextDigit);
        remaining.splice(index, 1);
      }
    }
    
    tempList.push(...chunk);
  }
  
  let rowIndex = 0;
  
  // デバッグ出力（開発時のみ）
  // @ts-ignore - process is available in Node.js environment
  const DEBUG = typeof process !== 'undefined' && process.env?.DEBUG_CHART === 'true';
  if (DEBUG) {
    console.log('[buildMainRows] 開始: nums =', nums);
    console.log('[buildMainRows] 初期 tempList =', tempList);
  }
  
  while (tempList.length > 0) {
    let newRow: number[] = [];
    
    // 最後のメイン行かどうかを判定（残りの数字が4つ以下なら最後の行）
    const isLastRow = tempList.length <= 4;
    const targetCount = isLastRow ? tempList.length : 4;
    
    // tempListは最小値順にソート済み
    // 4桁単位で最小値から順に重複せずに選択（連続していなくても良い、例：0,1,2,5）
    // 4桁埋めたら次の最小値から繰り返し
    // 4桁埋まらなかったら、次の未消費の最小値から埋めていく
    // tempListは事前に並べ替え済みなので、先頭から順に取るだけ
    
    if (DEBUG) {
      console.log(`[buildMainRows] 行${rowIndex}: tempList =`, tempList);
      console.log(`[buildMainRows] 行${rowIndex}: isLastRow =`, isLastRow);
      console.log(`[buildMainRows] 行${rowIndex}: targetCount =`, targetCount);
    }
    
    // tempListの先頭から順に取るだけ（既にソート済み）
    newRow = tempList.splice(0, targetCount);
    
    if (DEBUG) {
      console.log(`[buildMainRows] 行${rowIndex}: newRow =`, newRow);
      console.log(`[buildMainRows] 行${rowIndex}: 残りのtempList =`, tempList);
    }
    
    mainRows.push({ elements: newRow, rowIndex: rowIndex++ });
  }
  
  if (mainRows.length === 0) {
    throw new ChartGenerationError('メイン行が1本も生成されませんでした');
  }
  
  return mainRows;
}

/**
 * グリッドを初期化し、メイン行を配置する
 * 
 * メイン行は奇数行（1, 3, 5, 7行目）に配置する。
 * 列は奇数列（1, 3, 5, 7列目）に配置する。
 * 実装・表示・配列すべて1-indexedで統一（配列のインデックス1から使用、grid[0]は未使用）。
 * 
 * @param rows 行数（1-indexedでの行数）
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
  // 実装・表示・配列すべて1-indexedで統一（配列のインデックス1から使用、grid[0]は未使用）
  // メイン行がN本の場合、rows = 2*N（メイン行1本→2行、2本→4行、3本→6行、4本→8行）
  // 配列のサイズは rows + 1（grid[0]は未使用、grid[1]からgrid[rows]を使用）
  // これにより、最後のメイン行の下に必ず裏数字を配置する行が存在する
  // 例: メイン行3本の場合、行5にメイン行が配置され、行6に裏数字を配置する必要がある
  const grid: ChartGrid = Array(rows + 1)
    .fill(null)
    .map(() => Array(cols + 1).fill(null)); // 列も1-indexedに統一（col[0]は未使用）
  
  // メイン行を配置（奇数行の奇数列に配置: 1, 3, 5, 7行目の1, 3, 5, 7列目）
  // @ts-ignore - process is available in Node.js environment
  const DEBUG = typeof process !== 'undefined' && process.env?.DEBUG_CHART === 'true';
  
  if (DEBUG) {
    console.log('\n[initializeGrid] メイン行配置開始');
    console.log(`メイン行数: ${mainRows.length}`);
    for (let i = 0; i < mainRows.length; i++) {
      console.log(`  メイン行${i}: elements = [${mainRows[i].elements.join(', ')}]`);
    }
  }
  
  for (let i = 0; i < mainRows.length; i++) {
    const rowNum = i * 2 + 1; // 奇数行（1, 3, 5, 7行目）
    const mainRow = mainRows[i];
    
    // 最後のメイン行の下に必ず裏数字を配置する行が存在することを確認
    // メイン行が行(2*i+1)に配置される場合、その下の行(2*i+2)が必要
    // rows = 2*Nなので、最後のメイン行は行(2*N-1)に配置され、その下の行(2*N)が存在する
    if (rowNum + 1 > rows) {
      throw new ChartGenerationError(
        `メイン行配置エラー: 行${rowNum}にメイン行を配置するためには、行${rowNum + 1}が必要です（現在の行数: ${rows}行）`
      );
    }
    
    if (DEBUG) {
      console.log(`  行${rowNum}に配置: elements = [${mainRow.elements.join(', ')}]（要素数: ${mainRow.elements.length}）`);
    }
    
    // メイン行の要素数分だけ配置（最大4要素）
    for (let j = 0; j < mainRow.elements.length && j < 4; j++) {
      const colNum = j * 2 + 1; // 奇数列（1, 3, 5, 7列目）
      grid[rowNum][colNum] = mainRow.elements[j];
      if (DEBUG) {
        console.log(`    列${colNum}に${mainRow.elements[j]}を配置`);
      }
    }
  }
  
  return grid;
}

/**
 * パターンA2/B2の中心0配置
 * 
 * 行数に応じて対角線上に0を配置する。
 * 
 * - 6行: 4行5列目
 * - 8行: 5行5列目
 * - 10行: 6行6列目
 * - 12行: 7行7列目
 * 
 * 実装・表示・配列すべて1-indexedで統一（配列のインデックス1から使用）。
 * 
 * @param grid グリッド
 * @param rows 行数（1-indexedでの行数）
 * @param cols 列数（1-indexedでの列数、常に8）
 * @returns 0が配置された位置 [row, col]、配置されなかった場合はnull
 */
function placeCenterZero(grid: ChartGrid, rows: number, cols: number): [number, number] | null {
  // 行数に応じて対角線上の位置を決定
  let centerRow: number;
  let centerCol: number;
  
  if (rows === 6) {
    centerRow = 4;
    centerCol = 5;
  } else if (rows === 8) {
    centerRow = 5;
    centerCol = 5;
  } else if (rows === 10) {
    centerRow = 6;
    centerCol = 6;
  } else if (rows === 12) {
    centerRow = 7;
    centerCol = 7;
  } else {
    // その他の行数の場合は従来のロジック（後方互換性のため）
    if (rows >= 10) {
      centerRow = 6;
    } else if (rows >= 4) {
      centerRow = 4;
    } else {
      centerRow = rows;
    }
    
    // 中心列を計算（1-indexed）
    const centerCols = [
      Math.floor((cols + 1) / 2),  // 4列目
      Math.ceil((cols + 1) / 2)    // 5列目
    ];
    
    // 中心行の中心列を走査（列昇順）
    for (const c of centerCols) {
      if (grid[centerRow][c] === null) {
        grid[centerRow][c] = 0;
        return [centerRow, c]; // 配置した位置を返す
      }
    }
    
    return null; // 配置できなかった（すでにすべて埋まっていた）
  }
  
  // 対角線上の位置に0を配置
  if (grid[centerRow][centerCol] === null) {
    grid[centerRow][centerCol] = 0;
    return [centerRow, centerCol]; // 配置した位置を返す
  }
  
  return null; // 配置できなかった（すでに埋まっていた）
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
 * @param centerZeroPos 中心0配置の位置 [row, col]、nullの場合は通常通り処理
 */
function applyVerticalInverse(
  grid: ChartGrid, 
  rows: number, 
  cols: number,
  centerZeroPos: [number, number] | null = null
): void {
  let updated = true;
  
  while (updated) {
    updated = false;
    
    // 行1から開始（1-indexed）。配列のインデックス1から使用
    for (let row = 1; row <= rows; row++) {
      for (let col = 1; col <= cols; col++) {
        // 中心0配置で追加した0の下には裏数字を入れない
        if (centerZeroPos !== null) {
          const [centerRow, centerCol] = centerZeroPos;
          if (col === centerCol && row > centerRow && grid[centerRow][centerCol] === 0) {
            continue;
          }
        }
        
        if (grid[row][col] === null && row > 1 && grid[row - 1][col] !== null) {
          grid[row][col] = inverse(grid[row - 1][col]!);
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
    
    // 行1から開始（1-indexed）。配列のインデックス1から使用
    for (let row = 1; row <= rows; row++) {
      for (let col = 1; col <= cols; col++) {
        if (grid[row][col] === null && col > 1 && grid[row][col - 1] !== null) {
          grid[row][col] = inverse(grid[row][col - 1]!);
          updated = true;
        }
      }
    }
  }
}

/**
 * メイン行配置後の余りマスルールを適用する
 * 
 * 裏数字ルール適用前に、メイン行配置後の余ったマス（空のマス）に対して、
 * その上のメイン行（奇数行）の同じ列の数字をコピーする。
 * 
 * ルール:
 * - 奇数行（1, 3, 5, 7行目）でメイン行が配置されている場合、
 *   その行の奇数列（1, 3, 5, 7列目）で空のマスがあれば、
 *   その上のメイン行（1つ前の奇数行）の同じ列の数字をコピー
 * - 奇数行（1, 3, 5, 7行目）の偶数列（2, 4, 6, 8列目）が空の場合、
 *   その上のメイン行（1つ前の奇数行）の同じ列の数字をコピー
 * - 偶数行（2, 4, 6, 8行目）は対象外（裏数字ルール適用前は空のまま）
 * - ただし、その行に数字が1つも入っていない（メイン行が配置されていない）行は対象外
 * 
 * @param grid グリッド
 * @param rows 行数
 * @param cols 列数
 */
function applyMainRowRemainingCopy(grid: ChartGrid, rows: number, cols: number): void {
  // @ts-ignore - process is available in Node.js environment
  const DEBUG = typeof process !== 'undefined' && process.env?.DEBUG_CHART === 'true';
  
  if (DEBUG) {
    console.log('\n[applyMainRowRemainingCopy] 開始');
    console.log('メイン行配置後のグリッド状態（奇数行のみ）:');
    for (let row = 1; row <= rows; row += 2) {
      const rowData = [];
      for (let col = 1; col <= cols; col++) {
        rowData.push(grid[row][col] === null ? '.' : grid[row][col]);
      }
      console.log(`  行${row}: [${rowData.join(', ')}]`);
    }
  }
  
  // 各メイン行（奇数行）について、その行に数字が入っているかチェック
  const hasMainRow = (row: number): boolean => {
    // 奇数行の奇数列（1, 3, 5, 7列目）に数字が入っているかチェック
    for (let col = 1; col <= cols; col += 2) {
      if (grid[row][col] !== null) {
        return true;
      }
    }
    return false;
  };
  
  // 奇数行の奇数列（1, 3, 5, 7列目）を処理
  // メイン行が配置されているが、要素が4つ未満の場合の空のマスを補完
  for (let row = 1; row <= rows; row += 2) {
    // その行にメイン行が配置されているかチェック
    if (!hasMainRow(row)) {
      if (DEBUG) console.log(`  行${row}: メイン行なし、スキップ`);
      continue; // メイン行がなければスキップ
    }
    
    if (DEBUG) console.log(`  行${row}: メイン行あり、処理開始`);
    
    // 奇数列（1, 3, 5, 7列目）が空の場合、その上のメイン行の数字をコピー
    // メイン行配置後の余りマスルール: 空の奇数列に上のメイン行の同じ列の数字を反映
    for (let col = 1; col <= cols; col += 2) {
      if (grid[row][col] === null && row > 1) {
        // 上のメイン行（1つ前の奇数行）を探す
        let prevMainRow = row - 2;
        while (prevMainRow >= 1 && !hasMainRow(prevMainRow)) {
          prevMainRow -= 2;
        }
        
        // 上のメイン行が見つかり、その列に数字がある場合、コピー
        if (prevMainRow >= 1 && grid[prevMainRow][col] !== null) {
          if (DEBUG) {
            console.log(`    行${row}列${col}: 空 → 行${prevMainRow}列${col}の${grid[prevMainRow][col]}をコピー`);
          }
          grid[row][col] = grid[prevMainRow][col];
        } else {
          if (DEBUG) {
            console.log(`    行${row}列${col}: 空だが、上のメイン行が見つからないかその列に数字なし`);
          }
        }
      }
    }
  }
  
  // 奇数行の偶数列（2, 4, 6, 8列目）を処理
  for (let row = 1; row <= rows; row += 2) {
    // その行にメイン行が配置されているかチェック
    if (!hasMainRow(row)) {
      continue; // メイン行がなければスキップ
    }
    
    // 偶数列（2, 4, 6, 8列目）が空の場合、その上のメイン行の数字をコピー
    for (let col = 2; col <= cols; col += 2) {
      if (grid[row][col] === null && row > 1) {
        // 上のメイン行（1つ前の奇数行）を探す
        let prevMainRow = row - 2;
        while (prevMainRow >= 1 && !hasMainRow(prevMainRow)) {
          prevMainRow -= 2;
        }
        
        if (prevMainRow >= 1 && grid[prevMainRow][col] !== null) {
          if (DEBUG) {
            console.log(`    行${row}列${col}: 空 → 行${prevMainRow}列${col}の${grid[prevMainRow][col]}をコピー`);
          }
          grid[row][col] = grid[prevMainRow][col];
        }
      }
    }
  }
  
  if (DEBUG) {
    console.log('\n処理後のグリッド状態（奇数行のみ）:');
    for (let row = 1; row <= rows; row += 2) {
      const rowData = [];
      for (let col = 1; col <= cols; col++) {
        rowData.push(grid[row][col] === null ? '.' : grid[row][col]);
      }
      console.log(`  行${row}: [${rowData.join(', ')}]`);
    }
    console.log('[applyMainRowRemainingCopy] 終了\n');
  }
  
  // 注意: 偶数行（2, 4, 6, 8行目）は裏数字ルール適用前は空のままにするため、
  // ここでは処理しない
}

/**
 * 余りマスルールを適用する
 * 
 * 裏数字ルール適用後も空のマスに対して、上から値をコピーする。
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
    
    // 行1から開始（1-indexed）。配列のインデックス1から使用
    for (let row = 1; row <= rows; row++) {
      for (let col = 1; col <= cols; col++) {
        if (grid[row][col] === null && row > 1 && grid[row - 1][col] !== null) {
          grid[row][col] = grid[row - 1][col];
          updated = true;
        }
      }
    }
  }
}



