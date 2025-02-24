<!-- industrySearch.svelte -->
<script lang="ts">
	import { WEBUI_API_BASE_URL } from '$lib/constants';
	import { debounce } from 'lodash';
	import { createEventDispatcher } from 'svelte';

	const dispatch = createEventDispatcher();

	// 포함 업종 관련 상태 변수
	let includedSearchTerm = '';
	let includedOptions: Array<{ id: string; industry: string }> = [];
	let includedSelectedIndustries: Array<{ id: string; industry: string }> = [];
	let includedDropdownOpen = false;

	// 제외 업종 관련 상태 변수
	let excludedSearchTerm = '';
	let excludedOptions: Array<{ id: string; industry: string }> = [];
	let excludedSelectedIndustries: Array<{ id: string; industry: string }> = [];
	let excludedDropdownOpen = false;

	export let selectedFilters: any = null;

	function closeDropdown(event: MouseEvent) {
		if (!(event.target as HTMLElement).closest('.input-wrapper')) {
			includedDropdownOpen = false;
			excludedDropdownOpen = false;
		}
	}

	document.addEventListener('click', closeDropdown);

	$: if (includedOptions.length > 0) {
		includedDropdownOpen = true;
	}
	$: if (excludedOptions.length > 0) {
		excludedDropdownOpen = true;
	}

	async function fetchIndustries(query: string) {
		const response = await fetch(`${WEBUI_API_BASE_URL}/rooibos/corpsearch/industries?query=${query}`);
		const data = await response.json();
		return data.industries;
	}

	const debouncedIncludedFetch = debounce((query: string) => {
		if (query.length >= 2) {
			fetchIndustries(query).then((data) => (includedOptions = data));
		}
	}, 150);

	const debouncedExcludedFetch = debounce((query: string) => {
		if (query.length >= 2) {
			fetchIndustries(query).then((data) => (excludedOptions = data));
		}
	}, 150);

	$: if (includedSearchTerm) {
		debouncedIncludedFetch(includedSearchTerm);
	} else {
		includedOptions = [];
	}

	$: if (excludedSearchTerm) {
		debouncedExcludedFetch(excludedSearchTerm);
	} else {
		excludedOptions = [];
	}

	$: if (selectedFilters && selectedFilters.included_industries) {
		let industriesArr = [];
		if (Array.isArray(selectedFilters.included_industries)) {
			industriesArr = selectedFilters.included_industries;
		} else if (
			typeof selectedFilters.included_industries === 'object' &&
			selectedFilters.included_industries.value
		) {
			industriesArr = selectedFilters.included_industries.value.split(',').map((item) => item.trim());
		}
		const newIndustries = industriesArr.map((value: string) => ({
			id: value.replace(/[^가-힣]/g, ''),
			industry: value.trim()
		}));
		if (JSON.stringify(newIndustries) !== JSON.stringify(includedSelectedIndustries)) {
			includedSelectedIndustries = newIndustries;
		}
	}

	$: if (selectedFilters && selectedFilters.excluded_industries) {
		let industriesArr = [];
		if (Array.isArray(selectedFilters.excluded_industries)) {
			industriesArr = selectedFilters.excluded_industries;
		} else if (
			typeof selectedFilters.excluded_industries === 'object' &&
			selectedFilters.excluded_industries.value
		) {
			industriesArr = selectedFilters.excluded_industries.value.split(',').map((item) => item.trim());
		}
		const newIndustries = industriesArr.map((value: string) => ({
			id: value.replace(/[^가-힣]/g, ''),
			industry: value.trim()
		}));
		if (JSON.stringify(newIndustries) !== JSON.stringify(excludedSelectedIndustries)) {
			excludedSelectedIndustries = newIndustries;
		}
	}

	function selectIncludedIndustry(option: { id: string; industry: string }) {
		if (!includedSelectedIndustries.find((item) => item.id === option.id)) {
			includedSelectedIndustries = [...includedSelectedIndustries, option];
			dispatch('filterChange', { groupId: 'included_industries', value: includedSelectedIndustries });
		}
		includedSearchTerm = '';
		includedOptions = [];
	}

	function removeIncludedIndustry(id: string) {
		includedSelectedIndustries = includedSelectedIndustries.filter((item) => item.id !== id);
		dispatch('filterChange', { groupId: 'included_industries', value: includedSelectedIndustries });
	}

	function selectExcludedIndustry(option: { id: string; industry: string }) {
		if (!excludedSelectedIndustries.find((item) => item.id === option.id)) {
			excludedSelectedIndustries = [...excludedSelectedIndustries, option];
			dispatch('filterChange', { groupId: 'excluded_industries', value: excludedSelectedIndustries });
		}
		excludedSearchTerm = '';
		excludedOptions = [];
	}

	function removeExcludedIndustry(id: string) {
		excludedSelectedIndustries = excludedSelectedIndustries.filter((item) => item.id !== id);
		dispatch('filterChange', { groupId: 'excluded_industries', value: excludedSelectedIndustries });
	}
</script>

<div class="industry-search">
	<div class="input-wrapper">
		<input
			type="text"
			placeholder="포함 업종 검색"
			bind:value={includedSearchTerm}
			class="border p-2 rounded-md"
		/>
		{#if includedOptions.length > 0}
			<ul class="options-list border mt-1 rounded-md bg-gray-50 text-gray-900 dark:bg-gray-950 dark:text-white-200" class:hidden={!includedDropdownOpen}>
				{#each includedOptions as option}
					<li
						on:click={() => selectIncludedIndustry(option)}
						class="p-2 cursor-pointer bg-gray-50 text-gray-900 dark:text-gray-400 dark:bg-gray-950"
					>
						{option.industry}
					</li>
				{/each}
			</ul>
		{/if}
	</div>

	{#if includedSelectedIndustries.length > 0}
		<div class="selected-industries mt-2">
			{#each includedSelectedIndustries as industry (industry.id)}
				<span class="tag inline-flex items-center bg-gray-50 text-gray-900 dark:text-gray-400 dark:bg-gray-950 px-2 py-1 rounded mr-1 max-w-full">
					<span class="flex-1 truncate">{industry.industry}</span>
					<button on:click={() => removeIncludedIndustry(industry.id)} class="ml-1 flex-shrink-0">×</button>
				</span>
			{/each}
		</div>
	{/if}

	<!-- 제외 업종 영역: 기존 코드와 동일하게 유지하되, 간격(margin-top) 추가 -->
	<div class="input-wrapper" style="margin-top: 1rem;">
		<input
			type="text"
			placeholder="제외 업종 검색"
			bind:value={excludedSearchTerm}
			class="border p-2 rounded-md"
		/>
		{#if excludedOptions.length > 0}
			<ul class="options-list border mt-1 rounded-md bg-gray-50 text-gray-900 dark:bg-gray-950 dark:text-white-200" class:hidden={!excludedDropdownOpen}>
				{#each excludedOptions as option}
					<li
						on:click={() => selectExcludedIndustry(option)}
						class="p-2 cursor-pointer bg-gray-50 text-gray-900 dark:text-gray-400 dark:bg-gray-950"
					>
						{option.industry}
					</li>
				{/each}
			</ul>
		{/if}
	</div>

	{#if excludedSelectedIndustries.length > 0}
		<div class="selected-industries mt-2">
			{#each excludedSelectedIndustries as industry (industry.id)}
				<span class="tag inline-flex items-center bg-gray-50 text-gray-900 dark:text-gray-400 dark:bg-gray-950 px-2 py-1 rounded mr-1 max-w-full">
					<span class="flex-1 truncate">{industry.industry}</span>
					<button on:click={() => removeExcludedIndustry(industry.id)} class="ml-1 flex-shrink-0">×</button>
				</span>
			{/each}
		</div>
	{/if}
</div>

<style>
	.industry-search {
		width: 100%;
		max-width: 400px;
	}

	.input-wrapper {
		display: inline-block;
		position: relative;
	}

	.options-list {
		position: absolute;
		top: 100%;
		left: 0;
		width: 100%;
		z-index: 10;
		max-height: 300px;
		overflow-y: auto;
		scrollbar-width: thin;
		scrollbar-color: #999 transparent;
	}
	.options-list li {
		display: block;
		width: 100%;
		overflow: hidden;
		white-space: nowrap;
		text-overflow: ellipsis;
	}


</style>
