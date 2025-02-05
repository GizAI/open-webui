<script lang="ts">
  import { onMount, createEventDispatcher, afterUpdate } from 'svelte';
  import { filterGroups, filterActions } from './filterdata';
  import SearchFilter from './SearchFilter.svelte';
  import { mobile } from '$lib/stores';
  import { showSidebar } from '$lib/stores';
  import MenuLines from '$lib/components/icons/MenuLines.svelte';
	import { WEBUI_API_BASE_URL } from '$lib/constants';

  export let searchValue: string;
  export let selectedFilters: any = {};
  export let activeFilterGroup: string | null = null;
  export let onSearch: (searchValue: string, selectedFilters: any) => Promise<void>;
  export let onReset: () => void;
  export let onApply: () => void;
  export let onFilterChange: (groupId: string, optionId: string, checked: boolean | string) => void;

  let isSearchMode = false;
  let searchResults: any = [];
  let filterScrollRef: HTMLDivElement | null = null;
  let showLeftArrow = false;
  let showRightArrow = false;
  let resizeObserver: ResizeObserver;
  let inputRef: any;
  let filterPosition = { top: 0, left: 0 };
  let filterContainerRef: HTMLDivElement;

  function handleSubmit(event: SubmitEvent) {
    event.preventDefault();
    onSearch(searchValue, selectedFilters);
  }

  const dispatch = createEventDispatcher();

  const toggleFilter = (groupId: string, event: MouseEvent) => {
    const target = event.currentTarget as HTMLElement;
    const rect = target.getBoundingClientRect();
    const containerRect = filterContainerRef.getBoundingClientRect();
    const searchFilterWidth = 320;
   
    filterPosition = {
      top: rect.bottom - containerRect.top,
      left: rect.left - containerRect.left
    };
    
    if (filterPosition.left + searchFilterWidth > containerRect.width) {
      filterPosition.left = containerRect.width - searchFilterWidth - 20; // 여유 공간 16px
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
    isSearchMode = !isSearchMode;
    if (!isSearchMode) {
      searchValue = '';
      searchResults = [];
    }
  }

  async function handleSearch(event: SubmitEvent) {
    event.preventDefault();
    if (searchValue.trim()) {
      const queryParams = new URLSearchParams({
          query: searchValue
      });
      const response = await fetch(`${WEBUI_API_BASE_URL}/rooibos/corpsearch/?${queryParams.toString()}`, {
          method: 'GET',
          headers: {
              Accept: 'application/json',
              'Content-Type': 'application/json',
              authorization: `Bearer ${localStorage.token}`,
          },
      });
      const data = await response.json();
      searchResults = data.data;
    }
  }

  onMount(() => {
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
      onScroll();
    });

    if (filterScrollRef) {
      resizeObserver.observe(filterScrollRef);
    }

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

</script>

<div 
  bind:this={filterContainerRef}
  class="bg-gray-50 overflow-y-auto">
  <div class="flex items-center py-1">
    <div class="{ $showSidebar ? 'hidden' : '' } flex items-center">
      <button
        id="sidebar-toggle-button"
        class="cursor-pointer p-1.5 flex rounded-xl hover:bg-gray-100 dark:hover:bg-gray-850 transition"
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
    <div class="text-xl font-semibold text-gray-800 px-2">
      기업찾기
    </div>

    <button
      type="button"
      on:click={toggleSearchMode}
      class="text-blue-600 hover:text-blue-800 px-4 ml-auto"
      aria-label="검색"
    >
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
  {#if isSearchMode}
  <div class="px-4 py-2 h-[calc(100vh-50px)]">
      <form on:submit={handleSearch} class="relative">
        <input
          type="text"
          bind:value={searchValue}
          placeholder="기업명 대표자명 주소로 검색"
          class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          bind:this={inputRef}
        />
        <button
          type="button"
          class="absolute right-2 top-1/2 -translate-y-1/2 text-gray-500"
          on:click={toggleSearchMode}
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </form>

      {#if searchResults.length > 0}
        <div class="mt-2 h-full overflow-y-auto pb-20">
          {#each searchResults as result}
          <button
            type="button"
            class="w-full p-4 border-b text-left hover:bg-gray-100"
            on:click={() => {
              dispatch('searchResultClick', result);
              toggleSearchMode();
            }}
            on:keydown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                dispatch('searchResultClick', result);
                toggleSearchMode();
              }
            }}
          >
              <h3 class="font-medium font-semibold">{result.company_name}</h3>
              <p class="text-sm text-gray-600">{result.representative}</p>
              <p class="text-sm text-gray-600">{result.address}</p>
        </button>
          {/each}
        </div>
      {/if}
    </div>
  {:else}

  <div class="relative">
    {#if showLeftArrow}
    <div class="absolute left-0 top-1/2 -translate-y-1/2 z-10 bg-gradient-to-r from-gray-50 to-transparent pr-8 pl-2">
      <button
        class="rounded-full p-2 bg-white"
        on:click={scrollLeft}
        aria-label="왼쪽으로 스크롤"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M15 19l-7-7 7-7" />
        </svg>
      </button>
    </div>
    {/if}

    <div class="mx-2 pr-20"> <!-- 오른쪽 여백 추가 -->
      <div
        bind:this={filterScrollRef}
        class="flex flex-nowrap w-full items-center gap-0 overflow-x-auto scrollbar-hide py-2"
        on:scroll={onScroll}
      >
      {#each filterGroups as group}
        <button
          type="button"
          class="px-2 py-2 text-sm { (selectedFilters[group.id] || group.defaultValue ) ? 'font-bold text-blue-700' : 'font-medium text-gray-700' } whitespace-nowrap rounded-full"
          on:click={(e) => toggleFilter(group.id, e)}
        >
          {group.isMulti 
            ? `${group.title} ${Array.isArray(selectedFilters[group.id]?.value) && selectedFilters[group.id].value.length > 0 ? `(${selectedFilters[group.id].value.length})` : ''}`
            : (group.defaultValue || selectedFilters[group.id]?.value 
              ? group.options.find(opt => opt.id === (selectedFilters[group.id]?.value || group.defaultValue))?.label || group.title
              : group.title)
          }
        </button>

     {/each}

        {#each filterActions.filter(a => a.action === 'apply') as action}
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

    <div class="absolute right-0 top-1/2 -translate-y-1/2 z-10 flex items-center bg-gradient-to-l from-gray-50 to-transparent pl-8 pr-2">
      {#if showRightArrow}
        <button
         class="rounded-full p-2 bg-white"
         on:click={scrollRight}
         aria-label="오른쪽으로 스크롤"
       >
         <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
           <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                 d="M9 5l7 7-7 7" />
         </svg>
       </button>
      {/if}

      {#each filterActions.filter(a => a.action === 'reset') as action}
        <button
          type="button"
          class="text-sm px-3 py-2 font-medium text-gray-700 hover:bg-gray-100 rounded-full whitespace-nowrap"
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
    class="{$mobile ? '' : 'search-filter-container'}"
    style="{$mobile ? '' : `position: absolute; top: ${filterPosition.top}px; left: ${filterPosition.left}px; z-index: 1000;`}"
  >
    <SearchFilter
      {selectedFilters}
      {onFilterChange}
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