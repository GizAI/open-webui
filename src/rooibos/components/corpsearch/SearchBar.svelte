<script lang="ts">
  import { onMount, createEventDispatcher } from 'svelte';
  import { filterGroups, filterActions } from './filterdata';
  import SearchFilter from './SearchFilter.svelte';
  import { mobile } from '$lib/stores';
  import { showSidebar } from '$lib/stores';
  import MenuLines from '$lib/components/icons/MenuLines.svelte';

  export let searchValue: string;
  export let selectedFilters: any = {};
  export let activeFilterGroup: string | null = null;
  export let onSearch: (searchValue: string, selectedFilters: any) => Promise<void>;
  export let onReset: () => void;
  export let onApply: () => void;
  export let onFilterChange: (groupId: string, optionId: string, checked: boolean | string) => void;

  let filterScrollRef: HTMLDivElement | null = null;
  let showLeftArrow = false;
  let showRightArrow = false;
  let resizeObserver: ResizeObserver;

  function handleSubmit(event: SubmitEvent) {
    event.preventDefault();
    onSearch(searchValue, selectedFilters);
  }

  function handleAction(action: 'reset' | 'apply') {
    if (action === 'reset') {
      onReset();
    } else if (action === 'apply') {
      onApply();
    }
  }

  const dispatch = createEventDispatcher();
  const toggleFilter = (groupId: string) => {
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

  onMount(() => {
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
</script>

<div class="bg-gray-50 overflow-y-auto">
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
            class="px-2 py-2 text-sm {group.checked ? 'font-bold text-blue-700' : 'font-medium text-gray-700'} whitespace-nowrap rounded-full"
            on:click={() => toggleFilter(group.id)}
          >
            {group.title}
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
          on:click={() => handleAction(action.action)}
        >
          {action.label}
        </button>
      {/each}
    </div>
  </div>
</div>

{#if activeFilterGroup}
  <div
    class="{$mobile ? '' : 'search-filter-container'}"
    style="{$mobile ? '' : 'margin-top: 80px'}"
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
    position: fixed;
    left: 50%;
    transform: translate(-50%, -50%);
    z-index: 1000;
    border-radius: 8px;
    padding: 16px;
  }
</style>