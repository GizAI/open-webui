<script lang="ts">
	import dayjs from 'dayjs';
	import relativeTime from 'dayjs/plugin/relativeTime';
	dayjs.extend(relativeTime);

	import { onMount, getContext } from 'svelte';
	const i18n = getContext('i18n');

	import { user, WEBUI_NAME} from '$lib/stores';

	import { goto } from '$app/navigation';

	import DeleteConfirmDialog from '$lib/components/common/ConfirmDialog.svelte';
	import CorpBookmarks from '$rooibos/components/corpbookmarks/CorpBookmarksItemMenu.svelte';
	import Badge from '$lib/components/common/Badge.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import { WEBUI_API_BASE_URL } from '$lib/constants';
	import { get } from 'svelte/store';


	let loaded = false;

	let selectedItem: any = null;
	let showDeleteConfirm = false;

	let bookmarks: any = [];

	const deleteHandler = async (item: any) => {
		try {
        const response = await fetch(`${WEBUI_API_BASE_URL}/rooibos/corpbookmarks/${item.id}/delete`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            },
        });

        const data = await response.json();

        if (response.ok) {            
			bookmarks = bookmarks.filter((bookmark: any) => bookmark.id !== item.id);
        } else {
            console.error("Delete failed:", data);
            alert(`Failed to delete bookmark: ${data.error || "Unknown error"}`);
        }
    } catch (error) {
        console.error("Error in deleteHandler:", error);
        alert("An unexpected error occurred while deleting the bookmark.");
    }
	};

	onMount(async () => {
		const currentUser = get(user);
		const response = await fetch(`${WEBUI_API_BASE_URL}/rooibos/corpbookmarks/${currentUser?.id}`, {
        method: 'GET',
		headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.token}`
        },
    });
		if (!response.ok) {
			throw new Error('검색 요청 실패');
		}

		const data = await response.json();
		bookmarks = data.data;
		loaded = true;
	});
</script>

<svelte:head>
	<title>
		{$i18n.t('CorpBookmarks')} | {$WEBUI_NAME}
	</title>
</svelte:head>

{#if loaded}
	<DeleteConfirmDialog
		bind:show={showDeleteConfirm}
		title="북마크를 삭제하시겠습니까?"
		on:confirm={() => {
			deleteHandler(selectedItem);
		}}
	/>

	<div class="mb-5 grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-2">
		{#each bookmarks as bookmark}
			<button
				class=" flex space-x-4 cursor-pointer text-left w-full px-3 py-2 hover:bg-gray-50 dark:hover:bg-gray-850 transition rounded-xl"
				on:click={() => {
					goto(`/rooibos/corpbookmarks/${bookmark.id}`);
				}}
			>
				<div class=" w-full">
					<div class="flex items-center justify-between -mt-1">
						<Badge type="success" content={$i18n.t('Collection')} />
						<div class=" flex self-center -mr-1 translate-y-1">
							<CorpBookmarks
								on:delete={() => {
									selectedItem = bookmark;
									showDeleteConfirm = true;
								}}
							/>
						</div>
					</div>

					<div class=" self-center flex-1 px-1 mb-1">
						<div class=" font-semibold line-clamp-1 h-fit">{bookmark.company_name}</div>

						<div class=" text-xs overflow-hidden text-ellipsis line-clamp-1">
							{bookmark.memo}
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
