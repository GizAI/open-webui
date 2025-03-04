<!-- NoteList.svelte -->
<script lang="ts">
	import dayjs from 'dayjs';
	import relativeTime from 'dayjs/plugin/relativeTime';
	dayjs.extend(relativeTime);

	import { onMount, getContext } from 'svelte';
	const i18n = getContext('i18n');

	import { user, WEBUI_NAME, showSidebar } from '$lib/stores';

	import { goto } from '$app/navigation';

	import DeleteConfirmDialog from '$lib/components/common/ConfirmDialog.svelte';
	import CorpBookmarks from '$rooibos/components/corpbookmarks/CorpBookmarksItemMenu.svelte';
	import Badge from '$lib/components/common/Badge.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import MenuLines from '$lib/components/icons/MenuLines.svelte';
	import { WEBUI_API_BASE_URL } from '$lib/constants';
	import { get } from 'svelte/store';
	import { page } from '$app/stores';
	import NoteItemMenu from '../note/NoteItemMenu.svelte';

	let loaded = false;

	let selectedItem: any = null;
	let showDeleteConfirm = false;

	let notes: any = [];

	const deleteHandler = async (item: any) => {
		try {
			const response = await fetch(
				`${WEBUI_API_BASE_URL}/rooibos/corpbookmarks/${item.id}/delete`,
				{
					method: 'DELETE',
					headers: {
						'Content-Type': 'application/json'
					}
				}
			);

			const data = await response.json();

			if (response.ok) {
				notes = notes.filter((note: any) => note.id !== item.id);
			} else {
				console.error('Delete failed:', data);
				alert(`Failed to delete note: ${data.error || 'Unknown error'}`);
			}
		} catch (error) {
			console.error('Error in deleteHandler:', error);
			alert('An unexpected error occurred while deleting the note.');
		}
	};

	$: (async () => {
		if (!$page.params.id) return;
		loaded = false;
		const currentUser = get(user);
		const id = $page.params.id;
		const queryParams = new URLSearchParams({
			userId: currentUser?.id ?? ''
		});
		const response = await fetch(
			`${WEBUI_API_BASE_URL}/rooibos/folders/${id}/notes?${queryParams.toString()}`,
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
		notes = data.notes;
		loaded = true;
	})();
</script>

<svelte:head>
	<title>
		노트 | {$WEBUI_NAME}
	</title>
</svelte:head>

{#if loaded}
	<DeleteConfirmDialog
		bind:show={showDeleteConfirm}
		title="노트를 삭제하시겠습니까?"
		on:confirm={() => {
			deleteHandler(selectedItem);
		}}
	/>

	<div class="mb-2 flex items-center">
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
	</div>

	<div class="mb-5 grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-2">
		{#each notes as note}
			<button
				class=" flex space-x-4 cursor-pointer text-left w-full px-3 py-2 hover:bg-gray-50 dark:hover:bg-gray-850 transition rounded-xl"
				on:click={() => {
					goto(`/rooibos/note/${note.id}`);
				}}
			>
				<div class="w-full">
					<div class="flex items-center justify-between -mt-1">
						<div class="self-center flex-1 px-1 mb-1">
							<div class="flex items-center justify-between">
								<div class="font-semibold line-clamp-1 h-fit">{note.title}</div>
								<div class="flex self-center">
									<NoteItemMenu
										bookmark={note}
										on:delete={() => {
											selectedItem = note;
											showDeleteConfirm = true;
										}}
									/>
								</div>
							</div>
							<div class="text-xs overflow-hidden text-ellipsis line-clamp-1">
								{note.updated_at}
							</div>
						</div>
					</div>
				</div>
			</button>
		{/each}
	</div>
{:else}
	<div class="w-full h-full flex justify-center items-center">
		<Spinner />
	</div>
{/if}
