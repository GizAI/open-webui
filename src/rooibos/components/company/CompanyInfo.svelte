<!-- CompanyInfo.svelte -->
<script lang="ts">
	import Spinner from '$lib/components/common/Spinner.svelte';
	import ActionButtons from '../common/ActionButtons.svelte';
	import CompanyDetail from './CompanyDetail.svelte';
	import { mobile } from '$lib/stores';

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
		master_id: string;
		latitude: string;
		longitude: string;
		bookmark_id?: string;
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
		venture_confirmation_type?: string;
		svcl_region?: string;
		venture_valid_from?: string;
		venture_valid_until?: string;
		confirming_authority?: string;
		new_reconfirmation_code?: string;
		postal_code?: string;
	}

	export let isFullscreen = false;
	export let onClose: () => void;
	export let companyInfo: any = {};

	let startY = 0;
	let dragOffset = 0;
	let isDragging = false;
	let financialData: any = {};

	function toggleFullscreen() {
		isFullscreen = !isFullscreen;
	}

	function closeCompanyInfo() {
		isFullscreen = false;
		onClose();
	}

	function isIPadMini() {
		// iPad Mini 감지 (약 768 x 1024, iPad Mini 6 기준)
		const userAgent = navigator.userAgent.toLowerCase();
		const isIPad = /ipad/.test(userAgent);
		const isTablet = isIPad || 
			(/tablet/.test(userAgent) && !/android/.test(userAgent)) || 
			((/iphone|ipod/.test(userAgent) || /android/.test(userAgent)) && 
			window.innerWidth >= 750 && window.innerWidth <= 850);

		// iPad Mini의 화면 크기를 고려 (가로/세로 모두 지원)
		return isTablet && 
			((window.innerWidth >= 750 && window.innerWidth <= 850) || 
			(window.innerHeight >= 750 && window.innerHeight <= 850));
	}

	$: mobileHeight = (() => {
		if (!$mobile) return '';

		const fullHeight = `calc(100vh - env(safe-area-inset-top) - env(safe-area-inset-bottom))`;
		const initialHeight = `calc(20vh + env(safe-area-inset-top))`;

		if (isDragging) {
			if (!isFullscreen && dragOffset < 0) {
				return `calc(20vh + env(safe-area-inset-top) + ${-dragOffset}px)`;
			} else if (isFullscreen && dragOffset > 0) {
				return `calc(${fullHeight} - ${dragOffset}px)`;
			}
		}
		return isFullscreen ? fullHeight : initialHeight;
	})();
</script>

<div
	class="company-info-wrapper active {isFullscreen ? 'fullscreen' : ''} {isIPadMini() ? 'ipad-mini' : ''} flex flex-col w-full bg-gray-50 text-gray-900 dark:bg-gray-950 dark:text-white-200"
	class:mobile={$mobile}
	style={$mobile
		? isFullscreen
			? `height: ${mobileHeight}; transition: ${isDragging ? 'none' : 'height 0.3s ease'}; top: env(safe-area-inset-top); bottom: auto;`
			: `height: ${mobileHeight}; transition: ${isDragging ? 'none' : 'height 0.3s ease'}; top: auto; bottom: 0;`
		: isIPadMini()
			? 'height: 100vh; top: 0; bottom: auto;'
			: 'margin-top: 1rem;'}
>
	{#if companyInfo}
		<div
			class="header-container sticky z-10 shrink-0 px-4 pt-3 pb-2 border-b border-gray-200 bg-white text-gray-900 dark:bg-gray-950 dark:text-gray-200"
			style="top: {$mobile && isFullscreen ? 'env(safe-area-inset-top)' : '0'};"
		>
			<div class="flex items-center justify-between w-full mb-1">
				<h1
					class="{$mobile || isIPadMini()
						? 'sm:text-xl'
						: 'text-xl'} font-semibold mb-1 mt-1 truncate text-gray-900 dark:text-gray-200"
				>
					{companyInfo.company_name}
				</h1>

				<div class="flex items-center space-x-1 text-gray-900 dark:text-white-200">
					<ActionButtons {companyInfo} {financialData} type="companyinfo" />
					{#if !$mobile && !isIPadMini()}
						<button
							class="hover:bg-gray-100 dark:hover:bg-gray-800 rounded-full"
							on:click={closeCompanyInfo}
						>
							<svg
								xmlns="http://www.w3.org/2000/svg"
								class="h-5 w-5 text-gray-500"
								fill="none"
								viewBox="0 0 24 24"
								stroke="currentColor"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M6 18L18 6M6 6l12 12"
								/>
							</svg>
						</button>
					{:else}
						<button
							class="hover:bg-gray-100 dark:hover:bg-gray-800 rounded-full"
							on:click={isFullscreen || isIPadMini() ? closeCompanyInfo : toggleFullscreen}
						>
							<svg
								xmlns="http://www.w3.org/2000/svg"
								class="h-5 w-5 text-gray-500"
								fill="none"
								viewBox="0 0 24 24"
								stroke="currentColor"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d={isFullscreen || isIPadMini() ? 'M6 18L18 6M6 6l12 12' : 'M5 15l7-7 7 7'}
								/>
							</svg>
						</button>
					{/if}
				</div>
			</div>
		</div>

		<!-- 기업 상세 내용 -->
		<div class="flex-1 px-4 pb-4 bg-white text-gray-900 dark:bg-gray-950 dark:text-white-200">
			<CompanyDetail company={companyInfo} bind:financialData />
		</div>
	{:else}
		<Spinner />
	{/if}
</div>

<style>
	.company-info-wrapper {
		position: fixed;
		top: 80px;
		right: 0;
		width: 30%;
		height: calc(100vh - 80px);
		z-index: 49;
		box-shadow: -2px 0 5px rgba(0, 0, 0, 0.1);
		overflow-y: auto;
		transition: all 0.3s ease;
		transform: translateX(100%);
		background-color: white;
		border-left: 1px solid #e5e7eb;
	}

	.company-info-wrapper.active {
		transform: translateX(0);
	}

	/* 아이패드 미니 전용 스타일 */
	.company-info-wrapper.ipad-mini {
		width: 100%;
		top: 0;
		left: 0;
		right: 0;
		height: 100vh;
		z-index: 60;
		border-left: none;
	}

	/* 태블릿(아이패드 미니 제외) 대응 */
	@media (min-width: 769px) and (max-width: 1024px) {
		.company-info-wrapper:not(.ipad-mini) {
			width: 50%;
		}
	}

	@media (max-width: 768px) {
		.company-info-wrapper:not(.ipad-mini) {
			width: 100%;
			border-left: none;
		}

		.company-info-wrapper.mobile:not(.ipad-mini) {
			top: auto;
			bottom: 0;
			height: 20vh;
			transform: translateY(100%);
			transform-origin: bottom;
			margin-top: 0;
			z-index: 60;
		}

		.company-info-wrapper.mobile.fullscreen:not(.ipad-mini) {
			top: env(safe-area-inset-top);
			bottom: auto;
			height: calc(100vh - env(safe-area-inset-top) - env(safe-area-inset-bottom));
			padding-bottom: env(safe-area-inset-bottom);
			transform-origin: bottom;
			z-index: 60;
		}

		.company-info-wrapper.mobile.fullscreen.active:not(.ipad-mini) {
			border-top-left-radius: 0;
			border-top-right-radius: 0;
		}

		.company-info-wrapper.mobile.active:not(.ipad-mini) {
			transform: translateY(0);
			border-top: 1px solid #e5e7eb;
			border-top-left-radius: 20px;
			border-top-right-radius: 20px;
		}

		.company-info-wrapper.mobile.fullscreen:not(.ipad-mini) .header-container {
			top: 0 !important;
		}
	}

	.drag-handle {
		width: 100%;
		display: flex;
		justify-content: center;
		padding: 8px 0;
		touch-action: none;
	}
	.drag-handle .handle-bar {
		width: 40px;
		height: 6px;
		background-color: #ccc;
		border-radius: 2px;
	}
</style>
