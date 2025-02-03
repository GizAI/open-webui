<script lang="ts">
	import { onMount } from 'svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import {
		Briefcase, MapPin, Users, Phone, Globe, Calendar, DollarSign, List,
		Award, Building2, FlaskConical, CalendarCheck, Microscope, ClipboardList
	} from 'lucide-svelte';
	import { mobile, user } from '$lib/stores';
	import { WEBUI_API_BASE_URL } from '$lib/constants';
	import { get } from 'svelte/store';
	import { selectedCompanyInfo } from '$rooibos/stores';
	import { goto } from '$app/navigation';

	interface CompanyInfo {
		id: string;
		company_id: string;
		company_name: string;
		roadAddress?: string;
		address?: string;
		category?: string[];
		business_registration_number?: number;
		industry?: string;
		representative?: string;
		birth_date?: string;
		establishment_date?: string;
		employee_count?: number;
		phone_number?: string;
		website?: string;
		distance_from_user?: number;
		created_at?: string;
		updated_at?: string;
		files: any[];
		smtp_id: string;
		latitude: string;
		longitude: string;
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
		venture_confirmation_type?: string;
		svcl_region?: string;
		venture_valid_from?: string;
		venture_valid_until?: string;
		confirming_authority?: string;
		new_reconfirmation_code?: string;
		postal_code?: string;
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

	export let onClose: () => void;
	export let companyInfo: CompanyInfo = {
		id: '',
		company_id: '',
		company_name: '',
		files: [],
		smtp_id: '',
		latitude: '',
		longitude: ''
	};

	let financialData: FinancialData[] | null = null;

	onMount(async () => {
		const financialResponse = await fetch(`${WEBUI_API_BASE_URL}/rooibos/corpbookmarks/${companyInfo.smtp_id}/financialData`, {
			method: 'GET',
			headers: {
				Accept: 'application/json',
				'Content-Type': 'application/json',
				authorization: `Bearer ${localStorage.token}`
			}
		})
		const data = await financialResponse.json();
		financialData = data.data;
	});

	const years = ['2023', '2022', '2021'];	

	// 필요에 따라 섹션 표시 여부 함수들
	const hasBasicInfo = (info: CompanyInfo) => {
		return info.business_registration_number ||
			info.corporate_number ||
			info.representative ||
			info.address ||
			info.cri_company_size ||
			info.phone_number ||
			info.establishment_date ||
			info.employee_count ||
			info.fiscal_month ||
			info.main_bank ||
			info.website
		;
	};

	const hasIndustryInfo = (info: CompanyInfo) => {
		return info.industry || info.main_product;
	};

	const hasLabInfo = (info: CompanyInfo) => {
		return info.lab_name ||
			info.research_field ||
			info.division ||
			info.first_approval_date ||
			info.lab_location
		;
	};

	const hasCertificationInfo = (info: CompanyInfo) => {
		return info.venture_confirmation_type ||
			info.sme_type ||
			info.certificate_expiry_date ||
			info.venture_valid_from
		;
	};

	const hasShareholderInfo = (info: CompanyInfo) => {
		return info.family_shareholder_yn == 'Y' || info.external_shareholder_yn == 'Y';
	};

	const hasFinancialInfo = () => {
		return financialData && Array.isArray(financialData) && financialData.length > 0;
	};

	// 동적으로 사용 가능한 섹션 목록
	let availableSections = [
		{ id: 'basic', title: '기본', icon: MapPin, visible: hasBasicInfo(companyInfo) },
		{ id: 'industry', title: '업종', icon: Briefcase, visible: hasIndustryInfo(companyInfo) },
		{ id: 'lab', title: '연구소', icon: Microscope, visible: hasLabInfo(companyInfo) },
		{ id: 'certification', title: '인증', icon: Award, visible: hasCertificationInfo(companyInfo) },
		{ id: 'shareholders', title: '주주', icon: Users, visible: hasShareholderInfo(companyInfo) },
		{ id: 'financial', title: '재무', icon: DollarSign, visible: hasFinancialInfo() }
	].filter(section => section.visible);


	// 섹션 DOM 참조를 담을 객체
	let sectionRefs: { [key: string]: HTMLElement } = {};

	// 스크롤 컨테이너 참조
	let scrollContainer: HTMLDivElement;

	let basicSection: HTMLElement;
	let industrySection: HTMLElement;
	let labSection: HTMLElement;
	let certificationSection: HTMLElement;
	let shareholdersSection: HTMLElement;
	let financialSection: HTMLElement;

	let selectedSection = 'basic'; // 기본값

	const headerOffset = 0; // 필요 시 값 설정(예: 60)

	function scrollToSection(sectionId: string) {
    selectedSection = sectionId;
    let targetEl: HTMLElement | undefined;

    // 섹션 매핑
    const sectionMap = {
        'basic': basicSection,
        'industry': industrySection,
        'lab': labSection,
        'certification': certificationSection,
        'shareholders': shareholdersSection,
        'financial': financialSection
    };

    targetEl = sectionMap[sectionId];

    if (targetEl && scrollContainer) {
        // 스크롤 컨테이너의 상단 여백 계산
        const containerPadding = parseInt(window.getComputedStyle(scrollContainer).paddingTop) || 0;
        
        // 섹션의 절대 위치 계산
        const containerTop = scrollContainer.getBoundingClientRect().top;
        const targetTop = targetEl.getBoundingClientRect().top;
        
        // 스크롤 위치 계산
        const scrollTop = targetTop - containerTop + scrollContainer.scrollTop - containerPadding;

        // 부드럽게 스크롤
        scrollContainer.scrollTo({
            top: scrollTop,
            behavior: 'smooth'
        });
    }
}


	export let isFullscreen = false;

	function toggleFullscreen() {
		isFullscreen = !isFullscreen;
	}

	function closeCompanyInfo() {
		isFullscreen = false;
		onClose()
	}

	const saveCompany = async (company: any) => {	
		if(!company.bookmark_id) {
			const currentUser = get(user);
			const response = await fetch(`${WEBUI_API_BASE_URL}/rooibos/corpbookmarks/add`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${localStorage.token}`
			},
			body: JSON.stringify({ 
				userId: currentUser?.id, 
				companyId: company.smtp_id, 
				business_registration_number: company.business_registration_number 
			}),
			});    
			
			const data = await response.json();
			companyInfo.bookmark_id = data.data.id;
		}else {
			await fetch(`${WEBUI_API_BASE_URL}/rooibos/corpbookmarks/${companyInfo.bookmark_id}/delete`, {
				method: 'DELETE',
				headers: {
					'Content-Type': 'application/json',
				},
			});
			companyInfo.bookmark_id = null;     
		}
	}

	const openAIChat = async (company: any) => {	
		selectedCompanyInfo.set(company);
      	await goto('/');
	}
	
	const searchNaver = async (company: any) => {	
		await window.open(`https://map.naver.com/v5/search/${encodeURIComponent(
        	company.company_name)}`, '_blank');
	}


</script>

<!-- 전체 컨테이너: 상단 고정 영역 + 아래 스크롤 영역 -->
<div 
  class="company-info-wrapper active {isFullscreen ? 'fullscreen' : ''} flex flex-col w-full bg-gray-50 mt-4 h-[calc(100vh-8rem)]"
  class:mobile={$mobile}
>
	{#if companyInfo}
		<!-- 상단 고정 영역 -->
		<div class="bg-gray-50 sticky top-0 z-10 shrink-0 px-4 pt-2 pb-1 border-b border-gray-200">	
			<!-- 회사명 / 닫기 버튼 -->
			<div class="flex items-center justify-between w-full mb-1">
				<h1 class="{$mobile ? 'sm:text-xl' : 'text-xl'} font-semibold mb-1 truncate">
					{companyInfo.company_name}
				</h1>
			
				<div class="flex items-center space-x-1">
					<!-- 기업 저장 버튼 -->
					<button 
						class="flex flex-col items-center hover:bg-gray-100 rounded-lg"
						on:click={() => saveCompany(companyInfo)}
						>
						<svg 
							xmlns="http://www.w3.org/2000/svg" 
							class="h-5 w-5 transition-colors duration-200"
							fill="none" 
							viewBox="0 0 24 24" 
							stroke="currentColor"
							class:text-yellow-500={companyInfo.bookmark_id}
							class:text-gray-500={!companyInfo.bookmark_id}
						>
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 5v14l7-7 7 7V5z" />
						</svg>
						<span 
							class="text-xs mt-1 whitespace-nowrap transition-colors duration-200"
							class:text-yellow-500={companyInfo.bookmark_id}
							class:text-gray-500={!companyInfo.bookmark_id}
						>
							저장
						</span>
					</button>

				
					<!-- AI 채팅 버튼 -->
					<button class="flex flex-col items-center hover:bg-gray-100 rounded-lg" on:click={() => openAIChat(companyInfo)}>
						<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h8m-8 4h5m-9 6v-6a2 2 0 012-2h12a2 2 0 012 2v6l-4-4H5l-4 4z" />
						</svg>
						<span class="text-xs text-gray-500 mt-1 whitespace-nowrap">AI채팅</span>
					</button>
				
					<!-- 네이버 찾기 버튼 -->
					<button class="flex flex-col items-center hover:bg-gray-100 rounded-lg" on:click={() => searchNaver(companyInfo)}>
						<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-4.35-4.35m1.5-4.15a7 7 0 11-14 0 7 7 0 0114 0z" />
						</svg>
						<span class="text-xs text-gray-500 mt-1 whitespace-nowrap">네이버</span>
					</button>
				
					{#if !$mobile}
						<button class="hover:bg-gray-100 rounded-full" on:click={closeCompanyInfo}>
							<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
							</svg>
						</button>
					{:else}
						<button 
							class="hover:bg-gray-100 rounded-full" 
							on:click={isFullscreen ? closeCompanyInfo : toggleFullscreen}
						>
							<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path 
									stroke-linecap="round" 
									stroke-linejoin="round" 
									stroke-width="2" 
									d={isFullscreen ? "M6 18L18 6M6 6l12 12" : "M5 15l7-7 7 7"}
								/>
							</svg>
						</button>
					{/if}
				</div>
			</div>
			
			<!-- 섹션 네비게이션 -->
			<!-- <hr class="border-t border-gray-100 mt-2" />
			{#if availableSections.length > 0}
				<div class="flex overflow-x-auto space-x-2 mt-2">
					{#each availableSections as section}
						<button
							class="flex items-center px-2 text-sm whitespace-nowrap font-medium
								{selectedSection === section.id ? 'text-blue-700 font-bold' : 'text-gray-600'}
								hover:text-blue-500"
							on:click={() => scrollToSection(section.id)}
						>
							{section.title}
						</button>
					{/each}
				</div>
				<hr class="border-t border-gray-100 mt-2 mb-1" />
			{/if} -->
		</div>

		<!-- 스크롤 영역(섹션들) -->
		<div class="flex-1 px-4 pb-4" bind:this={scrollContainer}>
			<!-- 섹션들을 묶을 컨테이너 -->
			<div class="space-y-6 mt-2">
				<!-- 기본 정보 섹션 -->
				{#if hasBasicInfo(companyInfo)}
					<div
						bind:this={basicSection}
						id="basic"
						class="space-y-2 border-b border-gray-100 pb-4"
					>
						<h3 class="text-sm font-semibold text-gray-700 flex items-center gap-2">
							<MapPin size={16} class="text-blue-500" />
							기본 정보
						</h3>
						<div class="space-y-1">
							{#if companyInfo.business_registration_number}
								<p class="text-sm text-gray-600 flex items-center justify-between">
									<span>사업자 등록 번호</span>
									<span>{companyInfo.business_registration_number}</span>
								</p>
							{/if}
							{#if companyInfo.corporate_number}
								<p class="text-sm text-gray-600 flex items-center justify-between">
									<span>법인등록번호</span>
									<span>{companyInfo.corporate_number}</span>
								</p>
							{/if}
							{#if companyInfo.representative}
								<p class="text-sm text-gray-600 flex items-center justify-between">
									<span>대표이사</span>
									<span>
										{companyInfo.representative}
										{#if companyInfo.birth_year}
											({companyInfo.birth_year})
										{/if}
									</span>
								</p>
							{/if}
							{#if companyInfo.address}
								<p class="text-sm text-gray-600 flex items-center justify-between">
									<span>주소</span>
									<span>{companyInfo.address}</span>
								</p>
							{/if}
							{#if companyInfo.cri_company_size}
								<p class="text-sm text-gray-600 flex items-center justify-between">
									<span>기업규모</span>
									<span>{companyInfo.cri_company_size}</span>
								</p>
							{/if}
							{#if companyInfo.phone_number}
								<p class="text-sm text-gray-600 flex items-center justify-between">
									<span>전화번호</span>
									<span>{companyInfo.phone_number}</span>
								</p>
							{/if}
							{#if companyInfo.establishment_date}
								<p class="text-sm text-gray-600 flex items-center justify-between">
									<span>설립일</span>
									<span>{String(companyInfo.establishment_date).replace(/(\d{4})(\d{2})(\d{2})/, '$1-$2-$3')}</span>
								</p>
							{/if}
							{#if companyInfo.employee_count}
								<p class="text-sm text-gray-600 flex items-center justify-between">
									<span>임직원 수</span>
									<span>{companyInfo.employee_count}명</span>
								</p>
							{/if}
							{#if companyInfo.fiscal_month}
								<p class="text-sm text-gray-600 flex items-center justify-between">
									<span>결산월</span>
									<span>{companyInfo.fiscal_month}월</span>
								</p>
							{/if}
							{#if companyInfo.main_bank}
								<p class="text-sm text-gray-600 flex items-center justify-between">
									<span>주거래은행</span>
									<span>{companyInfo.main_bank}</span>
								</p>
							{/if}
							{#if companyInfo.website}
								<p class="text-sm text-gray-600 flex items-center justify-between">
									<span>웹사이트</span>
									<a
										href={companyInfo.website.startsWith("http") ? companyInfo.website : `https://${companyInfo.website}`}
										target="_blank"
										rel="noopener noreferrer"
										class="text-blue-500 underline"
									>
										{companyInfo.website.startsWith("http") ? companyInfo.website : `https://${companyInfo.website}`}
									</a>
								</p>
							{/if}
						</div>
					</div>
				{/if}

				<!-- 업종 정보 섹션 -->
				{#if hasIndustryInfo(companyInfo)}
					<div
						bind:this={industrySection}
						id="industry"
						class="space-y-2 border-b border-gray-100 pb-4"
					>
						<h3 class="text-sm font-semibold text-gray-700 flex items-center gap-2">
							<Briefcase size={16} class="text-blue-500" />
							업종 정보
						</h3>
						<div class="space-y-1">
							{#if companyInfo.industry}
								<p class="text-sm text-gray-600 flex items-center justify-between">
									<span>업종</span>
									<span>{companyInfo.industry}</span>
								</p>
							{/if}
							{#if companyInfo.main_product}
								<p class="text-sm text-gray-600 flex items-center justify-between">
									<span>주요상품</span>
									<span>{companyInfo.main_product}</span>
								</p>
							{/if}
						</div>
					</div>
				{/if}

				<!-- 연구소 정보 섹션 -->
				{#if hasLabInfo(companyInfo)}
					<div
						bind:this={labSection}
						id="lab"
						class="space-y-2 border-b border-gray-100 pb-4"
					>
						<h3 class="text-sm font-semibold text-gray-700 flex items-center gap-2">
							<Microscope size={16} class="text-indigo-500" />
							연구소 정보
						</h3>
						<div class="space-y-1">
							{#if companyInfo.lab_name}
								<p class="text-sm text-gray-600 flex items-center justify-between">
									<span>연구소명</span>
									<span>{companyInfo.lab_name}</span>
								</p>
							{/if}
							{#if companyInfo.research_field}
								<p class="text-sm text-gray-600 flex items-center justify-between">
									<span>연구분야</span>
									<span>{companyInfo.research_field}</span>
								</p>
							{/if}
							{#if companyInfo.first_approval_date}
								<p class="text-sm text-gray-600 flex items-center justify-between">
									<span>최초인정일</span>
									<span>{companyInfo.first_approval_date}</span>
								</p>
							{/if}
							{#if companyInfo.lab_location}
								<p class="text-sm text-gray-600 flex items-center justify-between">
									<span>연구소 위치</span>
									<span>{companyInfo.lab_location}</span>
								</p>
							{/if}
							{#if companyInfo.division}
								<p class="text-sm text-gray-600 flex items-center justify-between">
									<span>연구소 구분</span>
									<span>{companyInfo.division}</span>
								</p>
							{/if}
						</div>
					</div>
				{/if}

				<!-- 인증 정보 섹션 -->
				{#if hasCertificationInfo(companyInfo)}
					<div
						bind:this={certificationSection}
						id="certification"
						class="space-y-2 border-b border-gray-100 pb-4"
					>
						<h3 class="text-sm font-semibold text-gray-700 flex items-center gap-2">
							<Award size={16} class="text-purple-500" />
							인증 정보
						</h3>
						<div class="space-y-1">
							{#if companyInfo.sme_type}
								<p class="text-sm text-gray-600 flex items-center justify-between">
									<span>인증 유형</span>
									<span>{companyInfo.sme_type}</span>
								</p>
							{/if}
							{#if companyInfo.certificate_expiry_date}
								<p class="text-sm text-gray-600 flex items-center justify-between">
									<span>인증 만료일</span>
									<span>{companyInfo.certificate_expiry_date}</span>
								</p>
							{/if}
							{#if companyInfo.venture_confirmation_type}
								<p class="text-sm text-gray-600 flex items-center justify-between">
									<span>벤처기업 인증</span>
									<span>{companyInfo.venture_confirmation_type}</span>
								</p>
							{/if}
							{#if companyInfo.venture_valid_from || companyInfo.venture_valid_until || companyInfo.confirming_authority || companyInfo.new_reconfirmation_code}
								<p class="text-sm text-gray-600 flex items-center justify-between">
									<span>벤처 유효기간</span>
									<span>{companyInfo.venture_valid_from} ~ {companyInfo.venture_valid_until}</span>
								</p>
								<p class="text-sm text-gray-600 flex items-center justify-between">
									<span>확인기관</span>
									<span>{companyInfo.confirming_authority}</span>
								</p>
								<p class="text-sm text-gray-600 flex items-center justify-between">
									<span>재확인코드</span>
									<span>{companyInfo.new_reconfirmation_code}</span>
								</p>
							{/if}
						</div>
					</div>
				{/if}

				<!-- 주주 정보 섹션 -->
				{#if hasShareholderInfo(companyInfo)}
					<div
						bind:this={shareholdersSection}
						id="shareholders"
						class="space-y-2 border-b border-gray-100 pb-4"
					>
						<h3 class="text-sm font-semibold text-gray-700 flex items-center gap-2">
							<Users size={16} class="text-yellow-500" />
							주주 정보
						</h3>
						<div class="space-y-1">
							{#if companyInfo.family_shareholder_yn}
								<p class="text-sm text-gray-600 flex items-center justify-between">
									<span>가족주주</span>
									<span>{companyInfo.family_shareholder_yn === 'Y' ? '있음' : '없음'}</span>
								</p>
							{/if}
							{#if companyInfo.external_shareholder_yn}
								<p class="text-sm text-gray-600 flex items-center justify-between">
									<span>외부주주</span>
									<span>{companyInfo.external_shareholder_yn === 'Y' ? '있음' : '없음'}</span>
								</p>
							{/if}
						</div>
					</div>
				{/if}

				<script>
					let financialData = []; // 초기값 설정
					$: years = financialData && Array.isArray(financialData) 
						? [...new Set(financialData.map(d => String(d.year)))].sort().reverse()
						: [];
				</script>
				
				{#if financialData && Array.isArray(financialData) && financialData.length > 0}
				<div class="space-y-4 border-b border-gray-100 pb-4">
					<!-- 손익계산서 섹션 -->
					<div class="space-y-2">
					<h3 class="text-sm font-semibold text-gray-700 flex items-center gap-2">
						<DollarSign size={16} class="text-green-500" />
						재무분석 <div class="inline-block text-xs text-gray-500">단위: 백만원</div>
					</h3>
					
					<table class="w-full text-sm">
						<thead>
						<tr class="border-b border-gray-200">
							<th class="text-left px-2 font-medium text-gray-600 py-2">
							<div class="inline-block ext-sm font-semibold text-gray-700 flex items-center gap-2">손익계산서</div>
							</th>
							{#each years as year}
							<th class="w-1/5 text-right px-2 py-2 font-medium text-gray-600 whitespace-nowrap">
								{year}년
							</th>
							{/each}
						</tr>
						</thead>
						<tbody class="text-gray-600">
						{#each [
							{ name: '매출액', key: 'revenue' },
							{ name: '매출원가', key: 'sales_cost' },
							{ name: '매출총이익', key: 'sales_profit' },
							{ name: '판매관리비', key: 'sga' },
							{ name: '영업이익', key: 'operating_income' },
							{ name: '기타수익', key: 'other_income' },
							{ name: '기타비용', key: 'other_expenses' },
							{ name: '세전이익', key: 'pre_tax_income' },
							{ name: '법인세', key: 'corporate_tax' },
							{ name: '당기순이익', key: 'net_income' }
						] as metric}
							<tr class="border-b border-gray-100 hover:bg-gray-50">
							<td class="w-1/3 px-2 py-2 font-medium">{metric.name}</td>
							{#each years as year}
								{@const yearData = financialData.find(d => String(d.year) === year)}
								<td class="w-1/5 text-right px-2 py-2">
								{#if yearData && yearData[metric.key] != null}
									<span class={`${yearData[metric.key] < 0 ? 'text-red-500' : ''} whitespace-nowrap`}>
									{new Intl.NumberFormat('ko-KR').format(yearData[metric.key])}
									</span>
								{:else}
									-
								{/if}
								</td>
							{/each}
							</tr>
						{/each}
						</tbody>
					</table>
					</div>
				
					<!-- 재무상태표 섹션 -->
					<div class="space-y-2">
					<table class="w-full text-sm">
						<thead>
						<tr class="border-b border-gray-200">
							<th class="text-left px-2 font-medium text-gray-600 py-2">
							<div class="inline-block ext-sm font-semibold text-gray-700 flex items-center gap-2">재무상태표</div>
							</th>
							{#each years as year}
							<th class="w-1/5 text-right px-2 py-2 font-medium text-gray-600 whitespace-nowrap">
								{year}년
							</th>
							{/each}
						</tr>
						</thead>
						<tbody class="text-gray-600">
						<!-- 자산 -->
						<tr class="bg-gray-50">
							<td colspan={years.length + 1} class="px-2 py-1 font-semibold">자산</td>
						</tr>
						{#each [
							{ name: '유동자산', key: 'current_assets' },
							{ name: '• 당좌자산', key: 'quick_assets' },
							{ name: '• 재고자산', key: 'inventory' },
							{ name: '비유동자산', key: 'non_current_assets' },
							{ name: '• 투자자산', key: 'investment_assets' },
							{ name: '• 유형자산', key: 'tangible_assets' },
							{ name: '• 무형자산', key: 'intangible_assets' }
						] as metric}
							<tr class="border-b border-gray-100 hover:bg-gray-50">
							<td class="w-1/3 px-2 py-2 font-medium">{metric.name}</td>
							{#each years as year}
								{@const yearData = financialData.find(d => String(d.year) === year)}
								<td class="w-1/5 text-right px-2 py-2">
								{#if yearData && yearData[metric.key] != null}
									<span class="whitespace-nowrap">
									{new Intl.NumberFormat('ko-KR').format(yearData[metric.key])}
									</span>
								{:else}
									-
								{/if}
								</td>
							{/each}
							</tr>
						{/each}
						
						<!-- 부채와 자본 -->
						<tr class="bg-gray-50">
							<td colspan={years.length + 1} class="px-2 py-1 font-semibold">부채와 자본</td>
						</tr>
						{#each [
							{ name: '유동부채', key: 'current_liabilities' },
							{ name: '비유동부채', key: 'non_current_liabilities' },
							{ name: '자본금', key: 'capital_stock' },
							{ name: '총이익잉여금', key: 'retained_earnings' }
						] as metric}
							<tr class="border-b border-gray-100 hover:bg-gray-50">
							<td class="w-1/3 px-2 py-2 font-medium">{metric.name}</td>
							{#each years as year}
								{@const yearData = financialData.find(d => String(d.year) === year)}
								<td class="w-1/5 text-right px-2 py-2">
								{#if yearData && yearData[metric.key] != null}
									<span class="whitespace-nowrap">
									{new Intl.NumberFormat('ko-KR').format(yearData[metric.key])}
									</span>
								{:else}
									-
								{/if}
								</td>
							{/each}
							</tr>
						{/each}
						</tbody>
					</table>
					</div>
				</div>
				{/if}
			</div>
		</div>
	{:else}
		<Spinner />
	{/if}
</div>

<style>
	.company-info-wrapper {
	  position: fixed;
	  top: 70px;
	  right: 0;
	  width: 30%;
	  height: calc(100vh - 60px);
	  z-index: 40;
	  background: white;
	  box-shadow: -2px 0 5px rgba(0, 0, 0, 0.1);
	  overflow-y: auto;
	  transition: all 0.3s ease;
	  transform: translateX(100%);
	  border-left: 1px solid #e5e7eb;
	}
	
	.company-info-wrapper.active {
	  transform: translateX(0);
	}
	
	@media (max-width: 768px) {
	  .company-info-wrapper {
		width: 100%;
		border-left: none;
	  }
	  
	  .company-info-wrapper.mobile {
		top: auto;
		bottom: 0;
		height: 20vh;
		transform: translateY(100%);
	  }
	    
	  .company-info-wrapper.mobile.fullscreen {
		height: 100vh;
		border-top-left-radius: none;
		border-top-right-radius: none;
	  }

	  .company-info-wrapper.mobile.active {
		transform: translateY(0);
		border-top: 1px solid #e5e7eb;
		border-top-left-radius: 20px;
		border-top-right-radius: 20px;
	  }
	}

	
  </style>