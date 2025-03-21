<script lang="ts">
	import { onMount, getContext, createEventDispatcher } from 'svelte';
	import Modal from '$lib/components/common/Modal.svelte';
	import { WEBUI_API_BASE_URL } from '$lib/constants';
	import { getRooibosFolders, createNewRooibosFolder } from '../apis/folder';
	import { user } from '$lib/stores';
	import Spinner from '$lib/components/common/Spinner.svelte';
	// Assuming toast is available in the global scope or needs to be implemented
	
	const i18n: any = getContext('i18n');

	export let isOpen: boolean;
	export let onClose: () => void;
	export let folderType: string;
	export let bookmarkId: string;

	let folders: any[] = [];
	let isLoading = true;
	let showCreateFolderInput = false;
	let newFolderName = '';

	const dispatch = createEventDispatcher();

	// 폴더 목록 로드 함수
	async function loadFolders() {
		isLoading = true;
		try {
			const response = await getRooibosFolders(localStorage.token, $user?.id, folderType).catch((error) => {
				console.error(`${error}`);
				return null;
			});
			folders = await response || [];
			
			// 폴더 정렬: 휴지통 폴더는 항상 마지막에, 나머지는 이름순으로 정렬
			folders.sort((a, b) => {
				const isTrashA = a.isTrash || a.id.startsWith('trash-folder-') || a.name === '휴지통';
				const isTrashB = b.isTrash || b.id.startsWith('trash-folder-') || b.name === '휴지통';
				
				if (isTrashA) return 1;  // 휴지통 폴더는 뒤로
				if (isTrashB) return -1; // 다른 폴더는 앞으로
				
				// 일반 폴더는 이름 기준으로 정렬
				return a.name.localeCompare(b.name, undefined, {
					numeric: true,
					sensitivity: 'base'
				});
			});
		} catch (error) {
			console.error("폴더 로드 실패:", error);
			folders = [];
		} finally {
			isLoading = false;
		}
	}

	onMount(() => {
		loadFolders();
	});

	async function selectFolder(folder: any) {
		dispatch('close', folder);
		onClose();
	}

	function formatTimestamp(ts: number): string {
		const date = new Date(ts * 1000);
		const year = date.getFullYear();
		const month = (date.getMonth() + 1).toString().padStart(2, '0');
		const day = date.getDate().toString().padStart(2, '0');
		return `${year}-${month}-${day}`;
	}

	async function createFolder() {
		if (!newFolderName.trim()) {
			alert('폴더 이름을 입력해주세요.');
			return;
		}

		try {
			await createNewRooibosFolder(
				localStorage.token,
				newFolderName,
				$user?.id,
				folderType
			);
			newFolderName = '';
			showCreateFolderInput = false;
			await loadFolders();
		} catch (error) {
			alert(`폴더 생성 실패: ${error}`);
		}
	}
</script>

<Modal show={isOpen} on:close={onClose}>
	<div class="p-4 bg-gray-50 dark:bg-gray-950 text-gray-900 dark:text-white-200">
		<div class="flex justify-between items-center mb-4">
			<h2 class="text-lg font-bold text-gray-900 dark:text-gray-200">
				{i18n && typeof i18n.t === 'function' ? i18n.t('폴더 선택') : '폴더 선택'}
			</h2>
			<div class="flex items-center">
				<button 
					type="button" 
					on:click={() => showCreateFolderInput = !showCreateFolderInput}
					class="mr-2 text-sm px-2 py-1 bg-gray-500 text-white rounded hover:bg-blue-400 transition-colors"
				>
					<svg class="w-4 h-4 inline-block mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
					</svg>
					폴더 생성
				</button>
				<button type="button" on:click={onClose} class="text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300">
					<!-- 닫기 버튼 아이콘 -->
					<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
					</svg>
				</button>
			</div>
		</div>

		{#if showCreateFolderInput}
			<div class="mb-4 p-2 bg-gray-100 dark:bg-gray-800 rounded">
				<div class="flex flex-wrap items-center gap-2">
					<input 
						type="text" 
						bind:value={newFolderName} 
						placeholder="새 폴더 이름" 
						class="flex-1 min-w-[200px] p-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
					/>
					<button 
						on:click={createFolder}
						class="p-2 bg-gray-500 text-white hover:bg-blue-400 transition-colors rounded-md"
					>
						생성
					</button>
				</div>
			</div>
		{/if}

		{#if isLoading}
			<div class="w-full h-32 flex justify-center items-center">
				<Spinner />
			</div>
		{:else if folders.length > 0}
			<ul class="space-y-2">
				{#each folders as folder}
					<li>
						<button
							class="w-full text-left px-4 py-2 rounded bg-gray-50 dark:bg-gray-950 text-gray-900 dark:text-white-200 hover:bg-gray-100 dark:hover:bg-gray-800 border border-gray-200 dark:border-gray-700 flex justify-between items-center transition-colors duration-200"
							on:click={() => selectFolder(folder)}
						>
							<div class="flex items-center">
								<svg class="w-5 h-5 mr-2 text-gray-500 dark:text-gray-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7h4l2 2h8a2 2 0 012 2v7a2 2 0 01-2 2H5a2 2 0 01-2-2V7z" />
								</svg>
								<span class="text-gray-900 dark:text-gray-200">{folder.name}</span>
							</div>
							<span class="text-sm text-gray-500 dark:text-gray-400">{formatTimestamp(folder.updated_at)}</span>
						</button>
					</li>
				{/each}
			</ul>
		{:else}
			<div class="w-full h-32 flex justify-center items-center text-gray-500 dark:text-gray-400">
				폴더가 없습니다.
			</div>
		{/if}
	</div>
</Modal>
