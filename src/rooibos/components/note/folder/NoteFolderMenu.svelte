<!-- NoteFolderMenu.svelte -->
<script lang="ts">
	import { createEventDispatcher, getContext } from 'svelte';
	import Dropdown from '$lib/components/common/Dropdown.svelte';
	import { DropdownMenu } from 'bits-ui';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import { flyAndScale } from '$lib/utils/transitions';
	import { goto } from '$app/navigation';
	import { v4 as uuidv4 } from 'uuid';
	import { toast } from 'svelte-sonner';
	import { renameNoteFolder } from '$rooibos/components/apis/folder';
	import { NotebookIcon } from 'lucide-svelte';
	import Pencil from '$lib/components/icons/Pencil.svelte';
	import { createNote } from '$rooibos/components/apis/note';
	import { user } from '$lib/stores';

	// i18n을 스토어로 사용하기 위해 타입 정의
	const i18n: { subscribe: any; t: (key: string) => string } = getContext('i18n');
	const dispatch = createEventDispatcher();

	export let folders: Record<string, any> = {};
	export let parentId: string | null = null;

	let folderList = [];
	$: folderList = Object.keys(folders)
		.filter((key) => folders[key].parent_id === parentId)
		.sort((a, b) =>
			folders[a].name.localeCompare(folders[b].name, undefined, {
				numeric: true,
				sensitivity: 'base'
			})
		);

	let editingFolderId: string | null = null;
	let editedName = '';

	function handleFolderClick(folder: any) {
		if (folder.type === 'note') {
			goto(`/rooibos/folder/${folder.id}/notes`);
		} else {
			goto(`/rooibos/folder/${folder.id}/companies`);
		}
	}

	async function handleAddPage(e: Event, folderId: string) {
		e.stopPropagation();
		const newId = uuidv4();
		await createNote(localStorage.token, newId, $user?.id, folderId);
		goto(`/rooibos/note/${newId}`);
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
</script>

<ul class="folder-list">
	{#each folderList as folderId (folderId)}
		<li class="folder-item group relative">
			<div class="flex items-center justify-between hover:bg-gray-100 dark:hover:bg-gray-900 rounded-md">
				{#if editingFolderId === folderId}
					<input
						type="text"
						bind:value={editedName}
						class="cursor-text bg-transparent border-b border-dashed focus:outline-none"
						on:blur={() => submitRename(folderId)}
						on:keydown={(e) => { if (e.key === 'Enter') e.target.blur(); }}
						autofocus
					/>
				{:else}
					<span on:click={() => handleFolderClick(folders[folderId])} class="cursor-pointer">
						{folders[folderId].name}
					</span>
				{/if}

				<div class="invisible group-hover:visible">
					<Dropdown>
						<Tooltip content={$i18n.t('More')}>
							<button class="p-1">
								<span class="text-xl">…</span>
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
								{#if folders[folderId].type === 'note'}
									<DropdownMenu.Item
										class="flex gap-2 items-center px-3 py-1.5 text-sm cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 rounded-md"
										on:click={(e) => handleAddPage(e, folderId)}
									>
										<NotebookIcon strokeWidth="2" />
										<div class="flex items-center">{$i18n.t('새페이지')}</div>
									</DropdownMenu.Item>
								{/if}
							</DropdownMenu.Content>
						</div>
					</Dropdown>
				</div>
			</div>
		</li>
	{/each}
</ul>

<style>
	.folder-list {
		padding-left: 1.2rem;
		font-size: 0.8rem;
	}

	.folder-item {
		margin-bottom: 0.1rem;
	}
</style>
