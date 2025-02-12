<!-- companyList.svelte -->
<script lang="ts">
	import { slide } from 'svelte/transition';
	import ChevronDown from '$lib/components/icons/ChevronDown.svelte';
	import ChevronUp from '$lib/components/icons/ChevronUp.svelte';
	import CompanyDetail from '../corpinfo/CompanyDetail.svelte';

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

	let filters = {
		keyword: '',
		minEmployees: null as number | null,
		industry: '',
		radius: 'near',
		establishmentFrom: '',
		establishmentTo: '',
		smeType: '',
		labName: '',
	};

	$: filteredCompanies = companyList.filter(company => {
		let pass = true;
		if (filters.keyword) {
			const keyword = filters.keyword.toLowerCase();
			pass = pass && (
				company.company_name.toLowerCase().includes(keyword) ||
				company.address.toLowerCase().includes(keyword) ||
				company.business_registration_number.toLowerCase().includes(keyword) ||
				(company.representative && company.representative.toLowerCase().includes(keyword))
			);
		}
		
		if (filters.minEmployees !== null) {
			pass = pass && (company.employee_count !== undefined && company.employee_count >= filters.minEmployees);
		}
		
		if (filters.industry) {
			pass = pass && (company.industry && company.industry.toLowerCase().includes(filters.industry.toLowerCase()));
		}
		
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
		
		if (filters.smeType) {
			pass = pass && (company.sme_type && company.sme_type.toLowerCase().includes(filters.smeType.toLowerCase()));
		}
		if (filters.labName) {
			pass = pass && (
				(company.lab_name && company.lab_name.toLowerCase().includes(filters.labName.toLowerCase())) ||
				(company.research_field && company.research_field.toLowerCase().includes(filters.labName.toLowerCase()))
			);
		}
		
		return pass;
	});

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

<div class="company-list-wrapper fixed bottom-0 left-0 right-0 top-[50px] bg-gray-50 shadow-lg rounded-t-2xl transition-all duration-300"
	 class:sidebar-margin={$showSidebar}
	 class:mobile-layout={$mobile}>
	<div class="p-4 bg-gray-80 border-gray-300 flex flex-wrap items-center gap-2">
		<input type="text" placeholder="키워드" bind:value={filters.keyword} class="filter-input" />
		<input type="number" placeholder="임직원 수 (몇 명 이상)" bind:value={filters.minEmployees} class="filter-input" />
		<input type="text" placeholder="업종" bind:value={filters.industry} class="filter-input" />
		<select bind:value={filters.radius} class="filter-input">
			<option value="near">가까운거리</option>
			<option value="far">먼거리</option>
		</select>
		<input type="text" placeholder="인증/유형" bind:value={filters.smeType} class="filter-input" />
		<input type="text" placeholder="연구소명/분야" bind:value={filters.labName} class="filter-input" />
	</div>
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

	.sidebar-margin {
		left: 260px;
	}

	.mobile-layout {
		border-top-left-radius: 20px;
		border-top-right-radius: 20px;
	}
	
	.filter-input {
		width: 140px;
		padding: 0.2rem;
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
