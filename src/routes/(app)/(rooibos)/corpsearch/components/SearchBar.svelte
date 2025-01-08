<script lang="ts">
  import { Sliders, Map, List, Building2, Users, TrendingUp, DollarSign, Scale, UserPlus, CalendarDays, Landmark, Ban, RotateCcw, Check, MapPin, Award, History } from 'lucide-svelte';
  import { filterGroups, filterActions } from './filterdata';
  
  export let searchResults: any[] = [];
  export let onSearch: (searchValue: string, selectedFilters: any) => Promise<void>;
  export let searchValue: string;
  export let onSearchValueChange: (value: string) => void;
  export let handleListIconClick: () => void;
  export let isListIconVisible: boolean = false;

  export const isFilterOpen: boolean = false;
  export const activeFilterGroup: string | null = null;
  export let setIsFilterOpen: (open: boolean) => void;
  export let toggleFilter: (groupId: string) => void;
  export let onReset: () => void;
  export let onApply: () => void;

  async function handleSubmit(event: SubmitEvent) {
    event.preventDefault();
    setIsFilterOpen(false);
    await onSearch(searchValue, {});
    // input blur 처리
    const inputEl = (event.target as HTMLFormElement).querySelector('input');
    inputEl?.blur();
  }

  function handleAction(action: 'reset' | 'apply') {
    if (action === 'reset') {
      onReset();
    } else if (action === 'apply') {
      onApply();
    }
  }

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

<!-- Tailwind 클래스 그대로 사용한다고 가정 -->
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

  <!-- 지도/리스트 전환 버튼 + 필터 버튼 -->
  <div class="flex items-start gap-2 mt-2">
    {#if searchResults.length > 0}
    <!-- 지도/리스트 전환 버튼 -->
      <button
        type="button"
        on:click={handleListIconClick}
        aria-label={isListIconVisible ? "지도 보기" : "리스트 보기"}
        class="text-gray-700 hover:text-blue-600 transition-colors p-1 rounded-full hover:bg-blue-50"
      >
        {#if typeof isListIconVisible !== 'undefined' && !isListIconVisible}
          <Map class="h-6 w-6" />
        {:else}
          <List class="h-6 w-6" />
        {/if}
    
      </button>
      
      <div class="flex flex-wrap gap-2">
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
            class="p-2 rounded-full"
            on:click={() => handleAction(action.action)}
            aria-label={action.label}
          >
            {#if iconMapping[action.id]}
              <svelte:component this={iconMapping[action.id]} class="h-5 w-5 {action.iconClass}"  />
            {:else}
              <Sliders class="h-5 w-5" />
            {/if}
          </button>
        {/each}
      </div>
    {/if}
  </div>
</div>
