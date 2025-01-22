<script lang="ts">
  import { Sliders, Map, List, Building2, Users, TrendingUp, DollarSign, Scale, UserPlus, CalendarDays, Landmark, Ban, RotateCcw, Check, MapPin, Award, History } from 'lucide-svelte';
  import { filterGroups, filterActions } from './filterdata';
  import SearchFilter from './SearchFilter.svelte';
  import { mobile } from '$lib/stores';
  import { showSidebar } from '$lib/stores';
	import MenuLines from '$lib/components/icons/MenuLines.svelte';

  export let onSearch: (searchValue: string, selectedFilters: any) => Promise<void>;
  export let searchValue: string;
  export let isListIconVisible: boolean;
  export let selectedFilters: any = {};
  export let isFilterOpen: boolean = false;
  export let activeFilterGroup: string | null = null;
  export let onReset: () => void;
  export let onApply: () => void;
  export let onShowSearchListChange: (value: boolean) => void;
  export let onFilterOpenChange: (value: boolean) => void;
  export let onFilterChange: (groupId: string, optionId: string, checked: boolean | string) => void;

  async function handleSubmit(event: SubmitEvent) {
    event.preventDefault();
    await onSearch(searchValue, selectedFilters);
    const inputEl = (event.target as HTMLFormElement).querySelector('input');
    inputEl?.blur();
  }
  
  function handleListIconClick() {
    const newValue = !isListIconVisible;
    isFilterOpen = false;
    onShowSearchListChange(newValue);
  }

  function handleAction(action: 'reset' | 'apply') {
    if (action === 'reset') {
      onReset();
    } else if (action === 'apply') {
      onApply();
    }
  }

  const toggleFilter = (groupId: string) => {
    if (activeFilterGroup === groupId && isFilterOpen) {
      activeFilterGroup = null;
      onFilterOpenChange(false);
    } else {
      activeFilterGroup = groupId;
      onShowSearchListChange(false);
      onFilterOpenChange(true);
    }
  };

  const iconMapping: Record<string, any> = {
    radius: MapPin,
    certification: Award,
    employee_count: Users,
    sales: TrendingUp,
    profit: DollarSign,
    net_profit: Scale,
    gender: UserPlus,
    gender_age: History,
    unallocated_profit: Landmark,
    establishment_year: CalendarDays,
    loan: Building2,
    excluded_industries: Ban,
    reset: RotateCcw,
    apply: Check
  };
</script>

<div class="bg-gray-50 overflow-y: auto;">
  <div class="flex items-center py-2">
    <div class="{$showSidebar ? 'hidden' : ''} flex items-center">
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
    <!-- 기업찾기 라벨 -->
    <div class="text-xl font-semibold text-gray-800 px-2">기업찾기</div>

    <!-- 검색 아이콘 -->
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


  <div class="flex flex-wrap">
    {#each filterGroups as group, i}
      <button
        type="button"
        class="px-4 py-2 text-sm font-medium text-gray-700 rounded-full hover:bg-gray-200"
        on:click={() => toggleFilter(group.id)}
      >
        {group.title}
      </button>
      {#if i < filterGroups.length - 1}
        <span class="text-gray-400">|</span>
      {/if}
    {/each}

    {#each filterActions as action, i}
      <button
        type="button"
        class="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-full hover:bg-gray-200"
        on:click={() => handleAction(action.action)}
      >
        {action.label}
      </button>
      {#if i < filterActions.length - 1}
        <span class="text-gray-400">|</span>
      {/if}
    {/each}
  </div>

</div>
{#if isFilterOpen}
  <div
    class="search-filter-container"
    style="{$mobile ? 'margin-top: 80px' : ''}"
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
  
  .search-filter-container {
    position: fixed;
    top: 30%;
    left: 50%;
    transform: translate(-50%, -50%);
    z-index: 1000; 
    border-radius: 8px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    padding: 16px;
  }

  .filter-group-wrapper {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    padding-bottom: 1rem;
  }

  .absolute {
    margin: 0;
  }


  .fixed {
    left: 0;
    right: 0;
  }

  .sidebar-margin {
    left: 200px;
  }

  .mobile-layout {
    height: 70vh;
    max-height: 70vh;
    border-top-left-radius: 16px;
    border-top-right-radius: 16px;
  }
</style>

