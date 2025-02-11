<script lang="ts">
	import ChevronDown from '$lib/components/icons/ChevronDown.svelte';
	import ChevronUp from '$lib/components/icons/ChevronUp.svelte';

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

	function toggleFullscreen(smtp_id: string) {
		fullscreenStates = { ...fullscreenStates, [smtp_id]: !fullscreenStates[smtp_id] };
	}

	function closeCompanyInfo(smtp_id: string) {
		fullscreenStates = { ...fullscreenStates, [smtp_id]: false };
		onClose();
	}
</script>

<div 
	class="fixed bottom-0 bg-gray-50 shadow-lg pl-2 pt-2 rounded-t-2xl overflow-y-auto z-40 transition-all duration-300"
	class:sidebar-margin={$showSidebar}
	class:mobile-layout={$mobile}
	style="top: 50px;"
>
	<ul class="p-4 space-y-2 overflow-y-auto">
		{#each companyList as result}
			<li>
				<button 
					on:click={() => onResultClick(result)} 
					class="w-full text-left bg-white rounded-lg p-4 shadow-sm hover:bg-gray-50 transition-colors duration-200 border border-gray-200" 
					type="button"
				>
					<div class="flex items-start justify-between">
						<div class="flex-1">
							<div class="flex items-center">
								<span class="font-semibold text-gray-900">{result.company_name}</span>
								<span class="ml-1">({result.business_registration_number})</span>
								<button 
									type="button" 
									on:click|stopPropagation={() => toggleFullscreen(result.smtp_id)} 
									class="ml-2"
								>
									{#if fullscreenStates[result.smtp_id]}
										<ChevronUp size={20} strokeWidth="2.5"/>
									{:else}
										<ChevronDown size={20} strokeWidth="2.5"/>
									{/if}
								</button>
							</div>
							<div class="text-sm text-gray-600 mt-1.5">{result.address}</div>
							{#if result.representative}
								<div class="text-sm text-gray-500 mt-1">대표자: {result.representative}</div>
							{/if}
						</div>
					</div>
				</button>
			</li>
		{/each}
	</ul>
</div>

<style>
	ul {
		list-style-type: none;
		margin: 0;
		padding: 0;
	}

	.fixed {
		left: 0;
		right: 0;
	}

	.sidebar-margin {
		left: 260px;
	}

	.mobile-layout {
		border-top-left-radius: 20px;
		border-top-right-radius: 20px;
	}
</style>
