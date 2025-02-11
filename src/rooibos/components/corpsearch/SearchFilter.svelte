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
  export let filterChange: (
    groupId: string,
    optionId: string,
    checked: boolean | string
  ) => void;
  export let onReset: () => void;
  export let onApply: () => void;
  export let activeGroup: string | null;

  $: group = filterGroups.find((g) => g.id === activeGroup);

  let rangeMin = '';
  let rangeMax = '';
  let prevGroupId: string | null = null;

  // 그룹이 변경될 때만 초기값을 설정하도록 수정
  $: if (group && group.id !== prevGroupId && ['employee_count', 'sales', 'profit', 'net_profit', 'unallocated_profit'].includes(group.id)) {
    rangeMin = selectedFilters[group.id]?.min || "";
    rangeMax = selectedFilters[group.id]?.max || "";
    prevGroupId = group.id;
  }

  let ageValue = selectedFilters['representative_age']?.value || '';
  let establishmentYearValue = selectedFilters['establishment_year']?.value || '';

  const applyButtonGroups = [
    'employee_count',
    'sales',
    'profit',
    'net_profit',
    'representative_age',
    'unallocated_profit',
    'establishment_year'
  ];

  function shouldShowApplyButton(groupId: string): boolean {
    return applyButtonGroups.includes(groupId);
  }

  const checkFilter = async (filter: any) => {
    if (filter.id === 'representative_age') {
      await filterChange(filter.id, 'representative_age', ageValue);
    } else if (filter.id === 'establishment_year') {
      await filterChange(filter.id, 'establishment_year', establishmentYearValue);
    } else if (['employee_count', 'sales', 'profit', 'net_profit', 'unallocated_profit'].includes(filter.id)) {
      await filterChange(filter.id, '', { min: rangeMin, max: rangeMax });
    } else {
      const value = selectedFilters[filter.id];
      if (
        !value ||
        value === '' ||
        (typeof value === 'object' &&
          (Object.keys(value).length === 0 ||
            Object.keys(value).every((key) => value[key] === '')))
      ) {
        delete selectedFilters[filter.id];
      }
    }
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
        {#if group.id === 'representative_age'}
          <div class="border rounded-lg p-7 bg-gray-50"> 
            <div class="flex items-center gap-2">
              <input
                type="number"
                placeholder="나이 입력"
                bind:value={ageValue}
                class="w-20 px-2 py-1.5 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all" 
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
                    checked={selectedFilters[group.id]?.value === option.id || option.id == ''}
                    on:change={async () => await filterChange(group.id, option.id, option.id)}
                    class="w-4 h-4 text-blue-600 mr-2"
                  />
                  <span class="text-sm text-gray-700">{option.label}</span>
                </label>
              {/each}
            </div>
          </div>
        {:else if group.id === 'establishment_year'}
        <div class="border rounded-lg p-7 bg-gray-50"> 
          <div class="flex items-center gap-2">
            <input
              type="number"
              placeholder="연도 입력"
              bind:value={establishmentYearValue}
              on:input={(e) => establishmentYearValue = e.currentTarget.value}
              class="w-20 px-2 py-1.5 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all" 
            />
            <span class="text-sm text-gray-600 ml-1">년 이상</span>
          </div>
        </div> 

        {:else}
          <div class="border rounded-lg {shouldShowApplyButton(group.id) ? 'p-6' : 'p-3'} bg-gray-50">
            <div class="grid {shouldShowApplyButton(group.id) ? 'grid-cols-1 gap-1' : 'grid-cols-2 gap-2'}">
             
              {#if ['employee_count', 'sales', 'profit', 'net_profit', 'unallocated_profit'].includes(group.id)}
                <div class="flex items-center gap-1">
                  <label class="flex items-center hover:bg-white rounded-md transition-all">
                    <span class="text-sm text-gray-700 mr-2">최소</span>
                    <input
                      type="number"
                      name={`${group.id}-min`}
                      bind:value={rangeMin}
                      min={group.min}
                      class="w-20 h-8 text-gray-700 border rounded-md p-1"
                    />
                  </label>
                  
                  <label class="flex items-center hover:bg-white rounded-md transition-all">
                    <span class="text-sm text-gray-700 mr-2">최대</span>
                    <input
                      type="number"
                      name={`${group.id}-max`}
                      bind:value={rangeMax}
                      min={group.min}
                      max={group.max}
                      class="w-20 h-8 text-gray-700 border rounded-md p-1"
                    />
                  </label>
                </div>
              {/if}

                {#if group.options}
                {#each group.options as option}
                <div class="rounded-lg p-1 bg-gray-50"> 
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
                        on:change={async (e) => await filterChange(
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
                {/each}
                {/if}
            </div>
          </div>
        {/if}
      </div>
    </div>
  </div>
{/if}

