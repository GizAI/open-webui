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

	export let isFullscreen = false;
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

	let startY = 0;
	let dragOffset = 0;
	let isDragging = false;

	function handleTouchStart(e: TouchEvent) {
		// 풀스크린 상태에서는 드래그 제스처 비활성
		if (isFullscreen) return;
		startY = e.touches[0].clientY;
		isDragging = true;
	}

	function handleTouchMove(e: TouchEvent) {
		if (isFullscreen || !isDragging) return;
		const currentY = e.touches[0].clientY;
		dragOffset = currentY - startY;
	}

	function handleTouchEnd(e: TouchEvent) {
		if (isFullscreen) return;
		isDragging = false;
		const threshold = 50;
		if (dragOffset > threshold) {
			// 아래로 드래그가 threshold 이상일 때
			if (isFullscreen) {
				isFullscreen = false;
			} else {
				// closeCompanyInfo(); // 필요시 사용
			}
		} else if (dragOffset < -threshold) {
			// 위로 드래그가 threshold 이상일 때
			isFullscreen = true;
		}
		dragOffset = 0;
	}

	function toggleFullscreen() {
		isFullscreen = !isFullscreen;
	}

	function closeCompanyInfo() {
		isFullscreen = false;
		onClose();
	}

	// 모바일에서 높이를 계산하는 로직
	$: mobileHeight = (() => {
		if (!$mobile) return '';

		// 주소창 영역에 가리지 않도록 상단/하단 safe area 모두 반영
		const fullHeight = `calc(100vh - env(safe-area-inset-top) - env(safe-area-inset-bottom))`;
		const initialHeight = `20vh`;

		if (isDragging) {
			// 드래그 중 높이 실시간 변경
			if (!isFullscreen && dragOffset < 0) {
				return `calc(20vh + ${-dragOffset}px)`;
			} else if (isFullscreen && dragOffset > 0) {
				return `calc(${fullHeight} - ${dragOffset}px)`;
			}
		}
		// 풀스크린 여부에 따라 높이 결정
		return isFullscreen ? fullHeight : initialHeight;
	})();
</script>

<!--
  Wrapper가 mobile + active + fullscreen이 되면
  화면 전체를 덮으면서도 safe-area를 고려하여
  주소창 영역에 가려지지 않도록 함
-->
<div
	class="company-info-wrapper active {isFullscreen ? 'fullscreen' : ''} flex flex-col w-full bg-gray-50 text-gray-900 dark:bg-gray-950 dark:text-white-200"
	class:mobile={$mobile}
	style={$mobile
		? (isFullscreen
			? `height: ${mobileHeight}; transition: ${isDragging ? 'none' : 'height 0.3s ease'}; top: auto; bottom: env(safe-area-inset-bottom);`
			: `height: ${mobileHeight}; transition: ${isDragging ? 'none' : 'height 0.3s ease'}; top: auto; bottom: 0;`
		  )
		: 'margin-top: 1rem;'
	}
>
	<!-- 풀스크린 모드에서는 safe-area-spacer 사용 X (중복 적용 방지) -->
	{#if $mobile && isFullscreen}
		<!-- 필요하다면 spacer 높이를 0으로 처리
		     <div class="safe-area-spacer" style="height: 0;"></div>
		-->
	{/if}

	{#if companyInfo}
		<!-- 헤더 영역 -->
		<!-- sticky header 에서 top 값을 0 대신, fullscreen 모드에서는 env(safe-area-inset-top) 적용 -->
		<div 
  class="header-container sticky z-10 shrink-0 px-4 pt-2 pb-1 border-b bg-gray-50 text-gray-900 dark:bg-gray-950 dark:text-gray-200" 
  style="top: {isFullscreen ? 'env(safe-area-inset-top)' : '0'};"
>
			{#if $mobile && !isFullscreen}
				<div
					class="drag-handle"
					on:touchstart|preventDefault|stopPropagation={handleTouchStart}
					on:touchmove|preventDefault|stopPropagation={handleTouchMove}
					on:touchend|preventDefault|stopPropagation={handleTouchEnd}
				>
					<div class="handle-bar"></div>
				</div>
			{/if}

			<div class="flex items-center justify-between w-full mb-1">
				<h1
					class="{$mobile ? 'sm:text-xl' : 'text-xl'} font-semibold mb-1 truncate text-gray-900 dark:text-gray-200"
					on:touchstart|preventDefault|stopPropagation={handleTouchStart}
					on:touchmove|preventDefault|stopPropagation={handleTouchMove}
					on:touchend|preventDefault|stopPropagation={handleTouchEnd}
				>
					{companyInfo.company_name}
				</h1>

				<div class="flex items-center space-x-1 text-gray-900 dark:text-white-200">
					<ActionButtons companyInfo={companyInfo}/>
					{#if !$mobile}
						<button class="hover:bg-gray-100 dark:hover:bg-gray-800 rounded-full" on:click={closeCompanyInfo}>
							<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
							</svg>
						</button>
					{:else}
						<button 
							class="hover:bg-gray-100 dark:hover:bg-gray-800 rounded-full" 
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
		</div>

		<!-- 기업 상세 내용 -->
		<div class="flex-1 px-4 pb-4 bg-gray-50 text-gray-900 dark:bg-gray-950 dark:text-white-200">
			<CompanyDetail company={companyInfo} />
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
		z-index: 60;
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
			transform-origin: bottom;
			margin-top: 0;
		}

		.company-info-wrapper.mobile.fullscreen {
			/* 풀스크린 모드에서 safe area 처리 */
			top: auto;
			bottom: env(safe-area-inset-bottom);
			max-height: calc(100vh - env(safe-area-inset-top) - env(safe-area-inset-bottom));
			padding-bottom: env(safe-area-inset-bottom);
			transform-origin: bottom;
		}

		.company-info-wrapper.mobile.fullscreen.active {
			border-top-left-radius: 0;
			border-top-right-radius: 0;
		}

		.company-info-wrapper.mobile.active {
			transform: translateY(0);
			border-top: 1px solid #e5e7eb;
			border-top-left-radius: 20px;
			border-top-right-radius: 20px;
		}

		/* 풀스크린 모드에서 sticky 헤더가 주소창 뒤로 숨지지 않도록 보정 */
		.company-info-wrapper.mobile.fullscreen .header-container {
			top: env(safe-area-inset-top) !important;
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
