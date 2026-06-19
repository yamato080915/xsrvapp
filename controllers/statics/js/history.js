const table = document.getElementById("table");
const tbody = table.querySelector("tbody");

// ソート状態を管理するオブジェクト
const sortState = {
	day: 'desc',    // 初期状態: 降順
	place: null,
	perf: null,
	rate: null,
	diff: null
};

// アイコンを更新する関数
function updateIcon(column, direction) {
	// すべてのアイコンをリセット
	['day', 'place', 'perf', 'rate', 'diff'].forEach(col => {
		const icon = document.getElementById(col + 'sort');
		icon.className = 'bi bi-arrow-down-up';
	});
	
	// 選択された列のアイコンを更新
	const icon = document.getElementById(column + 'sort');
	if (direction === 'asc') {
		icon.className = 'bi bi-sort-down-alt';
	} else if (direction === 'desc') {
		icon.className = 'bi bi-sort-down';
	}
}

// ソート関数
function sortTable(column, columnIndex) {
	const rows = Array.from(tbody.querySelectorAll('tr'));
	
	// ソート方向を決定
	let direction;
	if (sortState[column] === null || sortState[column] === 'desc') {
		direction = 'asc';
	} else {
		direction = 'desc';
	}
	
	// すべての状態をリセット
	Object.keys(sortState).forEach(key => sortState[key] = null);
	sortState[column] = direction;
	
	// ソート実行
	rows.sort((a, b) => {
		let aValue = a.cells[columnIndex].textContent.trim();
		let bValue = b.cells[columnIndex].textContent.trim();
		
		// 数値として処理する列
		if (column === 'place' || column === 'perf' || column === 'rate') {
			aValue = parseInt(aValue.replace(/,/g, ''));
			bValue = parseInt(bValue.replace(/,/g, ''));
		} else if (column === 'diff') {
			// 差分の場合、±0を0として処理
			aValue = aValue === '±0' ? 0 : parseInt(aValue.replace(/\+/g, ''));
			bValue = bValue === '±0' ? 0 : parseInt(bValue.replace(/\+/g, ''));
		}
		
		// 比較
		if (aValue < bValue) {
			return direction === 'asc' ? -1 : 1;
		} else if (aValue > bValue) {
			return direction === 'asc' ? 1 : -1;
		}
		return 0;
	});
	
	// テーブルを再構築
	rows.forEach(row => tbody.appendChild(row));
	
	// アイコンを更新
	updateIcon(column, direction);
}

// イベントリスナーを設定
document.getElementById("daysort").addEventListener("click", () => sortTable('day', 0));
document.getElementById("placesort").addEventListener("click", () => sortTable('place', 2));
document.getElementById("perfsort").addEventListener("click", () => sortTable('perf', 3));
document.getElementById("ratesort").addEventListener("click", () => sortTable('rate', 4));
document.getElementById("diffsort").addEventListener("click", () => sortTable('diff', 5));

// 初期状態のアイコンを設定
updateIcon('day', 'desc');