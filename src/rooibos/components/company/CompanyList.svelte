<!-- companyList.svelte -->
<script lang="ts">
	import { slide } from 'svelte/transition';
	import ChevronDown from '$lib/components/icons/ChevronDown.svelte';
	import ChevronUp from '$lib/components/icons/ChevronUp.svelte';
	import CompanyDetail from '../company/CompanyDetail.svelte';

	interface SearchResult {
		master_id: string;
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
		sme_type?: {sme_type: string, certificate_expiry_date: string}[];
		research_info?: {lab_name: string, lab_location: string, first_approval_date: string, research_field: string; division: string }[];
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
	}

	import { showSidebar, mobile } from '$lib/stores';
	import ActionButtons from '../common/ActionButtons.svelte';
	import { formatBusinessNumber, formatDateForCompany, formatDistance } from '../common/helper';
	export let companyList: SearchResult[] = [];

	let fullscreenStates: Record<string, boolean> = {};

	let filters = {
		keyword: '',
		industry: '',
		radius: 'near',
		sortBy: 'distanceAscending',
		smeType: false,
		labName: false
	};

	$: filteredCompanies = companyList.filter((company) => {
		let pass: boolean = true;
		if (filters.keyword) {
			const keyword = filters.keyword.toLowerCase();
			pass =
				pass &&
				(company.company_name.toLowerCase().includes(keyword) ||
					(company.address && company.address.toLowerCase().includes(keyword)) ||
					(company.business_registration_number &&
						company.business_registration_number.toLowerCase().includes(keyword)) ||
					(company.representative && company.representative.toLowerCase().includes(keyword)));
		}

		if (filters.industry) {
			pass =
				pass &&
				company.industry &&
				company.industry.toLowerCase().includes(filters.industry.toLowerCase());
		}

		if (filters.smeType) {
			pass =
				pass &&
				(Boolean(company.venture_confirmation_type) ||
					Boolean(company.confirming_authority) ||
					Boolean(company.venture_valid_from));
		}
		if (filters.labName) {
			pass =
				pass &&
				(Boolean(company.research_info) );
		}

		return pass;
	});

	$: sortedCompanies = [...filteredCompanies].sort((a, b) => {
		switch (filters.sortBy) {
			case 'distanceAscending':
				return (a.distance_from_user ?? 0) - (b.distance_from_user ?? 0);
			case 'distanceDescending':
				return (b.distance_from_user ?? 0) - (a.distance_from_user ?? 0);
			case 'nameAscending':
				return a.company_name.localeCompare(b.company_name);
			case 'nameDescending':
				return b.company_name.localeCompare(a.company_name);
			case 'establishmentDateAscending':
				return (Number(a.establishment_date) || 0) - (Number(b.establishment_date) || 0);
			case 'establishmentDateDescending':
				return (Number(b.establishment_date) || 0) - (Number(a.establishment_date) || 0);
			case 'salesAmountAscending':
				return (a.sales_amount ?? 0) - (b.sales_amount ?? 0);
			case 'salesAmountDescending':
				return (b.sales_amount ?? 0) - (a.sales_amount ?? 0);
			case 'employeeCountAscending':
				return (a.employee_count ?? 0) - (b.employee_count ?? 0);
			case 'employeeCountDescending':
				return (b.employee_count ?? 0) - (a.employee_count ?? 0);
			case 'totalAssetsAscending':
				return (a.recent_total_assets ?? 0) - (b.recent_total_assets ?? 0);
			case 'totalAssetsDescending':
				return (b.recent_total_assets ?? 0) - (a.recent_total_assets ?? 0);
			case 'totalEquityAscending':
				return (a.recent_total_equity ?? 0) - (b.recent_total_equity ?? 0);
			case 'totalEquityDescending':
				return (b.recent_total_equity ?? 0) - (a.recent_total_equity ?? 0);
			default:
				return 0;
		}
	});

	function toggleFullscreen(master_id: string) {
		if (fullscreenStates[master_id]) {
			fullscreenStates = { ...fullscreenStates, [master_id]: false };
		} else {
			fullscreenStates = { [master_id]: true };
		}
	}

	function closeCompanyInfo(master_id: string) {
		fullscreenStates = { ...fullscreenStates, [master_id]: false };
	}
</script>

<div
	class="company-list-wrapper fixed bottom-0 left-0 right-0 top-[50px] bg-gray-50 text-gray-900 dark:bg-gray-950 dark:text-white-200 shadow-lg rounded-t-2xl transition-all duration-300"
	class:sidebar-margin={$showSidebar}
	class:mobile-layout={$mobile}
>
	<div
		class="p-4 pb-0 bg-gray-50 text-gray-900 dark:bg-gray-950 dark:text-white-200 border-gray-300 flex flex-wrap items-center gap-2"
	>
		<select
			bind:value={filters.sortBy}
			class="filter-input bg-gray-50 dark:bg-gray-950 text-gray-900 dark:text-gray-200"
		>
			<option value="distanceAscending">거리 (가까운 순)</option>
			<option value="distanceDescending">거리 (먼 순)</option>
			<option value="nameAscending">회사명 (오름차순)</option>
			<option value="nameDescending">회사명 (내림차순)</option>
			<option value="establishmentDateAscending">설립연도 (오래된 순)</option>
			<option value="establishmentDateDescending">설립연도 (최신 순)</option>
			<option value="employeeCountAscending">직원 수 (적은 순)</option>
			<option value="employeeCountDescending">직원 수 (많은 순)</option>
			<option value="totalAssetsAscending">총자산 (적은 순)</option>
			<option value="totalAssetsDescending">총자산 (많은 순)</option>
			<option value="totalEquityAscending">총자본 (적은 순)</option>
			<option value="totalEquityDescending">총자본 (많은 순)</option>
		</select>
		<input
			type="text"
			placeholder="키워드"
			bind:value={filters.keyword}
			class="filter-input bg-gray-50 dark:bg-gray-950 text-gray-900 dark:text-gray-200"
		/>
		<input
			type="text"
			placeholder="업종"
			bind:value={filters.industry}
			class="filter-input bg-gray-50 dark:bg-gray-950 text-gray-900 dark:text-gray-200"
		/>
		<label class="text-gray-900 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800">
			<input
				type="checkbox"
				bind:checked={filters.smeType}
				class="text-gray-900 dark:text-gray-200"
			/>
			벤처인증
		</label>
		<label class="text-gray-900 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800">
			<input
				type="checkbox"
				bind:checked={filters.labName}
				class="text-gray-900 dark:text-gray-200"
			/>
			연구소
		</label>
	</div>
	<div class="list-container flex-1 overflow-y-auto">
		<ul class="pt-2 p-4 space-y-2">
			{#each sortedCompanies as result}
				<li>
					<div
						class="bg-gray-50 text-gray-900 dark:bg-gray-950 dark:text-white-200 rounded-lg shadow-sm border border-gray-200 overflow-hidden"
					>
						<div
							role="button"
							tabindex="0"
							on:click={() => toggleFullscreen(result.master_id)}
							on:keydown={(e) => {
								if (e.key === 'Enter' || e.key === ' ') {
									e.preventDefault();
									toggleFullscreen(result.master_id);
								}
							}}
							class="w-full text-left p-4 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors duration-200"
						>
							<div class="flex items-center justify-between">
								<div class="flex items-center">
									<span class="font-semibold text-gray-900 dark:text-gray-200"
										>{result.company_name}</span
									>
									{#if !$mobile}
										<span class="ml-1 text-gray-900 dark:text-gray-200"
											>({formatBusinessNumber(result.business_registration_number)})</span
										>
									{/if}
									<button
										type="button"
										on:click|stopPropagation={() => toggleFullscreen(result.master_id)}
										class="ml-2 text-gray-900 dark:text-gray-200"
									>
										{#if fullscreenStates[result.master_id]}
											<ChevronUp strokeWidth="2.5" className="w-5 h-5" />
										{:else}
											<ChevronDown strokeWidth="2.5" className="w-5 h-5" />
										{/if}
									</button>
								</div>
								{#if fullscreenStates[result.master_id]}
									<div
										role="button"
										tabindex="0"
										on:click|stopPropagation
										on:keydown={(e) => {
											if (e.key === 'Enter' || e.key === ' ') {
												e.preventDefault();
											}
										}}
									>
										<ActionButtons companyInfo={result} type="companylist" />
									</div>
								{/if}
							</div>
							{#if result.address && !fullscreenStates[result.master_id]}
								<div class="text-sm text-gray-600 mt-1.5">{result.address}</div>
							{/if}
							{#if result.representative && !fullscreenStates[result.master_id]}
								<div class="text-sm text-gray-500 mt-1">
									대표자: {result.representative ?? '정보없음'} | 설립연도: {formatDateForCompany(
										result.establishment_date
									)} | 직원수: {result.employee_count ?? '정보없음'}
								</div>
							{/if}
						</div>

						{#if fullscreenStates[result.master_id]}
							<div transition:slide class="border-t border-gray-200">
								<div class="detail-scroll-container">
									<CompanyDetail company={result} />
								</div>
							</div>
						{/if}
					</div>
				</li>
			{/each}
		</ul>
	</div>
</div>

<style>
	.detail-scroll-container {
		max-height: 400px;
		overflow-y: auto;
	}
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
