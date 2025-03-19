<script lang="ts">
	import { DropdownMenu } from 'bits-ui';
	import { flyAndScale } from '$lib/utils/transitions';
	import { getContext, createEventDispatcher } from 'svelte';
	import Dropdown from '$lib/components/common/Dropdown.svelte';
	import GarbageBin from '$lib/components/icons/GarbageBin.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import EllipsisHorizontal from '$lib/components/icons/EllipsisHorizontal.svelte';
	import FolderSelect from '$rooibos/components/folder/FolderSelect.svelte';
	import { selectedCompanyInfo } from '$rooibos/stores/index.js';
	import { goto } from '$app/navigation';
	import { WEBUI_API_BASE_URL } from '$lib/constants';
	import { user } from '$lib/stores';

	const dispatch = createEventDispatcher();
	const i18n: any = getContext('i18n');

	export let bookmark: any = null;
	export let onClose: Function = () => {};
	export let isTrashView: boolean = false;

	let show = false;
	let showFolderSelect = false;

	async function moveBookmarkToFolder(selectedFolder: any) {
		const payload = {
			bookmarkId: bookmark.id,
			targetFolderId: selectedFolder.id
		};
		try {
			const response = await fetch(`${WEBUI_API_BASE_URL}/rooibos/mycompanies/move?userId=${$user?.id}`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify(payload)
			});
			const result = await response.json();
			if (result.success) {
				dispatch('moved', { folder: selectedFolder });
			} else {
				console.error('Error moving bookmark:', result);
			}
		} catch (error) {
			console.error('Error moving bookmark:', error);
		}
	}
</script>

<Dropdown
	bind:show
	on:change={(e) => {
		if (e.detail === false) {
			onClose();
		}
	}}
	align="end"
>
	<Tooltip content={$i18n.t('More')}>
		<slot>
			<button
				class="self-center w-fit text-sm p-1.5 dark:text-gray-300 dark:hover:text-white hover:bg-black/5 dark:hover:bg-white/5 rounded-xl"
				type="button"
				on:click={(e) => {
					e.stopPropagation();
					show = true;
				}}
			>
				<EllipsisHorizontal className="size-5" />
			</button>
		</slot>
	</Tooltip>

	<div slot="content">
		<DropdownMenu.Content
			class="w-full max-w-[160px] rounded-xl px-1 py-1.5 border border-gray-300/30 dark:border-gray-700/50 z-50 bg-white dark:bg-gray-850 dark:text-white shadow"
			sideOffset={-2}
			side="bottom"
			align="end"
			transition={flyAndScale}
		>
			<!-- <DropdownMenu.Item
				class="flex gap-2 items-center px-3 py-2 text-sm font-medium cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 rounded-md"
				on:click={async () => {
					await openCompanyChat(
						bookmark.id, 
						bookmark.business_registration_number,
						$user?.id,
						bookmark,
						{}
					);
				}}
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
				<div class="flex items-center">새채팅</div>
			</DropdownMenu.Item> -->

			{#if isTrashView}
				<DropdownMenu.Item
					class="flex gap-2 items-center px-3 py-2 text-sm font-medium cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 rounded-md"
					on:click={() => {
						dispatch('restore');
					}}
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
							d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6"
						/>
					</svg>
					<div class="flex items-center">복원</div>
				</DropdownMenu.Item>
			{:else}
				<DropdownMenu.Item
					class="flex gap-2 items-center px-3 py-2 text-sm font-medium cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 rounded-md"
					on:click={() => {
						showFolderSelect = true;
					}}
				>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						class="h-5 w-5 text-gray-500"
						fill="none"
						viewBox="0 0 24 24"
						stroke="currentColor"
					>
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7h4l2-2h8l2 2h4v13H3V7z" />
					</svg>
					<div class="flex items-center">이동</div>
				</DropdownMenu.Item>
			{/if}

			<DropdownMenu.Item
				class="flex gap-2 items-center px-3 py-2 text-sm font-medium cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 rounded-md"
				on:click={() => {
					dispatch('delete');
				}}
			>
				<GarbageBin strokeWidth="2" />
				<div class="flex items-center">
					{isTrashView ? $i18n.t('영구 삭제') : $i18n.t('Delete')}
				</div>
			</DropdownMenu.Item>

		</DropdownMenu.Content>
	</div>
</Dropdown>

{#if showFolderSelect}
	<FolderSelect
		isOpen={showFolderSelect}
		bookmarkId={bookmark.id}
		folderType="corp"
		onClose={() => {
			showFolderSelect = false;
		}}
		on:close={(e) => {
			if (e.detail) {
				moveBookmarkToFolder(e.detail);
			}
		}}
	/>
{/if}
