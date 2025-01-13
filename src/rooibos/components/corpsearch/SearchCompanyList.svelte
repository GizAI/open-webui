<script lang="ts">
  interface SearchResult {
    business_registration_number?: string;
    company_name: string;
    address: string;
    latitude: string;
    longitude: string;
  }
  import { showSidebar } from '$lib/stores';
  export let searchResults: SearchResult[] = [];
  export let onResultClick: (result: SearchResult) => void;
</script>

<div 
  class="fixed bottom-0 bg-gray-50 shadow-lg rounded-t-2xl overflow-y-auto z-40 transition-all duration-300"
  class:sidebar-margin={$showSidebar}
  style="max-height: calc(100% - 140px);"
>
  <ul class="p-4 space-y-3">
    {#each searchResults as result}
      <li>
        <button 
          on:click={() => onResultClick(result)} 
          class="w-full text-left bg-white rounded-lg p-4 shadow-sm hover:bg-gray-50 transition-colors duration-200 border border-gray-200" 
          type="button"
        >
          <div class="flex items-start justify-between">
            <div>
              <div class="font-semibold text-gray-900">{result.company_name}</div>
              <div class="text-sm text-gray-600 mt-1.5 leading-relaxed">{result.address}</div>
            </div>
            <svg 
              xmlns="http://www.w3.org/2000/svg" 
              class="h-5 w-5 text-gray-400 ml-4 flex-shrink-0" 
              fill="none" 
              viewBox="0 0 24 24" 
              stroke="currentColor"
            >
              <path 
                stroke-linecap="round" 
                stroke-linejoin="round" 
                stroke-width="2" 
                d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
              />
              <path 
                stroke-linecap="round" 
                stroke-linejoin="round" 
                stroke-width="2" 
                d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
              />
            </svg>
          </div>
        </button>
      </li>
    {/each}
  </ul>
</div>

<style>
  ul {
    list-style-type: none;
    margin: 0;
    padding: 0;
  }

  .fixed {
    left: 0;
    right: 0;
  }

  /* 사이드바가 보일 때 적용될 스타일 */
  .sidebar-margin {
    left: 210px;  /* 사이드바의 너비만큼 여백 설정 */
  }
</style>
