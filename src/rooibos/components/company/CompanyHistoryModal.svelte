<script lang="ts">
  import { selectedCompanyInfo } from '$rooibos/stores';
  import { goto } from '$app/navigation';
  import { fade } from 'svelte/transition';
  import XMark from '../../../lib/components/icons/XMark.svelte';

  export let show = false;
  export let onClose = () => {};

  let history: any[] = [];
  $: {
    if (show) {
      history = selectedCompanyInfo.getHistory() || [];
      if (history.length === 1) {
        selectedCompanyInfo.set(history[0]);
        onClose();
      } else if (history.length === 0) {
        goto('/rooibos/corpsearch');
      }
    }
  }
</script>

{#if show}
  <div
    class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50"
    transition:fade={{ duration: 200 }}
    on:click|self={onClose}
  >
    <div class="bg-white dark:bg-gray-800 rounded-xl w-full max-w-lg overflow-hidden">
      <div class="flex items-center justify-between p-4 border-b dark:border-gray-700">
        <h2 class="text-lg font-semibold">최근 선택한 기업</h2>
        <button
          class="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          on:click={onClose}
        >
          <XMark />
        </button>
      </div>
      
      <div class="p-4 max-h-[60vh] overflow-y-auto">
        {#if history.length > 0}
          <div class="space-y-2">
            {#each history as company}
              <button
                class="w-full p-3 text-left hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg transition-colors flex items-center justify-between"
                on:click={() => {
                  selectedCompanyInfo.set(company);
                  onClose();
                }}
              >
                <div>
                  <div class="font-medium">{company.company_name}</div>
                  {#if company.company_code}
                    <div class="text-sm text-gray-500">{company.company_code}</div>
                  {/if}
                </div>
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-gray-400"><path d="M9 18l6-6-6-6"/></svg>
              </button>
            {/each}
          </div>
        {:else}
          <div class="text-center text-gray-500 py-8">
            최근 선택한 기업이 없습니다
          </div>
        {/if}
      </div>
    </div>
  </div>
{/if} 