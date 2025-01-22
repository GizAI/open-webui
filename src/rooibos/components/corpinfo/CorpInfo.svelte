<script lang="ts">
	import { onMount } from 'svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import { Briefcase, MapPin, Users, Phone, Globe, Calendar, DollarSign, List, Award, Building2, FlaskConical, CalendarCheck, Microscope, ClipboardList } from 'lucide-svelte';

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
		longitude: '',
	};
	
	let financialData: FinancialData | null = null;

	onMount(async () => {
		
	});

	const metrics = [
		{ name: '매출액', key: 'revenue' },
		{ name: '당기순이익', key: 'net_income' },
		{ name: '영업이익', key: 'operating_income' },
		{ name: '총자산', key: 'total_assets' },
		{ name: '총부채', key: 'total_liabilities' },
		{ name: '총자본', key: 'total_equity' },
		{ name: '자본금', key: 'capital_stock' },
		{ name: '법인세', key: 'corporate_tax' },
		{ name: '유동자산', key: 'current_assets' },
		{ name: '당좌자산', key: 'quick_assets' },
		{ name: '재고자산', key: 'inventory' },
		{ name: '비유동자산', key: 'non_current_assets' },
		{ name: '투자자산', key: 'investment_assets' },
		{ name: '유형자산', key: 'tangible_assets' },
		{ name: '무형자산', key: 'intangible_assets' },
		{ name: '유동부채', key: 'current_liabilities' },
		{ name: '비유동부채', key: 'non_current_liabilities' },
		{ name: '이익잉여금', key: 'retained_earnings' },
		{ name: '이익', key: 'profit' },
		{ name: '매출원가', key: 'sales_cost' },
		{ name: '매출총이익', key: 'sales_profit' },
		{ name: '판매관리비', key: 'sga' },
		{ name: '기타수익', key: 'other_income' },
		{ name: '기타비용', key: 'other_expenses' },
		{ name: '세전이익', key: 'pre_tax_income' }
	];

	const years = ['2023', '2022', '2021'];
	let showAllMetrics = false;

	let selectedSection: string | null = null;
  let sectionRefs: { [key: string]: HTMLElement } = {};

	const sections = [
		{ id: 'basic', title: '기본', icon: MapPin },
		{ id: 'industry', title: '업종', icon: Briefcase },
		{ id: 'shareholders', title: '주주', icon: Users },
		{ id: 'lab', title: '연구소', icon: Microscope },
		{ id: 'certification', title: '인증', icon: Award },
		{ id: 'financial', title: '재무', icon: DollarSign },
	];

	const scrollToSection = (sectionId: string) => {
		selectedSection = sectionId;
		const element = sectionRefs[sectionId];
		if (element) {
		element.scrollIntoView({ behavior: 'smooth' });
		}
	};
	
</script>

<div class="flex flex-col w-full translate-y-1 bg-gray-50" >
	{#if companyInfo}		
		<div class="w-full mb-2.5">
			<div class="flex flex-col w-full px-6 py-4 overflow-y-auto space-y-6">
				<div class="flex items-center justify-between w-full px-0.5 mb-1">
					<h1 class="text-2xl font-semibold">{companyInfo.company_name}</h1>
					<button class="p-2 hover:bg-gray-100 rounded-full"
						on:click={onClose}>
						<svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
						</svg>
					</button>
				</div>
				<hr class="border-t border-gray-100">  

				<!-- 섹션 네비게이션 -->
				<div class="flex overflow-x-auto">
				{#each sections as section}
					<button
					class="flex items-center px-2 rounded-full text-sm whitespace-nowrap
						{selectedSection === section.id ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-600'}
						hover:bg-gray-200"
					on:click={() => scrollToSection(section.id)}
					>
					{section.title}
					</button>
				{/each}
				</div>
				<hr class="border-t border-gray-100">

			  <!-- 기본 정보 섹션 -->
			  <div class="space-y-2">
				<h3 class="text-sm font-semibold text-gray-700 flex items-center gap-2">
				  <MapPin size={16} class="text-blue-500" />
				  기본 정보
				</h3>
				<div class="space-y-1">
				  {#if companyInfo.business_registration_number}
					<p class="text-sm text-gray-600 flex items-center gap-2">
					  <Briefcase size={16} class="text-green-500" />
					  사업자 등록 번호: {companyInfo.business_registration_number}
					</p>
				  {/if}				  {#if companyInfo.corporate_number}
					<p class="text-sm text-gray-600 flex items-center gap-2">
						<Briefcase size={16} class="text-orange-500" />
						법인등록번호: {companyInfo.corporate_number}
					</p>
				  {/if}
			
				  {#if companyInfo.representative}
					<p class="text-sm text-gray-600 flex items-center gap-2">
					  <Users size={16} class="text-purple-500" />
					  대표이사: {companyInfo.representative}
					  {#if companyInfo.birth_year}
						({companyInfo.birth_year})
					  {/if}
					</p>
				  {/if}
			
				  {#if companyInfo.address}
					<p class="text-sm text-gray-600 flex items-center gap-2">
					  <MapPin size={16} class="text-red-500" />
					  주소: {companyInfo.address}
					</p>
				  {/if}

				  {#if companyInfo.cri_company_size}
					<p class="text-sm text-gray-600 flex items-center gap-2">
					  <Phone size={16} class="text-indigo-500" />
					  기업규모: {companyInfo.cri_company_size}
					</p>
				  {/if}
			
				  {#if companyInfo.phone_number}
					<p class="text-sm text-gray-600 flex items-center gap-2">
					  <Phone size={16} class="text-indigo-500" />
					  전화번호: {companyInfo.phone_number}
					</p>
				  {/if}

				  {#if companyInfo.establishment_date}
					<p class="text-sm text-gray-600 flex items-center gap-2">
					  <Calendar size={16} class="text-pink-500" />
					  설립일: {String(companyInfo.establishment_date).replace(/(\d{4})(\d{2})(\d{2})/, '$1-$2-$3')}
					</p>
				  {/if}
			
				  {#if companyInfo.employee_count}
					<p class="text-sm text-gray-600 flex items-center gap-2">
					  <Users size={16} class="text-purple-500" />
					  임직원 수: {companyInfo.employee_count}명
					</p>
				  {/if}

				  {#if companyInfo.fiscal_month}
					<p class="text-sm text-gray-600 flex items-center gap-2">
						<Calendar size={16} class="text-purple-500" />
						결산월: {companyInfo.fiscal_month}월
					</p>
				  {/if}
				  {#if companyInfo.main_bank}
					<p class="text-sm text-gray-600 flex items-center gap-2">
						<DollarSign size={16} class="text-green-500" />
						주거래은행: {companyInfo.main_bank}
					</p>
				  {/if}	
			
				  {#if companyInfo.website}
					<p class="text-sm text-gray-600 flex items-center gap-2">
					  <Globe size={16} class="text-yellow-500" />
					  웹사이트:
					  <a
						href={
						  companyInfo.website.startsWith("http")
							? companyInfo.website
							: `https://${companyInfo.website}`
						}
						target="_blank"
						rel="noopener noreferrer"
						class="text-blue-500 underline"
					  >
						{companyInfo.website.startsWith("http")
						  ? companyInfo.website
						  : `https://${companyInfo.website}`}
					  </a>
					</p>
				  {/if}
				</div>
			  </div>
			
			  <!-- 업종 정보 섹션 -->
			  {#if companyInfo.industry}
				<div class="space-y-2">
				  <h3 class="text-sm font-semibold text-gray-700 flex items-center gap-2">
					<Briefcase size={16} class="text-blue-500" />
					업종 정보
				  </h3>
				  {#if companyInfo.industry_major}
					<p class="text-sm text-gray-600">업종: {companyInfo.industry}</p>
				  {/if}
				  {#if companyInfo.main_product}
					<p class="text-sm text-gray-600">주요상품: {companyInfo.main_product}</p>
				  {/if}
				</div>
			  {/if}

			  {#if companyInfo.family_shareholder_yn || companyInfo.external_shareholder_yn}
				<div class="space-y-2">
					<h3 class="text-sm font-semibold text-gray-700 flex items-center gap-2">
					<Users size={16} class="text-yellow-500" />
					주주 정보
					</h3>
					<div class="space-y-1">
					{#if companyInfo.family_shareholder_yn}
						<p class="text-sm text-gray-600 flex items-center gap-2">
						<Users size={16} class="text-purple-500" />
						가족주주: {companyInfo.family_shareholder_yn === 'Y' ? '있음' : '없음'}
						</p>
					{/if}
					{#if companyInfo.external_shareholder_yn}
						<p class="text-sm text-gray-600 flex items-center gap-2">
						<Users size={16} class="text-blue-500" />
						외부주주: {companyInfo.external_shareholder_yn === 'Y' ? '있음' : '없음'}
						</p>
					{/if}
					</div>
				</div>
				{/if}

			  <!-- 연구소 정보 섹션 추가 -->
			  {#if companyInfo.lab_name || companyInfo.research_field || companyInfo.division}
				<div class="space-y-2">
					<h3 class="text-sm font-semibold text-gray-700 flex items-center gap-2">
					<Microscope size={16} class="text-indigo-500" />
					연구소 정보
					</h3>
					<div class="space-y-1">
					{#if companyInfo.lab_name}
						<p class="text-sm text-gray-600 flex items-center gap-2">
						<Building2 size={16} class="text-blue-500" />
						연구소명: {companyInfo.lab_name}
						</p>
					{/if}
					{#if companyInfo.research_field}
						<p class="text-sm text-gray-600 flex items-center gap-2">
						<FlaskConical size={16} class="text-green-500" />
						연구분야: {companyInfo.research_field}
						</p>
					{/if}
					{#if companyInfo.first_approval_date}
						<p class="text-sm text-gray-600 flex items-center gap-2">
						<CalendarCheck size={16} class="text-orange-500" />
						최초인정일: {companyInfo.first_approval_date}
						</p>
					{/if}
					{#if companyInfo.lab_location}
						<p class="text-sm text-gray-600 flex items-center gap-2">
						<MapPin size={16} class="text-red-500" />
						연구소 위치: {companyInfo.lab_location}
						</p>
					{/if}
					{#if companyInfo.division}
						<p class="text-sm text-gray-600 flex items-center gap-2">
						<ClipboardList size={16} class="text-purple-500" />
						연구소 구분: {companyInfo.division}
						</p>
					{/if}
					</div>
				</div>
				{/if}


			  <!-- 인증 정보 섹션 -->
			  {#if companyInfo.venture_confirmation_type || companyInfo.research_field}
              <div class="space-y-2">
                <h3 class="text-sm font-semibold text-gray-700 flex items-center gap-2">
                  <Award size={16} class="text-purple-500" />
                  인증 정보
                </h3>
                <div class="space-y-1">
                  {#if companyInfo.sme_type}
                    <p class="text-sm text-gray-600 flex items-center gap-2">
                      <Award size={16} class="text-yellow-500" />
                      인증 유형: {companyInfo.sme_type}
                    </p>
                  {/if}

                  {#if companyInfo.certificate_expiry_date}
                    <p class="text-sm text-gray-600 flex items-center gap-2">
                      <Calendar size={16} class="text-orange-500" />
                      인증 만료일: {companyInfo.certificate_expiry_date}
                    </p>
                  {/if}

				  {#if companyInfo.venture_confirmation_type}
                    <p class="text-sm text-gray-600 flex items-center gap-2">
                      <Award size={16} class="text-green-500" />
                      벤처기업 인증: {companyInfo.venture_confirmation_type}
                    </p>
                  {/if}

				  {#if companyInfo.venture_valid_from || companyInfo.venture_valid_until || companyInfo.confirming_authority || companyInfo.new_reconfirmation_code}
					<p class="text-sm text-gray-600 flex items-center gap-2">
						<CalendarCheck size={16} class="text-blue-500" />
						벤처 유효기간: {companyInfo.venture_valid_from} ~ {companyInfo.venture_valid_until}
					</p>
					<p class="text-sm text-gray-600 flex items-center gap-2">
						<Building2 size={16} class="text-indigo-500" />
						확인기관: {companyInfo.confirming_authority}
					</p>
					<p class="text-sm text-gray-600 flex items-center gap-2">
						<List size={16} class="text-emerald-500" />
						재확인코드: {companyInfo.new_reconfirmation_code}
					</p>
					{/if}
                	</div>
				</div>
				{/if}
			</div>
			  
			{#if financialData && Array.isArray(financialData) && financialData.length > 0}
			<div class="px-4 py-4 w-full">
				<table class="w-full text-sm">
					<thead>
					<tr class="border-b border-gray-200">
						<th class="sm:block text-left px-2 font-medium text-gray-600">
						<div class="sm:inline-block">재무정보</div>
						<div class="sm:inline-block sm:ml-2 text-xs text-gray-500">단위: 백만원</div>
						<button
							class="mt-1 sm:mt-0 sm:ml-2 inline-flex items-center px-2 py-1 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 text-xs"
							on:click={() => (showAllMetrics = !showAllMetrics)}
						>
							{#if showAllMetrics} 접기 {:else} 더보기 {/if}
						</button>
						</th>
						{#each years as year}
						<th class="w-1/5 text-right px-2 py-2 font-medium text-gray-600 whitespace-nowrap">
							{year}년
						</th>
						{/each}
					</tr>
					</thead>
					<tbody class="text-gray-600">
					{#if showAllMetrics}
						{#each metrics as metric}
						<tr class="border-b border-gray-100 hover:bg-gray-50">
							<td class="w-1/3 px-2 py-2 font-medium">{metric.name}</td>
							{#each years as year}
							{@const data = financialData.find(d => d.year == year)}
							<td class="w-1/5 text-right px-2 py-2">
								{#if data && data[metric.key] != null}
								<span class={`${data[metric.key] < 0 ? 'text-red-500' : ''} whitespace-nowrap`}>
									{new Intl.NumberFormat('ko-KR').format(data[metric.key])}
								</span>
								{:else}
								-
								{/if}
							</td>
							{/each}
						</tr>
						{/each}
					{:else}
						{#each metrics.slice(0, 7) as metric}
						<tr class="border-b border-gray-100 hover:bg-gray-50">
							<td class="w-1/3 px-2 py-2 font-medium">{metric.name}</td>
							{#each years as year}
							{@const data = financialData.find(d => d.year == year)}
							<td class="w-1/5 text-right px-2 py-2">
								{#if data && data[metric.key] != null}
								<span class={`${data[metric.key] < 0 ? 'text-red-500' : ''} whitespace-nowrap`}>
									{new Intl.NumberFormat('ko-KR').format(data[metric.key])}
								</span>
								{:else}
								-
								{/if}
							</td>
							{/each}
						</tr>
						{/each}
					{/if}
					</tbody>
				</table>
			</div>
			{/if}
		</div>
	{:else}
		<Spinner />
	{/if}
</div>
