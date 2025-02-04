<script lang="ts">
  import { filterGroups } from './filterdata';
  import { mobile } from '$lib/stores';

  type FilterValue = string | string[] | { 
    min?: string;
    max?: string;
    year?: string;
    age?: string;
  };

  export let selectedFilters: Record<string, FilterValue> = {};
  export let onFilterChange: (
    groupId: string,
    optionId: string,
    checked: boolean | string
  ) => void;
  export let onReset: () => void;
  export let onApply: () => void;
  export let activeGroup: string | null;

  $: group = filterGroups.find((g) => g.id === activeGroup);

  let ageValue = '';

  $: if (group?.id === 'gender_age') {
    const filterObj = selectedFilters[group.id];
    if (filterObj && typeof filterObj === 'object' && 'age' in filterObj) {
      ageValue = filterObj.age ?? '';
    } else {
      ageValue = '';
    }
  }

  const applyButtonGroups = [
    'employee_count',
    'sales',
    'profit',
    'net_profit',
    'representative_age',
    'unallocated_profit',
    'establishment_year',
    'gender_age'
  ];

  function shouldShowApplyButton(groupId: string): boolean {
    return applyButtonGroups.includes(groupId);
  }

  const checkFilter = (filter: any) => {
    const value = selectedFilters[filter.id];

    if (
      !value ||
      value === '' ||
      (typeof value === 'object' &&
        (Object.keys(value).length === 0 ||
          (Object.keys(value).every((key) => value[key] === ''))))
    ) {
      delete selectedFilters[filter.id];
    }

    console.log(filter.id);
    console.log(selectedFilters[filter.id]);
    console.log('selectedFilters: ', selectedFilters);
    onApply();
  };


  
</script>

{#if group}
  <div>
    <div class="bg-white rounded-lg shadow-sm {$mobile ? 'p-2' : 'p-4'}">
      <div class="filter-group-title flex items-center justify-between mb-3"> 
        <h3 class="font-semibold text-gray-800 text-sm">{group.title}</h3>
        {#if shouldShowApplyButton(group.id)}
          <button 
            on:click={() => {
              checkFilter(group)
            }}
            class="p-1.5 hover:bg-blue-50 rounded-md transition-all text-gray-600"
            aria-label="적용"
          >
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-5 h-5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
            </svg>
          </button>
        {/if}
      </div>
      <div>
        {#if group.id === 'gender_age'}
          <div class="border rounded-lg p-7 bg-gray-50"> 
            <div class="flex items-center gap-2">
              <input
                type="number"
                placeholder="나이 입력"
                value={selectedFilters[group.id]?.age || ''}
                class="w-20 px-2 py-1.5 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all" 
                on:input={(e) => onFilterChange(group.id, 'age', e.currentTarget?.value || '')}
              />
              <span class="text-sm text-gray-600 ml-1">세 이상</span>
            </div>
          </div>

        {:else if group.id === 'gender'}
          <div class="border rounded-lg p-7 bg-gray-50">
            <div class="flex items-center gap-2"> 
              {#each group.options as option}
                <label class="flex items-center hover:bg-white p-1.5 rounded-md transition-all">
                  <input
                    type="radio"
                    name="gender"
                    checked={selectedFilters[group.id]?.value === option.id}
                    on:change={() => onFilterChange(group.id, option.id, option.id)}
                    class="w-4 h-4 text-blue-600 mr-2"
                  />
                  <span class="text-sm text-gray-700">{option.label}</span>
                </label>
              {/each}
            </div>
          </div>
        {:else if group.id === 'establishment_year'}
          <div class="border rounded-lg p-6 bg-gray-50"> 
            <div class="flex items-center gap-2">
              <input
                type="number"
                placeholder="년도 입력"
                value={selectedFilters[group.id]?.establishment_year || ''}
                class="w-20 px-2 py-1.5 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all" 
                on:input={(e) => onFilterChange(group.id, 'establishment_year', e.currentTarget?.value || '')}
              />
              <span class="text-sm text-gray-600 ml-1">년도 이상</span>
            </div>
          </div>  

        {:else}
          <div class="border rounded-lg {shouldShowApplyButton(group.id) ? 'p-6' : 'p-3'} bg-gray-50">
            <div class="grid {shouldShowApplyButton(group.id) ? 'grid-cols-1 gap-1' : 'grid-cols-2 gap-2'}">
              {#each group.options as option}
                {#if (['employee_count', 'sales', 'profit', 'net_profit', 'unallocated_profit'].includes(group.id)) && option.id === 'range'}
                  <div class="flex items-center gap-1">
                    <input
                      type="number"
                      placeholder="최소"
                      value={selectedFilters[group.id]?.min || ''}
                      class="w-20 px-1.5 py-1 text-sm border border-gray-300 rounded-md focus:ring-1 focus:ring-blue-500 focus:border-blue-500 transition-all"
                      on:input={(e) => onFilterChange(group.id, 'min', e.currentTarget?.value || '')}
                    />
                    <span class="text-xs text-gray-600 whitespace-nowrap">{group.id === 'employee_count' ? '명' : '백만'}</span>
                    <span class="text-xs text-gray-600 mx-0.5">~</span>
                    <input
                      type="number"
                      placeholder="최대"
                      value={selectedFilters[group.id]?.max || ''}
                      class="w-20 px-1.5 py-1 text-sm border border-gray-300 rounded-md focus:ring-1 focus:ring-blue-500 focus:border-blue-500 transition-all"
                      on:input={(e) => onFilterChange(group.id, 'max', e.currentTarget?.value || '')}
                    />
                    <span class="text-xs text-gray-600 whitespace-nowrap">{group.id === 'employee_count' ? '명' : '백만'}</span>
                  </div>
                {:else}
                <div class="border rounded-lg p-1 bg-gray-50"> 
                  <div class="flex items-center gap-2">
                    <label class="flex items-center hover:bg-white rounded-md transition-all"> 
                      <input
                        type={group.isMulti ? 'checkbox' : 'radio'}
                        name={group.id}
                        checked={
                          group.isMulti
                            ? (Array.isArray(selectedFilters[group.id]?.value) 
                              && selectedFilters[group.id]?.value.includes(option.id))
                            : selectedFilters[group.id]?.value === option.id
                        }
                        on:change={(e) => onFilterChange(
                          group.id,
                          option.id,
                          group.isMulti ? e.currentTarget?.checked : option.id
                        )}
                        class="w-4 h-4 text-blue-600 mr-2"
                      />
                      <span class="text-sm text-gray-700">{option.label}</span>
                    </label>
                  </div>
                </div>

                {/if}
              {/each}
            </div>
          </div>
        {/if}
      </div>
    </div>
  </div>
{/if}

