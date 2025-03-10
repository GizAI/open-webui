<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { v4 as uuidv4 } from 'uuid';
	import { goto } from '$app/navigation';
	import {
		user,
		chats,
		settings,
		showSettings,
		chatId,
		tags,
		showSidebar,
		mobile,
		showArchivedChats,
		pinnedChats,
		scrollPaginationEnabled,
		currentChatPage,
		temporaryChatEnabled,
		channels,
		socket,
		config,
		isApp
	} from '$lib/stores';
	import { onMount, getContext, tick, onDestroy } from 'svelte';
	const i18n = getContext('i18n');

	import {
		deleteChatById,
		getChatList,
		getAllTags,
		getChatListBySearchText,
		createNewChat,
		getPinnedChatList,
		toggleChatPinnedStatusById,
		getChatPinnedStatusById,
		getChatById,
		updateChatFolderIdById,
		importChat
	} from '$lib/apis/chats';
	import { createNewFolder, getFolders, updateFolderParentIdById } from '$lib/apis/folders';
	import { WEBUI_BASE_URL } from '$lib/constants';
	import { selectedCompanyInfo } from '$rooibos/stores';
	import ArchivedChatsModal from './Sidebar/ArchivedChatsModal.svelte';
	import UserMenu from './Sidebar/UserMenu.svelte';
	import ChatItem from './Sidebar/ChatItem.svelte';
	import Spinner from '../common/Spinner.svelte';
	import Loader from '../common/Loader.svelte';
	import AddFilesPlaceholder from '../AddFilesPlaceholder.svelte';
	import SearchInput from './Sidebar/SearchInput.svelte';
	import Folder from '../common/Folder.svelte';
	import Plus from '../icons/Plus.svelte';
	import Tooltip from '../common/Tooltip.svelte';
	import Folders from './Sidebar/Folders.svelte';
	import { getChannels, createNewChannel } from '$lib/apis/channels';
	import ChannelModal from './Sidebar/ChannelModal.svelte';
	import ChannelItem from './Sidebar/ChannelItem.svelte';
	import PencilSquare from '../icons/PencilSquare.svelte';
	import Home from '../icons/Home.svelte';
	import { createNewRooibosFolder, getRooibosFolders } from '$rooibos/components/apis/folder';
	import RooibosFolderMenu from '$rooibos/components/folder/RooibosFolderMenu.svelte';
	import RooibosFolder from '$rooibos/components/folder/RooibosFolder.svelte';

	const BREAKPOINT = 768;

	let navElement;
	let search = '';

	let shiftKey = false;
	let selectedChatId = null;
	let showDropdown = false;
	let showPinnedChat = true;
	let showCreateChannel = false;

	// Pagination 변수
	let chatListLoading = false;
	let allChatsLoaded = false;
	let folders = {};
	let rooibosFolders = {}; // Notes 전용 폴더 상태

	// Chats 폴더 초기화
	const initFolders = async () => {
		const folderList = await getFolders(localStorage.token).catch((error) => {
			toast.error(`${error}`);
			return [];
		});

		folders = {};

		// 1차: 모든 폴더 초기화
		for (const folder of folderList) {
			folders[folder.id] = { ...(folders[folder.id] || {}), ...folder };
		}

		// 2차: 부모-자식 관계 연결
		for (const folder of folderList) {
			if (folder.parent_id) {
				if (!folders[folder.parent_id]) {
					folders[folder.parent_id] = {};
				}
				folders[folder.parent_id].childrenIds = folders[folder.parent_id].childrenIds
					? [...folders[folder.parent_id].childrenIds, folder.id]
					: [folder.id];
				folders[folder.parent_id].childrenIds.sort((a, b) => {
					return folders[b].updated_at - folders[a].updated_at;
				});
			}
		}
	};

	// Notes 폴더 초기화 (필요시 Notes 전용 필터 추가)
	const initRooibosFolders = async () => {
		const response = await getRooibosFolders(localStorage.token, $user?.id).catch((error) => {
			toast.error(`${error}`);
			return null;
		});

		// response가 null이거나, 배열이 아닌 경우를 처리
		let folderList = [];
		if (response) {
			// 만약 응답이 객체 형식이라면 data 필드에서 배열을 추출
			if (Array.isArray(response)) {
				folderList = response;
			} else if (Array.isArray(response.data)) {
				folderList = response.data;
			} else {
				toast.error('폴더 데이터 형식이 올바르지 않습니다.');
			}
		}

		rooibosFolders = {};

		for (const folder of folderList) {
			rooibosFolders[folder.id] = { ...(rooibosFolders[folder.id] || {}), ...folder };
		}

		for (const folder of folderList) {
			if (folder.parent_id) {
				if (!rooibosFolders[folder.parent_id]) {
					rooibosFolders[folder.parent_id] = {};
				}
				rooibosFolders[folder.parent_id].childrenIds = rooibosFolders[folder.parent_id].childrenIds
					? [...rooibosFolders[folder.parent_id].childrenIds, folder.id]
					: [folder.id];
				rooibosFolders[folder.parent_id].childrenIds.sort((a, b) => {
					return rooibosFolders[b].updated_at - rooibosFolders[a].updated_at;
				});
			}
		}

		console.log(rooibosFolders);
	};

	// Chats 폴더 생성 함수
	const createFolder = async (name = 'Untitled') => {
		if (name === '') {
			toast.error($i18n.t('Folder name cannot be empty.'));
			return;
		}
		const rootFolders = Object.values(folders).filter((folder) => folder.parent_id === null);
		if (rootFolders.find((folder) => folder.name.toLowerCase() === name.toLowerCase())) {
			let i = 1;
			while (
				rootFolders.find((folder) => folder.name.toLowerCase() === `${name} ${i}`.toLowerCase())
			) {
				i++;
			}
			name = `${name} ${i}`;
		}
		const tempId = uuidv4();
		folders = {
			...folders,
			[tempId]: {
				id: tempId,
				name: name,
				created_at: Date.now(),
				updated_at: Date.now()
			}
		};
		const res = await createNewFolder(localStorage.token, name).catch((error) => {
			toast.error(`${error}`);
			return null;
		});
		if (res) {
			await initFolders();
		}
	};

	// Notes 폴더 생성 함수
	const createRooibosFolder = async (name = 'Untitled', type = 'note') => {
		if (name === '') {
			toast.error($i18n.t('Folder name cannot be empty.'));
			return;
		}
		const rootFolders = Object.values(folders).filter((folder) => folder.parent_id === null);
		if (rootFolders.find((folder) => folder.name.toLowerCase() === name.toLowerCase())) {
			let i = 1;
			while (
				rootFolders.find((folder) => folder.name.toLowerCase() === `${name} ${i}`.toLowerCase())
			) {
				i++;
			}
			name = `${name} ${i}`;
		}
		const tempId = uuidv4();
		rooibosFolders = {
			...rooibosFolders,
			[tempId]: {
				id: tempId,
				name: name,
				created_at: Date.now(),
				updated_at: Date.now(),
				type: type
			}
		};
		const res = await createNewRooibosFolder(localStorage.token, name, $user?.id, type).catch(
			(error) => {
				toast.error(`${error}`);
				return null;
			}
		);
		if (res) {
			await initRooibosFolders();
		}
	};

	const initChannels = async () => {
		await channels.set(await getChannels(localStorage.token));
	};

	const initChatList = async () => {
		tags.set(await getAllTags(localStorage.token));
		pinnedChats.set(await getPinnedChatList(localStorage.token));
		initFolders();
		currentChatPage.set(1);
		allChatsLoaded = false;
		if (search) {
			await chats.set(await getChatListBySearchText(localStorage.token, search, $currentChatPage));
		} else {
			await chats.set(await getChatList(localStorage.token, $currentChatPage));
		}
		scrollPaginationEnabled.set(true);
	};

	const loadMoreChats = async () => {
		chatListLoading = true;
		currentChatPage.set($currentChatPage + 1);
		let newChatList = [];
		if (search) {
			newChatList = await getChatListBySearchText(localStorage.token, search, $currentChatPage);
		} else {
			newChatList = await getChatList(localStorage.token, $currentChatPage);
		}
		allChatsLoaded = newChatList.length === 0;
		await chats.set([...($chats ? $chats : []), ...newChatList]);
		chatListLoading = false;
	};

	let searchDebounceTimeout;
	const searchDebounceHandler = async () => {
		chats.set(null);
		if (searchDebounceTimeout) {
			clearTimeout(searchDebounceTimeout);
		}
		if (search === '') {
			await initChatList();
			return;
		} else {
			searchDebounceTimeout = setTimeout(async () => {
				allChatsLoaded = false;
				currentChatPage.set(1);
				await chats.set(await getChatListBySearchText(localStorage.token, search));
				if ($chats.length === 0) {
					tags.set(await getAllTags(localStorage.token));
				}
			}, 1000);
		}
	};

	const importChatHandler = async (items, pinned = false, folderId = null) => {
		for (const item of items) {
			if (item.chat) {
				await importChat(localStorage.token, item.chat, item?.meta ?? {}, pinned, folderId);
			}
		}
		initChatList();
	};

	const inputFilesHandler = async (files) => {
		for (const file of files) {
			const reader = new FileReader();
			reader.onload = async (e) => {
				const content = e.target.result;
				try {
					const chatItems = JSON.parse(content);
					importChatHandler(chatItems);
				} catch {
					toast.error($i18n.t(`Invalid file format.`));
				}
			};
			reader.readAsText(file);
		}
	};

	const tagEventHandler = async (type, tagName, chatId) => {
		if (type === 'delete' || type === 'add') {
			initChatList();
		}
	};

	let draggedOver = false;
	const onDragOver = (e) => {
		e.preventDefault();
		if (e.dataTransfer?.types?.includes('Files')) {
			draggedOver = true;
		} else {
			draggedOver = false;
		}
	};
	const onDragLeave = () => {
		draggedOver = false;
	};
	const onDrop = async (e) => {
		e.preventDefault();
		if (e.dataTransfer?.files) {
			const inputFiles = Array.from(e.dataTransfer?.files);
			if (inputFiles && inputFiles.length > 0) {
				inputFilesHandler(inputFiles);
			}
		}
		draggedOver = false;
	};

	let touchstart;
	let touchend;
	function checkDirection() {
		const screenWidth = window.innerWidth;
		const swipeDistance = Math.abs(touchend.screenX - touchstart.screenX);
		if (touchstart.clientX < 40 && swipeDistance >= screenWidth / 8) {
			if (touchend.screenX < touchstart.screenX) {
				showSidebar.set(false);
			}
			if (touchend.screenX > touchstart.screenX) {
				showSidebar.set(true);
			}
		}
	}
	const onTouchStart = (e) => {
		touchstart = e.changedTouches[0];
	};
	const onTouchEnd = (e) => {
		touchend = e.changedTouches[0];
		checkDirection();
	};
	const onKeyDown = (e) => {
		if (e.key === 'Shift') {
			shiftKey = true;
		}
	};
	const onKeyUp = (e) => {
		if (e.key === 'Shift') {
			shiftKey = false;
		}
	};
	const onFocus = () => {};
	const onBlur = () => {
		shiftKey = false;
		selectedChatId = null;
	};

	onMount(async () => {
		showPinnedChat = localStorage?.showPinnedChat ? localStorage.showPinnedChat === 'true' : true;
		mobile.subscribe((value) => {
			if ($showSidebar && value) {
				showSidebar.set(false);
			}
			if ($showSidebar && !value) {
				const navElement = document.getElementsByTagName('nav')[0];
				if (navElement) {
					navElement.style['-webkit-app-region'] = 'drag';
				}
			}
			if (!$showSidebar && !value) {
				showSidebar.set(true);
			}
		});
		showSidebar.set(!$mobile ? localStorage.sidebar === 'true' : false);
		showSidebar.subscribe((value) => {
			localStorage.sidebar = value;
			const navElement = document.getElementsByTagName('nav')[0];
			if (navElement) {
				if ($mobile) {
					navElement.style['-webkit-app-region'] = value ? 'no-drag' : 'drag';
				} else {
					navElement.style['-webkit-app-region'] = 'drag';
				}
			}
		});
		await initChannels();
		await initChatList();
		await initRooibosFolders();
		window.addEventListener('keydown', onKeyDown);
		window.addEventListener('keyup', onKeyUp);
		window.addEventListener('touchstart', onTouchStart);
		window.addEventListener('touchend', onTouchEnd);
		window.addEventListener('focus', onFocus);
		window.addEventListener('blur-sm', onBlur);
		const dropZone = document.getElementById('sidebar');
		dropZone?.addEventListener('dragover', onDragOver);
		dropZone?.addEventListener('drop', onDrop);
		dropZone?.addEventListener('dragleave', onDragLeave);
	});

	onDestroy(() => {
		window.removeEventListener('keydown', onKeyDown);
		window.removeEventListener('keyup', onKeyUp);
		window.removeEventListener('touchstart', onTouchStart);
		window.removeEventListener('touchend', onTouchEnd);
		window.removeEventListener('focus', onFocus);
		window.removeEventListener('blur-sm', onBlur);
		const dropZone = document.getElementById('sidebar');
		dropZone?.removeEventListener('dragover', onDragOver);
		dropZone?.removeEventListener('drop', onDrop);
		dropZone?.removeEventListener('dragleave', onDragLeave);
	});
</script>

<ArchivedChatsModal
	bind:show={$showArchivedChats}
	on:change={async () => {
		await initChatList();
	}}
/>

<ChannelModal
	bind:show={showCreateChannel}
	onSubmit={async ({ name, access_control }) => {
		const res = await createNewChannel(localStorage.token, {
			name: name,
			access_control: access_control
		}).catch((error) => {
			toast.error(`${error}`);
			return null;
		});
		if (res) {
			$socket.emit('join-channels', { auth: { token: $user.token } });
			await initChannels();
			showCreateChannel = false;
		}
	}}
/>

{#if $showSidebar}
	<div
		class="{$isApp
			? ' ml-[4.5rem] md:ml-0'
			: ''} fixed md:hidden z-40 top-0 right-0 left-0 bottom-0 bg-black/60 w-full min-h-screen h-screen flex justify-center overflow-hidden overscroll-contain"
		on:mousedown={() => {
			showSidebar.set(!$showSidebar);
		}}
	/>
{/if}

<div
	bind:this={navElement}
	id="sidebar"
	class="h-screen max-h-[100dvh] min-h-screen select-none {$showSidebar
		? 'md:relative w-[260px] max-w-[260px]'
		: '-translate-x-[260px] w-[0px]'} {$isApp
		? `ml-[4.5rem] md:ml-0 `
		: 'transition-width duration-200 ease-in-out'} shrink-0 bg-gray-50 text-gray-900 dark:bg-gray-950 dark:text-gray-200 text-sm fixed z-50 top-0 left-0 overflow-x-hidden"
	data-state={$showSidebar}
>
	<div
		class="py-2 my-auto flex flex-col justify-between h-screen max-h-[100dvh] w-[260px] overflow-x-hidden z-50 {$showSidebar
			? ''
			: 'invisible'}"
	>
		<div class="px-1.5 flex justify-between space-x-1 text-gray-600 dark:text-gray-400">
			<button
				class="cursor-pointer p-[7px] flex rounded-xl hover:bg-gray-100 dark:hover:bg-gray-900 transition"
				on:click={() => {
					showSidebar.set(!$showSidebar);
				}}
			>
				<div class="m-auto self-center">
					<svg
						xmlns="http://www.w3.org/2000/svg"
						fill="none"
						viewBox="0 0 24 24"
						stroke-width="2"
						stroke="currentColor"
						class="size-5"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25H12"
						/>
					</svg>
				</div>
			</button>
			<a
				id="sidebar-new-chat-button"
				class="flex justify-between items-center flex-1 rounded-lg px-2 py-1 h-full text-right hover:bg-gray-100 dark:hover:bg-gray-900 transition no-drag-region"
				href="/"
				draggable="false"
				on:click={async () => {
					selectedChatId = null;
					await goto('/');
					const newChatButton = document.getElementById('new-chat-button');
					setTimeout(() => {
						newChatButton?.click();
						if ($mobile) {
							showSidebar.set(false);
						}
					}, 0);
				}}
			>
				<div class="flex items-center">
					<div class="self-center mx-1.5">
						<img
							crossorigin="anonymous"
							src="{WEBUI_BASE_URL}/static/favicon.png"
							class="size-5 -translate-x-1.5 rounded-full"
							alt="logo"
						/>
					</div>
					<div class="self-center font-medium text-sm text-gray-850 dark:text-white font-primary">
						{$i18n.t('New Chat')}
					</div>
				</div>
				<div>
					<PencilSquare className="size-5" strokeWidth="2" />
				</div>
			</a>
		</div>

		{#if $user?.role === 'admin' || $user?.permissions?.workspace?.models || $user?.permissions?.workspace?.knowledge || $user?.permissions?.workspace?.prompts || $user?.permissions?.workspace?.tools}
			<div class="px-1.5 flex justify-center text-gray-800 dark:text-gray-200">
				<a
					class="grow flex items-center space-x-3 rounded-lg px-2 py-[7px] hover:bg-gray-100 dark:hover:bg-gray-900 transition"
					href="/workspace"
					on:click={() => {
						selectedChatId = null;
						chatId.set('');
						if ($mobile) {
							showSidebar.set(false);
						}
					}}
					draggable="false"
				>
					<div class="self-center">
						<svg
							xmlns="http://www.w3.org/2000/svg"
							fill="none"
							viewBox="0 0 24 24"
							stroke-width="2"
							stroke="currentColor"
							class="size-[1.1rem]"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								d="M13.5 16.875h3.375m0 0h3.375m-3.375 0V13.5m0 3.375v3.375M6 10.5h2.25a2.25 2.25 0 0 0 2.25-2.25V6a2.25 2.25 0 0 0-2.25-2.25H6A2.25 2.25 0 0 0 3.75 6v2.25A2.25 2.25 0 0 0 6 10.5Zm0 9.75h2.25A2.25 2.25 0 0 0 10.5 18v-2.25a2.25 2.25 0 0 0-2.25-2.25H6a2.25 2.25 0 0 0-2.25 2.25V18A2.25 2.25 0 0 0 6 20.25Zm9.75-9.75H18a2.25 2.25 0 0 0 2.25-2.25V6A2.25 2.25 0 0 0 18 3.75h-2.25A2.25 2.25 0 0 0 13.5 6v2.25a2.25 2.25 0 0 0 2.25 2.25Z"
							/>
						</svg>
					</div>
					<div class="flex self-center translate-y-[0.5px]">
						<div class="self-center font-medium text-sm font-primary">{$i18n.t('Workspace')}</div>
					</div>
				</a>
			</div>
			<div class="px-1.5 flex justify-center text-gray-800 dark:text-gray-200">
				<a
					class="flex-grow flex space-x-3 rounded-lg px-2 py-[7px] hover:bg-gray-100 dark:hover:bg-gray-900 transition"
					href="/rooibos/corpsearch"
					on:click={() => {
						selectedChatId = null;
						chatId.set('');
						if ($mobile) {
							showSidebar.set(false);
						}
					}}
					draggable="false"
				>
					<div class="self-center">
						<svg
							xmlns="http://www.w3.org/2000/svg"
							fill="none"
							viewBox="0 0 24 24"
							stroke-width="2"
							stroke="currentColor"
							class="size-[1.1rem]"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								d="M3.75 21h16.5M4.5 3h15M5.25 3v18m13.5-18v18M9 6.75h1.5m-1.5 3h1.5m-1.5 3h1.5m3-6H15m-1.5 3H15m-1.5 3H15M9 21v-3.375c0-.621.504-1.125 1.125-1.125h3.75c.621 0 1.125.504 1.125 1.125V21"
							/>
						</svg>
					</div>
					<div class="flex self-center">
						<div class="self-center font-medium text-sm font-primary">기업 찾기</div>
					</div>
				</a>
			</div>
			<div class="px-1.5 flex justify-center text-gray-800 dark:text-gray-200">
				<div class="flex self-center w-full">
					<RooibosFolder
						collapsible={!search}
						className="w-full flex justify-between items-center"
						name="나의 기업"
						onAdd={() => createRooibosFolder('Untitled', 'corp')}
						onAddLabel={$i18n.t('New Folder')}
						open={false}
					>
						<RooibosFolderMenu
							folders={Object.values(rooibosFolders)
								.filter((folder) => folder.type === 'corp')
								.reduce((acc, folder) => {
									acc[folder.id] = folder;
									return acc;
								}, {})}
							parentId={null}
						/>
					</RooibosFolder>
				</div>
			</div>
			
			<!-- Notes 폴더 컴포넌트 추가 -->
			
			<!-- <RooibosFolder
				collapsible={!search}
				className="px-2 mt-0.5"
				name={$i18n.t('Notes')}
				onAdd={() => createRooibosFolder('Untitled', 'note')}
				onAddLabel={$i18n.t('New Folder')}
				open={false}
			>
				<RooibosFolderMenu
					folders={Object.values(rooibosFolders)
						.filter((folder) => folder.type === 'note')
						.reduce((acc, folder) => {
							acc[folder.id] = folder;
							return acc;
						}, {})}
					parentId={null}
				/>
			</RooibosFolder> -->
			
		{/if}

		<div class="relative {$temporaryChatEnabled ? 'opacity-20' : ''}">
			{#if $temporaryChatEnabled}
				<div class="absolute z-40 w-full h-full flex justify-center"></div>
			{/if}
			<SearchInput
				bind:value={search}
				on:input={searchDebounceHandler}
				placeholder={$i18n.t('Search')}
			/>
		</div>

		<div
			class="relative flex flex-col flex-1 overflow-y-auto overflow-x-hidden {$temporaryChatEnabled
				? 'opacity-20'
				: ''}"
		>
			{#if $config?.features?.enable_channels && ($user.role === 'admin' || $channels.length > 0) && !search}
				<Folder
					className="px-2 mt-0.5"
					name={$i18n.t('Channels')}
					dragAndDrop={false}
					onAdd={async () => {
						if ($user.role === 'admin') {
							await tick();
							setTimeout(() => {
								showCreateChannel = true;
							}, 0);
						}
					}}
					onAddLabel={$i18n.t('Create Channel')}
				>
					{#each $channels as channel}
						<ChannelItem
							{channel}
							onUpdate={async () => {
								await initChannels();
							}}
						/>
					{/each}
				</Folder>
			{/if}

			<!-- Chats 폴더 컴포넌트 -->
			<Folder
				collapsible={!search}
				className="px-2 mt-0.5"
				name={$i18n.t('Chats')}
				onAdd={() => {
					createFolder();
				}}
				onAddLabel={$i18n.t('New Folder')}
				on:import={(e) => {
					importChatHandler(e.detail);
				}}
				on:drop={async (e) => {
					// Chats 폴더 drop 이벤트 처리
				}}
			>
				{#if $temporaryChatEnabled}
					<div class="absolute z-40 w-full h-full flex justify-center"></div>
				{/if}
				{#if !search && $pinnedChats.length > 0}
					<div class="flex flex-col space-y-1 rounded-xl">
						<Folder
							bind:open={showPinnedChat}
							on:change={(e) => {
								localStorage.setItem('showPinnedChat', e.detail);
							}}
							on:import={(e) => {
								importChatHandler(e.detail, true);
							}}
							on:drop={async (e) => {
								const { type, id, item } = e.detail;
								if (type === 'chat') {
									let chat = await getChatById(localStorage.token, id).catch((error) => null);
									if (!chat && item) {
										chat = await importChat(localStorage.token, item.chat, item?.meta ?? {});
									}
									if (chat) {
										if (chat.folder_id) {
											await updateChatFolderIdById(localStorage.token, chat.id, null).catch(
												(error) => {
													toast.error(`${error}`);
													return null;
												}
											);
										}
										if (!chat.pinned) {
											await toggleChatPinnedStatusById(localStorage.token, chat.id);
										}
										initChatList();
									}
								}
							}}
							name={$i18n.t('Pinned')}
						>
							<div
								class="ml-3 pl-1 mt-[1px] flex flex-col overflow-y-auto scrollbar-hidden border-s border-gray-100 dark:border-gray-900"
							>
								{#each $pinnedChats as chat, idx}
									<ChatItem
										id={chat.id}
										title={chat.title}
										{shiftKey}
										selected={selectedChatId === chat.id}
										on:select={() => {
											selectedChatId = chat.id;
										}}
										on:unselect={() => {
											selectedChatId = null;
										}}
										on:change={async () => {
											initChatList();
										}}
										on:tag={(e) => {
											const { type, name } = e.detail;
											tagEventHandler(type, name, chat.id);
										}}
									/>
								{/each}
							</div>
						</Folder>
					</div>
				{/if}

				{#if !search && folders}
					<Folders
						{folders}
						on:import={(e) => {
							const { folderId, items } = e.detail;
							importChatHandler(items, false, folderId);
						}}
						on:update={async (e) => {
							initChatList();
						}}
						on:change={async () => {
							initChatList();
						}}
					/>
				{/if}

				<div class="flex-1 flex flex-col overflow-y-auto scrollbar-hidden">
					<div class="pt-1.5">
						{#if $chats}
							{#each $chats as chat, idx}
								{#if idx === 0 || (idx > 0 && chat.time_range !== $chats[idx - 1].time_range)}
									<div
										class="w-full pl-2.5 text-xs text-gray-500 dark:text-gray-500 font-medium {idx ===
										0
											? ''
											: 'pt-5'} pb-1.5"
									>
										{$i18n.t(chat.time_range)}
									</div>
								{/if}
								<ChatItem
									id={chat.id}
									title={chat.title}
									{shiftKey}
									selected={selectedChatId === chat.id}
									on:select={() => {
										selectedChatId = chat.id;
									}}
									on:unselect={() => {
										selectedChatId = null;
									}}
									on:change={async () => {
										initChatList();
									}}
									on:tag={(e) => {
										const { type, name } = e.detail;
										tagEventHandler(type, name, chat.id);
									}}
								/>
							{/each}
							{#if $scrollPaginationEnabled && !allChatsLoaded}
								<Loader
									on:visible={(e) => {
										if (!chatListLoading) loadMoreChats();
									}}
								>
									<div
										class="w-full flex justify-center py-1 text-xs animate-pulse items-center gap-2"
									>
										<Spinner className="size-4" />
										<div>Loading...</div>
									</div>
								</Loader>
							{/if}
						{:else}
							<div class="w-full flex justify-center py-1 text-xs animate-pulse items-center gap-2">
								<Spinner className="size-4" />
								<div>Loading...</div>
							</div>
						{/if}
					</div>
				</div>
			</Folder>
		</div>

		<div class="px-2">
			<div class="flex flex-col font-primary">
				{#if $user !== undefined}
					<UserMenu
						role={$user.role}
						on:show={(e) => {
							if (e.detail === 'archived-chat') {
								showArchivedChats.set(true);
							}
						}}
					>
						<button
							class="flex items-center rounded-xl py-2.5 px-2.5 w-full hover:bg-gray-100 dark:hover:bg-gray-900 transition"
							on:click={() => {
								showDropdown = !showDropdown;
							}}
						>
							<div class="self-center mr-3">
								<img
									src={$user.profile_image_url}
									class="max-w-[30px] object-cover rounded-full"
									alt="User profile"
								/>
							</div>
							<div class="self-center font-medium">{$user.name}</div>
						</button>
					</UserMenu>
				{/if}
			</div>
		</div>
	</div>
</div>

<style>
	.scrollbar-hidden:active::-webkit-scrollbar-thumb,
	.scrollbar-hidden:focus::-webkit-scrollbar-thumb,
	.scrollbar-hidden:hover::-webkit-scrollbar-thumb {
		visibility: visible;
	}
	.scrollbar-hidden::-webkit-scrollbar-thumb {
		visibility: hidden;
	}
</style>
