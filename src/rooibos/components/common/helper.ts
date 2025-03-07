export function formatDate(timestamp: number | string): string {
	if (!timestamp) return '';
	const date = typeof timestamp === 'number' 
		? new Date(timestamp * 1000) // 유닉스 타임스탬프를 밀리초로 변환
		: new Date(timestamp);
	
	// yyyy-MM-dd HH:mm:ss 형식으로 포맷팅
	const year = date.getFullYear();
	const month = String(date.getMonth() + 1).padStart(2, '0');
	const day = String(date.getDate()).padStart(2, '0');
	const hours = String(date.getHours()).padStart(2, '0');
	const minutes = String(date.getMinutes()).padStart(2, '0');
	const seconds = String(date.getSeconds()).padStart(2, '0');
	
	return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
}

export function formatDateForCompany(date: any) {
	if (!date) return '정보없음';

	// yyyymmdd 형태인지 확인
	if (/^\d{8}$/.test(date)) {
		const yyyy = date.slice(0, 4);
		const mm = date.slice(4, 6);
		const dd = date.slice(6, 8);
		return `${yyyy}-${mm}-${dd}`;
	}

	// 만약 다른 형식이라면 Date 객체로 처리
	const d = new Date(date);
	if (isNaN(d)) return '정보없음';
	const yyyy = d.getFullYear();
	const mm = String(d.getMonth() + 1).padStart(2, '0');
	const dd = String(d.getDate()).padStart(2, '0');
	return `${yyyy}-${mm}-${dd}`;
}

export function formatBusinessNumber(bn: any) {
	if (!bn) return '정보없음';
	// 숫자만 추출
	const digits = bn.toString().replace(/\D/g, '');
	// 10자리가 아니라면 그대로 반환하거나 "정보없음"을 반환할 수 있음
	if (digits.length !== 10) return bn;
	// xxx-xx-xxxxx 형식으로 변환
	return `${digits.slice(0, 3)}-${digits.slice(3, 5)}-${digits.slice(5)}`;
}

export function formatCorporateNumber(corpNumber: any) {
	if (!corpNumber) return '정보없음';
	// 숫자만 추출
	const digits = corpNumber.toString().replace(/\D/g, '');
	// 13자리 숫자일 경우, 6자리-7자리 형식으로 포맷팅
	if (digits.length === 13) {
		return `${digits.slice(0, 6)}-${digits.slice(6)}`;
	}
	// 13자리가 아니면 그대로 반환하거나 다른 처리 가능
	return corpNumber;
}

export function formatDistance(distance?: number): string {
	if (distance === undefined || distance === null) return '정보없음';
	if (distance < 1000) return `${distance.toLocaleString('ko-KR')} m`;
	const km = distance / 1000;
	return `${km.toLocaleString('ko-KR', { maximumFractionDigits: 2 })} km`;
}
