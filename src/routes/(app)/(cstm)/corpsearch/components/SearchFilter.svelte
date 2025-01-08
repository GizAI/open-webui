<script lang="ts">
  import { onMount } from 'svelte';

  import { filterGroups, filterActions } from './filterdata';
  

  type FilterValue = string | string[] | { 
    min?: string;
    max?: string;
    year?: string;
    age?: string;
  };

  // 타입 가드 함수 추가
  function isStringArray(value: FilterValue): value is string[] {
    return Array.isArray(value);
  }

  export let selectedFilters: Record<string, FilterValue> = {};
  export let onFilterChange: (
    groupId: string,
    optionId: string,
    checked: boolean | string
  ) => void;
  export let onReset: () => void;
  export let onApply: () => void;
  export let activeGroup: string | null;

  let maxHeight = '60vh';

  onMount(() => {
    function updateMaxHeight() {
      const windowHeight = window.innerHeight;
      const searchBarHeight = 64;
      const bottomNavHeight = 80;
      const padding = 32;
      const availableHeight = windowHeight - searchBarHeight - bottomNavHeight - padding;
      maxHeight = `${availableHeight}px`;
    }
    updateMaxHeight();

    window.addEventListener('resize', updateMaxHeight);
    return () => window.removeEventListener('resize', updateMaxHeight);
  });

  $: group = filterGroups.find((g) => g.id === activeGroup);

  function handleAction(action: 'reset' | 'apply') {
    if (action === 'reset') {
      onReset();
    } else if (action === 'apply') {
      onApply();
    }
  }

  let ageValue = '';

  $: if (group?.id === 'gender_age') {
    const filterObj = selectedFilters[group.id];
    if (filterObj && typeof filterObj === 'object' && 'age' in filterObj) {
      ageValue = filterObj.age ?? '';
    } else {
      ageValue = '';
    }
  }
</script>

{#if group}
  <div
    class="space-y-4 p-4"
    style="max-height: {maxHeight}; overflow-y: auto;"
  >
    <div class="filter-group-title flex items-center space-x-2">
      <svelte:component this={group.icon} class="h-4 w-4" />
      <h3 class="font-medium text-gray-700">{group.title}</h3>
    </div>

    <div class="space-y-4">
      {#if group.id === 'gender_age'}
        <div class="border-b border-gray-200 pb-4">
          <div class="flex items-center gap-2">
            <input
              type="number"
              placeholder="나이 입력"
              bind:value={ageValue}
              class="w-20 px-2 py-1 text-sm border border-gray-300 rounded"
              on:input={(e) => onFilterChange(group.id, 'age', e.currentTarget?.value || '')}
            />
            <span class="text-sm ml-1">세</span>
          </div>
        </div>

      {:else if group.id === 'gender'}
        <div class="border-b border-gray-200 pb-4">
          <div class="flex items-center gap-4">
            {#each group.options as option}
              <label class="flex items-center hover:bg-gray-50 p-1.5 rounded">
                <input
                  type="radio"
                  name="gender"
                  checked={selectedFilters[group.id] === option.id}
                  on:change={() => onFilterChange('gender', option.id, option.id)}
                  class="mr-2"
                />
                <span class="text-sm text-gray-600">{option.label}</span>
              </label>
            {/each}
          </div>
        </div>

      {:else}
        <div class="border-b border-gray-200 pb-4 last:border-b-0">
          <div class="grid grid-cols-2 gap-2">
            {#each group.options as option}
              {#if (group.id === 'employee_count' 
                || group.id === 'sales' 
                || group.id === 'profit' 
                || group.id === 'net_profit' 
                || group.id === 'unallocated_profit') && option.id === 'range'}
                <div class="flex items-center gap-2">
                  <input
                    type="number"
                    placeholder="최소"
                    value={selectedFilters[group.id]?.min || ''}
                    class="w-16 px-2 py-1 text-sm border border-gray-300 rounded"
                    on:input={(e) => onFilterChange(group.id, 'min', e.currentTarget?.value || '')}
                  />
                  <span class="text-sm">{group.id === 'employee_count' ? '명' : '백만'}</span>
                  <span class="text-sm">~</span>
                  <input
                    type="number"
                    placeholder="최대"
                    value={selectedFilters[group.id]?.max || ''}
                    class="w-16 px-2 py-1 text-sm border border-gray-300 rounded"
                    on:input={(e) => onFilterChange(group.id, 'max', e.currentTarget?.value || '')}
                  />
                  <span class="text-sm">{group.id === 'employee_count' ? '명' : '백만'}</span>
                </div>

              {:else if group.id === 'establishment_year' && option.id === 'input_year'}
                <div class="flex items-center gap-2">
                  <input
                    type="number"
                    placeholder="연도 입력"
                    value={selectedFilters[group.id]?.year || ''}
                    class="w-20 px-2 py-1 text-sm border border-gray-300 rounded"
                    on:input={(e) => onFilterChange(group.id, 'year', e.currentTarget?.value || '')}
                  />
                  <span class="text-sm">년 이후</span>
                </div>

              {:else}
                <label class="flex items-center hover:bg-gray-50 p-1.5 rounded">
                  <input
                    type={group.isMulti ? 'checkbox' : 'radio'}
                    name={group.id}
                    checked={
                      group.isMulti
                        ? (isStringArray(selectedFilters[group.id]) 
                          && selectedFilters[group.id].includes(option.id))
                        : selectedFilters[group.id] === option.id
                    }
                    on:change={(e) => onFilterChange(
                      group.id,
                      option.id,
                      group.isMulti ? e.currentTarget?.checked : option.id
                    )}
                    class="mr-2"
                  />
                  <span class="text-sm text-gray-600">{option.label}</span>
                </label>
              {/if}
            {/each}
          </div>
        </div>
      {/if}
    </div>
  </div>
{/if}