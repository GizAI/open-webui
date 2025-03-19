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
	import Badge from '$lib/components/common/Badge.svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import MenuLines from '$lib/components/icons/MenuLines.svelte';
	import { WEBUI_API_BASE_URL } from '$lib/constants';
	import { get } from 'svelte/store';
	import { page } from '$app/stores';
	import { deleteCompanyBookmark, permanentDeleteCompanyBookmark } from '$rooibos/components/apis/company';

	// 다국어 텍스트
	let collectionText = 'Collection';
	$: if ($i18n) {
		collectionText = $i18n.t('Collection');
	}

	let loaded = false;

	let selectedItem: any = null;
	let showDeleteConfirm = false;
	let isTrashView = false; // Track if we're viewing trash items
	let deleteConfirmTitle = "나의기업에서 삭제하시겠습니까?";

	let bookmarks: any = [];

	const deleteHandler = async (item: any) => {
		let result;
		
		if (isTrashView) {
			// 휴지통에서 삭제하는 경우 영구 삭제
			result = await permanentDeleteCompanyBookmark(item.id);
		} else {
			// 일반 삭제 (소프트 삭제)
			result = await deleteCompanyBookmark(item.id);
		}
		
		if (result.success) {
			bookmarks = bookmarks.filter((bookmark: any) => bookmark.id !== item.id);
		} else {
			alert(`북마크 삭제 실패: ${result.error}`);
		}
	};

	$: (async () => {
		if (!$page.params.id) return;
		loaded = false;
		const folderId = $page.params.id;
		const currentUser = get(user);
		
		const urlParams = new URLSearchParams(window.location.search);
		const isDeleted = urlParams.get('deleted') || 'false';
		isTrashView = isDeleted === 'true';
		
		// 삭제 확인 메시지 설정
		deleteConfirmTitle = isTrashView ? 
			"휴지통에서 완전히 삭제하시겠습니까?" : "나의기업에서 삭제하시겠습니까?";
		
		const response = await fetch(
			`${WEBUI_API_BASE_URL}/rooibos/folders/${folderId}/companies?userId=${currentUser?.id}&deleted=${isDeleted}`,
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
		{#each bookmarks as bookmark}
			<button
				class=" flex space-x-4 cursor-pointer text-left w-full px-3 py-2 hover:bg-gray-50 dark:hover:bg-gray-850 transition rounded-xl"
				on:click={() => {
					goto(`/rooibos/mycompanies/${bookmark.id}`);
				}}
			>
				<div class=" w-full">
					<div class="flex items-center justify-between -mt-1">
						<Badge type="success" content={collectionText} />
						<div class=" flex self-center -mr-1 translate-y-1">
							<CorpBookmarks
								{bookmark}
								isTrashView={isTrashView}
								on:delete={() => {
									selectedItem = bookmark;
									showDeleteConfirm = true;
								}}
								on:moved={() => {
									bookmarks = bookmarks.filter((b) => b.id !== bookmark.id);
								}}
							/>

						</div>
					</div>

					<div class=" self-center flex-1 px-1 mb-1">
						<div class=" font-semibold line-clamp-1 h-fit">{bookmark.company_name}</div>

						<div class=" text-xs overflow-hidden text-ellipsis line-clamp-1">
							{bookmark.address}
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
