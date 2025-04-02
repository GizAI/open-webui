<script lang="ts">
	import { createEventDispatcher, getContext } from 'svelte';
	import Dropdown from '$lib/components/common/Dropdown.svelte';
	import { DropdownMenu } from 'bits-ui';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import { flyAndScale } from '$lib/utils/transitions';
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';
	import { renameNoteFolder, deleteFolderById, getFolderById } from '$rooibos/components/apis/folder';
	import Pencil from '$lib/components/icons/Pencil.svelte';
	import FolderForm from './FolderForm.svelte';
	import { FolderIcon, Trash2Icon, Share2Icon } from 'lucide-svelte';
	import ConfirmDialog from '$lib/components/common/ConfirmDialog.svelte';

	// i18n 스토어 설정
	const i18n: { subscribe: any; t: (key: string) => string } = getContext('i18n');
	const dispatch = createEventDispatcher();

	export let folders: Record<string, any> = {};
	export let parentId: string | null = null;

	let folderList = [];
	$: folderList = Object.keys(folders)
		.filter((key) => folders[key].parent_id === parentId)
		.sort((a, b) => {
			// 휴지통 폴더는 항상 마지막에 오도록 처리
			if (folders[a].isTrash) return 1;
			if (folders[b].isTrash) return -1;
			
			// 공유 기업 폴더는 휴지통 전에 오도록 처리
			if (folders[a].isShared) return 1;
			if (folders[b].isShared) return -1;
			
			// 일반 폴더는 이름 기준으로 정렬
			return folders[a].name.localeCompare(folders[b].name, undefined, {
				numeric: true,
				sensitivity: 'base'
			});
		});

	let editingFolderId: string | null = null;
	let editedName = '';
	let showManagementForm = false;
	let managementFolderId: string | null = null;
	let showDeleteConfirm = false;
	let deletingFolderId: string | null = null;

	function handleFolderClick(folder: any) {
		const isTrash = 
			folder.id.startsWith('trash-folder-') || 
			folder.name === '휴지통' || 
			folder.isTrash === true;				
		
		const isShared = 
			folder.id.startsWith('shared-folder-') || 
			folder.name === '공유 기업' || 
			folder.isShared === true;
		
		// 폴더 클릭 이벤트 전달
		dispatch('folderClick', { folder });
		
		if (isTrash) {
			goto(`/rooibos/folder/${folder.id}/companies?deleted=true`);
		} else if (isShared) {
			goto(`/rooibos/folder/${folder.id}/companies?shared=true`);
		} else {
			goto(`/rooibos/folder/${folder.id}/companies`);
		}
	}

	function startEditing(e: Event, folderId: string) {
		e.stopPropagation();
		editingFolderId = folderId;
		editedName = folders[folderId].name;
	}

	async function submitRename(folderId: string) {
		if (editedName && editedName !== folders[folderId].name) {
			const oldName = folders[folderId].name;
			folders[folderId].name = editedName;
			try {
				await renameNoteFolder(localStorage.token, folderId, editedName);
				dispatch('rename', { folderId, newName: editedName });
			} catch (error) {
				folders[folderId].name = oldName;
				toast.error(`${error}`);
			}
		}
		editingFolderId = null;
	}

	// 폴더 삭제 확인 대화상자 표시
	function showDeleteConfirmDialog(e: Event, folderId: string) {
		e.stopPropagation();
		deletingFolderId = folderId;
		showDeleteConfirm = true;
		
		// 삭제 확인 전에 폴더 정보를 서버에서 다시 가져와서 최신 상태 확인
		refreshFolderInfo(folderId);
	}

	// 폴더 정보 새로고침 함수
	async function refreshFolderInfo(folderId: string) {
		try {
			const updatedFolder = await getFolderById(localStorage.token, folderId);
			if (updatedFolder) {
				// 서버에서 가져온 최신 정보로 폴더 정보 업데이트
				folders[folderId] = { ...folders[folderId], ...updatedFolder };
			}
		} catch (error) {
			toast.error(`폴더 정보 가져오기 실패: ${error}`);
		}
	}

	// 폴더 삭제 함수
	async function deleteFolder() {
		if (!deletingFolderId) return;
		
		// 북마크 수 확인
		const folder = folders[deletingFolderId];
		if ((folder.active_bookmark_count && folder.active_bookmark_count > 0) || 
		    (folder.deleted_bookmark_count && folder.deleted_bookmark_count > 0)) {
			// 삭제 대화상자에서 보여주고 사용자가 취소하도록 함
			// 실제 삭제 로직은 실행하지 않음
			showDeleteConfirm = false;
			deletingFolderId = null;
			return;
		}
		
		try {
			await deleteFolderById(localStorage.token, deletingFolderId);
			delete folders[deletingFolderId];
			dispatch('delete', { folderId: deletingFolderId });
		} catch (error) {
			toast.error(`${error}`);
		} finally {
			deletingFolderId = null;
			showDeleteConfirm = false;
		}
	}

	// 관리 메뉴 열기/닫기
	function openManagement(folderId: string) {
		showManagementForm = true;
		managementFolderId = folderId;
	}

	function closeManagementForm() {
		showManagementForm = false;
		managementFolderId = null;
	}

	// FolderForm에서 업데이트 이벤트 수신
	function handleFolderUpdate(e: CustomEvent) {
		const updatedFolder = e.detail;
		// 업데이트된 폴더 정보를 반영
		folders[updatedFolder.id] = updatedFolder;
		dispatch('update', { folderId: updatedFolder.id, newData: updatedFolder });
	}
</script>

<ul class="folder-list">
	{#each folderList as folderId (folderId)}
		<li class="folder-item group relative">
			<div class="flex items-center justify-between hover:bg-gray-100 dark:hover:bg-gray-900 rounded-md py-1 text-xs">
				{#if editingFolderId === folderId}
					<input
						type="text"
						bind:value={editedName}
						class="cursor-text bg-transparent border-b border-dashed focus:outline-none"
						on:blur={() => submitRename(folderId)}
						on:keydown={(e) => {
							if (e.key === 'Enter') e.target.blur();
						}}
						autofocus
					/>
				{:else}
					<button on:click={() => handleFolderClick(folders[folderId])} class="cursor-pointer flex items-center gap-1.5 text-left bg-transparent border-0 p-0 text-xs">
						{#if folders[folderId].isTrash}
							<Trash2Icon size={16} strokeWidth={1.5} />
							{folders[folderId].name}
						{:else if folders[folderId].isShared}
							<Share2Icon size={16} strokeWidth={1.5} />
							{folders[folderId].name}
						{:else}
							<FolderIcon size={16} strokeWidth={1.5} />
							{folders[folderId].name}
						{/if}
					</button>
				{/if}

				<div class="invisible group-hover:visible flex items-center">
					{#if !folders[folderId].isTrash && !folders[folderId].isShared}
						<Dropdown>
							<Tooltip content={$i18n.t('More')}>
								<button class="flex items-center justify-center h-6 w-6">
									<span class="inline-block transform translate-y-[-2px]">...</span>
								</button>
							</Tooltip>
							<div slot="content">
								<DropdownMenu.Content
									class="w-full max-w-[160px] rounded-lg px-1 py-1.5 z-50 bg-white dark:bg-gray-850 dark:text-white shadow-lg"
									sideOffset={-2}
									side="bottom"
									align="start"
									transition={flyAndScale}
								>
									<DropdownMenu.Item
										class="flex gap-2 items-center px-3 py-1.5 text-sm cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 rounded-md"
										on:click={(e) => startEditing(e, folderId)}
									>
										<Pencil strokeWidth="2" />
										<div class="flex items-center">{$i18n.t('이름변경')}</div>
									</DropdownMenu.Item>
									<DropdownMenu.Item
										class="flex gap-2 items-center px-3 py-1.5 text-sm cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 rounded-md"
										on:click={(e) => showDeleteConfirmDialog(e, folderId)}
									>
										<Trash2Icon strokeWidth="2" />
										<div class="flex items-center">{$i18n.t('폴더삭제')}</div>
									</DropdownMenu.Item>
									<!-- 관리 메뉴 항목 추가 -->
									<!-- <DropdownMenu.Item
										class="flex gap-2 items-center px-3 py-1.5 text-sm cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 rounded-md"
										on:click={(e) => { e.stopPropagation(); openManagement(folderId); }}
									>
										<Cog6 strokeWidth="2" />
										<div class="flex items-center">{$i18n.t('폴더관리')}</div>
									</DropdownMenu.Item> -->								
								</DropdownMenu.Content>
							</div>
						</Dropdown>
					{/if}
				</div>
			</div>

			<!-- 재귀 렌더링: 자식 폴더가 있으면 -->
			{#if folders[folderId].childrenIds && folders[folderId].childrenIds.length > 0}
				<svelte:self {folders} parentId={folderId} on:folderClick />
			{/if}
		</li>
	{/each}
</ul>

<!-- 관리 메뉴를 위한 FolderForm (간단한 인라인 모달 형태) -->
{#if showManagementForm && managementFolderId}
	<FolderForm
		folder={folders[managementFolderId]}
		on:close={closeManagementForm}
		on:update={handleFolderUpdate}
	/>
{/if}

<!-- 삭제 확인 대화상자 -->
{#if showDeleteConfirm && deletingFolderId}
	<ConfirmDialog
		bind:show={showDeleteConfirm}
		title={$i18n.t('폴더 삭제')}
		on:confirm={deleteFolder}
	>
		<div class="text-sm text-gray-700 dark:text-gray-300 flex-1">
			{#if folders[deletingFolderId].active_bookmark_count > 0 || folders[deletingFolderId].deleted_bookmark_count > 0}
				<div class="mb-2">{$i18n.t('이 폴더에는 다음과 같은 기업이 포함되어 있습니다:')}</div>
				{#if folders[deletingFolderId].active_bookmark_count > 0}
					<div class="ml-2 mb-1">· {$i18n.t('활성화된 기업')}: {folders[deletingFolderId].active_bookmark_count}개</div>
				{/if}
				{#if folders[deletingFolderId].deleted_bookmark_count > 0}
					<div class="ml-2 mb-1">· {$i18n.t('휴지통의 기업')}: {folders[deletingFolderId].deleted_bookmark_count}개</div>
				{/if}
				<div class="mt-2 text-red-500">{$i18n.t('폴더를 삭제하기 전에 나의 기업에서 제거해주세요.')}</div>
			{:else}
				<div>{$i18n.t('이 작업은 "{{NAME}}" 폴더를 삭제합니다.', {
					NAME: folders[deletingFolderId].name
				})}</div>
			{/if}
		</div>
	</ConfirmDialog>
{/if}

<style>
	.folder-list {
		padding-left: 1.2rem;
		font-size: 0.8rem;
	}
	.folder-item {
		margin-bottom: 0.1rem;
	}
</style>
