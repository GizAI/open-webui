export function formatDate(date: any) {
	if (!date) return "정보없음";
	
	// yyyymmdd 형태인지 확인
	if (/^\d{8}$/.test(date)) {
		const yyyy = date.slice(0, 4);
		const mm = date.slice(4, 6);
		const dd = date.slice(6, 8);
		return `${yyyy}-${mm}-${dd}`;
	}

	// 만약 다른 형식이라면 Date 객체로 처리
	const d = new Date(date);
	if (isNaN(d)) return "정보없음";
	const yyyy = d.getFullYear();
	const mm = String(d.getMonth() + 1).padStart(2, '0');
	const dd = String(d.getDate()).padStart(2, '0');
	return `${yyyy}-${mm}-${dd}`;
}

export function formatBusinessNumber(bn: any) {
	if (!bn) return "정보없음";
	// 숫자만 추출
	const digits = bn.toString().replace(/\D/g, '');
	// 10자리가 아니라면 그대로 반환하거나 "정보없음"을 반환할 수 있음
	if (digits.length !== 10) return bn;
	// xxx-xx-xxxxx 형식으로 변환
	return `${digits.slice(0, 3)}-${digits.slice(3, 5)}-${digits.slice(5)}`;
}