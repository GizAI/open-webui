import { type Writable, writable } from 'svelte/store';

// 폴더 업데이트 관련 스토어
export const folderUpdateTrigger = writable<number>(0);

// 폴더 업데이트 트리거 함수
export function triggerFolderUpdate() {
	folderUpdateTrigger.update(n => n + 1);
}

interface CompanyStore extends Writable<CompanySettings> {
	getLastSelected: () => CompanySettings;
	getHistory: () => CompanySettings[];
	clearCompany: () => void;
	clearHistory: () => void;
	removeFromHistory: (masterId: string) => void;
}

// sessionStorage에서 초기 데이터를 불러오는 함수
function getInitialCompanyInfo(): CompanySettings {
	try {
		const storedData = sessionStorage.getItem('selectedCompany');
		return storedData ? JSON.parse(storedData) : {};
	} catch (error) {
		console.error('Error loading company info from sessionStorage:', error);
		return {};
	}
}

// 마지막 선택 기업 정보를 저장하는 함수
function saveLastSelectedCompany(companyInfo: CompanySettings) {
	try {
		sessionStorage.setItem('lastSelectedCompany', JSON.stringify(companyInfo));
	} catch (error) {
		console.error('Error saving last selected company:', error);
	}
}

// 마지막 선택 기업 정보를 가져오는 함수
function getLastSelectedCompany(): CompanySettings {
	try {
		const storedData = sessionStorage.getItem('lastSelectedCompany');
		return storedData ? JSON.parse(storedData) : {};
	} catch (error) {
		console.error('Error loading last selected company:', error);
		return {};
	}
}

// 회사 정보 히스토리를 저장하는 함수
function saveCompanyHistory(companyInfo: CompanySettings) {
	try {
		const history = sessionStorage.getItem('companyHistory');
		const historyList: CompanySettings[] = history ? JSON.parse(history) : [];
		
		// 중복 제거를 위해 같은 master_id가 있는지 확인
		const isDuplicate = historyList.some(item => item.master_id === companyInfo.master_id);
		
		if (!isDuplicate && companyInfo.master_id) {
			historyList.push(companyInfo);
			// 최대 10개까지만 저장
			if (historyList.length > 10) {
				historyList.shift();
			}
			sessionStorage.setItem('companyHistory', JSON.stringify(historyList));
		}
	} catch (error) {
		console.error('Error saving company history:', error);
	}
}

// 회사 정보 히스토리를 가져오는 함수
function getCompanyHistory(): CompanySettings[] {
	try {
		const history = sessionStorage.getItem('companyHistory');
		return history ? JSON.parse(history) : [];
	} catch (error) {
		console.error('Error loading company history:', error);
		return [];
	}
}

// 회사 정보 히스토리를 삭제하는 함수
function clearCompanyHistory() {
	try {
		sessionStorage.removeItem('companyHistory');
	} catch (error) {
		console.error('Error clearing company history:', error);
	}
}

// 특정 회사를 히스토리에서 삭제하는 함수
function removeCompanyFromHistory(masterId: string) {
	try {
		const history = sessionStorage.getItem('companyHistory');
		if (history) {
			const historyList: CompanySettings[] = JSON.parse(history);
			const filteredList = historyList.filter(item => item.master_id !== masterId);
			sessionStorage.setItem('companyHistory', JSON.stringify(filteredList));
		}
	} catch (error) {
		console.error('Error removing company from history:', error);
	}
}

// 커스텀 store 생성
function createCompanyStore(): CompanyStore {
	const store = writable<CompanySettings>(getInitialCompanyInfo());
	const { subscribe, set: originalSet, update } = store;

	return {
		subscribe,
		update,
		set: (value: CompanySettings) => {
			originalSet(value);
			if (value?.company_name) {
				sessionStorage.setItem('selectedCompany', JSON.stringify(value));
				saveLastSelectedCompany(value);
				saveCompanyHistory(value);
				console.log('Company info saved to sessionStorage:', value);
			}
		},
		getLastSelected: () => {
			return getLastSelectedCompany();
		},
		getHistory: () => {
			return getCompanyHistory();
		},
		clearCompany: () => {
			originalSet({});
			sessionStorage.removeItem('selectedCompany');
		},
		clearHistory: () => {
			clearCompanyHistory();
		},
		removeFromHistory: (masterId: string) => {
			removeCompanyFromHistory(masterId);
		}
	};
}

export const selectedCompanyInfo = createCompanyStore();

type CompanySettings = {
	master_id?: string;
	company_name?: string;
	address?: string;
	latitude?: string;
	longitude?: string;
	phone_number?: string;
	category?: string[];
	business_registration_number?: string;
	representative?: string;
	birth_date?: string;
	industry?: string;
	establishment_date?: string;
	employee_count?: number;
	recent_sales?: number;
	recent_revenue?: number;
	recent_profit?: number;
	website?: string;
	distance_from_user?: number;
	bookmark_id?: string | null;
	fax_number?: string;
	email?: string;
	company_type?: string;
	founding_date?: string;
	industry_code1?: string;
	industry_code2?: string;
	main_product?: string;
	main_bank?: string;
	main_branch?: string;
	group_name?: string;
	stock_code?: string;
	corporate_number?: string;
	english_name?: string;
	trade_name?: string;
	fiscal_month?: string;
	sales_year?: string;
	profit_year?: string;
	operating_profit_year?: string;
	recent_operating_profit?: number;
	asset_year?: string;
	recent_total_assets?: number;
	debt_year?: string;
	recent_total_debt?: number;
	equity_year?: string;
	recent_total_equity?: number;
	capital_year?: string;
	recent_capital?: number;
	region1?: string;
	region2?: string;
	industry_major?: string;
	industry_middle?: string;
	industry_small?: string;
	sme_type?: { sme_type: string; certificate_expiry_date: string }[];
	research_info?: {
		lab_name: string;
		lab_location: string;
		first_approval_date: string;
		research_field: string;
		division: string;
	}[];
	birth_year?: string;
	foundation_year?: string;
	is_family_shareholder?: string;
	is_non_family_shareholder?: string;
	financial_statement_year?: string;
	total_assets?: number;
	total_equity?: number;
	sales_amount?: number;
	net_income?: number;
	venture_confirmation_type?: string;
	svcl_region?: string;
	venture_valid_from?: string;
	venture_valid_until?: string;
	confirming_authority?: string;
	new_reconfirmation_code?: string;
	financialData?: FinancialData;
	files?: string[];
};

type FinancialData = {
	financial_company_id: string;
	year: string;
	revenue?: number;
	net_income?: number;
	operating_income?: number;
	total_assets?: number;
	total_liabilities?: number;
	total_equity?: number;
	capital_stock?: number;
	corporate_tax?: number;
	current_assets?: number;
	quick_assets?: number;
	inventory?: number;
	non_current_assets?: number;
	investment_assets?: number;
	tangible_assets?: number;
	intangible_assets?: number;
	current_liabilities?: number;
	non_current_liabilities?: number;
	retained_earnings?: number;
	profit?: number;
	sales_cost?: number;
	sales_profit?: number;
	sga?: number;
	other_income?: number;
	other_expenses?: number;
	pre_tax_income?: number;
};

export function formatCompanyInfo(companyInfo: CompanySettings): string {
	const allowedFields = [
		'master_id',
		'company_name',
		'representative',
		'postal_code',
		'address',
		'phone_number',
		'fax_number',
		'company_type',
		'establishment_date',
		'employee_count',
		'industry_code1',
		'industry_code2',
		'industry',
		'business_registration_number',
		'corporate_number',
		'fiscal_month',
		'sales_year',
		'recent_sales',
		'profit_year',
		'recent_profit',
		'operating_profit_year',
		'recent_operating_profit',
		'asset_year',
		'recent_total_assets',
		'equity_year',
		'recent_total_equity',
		'capital_year',
		'recent_capital',
		'region1',
		'region2',
		'industry_major',
		'industry_middle',
		'industry_small'
	];

	// allowedFields 목록에 포함된 항목만 추출하여 새 객체 생성
	const filteredCompanyInfo: Record<string, any> = {};
	allowedFields.forEach((field) => {
		if (companyInfo[field as keyof CompanySettings] !== undefined) {
			filteredCompanyInfo[field] = companyInfo[field as keyof CompanySettings];
		}
	});

	// 금액 항목에 ' (백만원)' 단위 추가
	const monetaryFields = [
		'recent_sales',
		'recent_profit',
		'recent_operating_profit',
		'recent_total_assets',
		'recent_total_equity',
		'recent_capital'
	];
	monetaryFields.forEach((field) => {
		if (filteredCompanyInfo[field]) {
			filteredCompanyInfo[field] = `${filteredCompanyInfo[field]} (백만원)`;
		}
	});

	// GPT가 이해하기 쉬운 형태의 문자열로 변환 (각 항목을 '키: 값' 형태의 줄로 변환)
	return Object.entries(filteredCompanyInfo)
		.map(([key, value]) => `${key}: ${value}`)
		.join('\n');
}
