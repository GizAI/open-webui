<script lang="ts">
    import { createEventDispatcher, getContext } from 'svelte';
    import { fade } from 'svelte/transition';
    import { flyAndScale } from '$lib/utils/transitions';
    import { toast } from 'svelte-sonner';
	import { WEBUI_API_BASE_URL } from '$lib/constants';
	import { get } from 'svelte/store';
	import { user } from '$lib/stores';
    
    // i18n 스토어 설정
    const i18n: { subscribe: any; t: (key: string) => string } = getContext('i18n');
    const dispatch = createEventDispatcher<{
        close: void;
        added: { company_name: string; smtp_id: string; item_type: string };
    }>();
    
    export let show = true;
    export let folderId: string | null = null;
    
    // 항목 유형 선택 (기업 또는 고객)
    let itemType: 'company' | 'customer' = 'company';
    
    // 기업 정보 폼 데이터
    let companyData = {
        company_name: '',
        representative: '',
        address: '',
        phone_number: '',
        website: '',
        email: '',
        establishment_date: '',
        employee_count: '',
        industry: '',
        main_product: ''
    };
    
    // 고객 정보 폼 데이터
    let customerData = {
        representative: '',
        address: '',
        phone_number: '',
        email: ''
    };
    
    let isSubmitting = false;
    let modalElement: HTMLElement | null = null;
    
    // 폼 제출 처리
    async function handleSubmit() {
        if (itemType === 'company') {
            if (!companyData.company_name) {
                toast.error('회사명은 필수 입력 항목입니다.');
                return;
            }
        } else {
            if (!customerData.representative) {
                toast.error('대표자는 필수 입력 항목입니다.');
                return;
            }
        }
        
        isSubmitting = true;
        
        try {
            const currentUser = get(user);
            const payload = itemType === 'company'
                ? {
                    company_data: companyData,
                    folder_id: folderId,
                    userId: currentUser?.id,
                    item_type: 'company',
                    entity_type: 'COMPANY'
                }
                : {
                    customer_data: customerData,
                    folder_id: folderId,
                    userId: currentUser?.id,
                    item_type: 'customer',
                    entity_type: 'CUSTOMER'
                };
            
            console.log('Sending payload:', payload);
            
            const response = await fetch(`${WEBUI_API_BASE_URL}/rooibos/mycompanies/company/add`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${localStorage.token}`
                },
                body: JSON.stringify(payload)
            });
            
            const result = await response.json();
            
            if (result.success) {
                const successMessage = itemType === 'company' 
                    ? '기업 정보가 성공적으로 저장되었습니다.' 
                    : '고객 정보가 성공적으로 저장되었습니다.';
                toast.success(successMessage);
                dispatch('added', itemType === 'company' 
                    ? { company_name: companyData.company_name, smtp_id: result.data.smtp_id, item_type: 'company' } 
                    : { company_name: customerData.representative, smtp_id: result.data.smtp_id, item_type: 'customer' });
                closeModal();
            } else {
                toast.error(result.message || '저장 중 오류가 발생했습니다.');
            }
        } catch (error) {
            toast.error('서버 연결 오류: ' + error);
        } finally {
            isSubmitting = false;
        }
    }
    
    // 모달 닫기
    function closeModal() {
        show = false;
        dispatch('close');
        
        // 폼 초기화
        companyData = {
            company_name: '',
            representative: '',
            address: '',
            phone_number: '',
            website: '',
            email: '',
            establishment_date: '',
            employee_count: '',
            industry: '',
            main_product: ''
        };
        
        customerData = {
            representative: '',
            address: '',
            phone_number: '',
            email: ''
        };
    }
    
    // ESC 키 처리
    function handleKeyDown(event: KeyboardEvent) {
        if (event.key === 'Escape') {
            closeModal();
        }
    }
    
    $: if (show && modalElement) {
        document.body.appendChild(modalElement);
        window.addEventListener('keydown', handleKeyDown);
        document.body.style.overflow = 'hidden';
    } else if (modalElement) {
        window.removeEventListener('keydown', handleKeyDown);
        try {
            document.body.removeChild(modalElement);
        } catch (e) {}
        document.body.style.overflow = 'unset';
    }
</script>

{#if show}
    <!-- svelte-ignore a11y-click-events-have-key-events -->
    <!-- svelte-ignore a11y-no-static-element-interactions -->
    <div
        bind:this={modalElement}
        class="fixed inset-0 bg-black/60 w-full h-screen flex items-center justify-center z-99999999"
        in:fade={{ duration: 100 }}
        on:mousedown={closeModal}
    >
        <div
            class="rounded-2xl w-[38rem] max-w-[calc(100%-2rem)] bg-gray-50 dark:bg-gray-950 max-h-[85vh] shadow-3xl overflow-hidden flex flex-col"
            in:flyAndScale
            on:mousedown={(e) => e.stopPropagation()}
        >
            <div class="px-4 py-1.5 border-b border-gray-200 dark:border-gray-800">
                <h2 class="text-base font-semibold dark:text-gray-200">
                    {itemType === 'company' ? '기업정보 추가' : '고객정보 추가'}
                </h2>
            </div>
            
            <form on:submit|preventDefault={handleSubmit} class="px-4 py-1 overflow-y-auto flex-1">
                <!-- 기업/고객 선택 탭 -->
                <div class="md:col-span-2 mb-3 border-b border-gray-200 dark:border-gray-800">
                    <div class="flex">
                        <button 
                            type="button"
                            class="py-1 px-4 text-sm font-medium transition-colors duration-200 focus:outline-none {itemType === 'company' ? 'text-blue-600 border-b-2 border-blue-600 dark:text-blue-400 dark:border-blue-400' : 'text-gray-600 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'}"
                            on:click={() => itemType = 'company'}
                        >
                            기업
                        </button>
                        <button 
                            type="button"
                            class="py-1 px-4 text-sm font-medium transition-colors duration-200 focus:outline-none {itemType === 'customer' ? 'text-blue-600 border-b-2 border-blue-600 dark:text-blue-400 dark:border-blue-400' : 'text-gray-600 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'}"
                            on:click={() => itemType = 'customer'}
                        >
                            고객
                        </button>
                    </div>
                </div>
                
                {#if itemType === 'company'}
                    <!-- 기업 정보 폼 -->
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-1.5">                        
                        <!-- 회사명 -->
                        <div class="form-group">
                            <label for="company_name" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-0">
                                회사명 <span class="text-red-500">*</span>
                            </label>
                            <input
                                type="text"
                                id="company_name"
                                bind:value={companyData.company_name}
                                class="w-full px-2 py-0.5 text-sm border border-gray-300 dark:border-gray-700 rounded-md dark:bg-gray-800 dark:text-gray-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
                                required
                            />
                        </div>
                        
                        <!-- 대표자 -->
                        <div class="form-group">
                            <label for="representative" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-0">
                                대표자
                            </label>
                            <input
                                type="text"
                                id="representative"
                                bind:value={companyData.representative}
                                class="w-full px-2 py-0.5 text-sm border border-gray-300 dark:border-gray-700 rounded-md dark:bg-gray-800 dark:text-gray-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
                            />
                        </div>
                        
                        <!-- 주소 -->
                        <div class="form-group md:col-span-2">
                            <label for="address" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-0">
                                주소
                            </label>
                            <input
                                type="text"
                                id="address"
                                bind:value={companyData.address}
                                class="w-full px-2 py-0.5 text-sm border border-gray-300 dark:border-gray-700 rounded-md dark:bg-gray-800 dark:text-gray-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
                            />
                        </div>
                        
                        <!-- 설립일 -->
                        <div class="form-group">
                            <label for="establishment_date" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-0">
                                설립일
                            </label>
                            <input
                                type="date"
                                id="establishment_date"
                                bind:value={companyData.establishment_date}
                                class="w-full px-2 py-0.5 text-sm border border-gray-300 dark:border-gray-700 rounded-md dark:bg-gray-800 dark:text-gray-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
                            />
                        </div>
                        
                        <!-- 직원 수 -->
                        <div class="form-group">
                            <label for="employee_count" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-0">
                                직원 수
                            </label>
                            <input
                                type="number"
                                id="employee_count"
                                bind:value={companyData.employee_count}
                                class="w-full px-2 py-0.5 text-sm border border-gray-300 dark:border-gray-700 rounded-md dark:bg-gray-800 dark:text-gray-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
                            />
                        </div>
                        
                        <!-- 전화번호 -->
                        <div class="form-group">
                            <label for="phone_number" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-0">
                                전화번호
                            </label>
                            <input
                                type="text"
                                id="phone_number"
                                bind:value={companyData.phone_number}
                                class="w-full px-2 py-0.5 text-sm border border-gray-300 dark:border-gray-700 rounded-md dark:bg-gray-800 dark:text-gray-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
                            />
                        </div>
                        
                        <!-- 웹사이트 -->
                        <div class="form-group">
                            <label for="website" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-0">
                                웹사이트
                            </label>
                            <input
                                type="url"
                                id="website"
                                bind:value={companyData.website}
                                class="w-full px-2 py-0.5 text-sm border border-gray-300 dark:border-gray-700 rounded-md dark:bg-gray-800 dark:text-gray-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
                                placeholder="https://example.com"
                            />
                        </div>
                        
                        <!-- 이메일 -->
                        <div class="form-group">
                            <label for="email" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-0">
                                이메일
                            </label>
                            <input
                                type="email"
                                id="email"
                                bind:value={companyData.email}
                                class="w-full px-2 py-0.5 text-sm border border-gray-300 dark:border-gray-700 rounded-md dark:bg-gray-800 dark:text-gray-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
                            />
                        </div>
                        
                        <!-- 업종 정보 섹션 -->
                        <div class="md:col-span-2 mt-0.5">
                            <h3 class="text-xs font-semibold text-gray-500 mb-0.5">업종 정보</h3>
                        </div>
                        
                        <!-- 업종 -->
                        <div class="form-group">
                            <label for="industry" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-0">
                                업종
                            </label>
                            <input
                                type="text"
                                id="industry"
                                bind:value={companyData.industry}
                                class="w-full px-2 py-0.5 text-sm border border-gray-300 dark:border-gray-700 rounded-md dark:bg-gray-800 dark:text-gray-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
                            />
                        </div>
                        
                        <!-- 주요상품 -->
                        <div class="form-group">
                            <label for="main_product" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-0">
                                주요상품
                            </label>
                            <input
                                type="text"
                                id="main_product"
                                bind:value={companyData.main_product}
                                class="w-full px-2 py-0.5 text-sm border border-gray-300 dark:border-gray-700 rounded-md dark:bg-gray-800 dark:text-gray-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
                            />
                        </div>
                    </div>
                {:else}
                    <!-- 고객 정보 폼 -->
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-1.5">
                        
                        <!-- 대표자 -->
                        <div class="form-group md:col-span-2">
                            <label for="customer_representative" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-0">
                                성명 <span class="text-red-500">*</span>
                            </label>
                            <input
                                type="text"
                                id="customer_representative"
                                bind:value={customerData.representative}
                                class="w-full px-2 py-0.5 text-sm border border-gray-300 dark:border-gray-700 rounded-md dark:bg-gray-800 dark:text-gray-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
                                required
                            />
                        </div>
                        
                        <!-- 주소 -->
                        <div class="form-group md:col-span-2">
                            <label for="customer_address" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-0">
                                주소
                            </label>
                            <input
                                type="text"
                                id="customer_address"
                                bind:value={customerData.address}
                                class="w-full px-2 py-0.5 text-sm border border-gray-300 dark:border-gray-700 rounded-md dark:bg-gray-800 dark:text-gray-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
                            />
                        </div>
                        
                        <!-- 전화번호 -->
                        <div class="form-group">
                            <label for="customer_phone" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-0">
                                전화번호
                            </label>
                            <input
                                type="text"
                                id="customer_phone"
                                bind:value={customerData.phone_number}
                                class="w-full px-2 py-0.5 text-sm border border-gray-300 dark:border-gray-700 rounded-md dark:bg-gray-800 dark:text-gray-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
                            />
                        </div>
                        
                        <!-- 이메일 -->
                        <div class="form-group">
                            <label for="customer_email" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-0">
                                이메일
                            </label>
                            <input
                                type="email"
                                id="customer_email"
                                bind:value={customerData.email}
                                class="w-full px-2 py-0.5 text-sm border border-gray-300 dark:border-gray-700 rounded-md dark:bg-gray-800 dark:text-gray-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
                            />
                        </div>
                    </div>
                {/if}
                
                <div class="flex justify-end gap-2 mb-2 mt-4 pt-2 border-t border-gray-200 dark:border-gray-800">
                    <button
                        type="button"
                        class="px-2 py-0.5 bg-gray-200 hover:bg-gray-300 text-gray-800 dark:bg-gray-700 dark:hover:bg-gray-600 dark:text-white rounded-md transition-colors text-xs"
                        on:click={closeModal}
                        disabled={isSubmitting}
                    >
                        취소
                    </button>
                    <button
                        type="submit"
                        class="px-2 py-0.5 bg-transparent border border-blue-500 text-blue-500 hover:text-blue-600 rounded-md transition-colors disabled:opacity-70 disabled:cursor-not-allowed text-xs"
                        disabled={isSubmitting}
                    >
                        {isSubmitting ? '저장 중...' : '저장'}
                    </button>
                </div>
            </form>
        </div>
    </div>
{/if}

<style>
    .form-group {
        margin-bottom: 0.125rem;
    }
    /* 폼이 내용에 맞게 자동으로 높이 조정되도록 설정 */
    form {
        max-height: calc(85vh - 6rem);
        overflow-y: auto;
    }
</style> 