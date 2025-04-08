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
        added: { company_name: string; smtp_id: string };
    }>();
    
    export let show = true;
    export let folderId: string | null = null;
    
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
    
    let isSubmitting = false;
    let modalElement: HTMLElement | null = null;
    
    // 폼 제출 처리
    async function handleSubmit() {
        if (!companyData.company_name) {
            toast.error('회사명은 필수 입력 항목입니다.');
            return;
        }
        
        isSubmitting = true;
        
        try {
            const currentUser = get(user);
            const response = await fetch(`${WEBUI_API_BASE_URL}/rooibos/mycompanies/company/add`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${localStorage.token}`
                },
                body: JSON.stringify({
                    company_data: companyData,
                    folder_id: folderId,
                    userId: currentUser?.id
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                toast.success('기업 정보가 성공적으로 저장되었습니다.');
                dispatch('added', result.data);
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
        class="fixed top-0 right-0 left-0 bottom-0 bg-black/60 w-full h-screen max-h-[100dvh] flex justify-center z-99999999 overflow-auto"
        in:fade={{ duration: 100 }}
        on:mousedown={closeModal}
    >
        <div
            class="m-auto rounded-2xl w-[38rem] max-w-full mx-4 my-2 bg-gray-50 dark:bg-gray-950 max-h-[85vh] shadow-3xl overflow-auto"
            in:flyAndScale
            on:mousedown={(e) => e.stopPropagation()}
        >
            <div class="px-6 py-3 border-b border-gray-200 dark:border-gray-800">
                <h2 class="text-lg font-semibold dark:text-gray-200">
                    {$i18n.t('기업정보 추가')}
                </h2>
            </div>
            
            <form on:submit|preventDefault={handleSubmit} class="px-6 py-1 pb-0">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-2">
                    <!-- 기본 정보 섹션 -->
                    <div class="md:col-span-2">
                        <h3 class="text-sm font-semibold text-gray-500 mb-1">기본 정보</h3>
                    </div>
                    
                    <!-- 회사명 -->
                    <div class="form-group">
                        <label for="company_name" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-0.5">
                            회사명 <span class="text-red-500">*</span>
                        </label>
                        <input
                            type="text"
                            id="company_name"
                            bind:value={companyData.company_name}
                            class="w-full px-3 py-1 border border-gray-300 dark:border-gray-700 rounded-md dark:bg-gray-800 dark:text-gray-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
                            required
                        />
                    </div>
                    
                    <!-- 대표자 -->
                    <div class="form-group">
                        <label for="representative" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-0.5">
                            대표자
                        </label>
                        <input
                            type="text"
                            id="representative"
                            bind:value={companyData.representative}
                            class="w-full px-3 py-1 border border-gray-300 dark:border-gray-700 rounded-md dark:bg-gray-800 dark:text-gray-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
                        />
                    </div>
                    
                    <!-- 주소 -->
                    <div class="form-group md:col-span-2">
                        <label for="address" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-0.5">
                            주소
                        </label>
                        <input
                            type="text"
                            id="address"
                            bind:value={companyData.address}
                            class="w-full px-3 py-1 border border-gray-300 dark:border-gray-700 rounded-md dark:bg-gray-800 dark:text-gray-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
                        />
                    </div>
                    
                    <!-- 설립일 -->
                    <div class="form-group">
                        <label for="establishment_date" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-0.5">
                            설립일
                        </label>
                        <input
                            type="date"
                            id="establishment_date"
                            bind:value={companyData.establishment_date}
                            class="w-full px-3 py-1 border border-gray-300 dark:border-gray-700 rounded-md dark:bg-gray-800 dark:text-gray-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
                        />
                    </div>
                    
                    <!-- 직원 수 -->
                    <div class="form-group">
                        <label for="employee_count" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-0.5">
                            직원 수
                        </label>
                        <input
                            type="number"
                            id="employee_count"
                            bind:value={companyData.employee_count}
                            class="w-full px-3 py-1 border border-gray-300 dark:border-gray-700 rounded-md dark:bg-gray-800 dark:text-gray-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
                        />
                    </div>
                    
                    <!-- 전화번호 -->
                    <div class="form-group">
                        <label for="phone_number" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-0.5">
                            전화번호
                        </label>
                        <input
                            type="text"
                            id="phone_number"
                            bind:value={companyData.phone_number}
                            class="w-full px-3 py-1 border border-gray-300 dark:border-gray-700 rounded-md dark:bg-gray-800 dark:text-gray-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
                        />
                    </div>
                    
                    <!-- 웹사이트 -->
                    <div class="form-group">
                        <label for="website" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-0.5">
                            웹사이트
                        </label>
                        <input
                            type="url"
                            id="website"
                            bind:value={companyData.website}
                            class="w-full px-3 py-1 border border-gray-300 dark:border-gray-700 rounded-md dark:bg-gray-800 dark:text-gray-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
                            placeholder="https://example.com"
                        />
                    </div>
                    
                    <!-- 이메일 -->
                    <div class="form-group">
                        <label for="email" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-0.5">
                            이메일
                        </label>
                        <input
                            type="email"
                            id="email"
                            bind:value={companyData.email}
                            class="w-full px-3 py-1 border border-gray-300 dark:border-gray-700 rounded-md dark:bg-gray-800 dark:text-gray-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
                        />
                    </div>
                    
                    <!-- 업종 정보 섹션 -->
                    <div class="md:col-span-2 mt-1">
                        <h3 class="text-sm font-semibold text-gray-500 mb-1">업종 정보</h3>
                    </div>
                    
                    <!-- 업종 -->
                    <div class="form-group">
                        <label for="industry" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-0.5">
                            업종
                        </label>
                        <input
                            type="text"
                            id="industry"
                            bind:value={companyData.industry}
                            class="w-full px-3 py-1 border border-gray-300 dark:border-gray-700 rounded-md dark:bg-gray-800 dark:text-gray-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
                        />
                    </div>
                    
                    <!-- 주요상품 -->
                    <div class="form-group">
                        <label for="main_product" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-0.5">
                            주요상품
                        </label>
                        <input
                            type="text"
                            id="main_product"
                            bind:value={companyData.main_product}
                            class="w-full px-3 py-1 border border-gray-300 dark:border-gray-700 rounded-md dark:bg-gray-800 dark:text-gray-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
                        />
                    </div>
                </div>
                
                <div class="flex justify-end gap-3 mb-0">
                    <button
                        type="button"
                        class="px-4 py-1 bg-gray-200 hover:bg-gray-300 text-gray-800 dark:bg-gray-700 dark:hover:bg-gray-600 dark:text-white rounded-md transition-colors"
                        on:click={closeModal}
                        disabled={isSubmitting}
                    >
                        {$i18n.t('취소')}
                    </button>
                    <button
                        type="submit"
                        class="px-4 py-1 bg-transparent border border-yellow-500 text-yellow-500 hover:bg-yellow-50 rounded-md transition-colors disabled:opacity-70 disabled:cursor-not-allowed"
                        disabled={isSubmitting}
                    >
                        {isSubmitting ? $i18n.t('저장 중...') : $i18n.t('저장')}
                    </button>
                </div>
            </form>
        </div>
    </div>
{/if}

<style>
    .form-group {
        margin-bottom: 0.25rem;
    }
</style> 