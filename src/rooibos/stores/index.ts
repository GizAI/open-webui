import { type Writable, writable } from 'svelte/store';

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

// 커스텀 store 생성
function createCompanyStore(): Writable<CompanySettings> {
    const store = writable<CompanySettings>(getInitialCompanyInfo());
    const { subscribe, set: originalSet, update } = store;

    return {
        subscribe,
        update,
        set: (value: CompanySettings) => {
            originalSet(value);
            if (value?.company_name) {
                sessionStorage.setItem('selectedCompany', JSON.stringify(value));
                console.log('Company info saved to sessionStorage:', value);
            }
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
    sme_type?: string;
    cri_company_size?: string;
    lab_name?: string;
    first_approval_date?: string;
    lab_location?: string;
    research_field?: string;
    division?: string;
    birth_year?: string;
    foundation_year?: string;
    is_family_shareholder?: string;
    is_non_family_shareholder?: string;
    financial_statement_year?: string;
    employees?: number;
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
};

export function formatCompanyInfo(companyInfo: CompanySettings): string {
    const allowedFields = [
        "master_id",
        "company_name",
        "representative",
        "postal_code",
        "address",
        "phone_number",
        "fax_number",
        "company_type",
        "establishment_date",
        "employee_count",
        "industry_code1",
        "industry_code2",
        "industry",
        "business_registration_number",
        "corporate_number",
        "fiscal_month",
        "sales_year",
        "recent_sales",
        "profit_year",
        "recent_profit",
        "operating_profit_year",
        "recent_operating_profit",
        "asset_year",
        "recent_total_assets",
        "equity_year",
        "recent_total_equity",
        "capital_year",
        "recent_capital",
        "region1",
        "region2",
        "industry_major",
        "industry_middle",
        "industry_small"
    ];

    // allowedFields 목록에 포함된 항목만 추출하여 새 객체 생성
    const filteredCompanyInfo: Record<string, any> = {};
    allowedFields.forEach(field => {
        if (companyInfo[field as keyof CompanySettings] !== undefined) {
            filteredCompanyInfo[field] = companyInfo[field as keyof CompanySettings];
        }
    });

    // 금액 항목에 ' (백만원)' 단위 추가
    const monetaryFields = [
        "recent_sales",
        "recent_profit",
        "recent_operating_profit",
        "recent_total_assets",
        "recent_total_equity",
        "recent_capital"
    ];
    monetaryFields.forEach(field => {
        if (filteredCompanyInfo[field]) {
            filteredCompanyInfo[field] = `${filteredCompanyInfo[field]} (백만원)`;
        }
    });

    // GPT가 이해하기 쉬운 형태의 문자열로 변환 (각 항목을 '키: 값' 형태의 줄로 변환)
    return Object.entries(filteredCompanyInfo)
        .map(([key, value]) => `${key}: ${value}`)
        .join("\n");
}