<script lang="ts">
	import { onMount, getContext, createEventDispatcher } from 'svelte';
	import Modal from '$lib/components/common/Modal.svelte';
	import { WEBUI_API_BASE_URL } from '$lib/constants';
	import { getNoteFolders } from '../apis/folder';
	import { user } from '$lib/stores';
	import { goto } from '$app/navigation';
	const i18n = getContext('i18n');

	// 부모에서 전달하는 프라퍼티 및 이벤트 핸들러
	export let isOpen: boolean;
	export let onClose: () => void;
	// 선택할 북마크 ID (부모에서 전달)
	export let bookmarkId: string;

	let folders = [];

	const dispatch = createEventDispatcher();

	// 폴더 목록 로드 함수
	async function loadFolders() {
		try {
			const response = await getNoteFolders(localStorage.token, $user?.id).catch((error) => {
				toast.error(`${error}`);
				return null;
			});
			folders = await response;
		} catch (error) {
			console.error("폴더 로드 실패:", error);
		}
	}

	onMount(() => {
		loadFolders();
	});

	async function selectFolder(folder) {
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
</script>

<Modal {isOpen} on:close={onClose}>
	<div class="p-4">
		<div class="flex justify-between items-center mb-4">
			<h2 class="text-lg font-bold">{$i18n.t('폴더 선택')}</h2>
			<button type="button" on:click={onClose} class="text-gray-500 hover:text-gray-700">
				<!-- 닫기 버튼 아이콘 -->
				<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
				</svg>
			</button>
		</div>
		{#if folders.length > 0}
			<ul class="space-y-2">
				{#each folders as folder}
					<li>
						<button
							class="w-full text-left px-4 py-2 rounded hover:bg-gray-100 flex justify-between items-center"
							on:click={() => selectFolder(folder)}
						>
							<div class="flex items-center">
								<!-- 폴더 아이콘 (Heroicons) -->
								<svg class="w-5 h-5 mr-2 text-gray-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7h4l2 2h8a2 2 0 012 2v7a2 2 0 01-2 2H5a2 2 0 01-2-2V7z" />
								</svg>
								<span>{folder.name}</span>
							</div>
							<span class="text-sm text-gray-500">{formatTimestamp(folder.updated_at)}</span>
						</button>
					</li>
				{/each}
			</ul>
		{:else}
			
		{/if}
	</div>
</Modal>
