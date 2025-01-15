<script lang="ts">
  import { Sliders, Map, List, Building2, Users, TrendingUp, DollarSign, Scale, UserPlus, CalendarDays, Landmark, Ban, RotateCcw, Check, MapPin, Award, History } from 'lucide-svelte';
  import { filterGroups, filterActions } from './filterdata';
  import SearchFilter from './SearchFilter.svelte';
  import { mobile } from '$lib/stores';
  
  export let searchResults: any[] = [];
  export let onSearch: (searchValue: string, selectedFilters: any) => Promise<void>;
  export let searchValue: string;
  export let onSearchValueChange: (value: string) => void;
  export let isListIconVisible: boolean;
  export let selectedFilters: any = {};
  export let onFilterChange: (groupId: string, optionId: string, checked: boolean | string) => void;
  export let isFilterOpen: boolean = false;
  export let activeFilterGroup: string | null = null;
  export let onReset: () => void;
  export let onApply: () => void;
  export let onShowSearchListChange: (value: boolean) => void;
  export let onFilterOpenChange: (value: boolean) => void;

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
    activeFilterGroup = groupId === activeFilterGroup ? null : groupId;
    onShowSearchListChange(false);
    onFilterOpenChange(true);
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

<div class="absolute top-5 left-1/2 -translate-x-1/2 z-10 w-full max-w-md px-4 space-y-2">
  <form 
    on:submit|preventDefault={handleSubmit}
    class="relative max-w-md mx-auto"
  >
    <input
      type="text"
      bind:value={searchValue}
      on:input={(e) => onSearchValueChange(e.target.value)}
      placeholder="기업명, 대표자명, 주소로 검색"
      class="w-full px-4 py-2 rounded-full shadow-lg border border-gray-300 focus:outline-none focus:border-blue-500 pr-24"
    />
    <div class="absolute right-2 top-1/2 -translate-y-1/2 flex items-center space-x-2">
      <button
        type="submit"
        class="bg-blue-500 text-white px-4 py-1.5 rounded-full hover:bg-blue-600 text-sm"
      >
        검색
      </button>
    </div>
  </form>

  <div class="absolute left-1/2 transform -translate-x-1/2 z-10 flex items-center gap-2 {$mobile ? 'w-11/12' : ''}">
    {#if searchResults.length > 0}
      <button
        type="button"
        on:click={handleListIconClick}
        aria-label={isListIconVisible ? "지도 보기" : "리스트 보기"}
        class="text-gray-700 hover:text-blue-600 transition-colors p-1 rounded-full hover:bg-blue-50"
      >
        {#if isListIconVisible}
          <Map class="h-6 w-6" />
        {:else}
          <List class="h-6 w-6" />
        {/if}
      </button>
      
      <div class="flex items-start gap-2 w-full {$mobile ? 'grid grid-cols-7' : ''}">  
        {#each filterGroups as group}
          <button
            type="button"
            class="p-2 rounded-full hover:bg-gray-100"
            on:click={() => toggleFilter(group.id)}
            aria-label={group.title}
          >
            {#if iconMapping[group.id]}
              <svelte:component 
                this={iconMapping[group.id]} 
                class="h-5 w-5 {group.iconClass}" 
              />
            {:else}
              <Sliders class="h-5 w-5 text-gray-500" />
            {/if}
          </button>
        {/each}

        {#each filterActions as action}
          <button
            type="button"
            class="p-2 rounded-full hover:bg-gray-100"
            on:click={() => handleAction(action.action)}
            aria-label={action.label}
          >
            {#if iconMapping[action.id]}
              <svelte:component this={iconMapping[action.id]} class="h-5 w-5 {action.iconClass}" />
            {:else}
              <Sliders class="h-5 w-5" />
            {/if}
          </button>
        {/each}
      </div>
    {/if}
  </div>
  {#if isFilterOpen}
  <div
  style="margin-top: {mobile ? '80px' : '10px'}"
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
</div>