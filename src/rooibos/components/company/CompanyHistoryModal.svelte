<script lang="ts">
  import { selectedCompanyInfo } from '$rooibos/stores';
  import { goto } from '$app/navigation';
  import { fade } from 'svelte/transition';
  import XMark from '../../../lib/components/icons/XMark.svelte';
  import { onMount, onDestroy } from 'svelte';

  export let show = false;
  export let onClose = () => {};

  let history: any[] = [];
  $: {
    if (show) {
      history = selectedCompanyInfo.getHistory() || [];
      if (history.length === 1) {
        selectedCompanyInfo.set(history[0]);
        onClose();
        show = false;
      }
    }
  }

  function handleKeydown(event: KeyboardEvent) {
    if (event.key === 'Escape' && show) {
      onClose();
    }
  }

  onMount(() => {
    window.addEventListener('keydown', handleKeydown);
  });

  onDestroy(() => {
    window.removeEventListener('keydown', handleKeydown);
  });
</script>

{#if show && history.length !== 1}
  <div
    class="fixed inset-0 z-50 flex items-center justify-center p-4"
    transition:fade={{ duration: 200 }}
  >
    <!-- 배경 오버레이 -->
    <div 
      class="absolute inset-0 bg-black/50" 
      on:click={onClose}
    ></div>
    
    <!-- 모달 컨텐츠 -->
    <div class="relative bg-white dark:bg-gray-800 rounded-xl w-full max-w-lg overflow-hidden">
      <div class="flex items-center justify-between p-4 border-b dark:border-gray-700">
        <h2 class="text-lg font-semibold">최근 선택한 기업</h2>
        <button
          type="button"
          class="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          on:click={onClose}
        >
          <XMark />
        </button>
      </div>
      
      <div class="p-4 max-h-[60vh] overflow-y-auto">
        {#if history.length > 0}
          <div class="space-y-2">
            {#if history.length > 0}
              <div class="flex justify-end mb-2">
                <button
                  class="px-3 py-1.5 text-sm font-medium text-red-500 hover:text-white border border-red-500 hover:bg-red-600 rounded-lg transition-colors"
                  on:click={() => {
                    selectedCompanyInfo.clearHistory();
                    history = [];
                  }}
                >
                  전체 삭제
                </button>
              </div>
            {/if}
            {#each history as company}
              <div class="flex items-center gap-2">
                <button
                  class="flex-1 p-3 text-left hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg transition-colors flex items-center justify-between"
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
                <button
                  class="p-2 text-gray-400 hover:text-red-500 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                  on:click={() => {
                    selectedCompanyInfo.removeFromHistory(company.master_id);
                    history = selectedCompanyInfo.getHistory();
                  }}
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
                </button>
              </div>
            {/each}
          </div>
        {:else}
          <div class="text-center py-8">
            <div class="text-gray-500 mb-4">
              최근 선택한 기업이 없습니다
            </div>
            <button
              class="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
              on:click={() => {
                onClose();
                goto('/rooibos/corpsearch');
              }}
            >
              기업 검색
            </button>
          </div>
        {/if}
      </div>
    </div>
  </div>
{/if} 