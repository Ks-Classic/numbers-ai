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
    const rows = mainRows.length * 2; // メイン行N本の場合、2*N行必要
    const cols = 8;
    const grid = initializeGrid(rows, cols, mainRows);
    
    // ステップ5: メイン行配置後の余りマスルール（裏数字適用前）
    // 奇数行の奇数列・偶数列の空マスに対して、
    // その上のメイン行（奇数行）の同じ列の数字をコピー
    applyMainRowRemainingCopy(grid, rows, cols);
    
    // ステップ5.5: パターンA2/B2中心0配置
    // メイン行配置後の余りマスルールの後に実行することで、
    // 余りマスルールで補完された数字が中心0配置で上書きされないようにする
    let centerZeroPlaced = false;
    if (pattern === ('A2' as Pattern) || pattern === ('B2' as Pattern)) {
      centerZeroPlaced = placeCenterZero(grid, rows, cols);
    }
    
    // ステップ6-8: 裏数字・余りマスルール
    // ステップ6: 縦パス（上から下へ裏数字を配置）
    applyVerticalInverse(grid, rows, cols);
    // ステップ7: 横パス（左から右へ裏数字を配置）
    applyHorizontalInverse(grid, rows, cols);
    // ステップ8: 余りマスルール（裏数字適用後の空マスを上からコピー）
    applyRemainingCopy(grid, rows, cols);
    
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
  
  // 昇順ソート
  sourceList.sort((a, b) => a - b);
  
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
 * 仕様: docs/元ネタ/表作成ルール.,md の「4. メイン行の組み立て（vFinal 3.0）」
 * 
 * @param nums 元数字リスト
 * @returns メイン行の配列
 */
function buildMainRows(nums: number[]): MainRow[] {
  const mainRows: MainRow[] = [];
  let tempList = [...nums];
  let rowIndex = 0;
  
  // デバッグ出力（開発時のみ）
  // @ts-ignore - process is available in Node.js environment
  const DEBUG = typeof process !== 'undefined' && process.env?.DEBUG_CHART === 'true';
  if (DEBUG) {
    console.log('[buildMainRows] 開始: nums =', nums);
    console.log('[buildMainRows] 初期 tempList =', tempList);
  }
  
  while (tempList.length > 0) {
    // ユニーク値を昇順で取得
    const uniqueDigits = [...new Set(tempList)].sort((a, b) => a - b);
    
    if (DEBUG) {
      console.log(`[buildMainRows] 行${rowIndex}: uniqueDigits =`, uniqueDigits);
    }
    
    if (uniqueDigits.length >= 4) {
      // 4種類以上の場合: 最初の4種類を構成メンバーとして使用
      const members = uniqueDigits.slice(0, 4);
      const newRow: number[] = [];
      
      if (DEBUG) {
        console.log(`[buildMainRows] 行${rowIndex}: members =`, members);
        console.log(`[buildMainRows] 行${rowIndex}: tempList =`, tempList);
      }
      
      // tempListから順に取り出してnewRowに格納
      for (let i = 0; i < 4; i++) {
        const idx = tempList.indexOf(members[i]);
        if (idx === -1) {
          throw new ChartGenerationError(
            `メイン行組み立てエラー: 数字${members[i]}が見つかりません`
          );
        }
        const digit = tempList[idx];
        newRow.push(digit);
        tempList.splice(idx, 1);
        
        if (DEBUG) {
          console.log(`[buildMainRows] 行${rowIndex}: members[${i}] = ${members[i]}, indexOf = ${idx}, tempList[${idx}] = ${digit}, 削除後のtempList =`, tempList);
        }
      }
      
      if (DEBUG) {
        console.log(`[buildMainRows] 行${rowIndex}: newRow =`, newRow);
      }
      
      mainRows.push({ elements: newRow, rowIndex: rowIndex++ });
    } else {
      // 4種類未満の場合: ユニーク値のみを使用（最大値を繰り返し追加しない）
      // 余りマスは applyMainRowRemainingCopy で補完される
      const newRow: number[] = [...uniqueDigits];
      
      if (DEBUG) {
        console.log(`[buildMainRows] 行${rowIndex}: uniqueDigits =`, uniqueDigits);
        console.log(`[buildMainRows] 行${rowIndex}: tempList =`, tempList);
      }
      
      // tempListから使用した数字を削除
      // 各数字を1個ずつ削除（重複を考慮）
      for (const digit of newRow) {
        const idx = tempList.indexOf(digit);
        if (idx !== -1) {
          tempList.splice(idx, 1);
          
          if (DEBUG) {
            console.log(`[buildMainRows] 行${rowIndex}: digit = ${digit}, indexOf = ${idx}, tempList[${idx}] = ${digit}, 削除後のtempList =`, tempList);
          }
        }
      }
      
      if (DEBUG) {
        console.log(`[buildMainRows] 行${rowIndex}: newRow =`, newRow);
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
 * 中心マス群を (row昇順, col昇順) で走査し、
 * 最初に見つかる空白マスに0を1つ配置する。
 * 実装・表示・配列すべて1-indexedで統一（配列のインデックス1から使用）。
 * 
 * @param grid グリッド
 * @param rows 行数（1-indexedでの行数）
 * @param cols 列数（1-indexedでの列数、常に8）
 * @returns 0が配置されたかどうか
 */
function placeCenterZero(grid: ChartGrid, rows: number, cols: number): boolean {
  // 中心行・列を計算（1-indexed）
  const centerRows = [
    Math.floor((rows + 1) / 2),
    Math.ceil((rows + 1) / 2)
  ];
  const centerCols = [
    Math.floor((cols + 1) / 2),
    Math.ceil((cols + 1) / 2)
  ];
  
  // 中心マス群を走査（配列のインデックス1から使用）
  for (const r of centerRows) {
    for (const c of centerCols) {
      if (grid[r][c] === null) {
        grid[r][c] = 0;
        return true; // 1つ配置したら終了
      }
    }
  }
  
  return false; // 配置できなかった（すでにすべて埋まっていた）
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
    
    // 行1から開始（1-indexed）。配列のインデックス1から使用
    for (let row = 1; row <= rows; row++) {
      for (let col = 1; col <= cols; col++) {
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

