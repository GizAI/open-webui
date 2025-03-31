<!-- src/lib/components/common/ActionButtons.svelte -->
<script lang="ts">
	import { goto } from '$app/navigation';
	import { WEBUI_API_BASE_URL } from '$lib/constants';
	import { user } from '$lib/stores';
	import { selectedCompanyInfo, triggerFolderUpdate } from '$rooibos/stores';
	import { get } from 'svelte/store';
	import DeleteConfirmDialog from '$lib/components/common/ConfirmDialog.svelte';
	import FolderSelect from '$rooibos/components/folder/FolderSelect.svelte';
	import { deleteCompanyBookmark } from '$rooibos/components/apis/company';
	import ChatCategories from '$rooibos/components/chat/ChatCategories.svelte';

	export let companyInfo: any = {};
	export let financialData: any = {};
	export let type: string = 'mycompany';
	export let isShared: boolean = false;

	const currentUser = get(user);

	let showDeleteConfirm = false;
	let showFolderSelect = false;
	let showCategoryModal = false;

	const addCompany = async (company: any, folderId: string = '') => {
		const response = await fetch(`${WEBUI_API_BASE_URL}/rooibos/mycompanies/add`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${localStorage.token}`
			},
			body: JSON.stringify({
				userId: currentUser?.id,
				companyId: company.master_id,
				business_registration_number: company.business_registration_number,
				folderId: folderId
			})
		});
		const data = await response.json();
		companyInfo.bookmark_id = data.id;
		companyInfo.bookmark_user_id = currentUser?.id;
	};

	const confirmDelete = async () => {
		try {
			await deleteCompanyBookmark(companyInfo.bookmark_id);
			// 삭제 후 상태 업데이트
			companyInfo.bookmark_id = null;
			companyInfo.bookmark_user_id = null;
		} catch (error) {
			console.error('Error in confirmDelete:', error);
		} finally {
			showDeleteConfirm = false;
		}
	};

	const saveCompany = async (company: any) => {
		if (company.bookmark_user_id != null && company.bookmark_user_id == currentUser?.id) {
			showDeleteConfirm = true;
		} else {
			showFolderSelect = true;
		}
	};

	const handleFolderSelect = async (event: { detail: any }) => {
		const selectedFolder = event.detail;
		if (selectedFolder && selectedFolder.id) {
			await addCompany(companyInfo, selectedFolder.id);
		} else {
			await addCompany(companyInfo);
		}
		showFolderSelect = false;
	};

	const closeFolderSelect = () => {
		showFolderSelect = false;
	};
	
	// 폴더 생성 이벤트 핸들러
	const handleFolderCreated = () => {
		// 폴더가 생성되면 전역 트리거 업데이트
		triggerFolderUpdate();
	};

	const openAIChat = async (company: any) => {	
		console.log('Before setting selectedCompanyInfo:', get(selectedCompanyInfo));
		console.log('Company data received:', company);
		
		if (type == 'mycompany') {
			const response = await fetch(`${WEBUI_API_BASE_URL}/rooibos/mycompanies/${company.bookmark_id}?business_registration_number=${company.business_registration_number}&user_id=${currentUser?.id}`, {
				method: 'GET',
				headers: {
					Accept: 'application/json',
					'Content-Type': 'application/json',
					Authorization: `Bearer ${localStorage.token}`
				}
			});
			
			const data = await response.json();
			console.log('API response data:', data);
			
			if (data.success !== false && data.bookmark && data.bookmark[0]) {
				const updatedCompany = data.bookmark[0];
				
				selectedCompanyInfo.set({
					...updatedCompany,
					financialData: financialData,
					files: updatedCompany.files
				});
				console.log('Set selectedCompanyInfo with bookmark data:', get(selectedCompanyInfo));
			} else {
				selectedCompanyInfo.set({
					...company,
					financialData: financialData,
					files: company.files
				});
				console.log('Set selectedCompanyInfo with company data (bookmark not found):', get(selectedCompanyInfo));
			}	
		} else if (type == 'companylist') {
			const financialResponse = await fetch(
				`${WEBUI_API_BASE_URL}/rooibos/corpsearch/${company.master_id}/financialData`,
				{
					method: 'GET',
					headers: {
						Accept: 'application/json',
						'Content-Type': 'application/json',
						authorization: `Bearer ${localStorage.token}`
					}
				}
			);
			const data = await financialResponse.json();
			financialData = data.financial_data;

			selectedCompanyInfo.set({
				...company,
				financialData: financialData,
				files: company.files
			});
			console.log('Set selectedCompanyInfo with company data (not companylist type):', get(selectedCompanyInfo));
		} else {
			selectedCompanyInfo.set({
				...company,
				financialData: financialData,
				files: company.files
			});
			console.log('Set selectedCompanyInfo with company data (not companyinfo type):', get(selectedCompanyInfo));
		}
		
		// URL 쿼리 파라미터를 추가하여 메인 페이지로 이동
		await goto('/?showCategory=true');
	};

	// 카테고리 선택 후 채팅 페이지로 이동하는 핸들러
	const handleModelSelect = async (event: { detail: any }) => {
		await goto('/');
	};

	const searchNaver = async (company: any) => {
		await window.open(
			`https://map.naver.com/v5/search/${encodeURIComponent(company.company_name)}`,
			'_blank'
		);
	};
</script>

<div class="flex items-center space-x-1">
	{#if !isShared}
		<button
			class="flex flex-col items-center hover:bg-gray-100 dark:hover:bg-gray-300 rounded-lg"
			on:click={() => saveCompany(companyInfo)}
		>
			<svg
				xmlns="http://www.w3.org/2000/svg"
				class="h-5 w-5 transition-colors duration-200"
				fill="none"
				viewBox="0 0 24 24"
				stroke="currentColor"
				class:text-yellow-500={companyInfo.bookmark_user_id == currentUser?.id}
				class:text-gray-500={companyInfo.bookmark_user_id != currentUser?.id}
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z"
				/>
			</svg>
			<span
				class="text-xs mt-1 whitespace-nowrap transition-colors duration-200"
				class:text-yellow-500={companyInfo.bookmark_user_id == currentUser?.id}
				class:text-gray-500={companyInfo.bookmark_user_id != currentUser?.id}
			>
				{companyInfo.bookmark_user_id == currentUser?.id ? '삭제' : '저장'}
			</span>
		</button>
	{/if}

	<!-- 새채팅 버튼 -->
	<button
		class="flex flex-col items-center hover:bg-gray-100 dark:hover:bg-gray-300 rounded-lg"
		on:click={() => openAIChat(companyInfo)}
	>
		<svg
			xmlns="http://www.w3.org/2000/svg"
			class="h-5 w-5 text-gray-500"
			fill="none"
			viewBox="0 0 24 24"
			stroke="currentColor"
		>
			<path
				stroke-linecap="round"
				stroke-linejoin="round"
				stroke-width="2"
				d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L10.582 16.07a4.5 4.5 0 0 1-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 0 1 1.13-1.897l8.932-8.931Zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0 1 15.75 21H5.25A2.25 2.25 0 0 1 3 18.75V8.25A2.25 2.25 0 0 1 5.25 6H10"
			/>
		</svg>
		<span class="text-xs text-gray-500 mt-1 whitespace-nowrap">새채팅</span>
	</button>

	<button
		class="flex flex-col items-center hover:bg-gray-100 dark:hover:bg-gray-300 rounded-lg"
		on:click={() => searchNaver(companyInfo)}
	>
		<svg
			xmlns="http://www.w3.org/2000/svg"
			class="h-5 w-5 text-gray-500"
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
		<span class="text-xs text-gray-500 mt-1 whitespace-nowrap">네이버지도</span>
	</button>
</div>

<DeleteConfirmDialog
	bind:show={showDeleteConfirm}
	title="나의기업에서 삭제하시겠습니까?"
	on:confirm={confirmDelete}
/>

{#if showFolderSelect}
	<FolderSelect
		isOpen={showFolderSelect}
		folderType="corp"
		bookmarkId={companyInfo.bookmark_id || ""}
		onClose={closeFolderSelect}
		on:close={handleFolderSelect}
		on:folderCreated={handleFolderCreated}
	/>
{/if}

<ChatCategories 
	bind:show={showCategoryModal} 
	on:select={handleModelSelect}
/>
