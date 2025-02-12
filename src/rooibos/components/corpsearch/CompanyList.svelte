<!-- companyList.svelte -->
<script lang="ts">
	import { slide } from 'svelte/transition';
	import ChevronDown from '$lib/components/icons/ChevronDown.svelte';
	import ChevronUp from '$lib/components/icons/ChevronUp.svelte';
	import CompanyDetail from '../corpinfo/CompanyDetail.svelte';

	// 검색 결과에 포함된 회사 정보를 나타내는 인터페이스
	interface SearchResult {
	  smtp_id: string;
	  company_name: string;
	  address: string;
	  latitude: string;
	  longitude: string;
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
	  certificate_expiry_date?: string;
	  sme_type?: string;
	  cri_company_size?: string;
	  lab_name?: string;
	  first_approval_date?: string;
	  lab_location?: string;
	  research_field?: string;
	  division?: string;
	  birth_year?: string;
	  foundation_year?: string;
	  family_shareholder_yn?: string;
	  external_shareholder_yn?: string;
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
	}

	import { showSidebar, mobile } from '$lib/stores';
	export let companyList: SearchResult[] = [];
	export let onResultClick: (result: SearchResult) => void;
	export let onClose: () => void;

	let fullscreenStates: Record<string, boolean> = {};

	// 필터링 조건 – 총 8가지
	let filters = {
		// (8-1) 기타 키워드: 기업명, 주소, 대표자
		keyword: '',
		// (8-2) 임직원 수: 몇 명 이상
		minEmployees: null as number | null,
		// (8-3) 업종 및 산업 분류
		industry: '',
		// (8-4) 위치 및 거리: '가까운거리' 또는 '먼거리'
		// 쿼리에서 이미 200m 이내의 데이터만 조회되므로, 이 값은 정렬 기준으로만 사용
		radius: 'near',  // 'near' 또는 'far'
		// (8-5) 설립 및 창립 정보: 설립일 범위 (YYYY-MM-DD 형식)
		establishmentFrom: '',
		establishmentTo: '',
		// (8-6) 인증 및 기업 유형: 예를 들어 SME 유형 등
		smeType: '',
		// (8-7) 연구소 및 기술 관련 정보: 연구소명 또는 연구분야
		labName: '',
		// (8-8) 주주 정보: 가족주주, 외부주주 여부 (체크 시 해당 조건 만족하는 회사만)
		familyShareholder: false,
		externalShareholder: false
	};

	// companyList에서 위 필터 조건을 모두 만족하는 회사만 골라내는 reactive 변수
	$: filteredCompanies = companyList.filter(company => {
		let pass = true;
		// [1] 키워드 검색 (기업명, 주소, 대표자)
		if (filters.keyword) {
			const keyword = filters.keyword.toLowerCase();
			pass = pass && (
				company.company_name.toLowerCase().includes(keyword) ||
				company.address.toLowerCase().includes(keyword) ||
				company.business_registration_number.toLowerCase().includes(keyword) ||
				(company.representative && company.representative.toLowerCase().includes(keyword))
			);
		}
		// [2] 임직원 수 (몇 명 이상)
		if (filters.minEmployees !== null) {
			pass = pass && (company.employee_count !== undefined && company.employee_count >= filters.minEmployees);
		}
		// [3] 업종
		if (filters.industry) {
			pass = pass && (company.industry && company.industry.toLowerCase().includes(filters.industry.toLowerCase()));
		}
		// [4] 거리 필터 제거 – 쿼리에서 이미 200m 이내로 제한됨
		// [5] 설립일 범위 (회사 데이터의 establishment_date는 YYYYMMDD 또는 YYYY-MM-DD 형식이라 가정)
		if (filters.establishmentFrom) {
			const estDate = company.establishment_date ? String(company.establishment_date).replace(/-/g, '') : '';
			const filterFrom = filters.establishmentFrom.replace(/-/g, '');
			pass = pass && (estDate >= filterFrom);
		}
		if (filters.establishmentTo) {
			const estDate = company.establishment_date ? String(company.establishment_date).replace(/-/g, '') : '';
			const filterTo = filters.establishmentTo.replace(/-/g, '');
			pass = pass && (estDate <= filterTo);
		}
		// [6] 인증 및 기업 유형
		if (filters.smeType) {
			pass = pass && (company.sme_type && company.sme_type.toLowerCase().includes(filters.smeType.toLowerCase()));
		}
		// [7] 연구소 정보: 연구소명 또는 연구분야
		if (filters.labName) {
			pass = pass && (
				(company.lab_name && company.lab_name.toLowerCase().includes(filters.labName.toLowerCase())) ||
				(company.research_field && company.research_field.toLowerCase().includes(filters.labName.toLowerCase()))
			);
		}
		// [8] 주주 정보: 체크된 경우 해당 조건 만족
		if (filters.familyShareholder) {
			pass = pass && (company.family_shareholder_yn === 'Y');
		}
		if (filters.externalShareholder) {
			pass = pass && (company.external_shareholder_yn === 'Y');
		}
		return pass;
	});

	// 정렬 로직: filters.radius 값에 따라 결과를 정렬합니다.
	// 예) 가까운거리 선택 시 오름차순(38m, 50m), 먼거리 선택 시 내림차순(50m, 38m)
	$: sortedCompanies = [...filteredCompanies].sort((a, b) => {
		const distanceA = a.distance_from_user ?? 0;
		const distanceB = b.distance_from_user ?? 0;
		return filters.radius === 'near' ? distanceA - distanceB : distanceB - distanceA;
	});

	function toggleFullscreen(smtp_id: string) {
		fullscreenStates = { ...fullscreenStates, [smtp_id]: !fullscreenStates[smtp_id] };
	}

	function closeCompanyInfo(smtp_id: string) {
		fullscreenStates = { ...fullscreenStates, [smtp_id]: false };
		onClose();
	}
</script>

<!-- 최상위 컨테이너는 좌측 사이드바를 고려하여 fixed 위치를 지정합니다 -->
<div class="company-list-wrapper fixed bottom-0 left-0 right-0 top-[50px] bg-gray-50 shadow-lg rounded-t-2xl transition-all duration-300"
	 class:sidebar-margin={$showSidebar}
	 class:mobile-layout={$mobile}>
	<!-- 필터 패널 -->
	<div class="filter-panel p-2 bg-gray-80 border-b border-gray-300 flex flex-wrap items-center gap-2">
		<input type="text" placeholder="키워드" bind:value={filters.keyword} class="filter-input" />
		<!-- 임직원 수 필터: 몇 명 이상 -->
		<input type="number" placeholder="임직원 수 (몇 명 이상)" bind:value={filters.minEmployees} class="filter-input" />
		<input type="text" placeholder="업종" bind:value={filters.industry} class="filter-input" />
		<!-- 위치 및 거리 필터: '가까운거리'와 '먼거리' (정렬 기준으로 사용) -->
		<select bind:value={filters.radius} class="filter-input">
			<option value="near">가까운거리</option>
			<option value="far">먼거리</option>
		</select>
		<!-- 설립일 범위 필터 (필요 시 주석 해제)
		<input type="date" placeholder="설립일(시작)" bind:value={filters.establishmentFrom} class="filter-input" />
		<input type="date" placeholder="설립일(종료)" bind:value={filters.establishmentTo} class="filter-input" />
		-->
		<input type="text" placeholder="인증/유형" bind:value={filters.smeType} class="filter-input" />
		<input type="text" placeholder="연구소명/분야" bind:value={filters.labName} class="filter-input" />
	</div>
	<!-- 스크롤 가능한 목록 영역 -->
	<div class="list-container flex-1 overflow-y-auto">
		<ul class="p-4 space-y-2">
			{#each sortedCompanies as result}
				<li>
					<div class="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
						<div role="button" tabindex="0"
							on:click={() => onResultClick(result)}
							on:keydown={(e) => { if(e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onResultClick(result); } }}
							class="w-full text-left p-4 hover:bg-gray-50 transition-colors duration-200">
							<div class="flex items-start justify-between">
								<div class="flex-1">
									<div class="flex items-center">
										<span class="font-semibold text-gray-900">{result.company_name}</span>
										<span class="ml-1">({result.business_registration_number})</span>
										<button type="button" on:click|stopPropagation={() => toggleFullscreen(result.smtp_id)} class="ml-2">
											{#if fullscreenStates[result.smtp_id]}
												<ChevronUp size={20} strokeWidth="2.5"/>
											{:else}
												<ChevronDown size={20} strokeWidth="2.5"/>
											{/if}
										</button>
									</div>
									{#if result.address && !fullscreenStates[result.smtp_id]}
										<div class="text-sm text-gray-600 mt-1.5">{result.address}</div>
									{/if}
									{#if result.representative && !fullscreenStates[result.smtp_id]}
										<div class="text-sm text-gray-500 mt-1">
											대표자: {result.representative} | 거리: {result.distance_from_location} m
										</div>
									{/if}
								</div>
							</div>
						</div>
						{#if fullscreenStates[result.smtp_id]}
							<div transition:slide class="border-t border-gray-200">
								<CompanyDetail company={result} onClose={() => closeCompanyInfo(result.smtp_id)} />
							</div>
						{/if}
					</div>
				</li>
			{/each}
		</ul>
	</div>
</div>

<style>
	.company-list-wrapper {
		display: flex;
		flex-direction: column;
	}

	/* 사이드바가 있을 때 왼쪽 margin 적용 */
	.sidebar-margin {
		left: 260px;
	}

	.mobile-layout {
		border-top-left-radius: 20px;
		border-top-right-radius: 20px;
	}

	.filter-panel {
		/* 필터 패널 스타일 */
	}
	.filter-input {
		width: 100px;          /* 기존보다 작은 너비 */
		padding: 0.2rem;       /* 컴팩트한 패딩 */
		font-size: 0.8rem;
		border: 1px solid #d1d5db;
		border-radius: 0.375rem;
	}
	.filter-label {
		display: flex;
		align-items: center;
		font-size: 0.875rem;
	}
	.list-container {
		flex: 1;
		overflow-y: auto;
	}
</style>
