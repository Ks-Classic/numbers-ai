/**
 * メイン行組み立てロジックのデバッグ用スクリプト
 */

const nums = [0, 0, 0, 1, 2, 3, 4, 5, 6, 7, 7, 8, 8, 9];
let tempList = [...nums];

console.log('初期 tempList:', tempList);
console.log('ユニーク値:', [...new Set(tempList)].sort((a, b) => a - b));
console.log();

const uniqueDigits = [...new Set(tempList)].sort((a, b) => a - b);

if (uniqueDigits.length >= 4) {
  const members = uniqueDigits.slice(0, 4);
  console.log('構成メンバー（最初の4種類）:', members);
  console.log();
  
  const newRow: number[] = [];
  
  for (let i = 0; i < 4; i++) {
    const member = members[i];
    const idx = tempList.indexOf(member);
    const value = tempList[idx];
    
    console.log(`members[${i}] = ${member} を探す:`);
    console.log(`  tempList.indexOf(${member}) = ${idx}`);
    console.log(`  tempList[${idx}] = ${value}`);
    console.log(`  → newRow[${i}] = ${value}`);
    
    newRow.push(value);
    tempList.splice(idx, 1);
    
    console.log(`  削除後の tempList: [${tempList.join(', ')}]`);
    console.log();
  }
  
  console.log('最終的な newRow:', newRow);
  console.log('残りの tempList:', tempList);
}
