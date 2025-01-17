<script lang="ts">
  interface SearchResult {
    smtp_id: string;
    company_name: string;
    address: string;
    latitude: string;
    longitude: string;
    phone_number?: string;
    category?: string[];
    business_registration_number?: string;
    representative?: string;
    birth_date?: string;
    industry?: string;
    establishment_date?: string;
    employee_count?: number;
    recent_sales?: number;
    recent_revenue?: number;
    recent_profit?: number;
    website?: string;
    distance_from_user?: number;
    bookmark_id?: string | null;    
    fax_number?: string;
    email?: string;
    company_type?: string;
    founding_date?: string;
    industry_code1?: string;
    industry_code2?: string;
    main_product?: string;
    main_bank?: string;
    main_branch?: string;
    group_name?: string;
    stock_code?: string;
    corporate_number?: string;
    english_name?: string;
    trade_name?: string;
    fiscal_month?: string;
    sales_year?: string;
    profit_year?: string;
    operating_profit_year?: string;
    recent_operating_profit?: number;
    asset_year?: string;
    recent_total_assets?: number;
    debt_year?: string;
    recent_total_debt?: number;
    equity_year?: string;
    recent_total_equity?: number;
    capital_year?: string;
    recent_capital?: number;
    region1?: string;
    region2?: string;
    industry_major?: string;
    industry_middle?: string;
    industry_small?: string;
    certificate_expiry_date?: string;
    sme_type?: string;
    cri_company_size?: string;
    lab_name?: string;
    first_approval_date?: string;
    lab_location?: string;
    research_field?: string;
    division?: string;
    birth_year?: string;
    foundation_year?: string;
    family_shareholder_yn?: string;
    external_shareholder_yn?: string;
    financial_statement_year?: string;
    employees?: number;
    total_assets?: number;
    total_equity?: number;
    sales_amount?: number;
    net_income?: number;
    venture_confirmation_type?: string;
    svcl_region?: string;
    venture_valid_from?: string;
    venture_valid_until?: string;
    confirming_authority?: string;
    new_reconfirmation_code?: string;
  }
  import { showSidebar, mobile } from '$lib/stores';
  export let searchResults: SearchResult[] = [];
  export let onResultClick: (result: SearchResult) => void;
</script>

<div 
  class="fixed bottom-0 bg-gray-50 shadow-lg pl-2 pt-2 rounded-t-2xl overflow-y-auto z-40 transition-all duration-300
  md:max-h-[calc(100vh-140px)] 
  max-h-[calc(100vh+50px)]"
  class:sidebar-margin={$showSidebar}
  class:mobile-layout={$mobile}
>
  <ul class="p-4 space-y-2 overflow-y-auto">
    {#each searchResults as result}
      <li>
        <button 
          on:click={() => onResultClick(result)} 
          class="w-full text-left bg-white rounded-lg p-4 shadow-sm hover:bg-gray-50 transition-colors duration-200 border border-gray-200" 
          type="button"
        >
          <div class="flex items-start justify-between">
            <div class="flex-1">
              <div class="font-semibold text-gray-900">{result.company_name} ({result.business_registration_number})</div>
              <div class="text-sm text-gray-600 mt-1.5">{result.address}</div>
              {#if result.representative}
                <div class="text-sm text-gray-500 mt-1">대표자: {result.representative}</div>
              {/if}
              {#if result.industry}
                <div class="text-sm text-gray-500 mt-1">업종: {result.industry}</div>
              {/if}
              {#if result.phone_number}
                <div class="text-sm text-gray-500 mt-1">전화번호: {result.phone_number}</div>
              {/if}
              {#if result.main_product}
                <div class="text-sm text-gray-500 mt-1">주요 상품: {result.main_product}</div>
              {/if}
              {#if result.total_assets}
                <div class="text-sm text-gray-500 mt-1">총 자산: {result.total_assets.toLocaleString()}역</div>
              {/if}
              {#if result.total_equity}
                <div class="text-sm text-gray-500 mt-1">총 자본: {result.total_equity.toLocaleString()}억</div>
              {/if}
              {#if result.sales_amount}
                <div class="text-sm text-gray-500 mt-1">최근 매출: {result.sales_amount.toLocaleString()}억</div>
              {/if}
              {#if result.net_income}
                <div class="text-sm text-gray-500 mt-1">당기 순이익: {result.net_income.toLocaleString()}억</div>
              {/if}
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

  .sidebar-margin {
    left: 210px;
  }

  .mobile-layout {
    height: 70vh;
    max-height: 70vh;
    border-top-left-radius: 16px;
    border-top-right-radius: 16px;
  }
</style>
