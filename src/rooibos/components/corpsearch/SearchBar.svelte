<!-- SearchBar.svelte-->
<script lang="ts">
	import { onMount, createEventDispatcher, afterUpdate } from 'svelte';
	import { filterGroups, filterActions } from './filterdata';
	import SearchFilter from './SearchFilter.svelte';
	import { mobile, user } from '$lib/stores';
	import { showSidebar } from '$lib/stores';
	import MenuLines from '$lib/components/icons/MenuLines.svelte';
	import { WEBUI_API_BASE_URL } from '$lib/constants';
	import { get } from 'svelte/store';

	export let searchValue: string;
	export let selectedFilters: any = {};
	export let searchCompanyResults: any = {};
	export let activeFilterGroup: string | null = null;
	export let resultViewMode = 'map';
	export let currentLocation: any = {};
	export let onSearch: (searchValue: string, selectedFilters: any) => Promise<void>;
	export let onReset: () => void;
	export let onApply: () => void;
	export let filterChange: (groupId: string, optionId: string, checked: boolean | string) => void;

	let isSearchMode = false;
	let searchResults: any = [];
	let addressList: any = [];
	let filterScrollRef: HTMLDivElement | null = null;
	let showLeftArrow = false;
	let showRightArrow = false;
	let resizeObserver: ResizeObserver;
	let inputRef: any;
	let filterPosition = { top: 0, left: 0 };
	let filterContainerRef: HTMLDivElement;
	let searchByCompany = true;
	let searchByRepresentative = false;
	let searchByBizNumber = false;
	let searchByLocation = false;

	let searchHistory: Array<{
		query: string;
		conditions: string[];
	}> = [];

	// 검색 실행 여부를 확인하기 위한 변수
	let hasSearched = false;

	const dispatch = createEventDispatcher();

	function handleSubmit(event: SubmitEvent) {
		event.preventDefault();
		onSearch(searchValue, selectedFilters);
	}

	const toggleFilter = (groupId: string, event: MouseEvent) => {
		dispatch('showCompanyInfo', false);
		const target = event.currentTarget as HTMLElement;
		const rect = target.getBoundingClientRect();
		const containerRect = filterContainerRef.getBoundingClientRect();
		const searchFilterWidth = 320;

		filterPosition = {
			top: rect.bottom - containerRect.top,
			left: rect.left - containerRect.left
		};

		if (filterPosition.left + searchFilterWidth > containerRect.width) {
			filterPosition.left = containerRect.width - searchFilterWidth - 20;
		}

		if (activeFilterGroup === groupId) {
			dispatch('filterGroupChange', null);
		} else {
			dispatch('filterGroupChange', groupId);
		}
	};

	function onScroll() {
		if (!filterScrollRef) return;
		const { scrollLeft, scrollWidth, clientWidth } = filterScrollRef;
		showLeftArrow = scrollLeft > 0;
		showRightArrow = scrollLeft + clientWidth < scrollWidth - 1;
	}

	function scrollLeft() {
		filterScrollRef?.scrollBy({ left: -150, behavior: 'smooth' });
	}
	function scrollRight() {
		filterScrollRef?.scrollBy({ left: 150, behavior: 'smooth' });
	}

	function toggleSearchMode() {
		dispatch('showCompanyInfo', false);
		searchByCompany = true;
		searchByRepresentative = false;
		searchByBizNumber = false;
		searchByLocation = false;
		activeFilterGroup = null;
		isSearchMode = !isSearchMode;
		if (!isSearchMode) {
			searchValue = '';
			searchResults = [];
			addressList = [];
		}
		// resultViewMode = 'list'; // 이 라인을 주석처리하여 지도 뷰를 유지합니다
		// toggleViewMode(); // 불필요한 뷰 전환을 제거합니다
	}

	function handleLocationChange() {
		if (searchByLocation) {
			searchByCompany = false;
			searchByRepresentative = false;
			searchByBizNumber = false;
		}
	}

	// 만약 '지명' 이외의 체크박스가 선택되면 '지명' 체크 해제
	function handleNonLocationChange(event: Event) {
		const target = event.target as HTMLInputElement;
		if (target.checked) {
			searchByLocation = false;
		}
	}

	async function handleSearch(event: SubmitEvent) {
		event.preventDefault();
		if (searchValue.trim()) {
			const queryCategories: string[] = [];
			if (searchByCompany) queryCategories.push('company');
			if (searchByRepresentative) queryCategories.push('representative');
			if (searchByBizNumber) queryCategories.push('bizNumber');
			if (searchByLocation) queryCategories.push('location');

			const queryParams = new URLSearchParams({
				query: searchValue,
				queryCategories: queryCategories.join(',')
			});

			const response = await fetch(
				`${WEBUI_API_BASE_URL}/rooibos/corpsearch/?${queryParams.toString()}`,
				{
					method: 'GET',
					headers: {
						Accept: 'application/json',
						'Content-Type': 'application/json',
						authorization: `Bearer ${localStorage.token}`
					}
				}
			);

			const data = await response.json();

			if (data.data.length < 1) {
				hasSearched = true;
				return;
			}

			if (searchByLocation) {
				if (data.data.length == 1) {
					handleAddressSelect(data.data[0]);
				} else {
					addressList = data.data;
					searchResults = [];
				}
			} else {
				searchResults = data.data;
				addressList = [];
			}

			const conditionNames = [];
			if (searchByCompany) conditionNames.push('기업명');
			if (searchByRepresentative) conditionNames.push('대표자명');
			if (searchByBizNumber) conditionNames.push('사업자번호');
			if (searchByLocation) conditionNames.push('지명');

			const newHistoryItem = {
				query: searchValue,
				conditions: conditionNames,
				date: new Date().toLocaleDateString('ko-KR', {
					year: 'numeric',
					month: '2-digit',
					day: '2-digit'
				}),
				timestamp: Date.now()
			};

			const duplicateIndex = searchHistory.findIndex((item) => {
				if (item.query !== newHistoryItem.query) return false;
				if (item.conditions.length !== newHistoryItem.conditions.length) return false;
				return item.conditions.every((c) => newHistoryItem.conditions.includes(c));
			});

			if (duplicateIndex > -1) {
				searchHistory.splice(duplicateIndex, 1);
			}
			searchHistory.unshift(newHistoryItem);
			localStorage.setItem('searchHistory', JSON.stringify(searchHistory));
		}
	}

	function clearSearch() {
		searchValue = '';
		searchResults = [];
		addressList = [];
		hasSearched = false;
	}

	function repeatSearch(item: { query: string; conditions: string[] }) {
		searchByCompany = item.conditions.includes('기업명');
		searchByRepresentative = item.conditions.includes('대표자명');
		searchByBizNumber = item.conditions.includes('사업자번호');
		searchByLocation = item.conditions.includes('지명');

		searchValue = item.query;

		handleSearch(new SubmitEvent('submit'));
	}

	function removeHistoryItem(item: { query: string; conditions: string[] }) {
		searchHistory = searchHistory.filter((h) => h !== item);
		localStorage.setItem('searchHistory', JSON.stringify(searchHistory));
	}

	async function sendAddressCoordinates(x: string, y: string) {
		try {
			const currentUser = get(user);
			const queryParams = new URLSearchParams({
				query: '',
				latitude: y,
				longitude: x,
				userLatitude: currentLocation?.lat?.toString() || '',
				userLongitude: currentLocation?.lng?.toString() || '',
				user_id: currentUser?.id ? currentUser.id : ''
			});

			const response = await fetch(
				`${WEBUI_API_BASE_URL}/rooibos/corpsearch/?${queryParams.toString()}`,
				{
					method: 'GET',
					headers: {
						Accept: 'application/json',
						'Content-Type': 'application/json',
						authorization: `Bearer ${localStorage.token}`
					}
				}
			);
			currentLocation.lat = y;
			currentLocation.lng = x
			const data = await response.json();
			const list = data.data;

			dispatch('addressResultClick', list);
		} catch (error) {
			console.error('Error sending address coordinates:', error);
		}
	}

	async function handleAddressSelect(address: any) {
		await sendAddressCoordinates(address.x, address.y);
		toggleSearchMode();
	}

	onMount(() => {
		try {
			const savedHistory = localStorage.getItem('searchHistory');
			if (savedHistory) {
				searchHistory = JSON.parse(savedHistory);
			}
		} catch (error) {
			console.error('검색 이력을 불러오는데 실패했습니다:', error);
		}

		filterGroups.forEach((group) => {
			if (group.defaultValue && !selectedFilters[group.id]) {
				selectedFilters[group.id] = {
					checked: true,
					value: group.defaultValue
				};
			}
		});

		onScroll();

		resizeObserver = new ResizeObserver(() => {
			if (filterScrollRef) {
				onScroll();
			}
		});

		if (filterScrollRef) {
			resizeObserver.observe(filterScrollRef);
		}
		
		// 항상 지도 뷰로 시작하도록 설정
		resultViewMode = 'map';
		dispatch('showCompanyListClick', resultViewMode);

		return () => {
			if (filterScrollRef) {
				resizeObserver.unobserve(filterScrollRef);
			}
			resizeObserver.disconnect();
		};
	});

	afterUpdate(() => {
		if (isSearchMode && inputRef) {
			inputRef.focus();
		}
	});

	function toggleViewMode() {
		resultViewMode = resultViewMode === 'map' ? 'list' : 'map';
		dispatch('showCompanyListClick', resultViewMode);
	}

	// 필터 액션 핸들러 추가
	function handleAction(action: string) {
		if (action === 'apply') {
			onApply();
		} else if (action === 'reset') {
			onReset();
		}
	}
</script>

<div bind:this={filterContainerRef} 
	class="overflow-y-auto bg-gray-50 text-gray-900 dark:bg-gray-950 dark:text-white-200">
	<div class="flex items-center py-1">
		<div class="{$showSidebar ? 'hidden' : ''} flex items-center">
			<button
				id="sidebar-toggle-button"
				class="cursor-pointer p-1.5 flex rounded-xl text-gray-800 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-850 transition"
				on:click={() => {
					showSidebar.set(!$showSidebar);
				}}
				aria-label="Toggle Sidebar"
			>
				<div class="m-auto self-center">
					<MenuLines />
				</div>
			</button>
		</div>
		<div class="text-xl font-semibold text-gray-800 dark:text-gray-400 px-2">기업찾기</div>
		{#if searchCompanyResults.length >= 1 && !isSearchMode}
			<button
				type="button"
				on:click={toggleViewMode}
				class="ml-4 px-3 py-1 text-sm font-medium hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-600 dark:text-gray-400 rounded-full inline-flex items-center gap-1"
			>
				{#if resultViewMode === 'list'}
					지도보기
				{:else}
					목록보기
				{/if}
			</button>
		{/if}
		<button
			type="button"
			on:click={toggleSearchMode}
			class="text-blue-600 dark:text-gray-400 hover:text-blue-800 px-4 ml-auto"
			aria-label={isSearchMode ? '닫기' : '검색'}
		>
			{#if isSearchMode}
				<svg
					xmlns="http://www.w3.org/2000/svg"
					width="24"
					height="24"
					fill="none"
					viewBox="0 0 24 24"
					stroke="currentColor"
					stroke-width="2"
				>
					<path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
				</svg>
			{:else}
				<svg
					xmlns="http://www.w3.org/2000/svg"
					width="24"
					height="24"
					fill="none"
					viewBox="0 0 24 24"
					stroke="currentColor"
					stroke-width="2"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						d="M21 21l-4.35-4.35M10 18a8 8 0 100-16 8 8 0 000 16z"
					/>
				</svg>
			{/if}
		</button>
	</div>

	{#if isSearchMode}
		<div class="flex flex-col h-[calc(100vh-56px)] text-gray-600 dark:text-gray-400">
			<div class="px-4 py-2 flex-shrink-0">
				<form on:submit={handleSearch} class="relative">
					<div
						class="flex items-center justify-between mb-2 flex-nowrap overflow-x-auto gap-2"
						style="white-space: nowrap; font-size: {$mobile ? '0.875rem' : '1rem'};"
					>
						<div class="flex gap-4">
							<label class="flex items-center">
								<input
									type="checkbox"
									bind:checked={searchByCompany}
									on:change={handleNonLocationChange}
								/>
								<span class="ml-1">기업명</span>
							</label>
							<label class="flex items-center">
								<input
									type="checkbox"
									bind:checked={searchByRepresentative}
									on:change={handleNonLocationChange}
								/>
								<span class="ml-1">대표자명</span>
							</label>
							<label class="flex items-center">
								<input
									type="checkbox"
									bind:checked={searchByBizNumber}
									on:change={handleNonLocationChange}
								/>
								<span class="ml-1">사업자번호</span>
							</label>
							<label class="flex items-center">
								<input
									type="checkbox"
									bind:checked={searchByLocation}
									on:change={handleLocationChange}
								/>
								<span class="ml-1">지명</span>
							</label>
						</div>
					</div>
					<div class="relative">
						<input
							type="text"
							bind:value={searchValue}
							class="w-full pl-4 pr-16 py-2 dark:bg-gray-950 dark:text-gray-200 border border-gray-300 rounded-lg"
							bind:this={inputRef}
						/>
						{#if searchValue}
							<button
								type="button"
								class="absolute inset-y-0 right-10 flex items-center px-2 text-gray-400 hover:text-gray-600"
								on:click={clearSearch}
								aria-label="검색어 삭제"
							>
								<!-- 삭제 아이콘 -->
								<svg
									xmlns="http://www.w3.org/2000/svg"
									width="20"
									height="20"
									fill="none"
									viewBox="0 0 24 24"
									stroke="currentColor"
									stroke-width="2"
								>
									<line
										x1="18"
										y1="6"
										x2="6"
										y2="18"
										stroke-linecap="round"
										stroke-linejoin="round"
									/>
									<line
										x1="6"
										y1="6"
										x2="18"
										y2="18"
										stroke-linecap="round"
										stroke-linejoin="round"
									/>
								</svg>
							</button>
						{/if}
						<button
							type="submit"
							class="absolute inset-y-0 right-0 flex items-center px-3 text-gray-400 hover:bg-blue-700 dark:hover:bg-gray-600 rounded-r-lg"
							aria-label="검색"
						>
							<!-- 검색 아이콘 -->
							<svg
								xmlns="http://www.w3.org/2000/svg"
								width="24"
								height="24"
								fill="none"
								viewBox="0 0 24 24"
								stroke="currentColor"
								stroke-width="2"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									d="M21 21l-4.35-4.35M10 18a8 8 0 100-16 8 8 0 000 16z"
								/>
							</svg>
						</button>
					</div>
				</form>
			</div>
			<!-- 스크롤 영역: 검색 결과, 주소 목록, 최근 검색 이력 -->
			<div class="flex-1 overflow-y-auto px-4 pb-20 text-gray-600 dark:text-gray-400">
				{#if addressList.length > 0}
					{#each addressList as address}
						<button
							type="button"
							class="w-full p-4 border-b text-left hover:bg-gray-100 dark:hover:bg-gray-800"
							on:click={() => handleAddressSelect(address)}
						>
							<h3 class="font-medium font-semibold">{address.roadAddress}</h3>
						</button>
					{/each}
				{:else if searchResults.length > 0}
					{#each searchResults as result}
						<button
							type="button"
							class="w-full p-4 border-b text-left hover:bg-gray-100 dark:hover:bg-gray-800"
							on:click={() => {
								toggleSearchMode();
								dispatch('searchResultClick', result);
							}}
						>
							<h3 class="font-medium font-semibold">{result.company_name}</h3>
							<p class="text-sm text-gray-600">{result.representative}</p>
							<p class="text-sm text-gray-600">{result.address}</p>
						</button>
					{/each}
				{:else if searchValue.trim() !== '' && hasSearched}
					<div class="mt-2 pb-4">
						<p class="text-center text-gray-600">조건에 맞는 업체가 없습니다.</p>
					</div>
				{:else if !searchValue.trim() && searchHistory.length > 0}
					<div class="mt-2 pb-20">
						<h2 class="text-base font-semibold mb-2">최근 검색 이력</h2>
						{#each searchHistory as item}
							<div
								class="flex items-center w-full text-left p-2 border-b hover:bg-gray-100 dark:hover:bg-gray-800"
							>
								<button
									type="button"
									class="flex-grow text-left"
									on:click={() => repeatSearch(item)}
								>
									{#each item.conditions as c}
										[{c}]
									{/each}
									<span class="font-bold">{item.query}</span>
								</button>
								<button
									type="button"
									class="text-gray-400 hover:text-gray-600 ml-2"
									on:click={() => removeHistoryItem(item)}
								>
									X
								</button>
							</div>
						{/each}
					</div>
				{/if}
			</div>
		</div>
	{:else}
		<div class="relative">
			{#if showLeftArrow}
				<div class="absolute left-0 top-1/2 -translate-y-1/2 z-10 to-transparent pr-8 pl-2">
					<button
						class="rounded-full p-0.5 bg-white dark:bg-gray-600 hover:bg-gray-100 dark:hover:bg-gray-800"
						on:click={scrollLeft}
						aria-label="왼쪽으로 스크롤"
					>
						<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M15 19l-7-7 7-7"
							/>
						</svg>
					</button>
				</div>
			{/if}

			<div class="mx-2 pr-20">
				<div
					bind:this={filterScrollRef}
					class="flex flex-nowrap w-full items-center gap-0 overflow-x-auto scrollbar-hide py-2"
					on:scroll={onScroll}
				>
					{#each filterGroups as group}
						<button
							type="button"
							class="px-2 py-2 text-sm {
								(group.id === 'included_industries'
									? ((selectedFilters[group.id]?.value || selectedFilters[group.id]?.min || selectedFilters[group.id]?.max) || selectedFilters.excluded_industries?.value)
									: (selectedFilters[group.id]?.value || selectedFilters[group.id]?.min || selectedFilters[group.id]?.max))
									? 'font-bold text-blue-700 dark:text-yellow-700'
									: 'font-medium text-gray-600 dark:text-gray-400'
							} whitespace-nowrap rounded-full"
							on:click={(e) => toggleFilter(group.id, e)}
						>
							{group.isMulti
								? `${group.title} ${Array.isArray(selectedFilters[group.id]?.value) && selectedFilters[group.id].value.length > 0 ? `(${selectedFilters[group.id].value.length})` : ''}`
								: group.defaultValue || selectedFilters[group.id]?.value
									? group.options?.find((opt) => opt.id === (selectedFilters[group.id]?.value || group.defaultValue))?.label || group.title
									: group.title}
						</button>
					{/each}

					{#each filterActions.filter((a) => a.action === 'apply') as action}
						<button
							type="button"
							class="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-full whitespace-nowrap"
							on:click={() => handleAction(action.action)}
						>
							{action.label}
						</button>
					{/each}
				</div>
			</div>

			<div
				class="absolute right-0 top-1/2 -translate-y-1/2 z-10 flex items-center to-transparent pl-8 pr-2"
			>
				{#if showRightArrow}
					<button
						class="rounded-full p-0.5 bg-white dark:bg-gray-600 hover:bg-gray-100 dark:hover:bg-gray-800"
						on:click={scrollRight}
						aria-label="오른쪽으로 스크롤"
					>
						<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M9 5l7 7-7 7"
							/>
						</svg>
					</button>
				{/if}

				{#each filterActions.filter((a) => a.action === 'reset') as action}
					<button
						type="button"
						class="text-sm px-3 py-2 font-medium text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-full"
						on:click={() => onReset()}
					>
						{action.label}
					</button>
				{/each}
			</div>
		</div>
	{/if}
</div>

{#if activeFilterGroup}
	<div
		class={$mobile ? '' : 'search-filter-container'}
		style={$mobile
			? ''
			: `position: absolute; top: ${filterPosition.top}px; left: ${filterPosition.left}px; z-index: 1000;`}
	>
		<SearchFilter
			{selectedFilters}
			{filterChange}
			{onReset}
			{onApply}
			activeGroup={activeFilterGroup}
		/>
	</div>
{/if}

<style>
	.scrollbar-hide::-webkit-scrollbar {
		display: none;
	}
	.scrollbar-hide {
		-ms-overflow-style: none;
		scrollbar-width: none;
	}

	.search-filter-container {
		z-index: 1000;
		border-radius: 8px;
		padding: 16px;
	}
</style>
