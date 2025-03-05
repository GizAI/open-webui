<script lang="ts">
	import { getContext, createEventDispatcher, onMount } from 'svelte';
	import Modal from '$lib/components/common/Modal.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import FolderAccessControl from './FolderAccessControl.svelte';
	import { WEBUI_API_BASE_URL } from '$lib/constants';
	import { renameNoteFolder } from '../apis/folder';
	import { formatDate } from '../common/helper';
	
	// Get i18n context but don't rely on it for now
	const i18n = getContext('i18n');

	// Define explicit type for folder based on database schema
	export let folder: {
		id: string;
		parent_id?: string;
		user_id?: string;
		name: string;
		type?: string;
		items?: any;
		meta?: any;
		is_expanded?: boolean;
		created_at?: number;
		updated_at: string;
		access_control?: any;
	} | null = null;

	const dispatch = createEventDispatcher();
	
	// Form state
	let isEditing = false;
	let folderName = folder?.name || '';
	let isSaving = false;
	let errorMessage = '';
	
	// Access control state
	let accessControl = folder?.access_control || null;

	// Function to close the modal
	function onClose() {
		dispatch('close');
	}

	// Function to select a folder
	function selectFolder(selectedFolder: typeof folder) {
		dispatch('select', { folder: selectedFolder });
		onClose();
	}
	
	// Function to handle access control changes
	function handleAccessControlChange(newAccessControl: any) {
		accessControl = newAccessControl;
		if (folder) {
			folder = { ...folder, access_control: accessControl };
		}
	}

	// Function to save folder name changes
	async function saveFolder() {
		if (!folder || !folderName.trim()) {
			errorMessage = '폴더명을 입력해주세요';
			return;
		}
		
		isSaving = true;
		errorMessage = '';
		
		try {
			const updatedFolder = await renameNoteFolder(localStorage.token, folder.id, folderName);
			// 서버에서 받아온 업데이트된 폴더 정보로 갱신
			if (updatedFolder) {
				folder = updatedFolder;
				// 폴더 이름 갱신
				folderName = updatedFolder.name;
			}
			// Update the UI by toggling edit mode off
			isEditing = false;
			// Dispatch an update event to notify parent components
			dispatch('update', folder);
		} catch (error) {
			console.error(error);
			errorMessage = '서버 오류가 발생했습니다';
		} finally {
			isSaving = false;
		}
	}

	// Toggle edit mode
	function toggleEditMode() {
		isEditing = !isEditing;
		if (isEditing) {
			folderName = folder?.name || '';
		}
	}
	
	// Handle key press in the input field
	function handleKeyPress(event: KeyboardEvent) {
		if (event.key === 'Enter') {
			saveFolder();
		} else if (event.key === 'Escape') {
			isEditing = false;
			folderName = folder?.name || '';
		}
	}
</script>

<Modal on:close={onClose}>
	<div class="p-4">
		<div class="flex justify-between items-center mb-4">
			<h2 class="text-lg font-bold">폴더 관리</h2>
			<button type="button" on:click={onClose} class="text-gray-500 hover:text-gray-700">
				<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
				</svg>
			</button>
		</div>
		{#if folder}
			<div class="space-y-4">
				<!-- Folder Information Card -->
				<div class="w-full p-4 bg-gray-50 dark:bg-gray-800 rounded-lg shadow-sm">
					<div class="flex flex-col gap-3">
						<!-- Folder Name with Edit Option -->
						<div class="flex flex-col">
							<label class="text-sm font-medium text-gray-600 dark:text-gray-300 mb-1">폴더명</label>
							{#if isEditing}
								<div class="flex gap-2">
									<input 
										type="text" 
										bind:value={folderName} 
										class="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
										placeholder="폴더명을 입력하세요"
										on:keydown={handleKeyPress}
									/>
									<div class="flex gap-1">
										<button 
											on:click={saveFolder} 
											class="px-3 py-1 bg-blue-500 text-white rounded-md hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
											disabled={isSaving}
										>
											{#if isSaving}
												<Spinner className="w-4 h-4" />
											{:else}
												저장
											{/if}
										</button>
									</div>
								</div>
								{#if errorMessage}
									<p class="text-red-500 text-sm mt-1">{errorMessage}</p>
								{/if}
							{:else}
								<div class="flex justify-between items-center">
									<div class="flex items-center">
										<svg class="w-5 h-5 mr-2 text-gray-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7h4l2 2h8a2 2 0 012 2v7a2 2 0 01-2 2H5a2 2 0 01-2-2V7z" />
										</svg>
										<span class="font-medium">{folder.name}</span>
									</div>
									<button 
										on:click={toggleEditMode}
										class="text-blue-500 hover:text-blue-600 focus:outline-none"
									>
										<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
										</svg>
									</button>
								</div>
							{/if}
						</div>
						
						<!-- Folder Details -->
						<div class="grid grid-cols-1 md:grid-cols-2 gap-3 mt-2">						
							
							<!-- Created At -->
							{#if folder.created_at}
								<div>
									<label class="text-xs font-medium text-gray-500 dark:text-gray-400">생성일</label>
									<p class="text-sm">{formatDate(folder.created_at)}</p>
								</div>
							{/if}
							
							<!-- Updated At -->
							<div>
								<label class="text-xs font-medium text-gray-500 dark:text-gray-400">수정일</label>
								<p class="text-sm">{formatDate(folder.updated_at)}</p>
							</div>
						</div>
					</div>
				</div>
				
				<!-- Access Control Section -->
				<div class="mt-4 border-t pt-3 border-gray-100 dark:border-gray-700">
					<FolderAccessControl 
						folder={folder}
						bind:accessControl={accessControl}
						onChange={handleAccessControlChange}
					/>
				</div>
				
				<!-- Action Buttons -->
				<div class="flex justify-end gap-2 mt-4">
					<button 
						on:click={() => selectFolder(folder)}
						class="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
					>
						선택
					</button>
					<button 
						on:click={onClose}
						class="px-4 py-2 bg-gray-300 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-400 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-gray-500"
					>
						취소
					</button>
				</div>
			</div>
		{:else}
			<div class="w-full h-full flex justify-center items-center">
				<Spinner />
			</div>
		{/if}
	</div>
</Modal>
