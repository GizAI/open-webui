<!-- src/lib/components/common/ActionButtons.svelte -->
<script lang="ts">
	import { goto } from '$app/navigation';
	import { WEBUI_API_BASE_URL } from '$lib/constants';
	import { user } from '$lib/stores';
	import { selectedCompanyInfo } from '$rooibos/stores';
	import { get } from 'svelte/store';
	import DeleteConfirmDialog from '$lib/components/common/ConfirmDialog.svelte';
	import FolderSelect from '$rooibos/components/folder/FolderSelect.svelte';

	export let companyInfo: any = {};
	export let financialData: any = {};

	const currentUser = get(user);

	// 삭제 확인 대화상자 제어 변수
	let showDeleteConfirm = false;
	// 폴더 선택 모달 제어 변수
	let showFolderSelect = false;

	// 북마크 추가 요청
	const addCompany = async (company: any, folderId: string = '') => {
		const response = await fetch(`${WEBUI_API_BASE_URL}/rooibos/corpbookmarks/add`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${localStorage.token}`
			},
			body: JSON.stringify({
				userId: currentUser?.id,
				companyId: company.master_id,
				business_registration_number: company.business_registration_number,
				folderId: folderId // 선택한 폴더 ID 추가
			})
		});
		const data = await response.json();
		companyInfo.bookmark_id = data.id;
		companyInfo.bookmark_user_id = currentUser?.id;
	};

	// 삭제 요청을 실제 진행하는 함수
	const confirmDelete = async () => {
		try {
			const response = await fetch(
				`${WEBUI_API_BASE_URL}/rooibos/corpbookmarks/${companyInfo.bookmark_id}/delete`,
				{
					method: 'DELETE',
					headers: {
						'Content-Type': 'application/json'
					}
				}
			);
			const data = await response.json();
			if (response.ok) {
				companyInfo.bookmark_user_id = null;
			} else {
				console.error('Delete failed:', data);
				alert(`북마크 삭제 실패: ${data.error || '알 수 없는 오류'}`);
			}
		} catch (error) {
			console.error('Error in confirmDelete:', error);
			alert('북마크 삭제 중 예기치 못한 오류가 발생했습니다.');
		} finally {
			// 대화상자 닫기
			showDeleteConfirm = false;
		}
	};

	// 북마크 추가 또는 삭제(확인 후) 처리
	const saveCompany = async (company: any) => {
		if (!company.bookmark_user_id) {
			// 북마크 추가 전 폴더 선택 모달 표시
			showFolderSelect = true;
		} else {
			// 삭제 전 확인 대화상자 호출
			showDeleteConfirm = true;
		}
	};

	// 폴더 선택 후 북마크 추가 처리
	const handleFolderSelect = async (event) => {
		const selectedFolder = event.detail;
		if (selectedFolder && selectedFolder.id) {
			await addCompany(companyInfo, selectedFolder.id);
		} else {
			// 폴더 없이 추가 (루트에 추가)
			await addCompany(companyInfo);
		}
		showFolderSelect = false;
	};

	// 폴더 선택 모달 닫기
	const closeFolderSelect = () => {
		showFolderSelect = false;
	};

	const openAIChat = async (company: any) => {
		selectedCompanyInfo.set({
			...company,
			financialData: financialData,
			files: company.data_files?.file_ids ?? company.files?.file_ids
		});
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
	<!-- 저장 버튼 (추가/삭제) -->
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
				d="M5 5v14l7-7 7 7V5z"
			/>
		</svg>
		<span
			class="text-xs mt-1 whitespace-nowrap transition-colors duration-200"
			class:text-yellow-500={companyInfo.bookmark_user_id == currentUser?.id}
			class:text-gray-500={companyInfo.bookmark_user_id != currentUser?.id}
		>
			저장
		</span>
	</button>

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

	<!-- 네이버지도 버튼 -->
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

<!-- 삭제 확인 대화상자 -->
<DeleteConfirmDialog
	bind:show={showDeleteConfirm}
	title="북마크를 삭제하시겠습니까?"
	on:confirm={confirmDelete}
/>

<!-- 폴더 선택 모달 -->
{#if showFolderSelect}
	<FolderSelect 
		isOpen={showFolderSelect} 
		onClose={closeFolderSelect}
		folderType="corp"
		bookmarkId=""
		on:close={handleFolderSelect}
	/>
{/if}
