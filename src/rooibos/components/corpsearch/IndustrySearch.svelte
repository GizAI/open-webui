<!-- industrySearch.svelte -->
<script lang="ts">
	import { WEBUI_API_BASE_URL } from '$lib/constants';
	import { debounce } from 'lodash';
	import { createEventDispatcher } from 'svelte';

	const dispatch = createEventDispatcher();

	let searchTerm = '';
	let options: Array<{ id: string; industry: string }> = [];
	let selectedIndustries: Array<{ id: string; industry: string }> = [];

    export let selectedFilters: any = null;

	async function fetchIndustries(query: string) {
		const response = await fetch(`${WEBUI_API_BASE_URL}/rooibos/corpsearch/industries?query=${query}`);
		const data = await response.json();
		options = data.industries;     
	}

	const debouncedFetch = debounce((query: string) => {
		fetchIndustries(query);
	}, 200);

	$: if (searchTerm) {
		debouncedFetch(searchTerm);
	} else {
		options = [];
	}

    $: if (selectedFilters && selectedFilters.included_industries) {
        let industriesArr = [];

        if (Array.isArray(selectedFilters.included_industries)) {
            industriesArr = selectedFilters.included_industries;
        } 
        
        else if (typeof selectedFilters.included_industries === 'object' && selectedFilters.included_industries.value) {
            industriesArr = selectedFilters.included_industries.value.split(',').map(item => item.trim());
        }

        const newIndustries = industriesArr.map((value: string) => ({
            id: value.replace(/[^가-힣]/g, ''), // 한글만 남김
            industry: value.trim()
        }));

        if (JSON.stringify(newIndustries) !== JSON.stringify(selectedIndustries)) {
            selectedIndustries = newIndustries;
        }
    }


	function selectIndustry(option: { id: string; industry: string }) {
		if (!selectedIndustries.find((item) => item.id === option.id)) {
			const updatedIndustries = [...selectedIndustries, option];
			selectedIndustries = updatedIndustries;
			dispatch('filterChange', { groupId: 'included_industries', value: updatedIndustries });
		}
		searchTerm = '';
		options = [];
	}


	function removeIndustry(id: string) {
		const updatedIndustries = selectedIndustries.filter((item) => item.id !== id);
		selectedIndustries = updatedIndustries;
		dispatch('filterChange', { groupId: 'included_industries', value: updatedIndustries });
	}
</script>

<div class="industry-search">
	<div class="input-wrapper">
		<input
			type="text"
			placeholder="업종 검색"
			bind:value={searchTerm}
			class="border p-2 rounded-md"
		/>
		{#if options.length > 0}
			<ul class="options-list border mt-1 rounded-md bg-gray-50 text-gray-900 dark:bg-gray-950 dark:text-white-200">
				{#each options as option}
					<li
						on:click={() => selectIndustry(option)}
						class="p-2 cursor-pointer bg-gray-50 text-gray-900 dark:text-gray-400 dark:bg-gray-950"
					>
						{option.industry}
					</li>
				{/each}
			</ul>
		{/if}
	</div>

	{#if selectedIndustries.length > 0}
		<div class="selected-industries mt-2">
			{#each selectedIndustries as industry (industry.id)}
                <span class="tag inline-block whitespace-nowrap bg-gray-50 text-gray-900 dark:text-gray-400 dark:bg-gray-950 px-2 py-1 rounded mr-1">
                    {industry.industry}
                    <button on:click={() => removeIndustry(industry.id)} class="ml-1">×</button>
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
	}
</style>


