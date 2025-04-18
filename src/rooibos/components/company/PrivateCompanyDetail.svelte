<script lang="ts">
	import { MapPin, Briefcase, Calendar, Phone, Mail, Globe, Users } from 'lucide-svelte';
	import { toast } from 'svelte-sonner';
	import { onMount } from 'svelte';
	import { WEBUI_API_BASE_URL } from '$lib/constants';
	import { mobile } from '$lib/stores';
	
	// 북마크 데이터 받기
	export let bookmark: any;
	// URL에서 받은 엔티티 타입 (company 또는 customer)
	export let entityType: string = '';	
	
	// 수정 모드 관련 상태 - 항상 수정 가능하도록 변경
	let isSaving = false;
	let editableData: any = null;
	let entityTypeValue: string = '';
	
	// 컴포넌트 초기화 시 바로 데이터 로드
	onMount(() => {
		// URL에서 전달받은 entityType을 우선적으로 사용하고, 없으면 bookmark에서 가져옴
		// 대소문자 구분 없이 처리
		entityTypeValue = entityType || bookmark?.entity_type?.toLowerCase() || 'company';
		
		// 컴포넌트가 마운트되면 바로 편집 가능한 데이터 초기화
		if (entityTypeValue === 'customer') {
			// 고객용 데이터 초기화
			editableData = {
				representative: bookmark?.representative || '',
				company_name: bookmark?.company_name || '',
				address: bookmark?.address || '',
				phone_number: bookmark?.phone_number || '',
				email: bookmark?.email || '',
				business_registration_number: bookmark?.business_registration_number || ''
			};
		} else {
			// 기업용 데이터 초기화 (기본값)
			editableData = {
				company_name: bookmark?.company_name || '',
				representative: bookmark?.representative || '',
				address: bookmark?.address || '',
				phone_number: bookmark?.phone_number || '',
				fax_number: bookmark?.fax_number || '',
				email: bookmark?.email || '',
				website: bookmark?.website || '',
				establishment_date: bookmark?.establishment_date || '',
				employee_count: bookmark?.employee_count || '',
				industry: bookmark?.industry || '',
				main_product: bookmark?.main_product || '',
				business_registration_number: bookmark?.business_registration_number || ''
			};
		}
	});
	
	// 데이터 저장
	async function saveData() {
		if (!editableData) return;
		
		isSaving = true;
		
		try {
			const response = await fetch(`${WEBUI_API_BASE_URL}/rooibos/mycompanies/company/update`, {
				method: 'PUT',
				headers: {
					'Content-Type': 'application/json',
					'Authorization': `Bearer ${localStorage.token}`
				},
				body: JSON.stringify({
					company_data: editableData,
					business_registration_number: bookmark.business_registration_number,
					entity_type: entityTypeValue
				})
			});
			
			const data = await response.json();
			
			if (data.success) {
				Object.assign(bookmark, editableData);
			} else {
				toast.error(`저장 실패: ${data.message || '알 수 없는 오류'}`);
			}
		} catch (error) {
			console.error('정보 저장 중 오류:', error);
			toast.error('정보 저장 중 오류가 발생했습니다.');
		} finally {
			isSaving = false;
		}
	}
	
	// 날짜 포맷 함수
	function formatDate(dateString: string): string {
		if (!dateString) return '';
		
		try {
			const date = new Date(dateString);
			return date.toLocaleDateString('ko-KR', {
				year: 'numeric',
				month: 'long',
				day: 'numeric'
			});
		} catch (error) {
			return dateString;
		}
	}
</script>

<div class="company-info-wrapper active flex flex-col w-full">
	<div class="{$mobile ? 'pt-0' : ''}">
		<div class="mt-2">
			<!-- 기본 정보 -->
			<div class="border-gray-100 pb-4 text-gray-900 dark:text-gray-500">
				<div class="flex justify-between items-center mb-2">
					<h3 class="text-sm font-semibold text-gray-400 flex items-center gap-2">
						<MapPin size={16} class="text-blue-500" />
						{entityTypeValue === 'customer' ? '고객 정보' : '기업 정보'}
					</h3>
					{#if editableData}
						<button
							class="px-4 py-1.5 text-sm font-medium text-blue-500 border border-blue-500 hover:bg-blue-50 bg-transparent rounded-md transition-colors"
							on:click={saveData}
							disabled={isSaving}
						>
							{isSaving ? '저장 중...' : '저장'}
						</button>
					{/if}
				</div>
				
				{#if editableData}
					<!-- 수정 폼 -->
					<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm">
						{#if entityTypeValue === 'customer'}
							<!-- 고객 정보 폼 -->
							<div class="grid grid-cols-2 gap-3 p-3">
								<div class="space-y-1 col-span-2">
									<label class="block text-sm font-medium text-gray-700 dark:text-gray-300">성명</label>
									<input
										type="text"
										bind:value={editableData.representative}
										class="w-full px-3 py-1.5 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
									/>
								</div>
								
								<div class="space-y-1 col-span-2">
									<label class="block text-sm font-medium text-gray-700 dark:text-gray-300">주소</label>
									<input
										type="text"
										bind:value={editableData.address}
										class="w-full px-3 py-1.5 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
									/>
								</div>
								
								<div class="space-y-1 col-span-2">
									<label class="block text-sm font-medium text-gray-700 dark:text-gray-300">전화번호</label>
									<input
										type="text"
										bind:value={editableData.phone_number}
										class="w-full px-3 py-1.5 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
									/>
								</div>
								
								<div class="space-y-1 col-span-2">
									<label class="block text-sm font-medium text-gray-700 dark:text-gray-300">이메일</label>
									<input
										type="email"
										bind:value={editableData.email}
										class="w-full px-3 py-1.5 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
									/>
								</div>
							</div>
						{:else}
							<!-- 기업 정보 폼 -->
							<div class="grid grid-cols-2 gap-3 p-3">
								<div class="{$mobile ? 'col-span-2' : ''} space-y-1">
									<label class="block text-sm font-medium text-gray-700 dark:text-gray-300">회사명</label>
									<input
										type="text"
										bind:value={editableData.company_name}
										class="w-full px-3 py-1.5 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
									/>
								</div>
								
								<div class="{$mobile ? 'col-span-2' : ''} space-y-1">
									<label class="block text-sm font-medium text-gray-700 dark:text-gray-300">대표자</label>
									<input
										type="text"
										bind:value={editableData.representative}
										class="w-full px-3 py-1.5 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
									/>
								</div>
								
								<div class="space-y-1 col-span-2">
									<label class="block text-sm font-medium text-gray-700 dark:text-gray-300">주소</label>
									<input
										type="text"
										bind:value={editableData.address}
										class="w-full px-3 py-1.5 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
									/>
								</div>
								
								<div class="{$mobile ? 'col-span-2' : ''} space-y-1">
									<label class="block text-sm font-medium text-gray-700 dark:text-gray-300">전화번호</label>
									<input
										type="text"
										bind:value={editableData.phone_number}
										class="w-full px-3 py-1.5 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
									/>
								</div>
								
								<div class="{$mobile ? 'col-span-2' : ''} space-y-1">
									<label class="block text-sm font-medium text-gray-700 dark:text-gray-300">팩스</label>
									<input
										type="text"
										bind:value={editableData.fax_number}
										class="w-full px-3 py-1.5 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
									/>
								</div>
								
								<div class="{$mobile ? 'col-span-2' : ''} space-y-1">
									<label class="block text-sm font-medium text-gray-700 dark:text-gray-300">이메일</label>
									<input
										type="email"
										bind:value={editableData.email}
										class="w-full px-3 py-1.5 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
									/>
								</div>
								
								<div class="{$mobile ? 'col-span-2' : ''} space-y-1">
									<label class="block text-sm font-medium text-gray-700 dark:text-gray-300">웹사이트</label>
									<input
										type="text"
										bind:value={editableData.website}
										class="w-full px-3 py-1.5 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
									/>
								</div>
								
								<div class="{$mobile ? 'col-span-2' : ''} space-y-1">
									<label class="block text-sm font-medium text-gray-700 dark:text-gray-300">설립일</label>
									<input
										type="date"
										bind:value={editableData.establishment_date}
										class="w-full px-3 py-1.5 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
									/>
								</div>
								
								<div class="{$mobile ? 'col-span-2' : ''} space-y-1">
									<label class="block text-sm font-medium text-gray-700 dark:text-gray-300">직원수</label>
									<input
										type="number"
										bind:value={editableData.employee_count}
										class="w-full px-3 py-1.5 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
									/>
								</div>
							
								<!-- 업종 정보 -->
								<div class="pt-3 border-gray-100 col-span-2 mt-2">									
									<div class="grid grid-cols-2 gap-3">
										<div class="{$mobile ? 'col-span-2' : ''}">
											<label class="block text-sm font-medium text-gray-700 dark:text-gray-300">업종</label>
											<input
												type="text"
												bind:value={editableData.industry}
												class="w-full px-3 py-1.5 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
											/>
										</div>
										
										<div class="{$mobile ? 'col-span-2' : ''}">
											<label class="block text-sm font-medium text-gray-700 dark:text-gray-300">주요 상품</label>
											<input
												type="text"
												bind:value={editableData.main_product}
												class="w-full px-3 py-1.5 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
											/>
										</div>
									</div>
								</div>
							</div>
						{/if}
					</div>
				{:else}
					<div class="h-40 flex items-center justify-center">
						<div class="text-gray-400">로딩 중...</div>
					</div>
				{/if}
			</div>

			<!-- 업종 정보 (기업에만 표시) -->
			{#if entityTypeValue !== 'customer' && (bookmark.industry || bookmark.main_product) && !editableData}
				<div class="border-t border-gray-100 pt-4 mt-2 text-gray-900 dark:text-gray-400">
					<h3 class="text-sm font-semibold text-gray-400 flex items-center gap-2 mb-2">
						<Briefcase size={16} class="text-blue-500" />
						업종 정보
					</h3>
					<div>
						<div class="text-sm flex items-center justify-between">
							<div class="flex gap-2">
								<span>업종:</span>
								<span>{bookmark.industry || '-'}</span>
							</div>
							<div class="flex gap-2">
								<span>주요상품:</span>
								<span>{bookmark.main_product || '-'}</span>
							</div>
						</div>
					</div>
				</div>
			{/if}
		</div>
	</div>
</div> 