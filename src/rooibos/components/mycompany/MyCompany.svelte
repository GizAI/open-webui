<!-- CorpBookmarks.svelte -->
<script lang="ts">
	import dayjs from 'dayjs';
	import relativeTime from 'dayjs/plugin/relativeTime';
	dayjs.extend(relativeTime);

	import { onMount, getContext } from 'svelte';
	import i18n from '$lib/i18n';

	import { user, WEBUI_NAME, showSidebar } from '$lib/stores';

	import { goto } from '$app/navigation';

	import DeleteConfirmDialog from '$lib/components/common/ConfirmDialog.svelte';
	import CorpBookmarks from '$rooibos/components/mycompany/MyCompanyItemMenu.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import MenuLines from '$lib/components/icons/MenuLines.svelte';
	import { WEBUI_API_BASE_URL } from '$lib/constants';
	import { get } from 'svelte/store';
	import { page } from '$app/stores';
	import { deleteCompanyBookmark, permanentDeleteCompanyBookmark, restoreCompanyBookmark } from '$rooibos/components/apis/company';
	import { getFolderById } from '$rooibos/components/apis/folder';
	import { triggerFolderUpdate } from '$rooibos/stores';
	import Badge from '$lib/components/common/Badge.svelte';
	import { Building2Icon } from 'lucide-svelte';
	import CompanyForm from '$rooibos/components/folder/CompanyForm.svelte';

	let loaded = false;
	let selectedItem: any = null;
	let showDeleteConfirm = false;
	let isTrashView = false;
	let deleteConfirmTitle = "나의기업에서 삭제하시겠습니까?";
	let folderName = ""; // Variable to store folder name
	let isSharedView = false;
	
	// 기업 추가 모달 관련 변수
	let showCompanyForm = false;
	let currentFolderId: string | null = null;
	
	interface Bookmark {
		id: string;
		company_name: string;
		address: string;
		[key: string]: any;
	}

	let bookmarks: Bookmark[] = [];

	// 사용자 정보를 캐시하기 위한 맵
	let userCache = new Map();
	
	// 사용자 정보를 가져오는 함수
	async function getUserInfo(userId: string) {
		if (userCache.has(userId)) {
			return userCache.get(userId);
		}
		
		try {
			const response = await fetch(`${WEBUI_API_BASE_URL}/users/${userId}`, {
				method: 'GET',
				headers: {
					'Content-Type': 'application/json',
					'Authorization': `Bearer ${localStorage.token}`
				}
			});
			
			if (!response.ok) {
				throw new Error('사용자 정보를 가져오는데 실패했습니다.');
			}
			
			const data = await response.json();
			userCache.set(userId, data);
			return data;
		} catch (error) {
			console.error('사용자 정보 조회 오류:', error);
			return { name: '알 수 없는 사용자' };
		}
	}

	const deleteHandler = async (item: Bookmark) => {
		let result;
		
		if (isTrashView) {
			result = await permanentDeleteCompanyBookmark(item.id);
		} else {
			result = await deleteCompanyBookmark(item.id);
		}
		
		if (result.success) {
			bookmarks = bookmarks.filter((bookmark:any) => bookmark.id !== item.id);
			// 기업 삭제 후 폴더 정보 갱신을 위해 전역 트리거 업데이트
			triggerFolderUpdate();
		} 
	};

	const restoreHandler = async (item: Bookmark) => {
		const result = await restoreCompanyBookmark(item.id);
		
		if (result.success) {
			bookmarks = bookmarks.filter((bookmark: any) => bookmark.id !== item.id);
			// 기업 복원 후 폴더 정보 갱신을 위해 전역 트리거 업데이트
			triggerFolderUpdate();
		}
	};

	// 기업 정보 추가 성공 처리
	function handleCompanyAdded(e: CustomEvent) {
		const companyData = e.detail;
		// 기업 추가 후 폴더 정보 갱신을 위해 전역 트리거 업데이트
		triggerFolderUpdate();
		// 현재 페이지 데이터도 새로고침
		refreshFolderData();
	}
	
	// 기업 추가 모달 열기/닫기
	function openCompanyForm() {
		if(!$page.params.id) return;
		currentFolderId = $page.params.id;
		showCompanyForm = true;
	}
	
	function closeCompanyForm() {
		showCompanyForm = false;
		currentFolderId = null;
	}
	
	// 페이지 데이터 새로고침
	async function refreshFolderData() {
		if (!$page.params.id) return;
		loaded = false;
		
		const folderId = $page.params.id;
		const currentUser = get(user);
		
		const urlParams = new URLSearchParams(window.location.search);
		const isDeleted = urlParams.get('deleted') || 'false';
		const isShared = urlParams.get('shared') || 'false';
		
		const response = await fetch(
			`${WEBUI_API_BASE_URL}/rooibos/folders/${folderId}/companies?userId=${currentUser?.id}&deleted=${isDeleted}&shared=${isShared}`,
			{
				method: 'GET',
				headers: {
					'Content-Type': 'application/json',
					authorization: `Bearer ${localStorage.token}`
				}
			}
		);

		if (!response.ok) {
			throw new Error('검색 요청 실패');
		}

		const data = await response.json();
		bookmarks = data.data;
		loaded = true;
	}

	$: (async () => {
		if (!$page.params.id) return;
		loaded = false;
		const folderId = $page.params.id;
		const currentUser = get(user);
		
		const urlParams = new URLSearchParams(window.location.search);
		const isDeleted = urlParams.get('deleted') || 'false';
		const isShared = urlParams.get('shared') || 'false';
		isTrashView = isDeleted === 'true';
		isSharedView = isShared === 'true';
		
		deleteConfirmTitle = isTrashView ? 
			"휴지통에서 완전히 삭제하시겠습니까?" : "나의기업에서 삭제하시겠습니까?";
		
		// 특별 폴더의 경우 고정된 이름 설정
		if (isTrashView || folderId.startsWith('trash-folder-')) {
			folderName = "휴지통";
		} else if (isSharedView || folderId.startsWith('shared-folder-')) {
			folderName = "공유 기업";
		} else {
			// 일반 폴더인 경우만 폴더 정보 가져오기
			try {
				const folderInfo = await getFolderById(localStorage.token, folderId);
				if (folderInfo && folderInfo.name) {
					folderName = folderInfo.name;
				}
			} catch (error) {
				console.error("Failed to fetch folder info:", error);
			}
		}
		
		const response = await fetch(
			`${WEBUI_API_BASE_URL}/rooibos/folders/${folderId}/companies?userId=${currentUser?.id}&deleted=${isDeleted}&shared=${isShared}`,
			{
				method: 'GET',
				headers: {
					'Content-Type': 'application/json',
					authorization: `Bearer ${localStorage.token}`
				}
			}
		);

		if (!response.ok) {
			throw new Error('검색 요청 실패');
		}

		const data = await response.json();
		bookmarks = data.data;
		loaded = true;
	})();
</script>

<svelte:head>
	<title>
		나의기업 | {$WEBUI_NAME}
	</title>
</svelte:head>

{#if loaded}
	<DeleteConfirmDialog
		bind:show={showDeleteConfirm}
		title={deleteConfirmTitle}
		on:confirm={() => {
			deleteHandler(selectedItem);
		}}
	/>

	<div class="mb-2 flex items-center justify-between">
		<div class="flex items-center">
			{#if !$showSidebar}
				<button
					id="sidebar-toggle-button"
					class="sidebar-toggle-button p-2 mr-2"
					on:click={() => showSidebar.set(true)}
					aria-label="Toggle Sidebar"
				>
					<MenuLines />
				</button>
			{/if}
			<!-- Display folder name here -->
			{#if folderName}
				<h2 class="text-xl font-bold">{folderName}</h2>
			{/if}
		</div>
		
		<!-- 기업 추가 버튼 -->
		{#if !isTrashView && !isSharedView}
			<button 
				class="flex items-center gap-1 px-3 py-1.5 bg-transparent border border-yellow-500 text-yellow-500 hover:bg-yellow-50 rounded-md text-sm transition-colors mt-1"
				on:click={openCompanyForm}
			>
				<Building2Icon size={16} />
				<span>기업추가</span>
			</button>
		{/if}
	</div>

	<div class="mb-5 grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-2">
		{#each bookmarks as bookmark}
			<button
				class="flex space-x-4 cursor-pointer text-left w-full px-3 py-2 hover:bg-gray-50 dark:hover:bg-gray-850 transition rounded-xl"
				on:click={() => {
					if(isTrashView) return;
					if(bookmark.company_type === 'private') {
						goto(`/rooibos/mycompanies/${bookmark.id}?type=private`);
					} else {
						goto(`/rooibos/mycompanies/${bookmark.id}`);
					}
				}}
			>
				<div class="w-full flex items-start justify-between">
					<div class="self-start flex-1 px-1 mb-1">
						<div class="flex items-center gap-2 mb-1">
							<div class="font-semibold line-clamp-1 h-fit">
								{#if isTrashView}
									{bookmark.folder_name} / {bookmark.company_name}
								{:else}
									{bookmark.company_name}
								{/if}
							</div>
							{#if bookmark.company_type === 'private'}
								<Badge type="success" content="내가 추가한 기업" />
							{/if}
						</div>
						<div class="text-xs overflow-hidden text-ellipsis line-clamp-1">
							{bookmark.address}
						</div>
						{#if isSharedView && bookmark.user_id}
							{#await getUserInfo(bookmark.user_id) then userInfo}
								<div class="text-xs text-gray-500 mt-1">
									공유자: {userInfo.name || '알 수 없는 사용자'}
								</div>
							{/await}
						{/if}
					</div>
					{#if !isSharedView}
					<div class="self-start ml-2">
						<CorpBookmarks
							{bookmark}
							{isTrashView}
							on:delete={() => {
								selectedItem = bookmark;
								showDeleteConfirm = true;
							}}
							on:restore={() => {
								restoreHandler(bookmark);
							}}
							on:moved={() => {
								bookmarks = bookmarks.filter((b) => b.id !== bookmark.id);
							}}
						/>
					</div>
					{/if}
				</div>
			</button>
		{/each}
	</div>
{:else}
	<div class="w-full h-full flex justify-center items-center">
		<Spinner />
	</div>
{/if}

<!-- 기업 추가 모달 -->
{#if showCompanyForm && currentFolderId}
	<CompanyForm
		show={showCompanyForm}
		folderId={currentFolderId}
		on:close={closeCompanyForm}
		on:added={handleCompanyAdded}
	/>
{/if}
