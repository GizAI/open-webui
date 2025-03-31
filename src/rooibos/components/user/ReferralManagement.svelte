<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import dayjs from 'dayjs';
	import relativeTime from 'dayjs/plugin/relativeTime';
	import localizedFormat from 'dayjs/plugin/localizedFormat';
	
	dayjs.extend(relativeTime);
	dayjs.extend(localizedFormat);

	import { WEBUI_NAME, config, user, showSidebar } from '$lib/stores';
	import { toast } from 'svelte-sonner';
	import { updateUserRole, deleteUserById, getReferredUsers } from '$lib/apis/users';
	import Badge from '$lib/components/common/Badge.svelte';
	import ChevronUp from '$lib/components/icons/ChevronUp.svelte';
	import ChevronDown from '$lib/components/icons/ChevronDown.svelte';
	import ConfirmDialog from '$lib/components/common/ConfirmDialog.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import ChatBubbles from '$lib/components/icons/ChatBubbles.svelte';
	import UserChatsModal from '$lib/components/admin/Users/UserList/UserChatsModal.svelte';

	const i18n = getContext('i18n');

	export let show = false;
	export let referralUsers: any[] = [];

	let showUserChatsModal = false;

	let isLoading = false;

	let showDeleteConfirmDialog = false;
	let selectedUser: any | null = null;

	let sortKey: keyof any = 'created_at';
	let sortOrder: 'asc' | 'desc' = 'asc';

	// 추천된 사용자 목록 로드
	async function loadReferredUsers(): Promise<void> {
		if (!show) return;
		
		isLoading = true;
		try {
			referralUsers = await getReferredUsers(localStorage.token);
		} catch (error) {
			console.error('Failed to load referral users:', error);
			toast.error('Failed to load referral users');
		} finally {
			isLoading = false;
		}
	}

	// 컴포넌트가 표시될 때마다 데이터 로드
	$: if (show) {
		loadReferredUsers();
	}

	function setSortKey(key: keyof any): void {
		if (sortKey === key) {
			sortOrder = sortOrder === 'asc' ? 'desc' : 'asc';
		} else {
			sortKey = key;
			sortOrder = 'asc';
		}
	}

	const updateRoleHandler = async (id: string, role: string): Promise<void> => {
		const res = await updateUserRole(localStorage.token, id, role).catch((error) => {
			toast.error(`${error}`);
			return null;
		});

		if (res) {
			// Refresh the user list after update
			const index = referralUsers.findIndex(u => u.id === id);
			if (index !== -1) {
				referralUsers[index].role = role;
				referralUsers = [...referralUsers];
			}
		}
	};

	const deleteUserHandler = async (id: string): Promise<void> => {
		const res = await deleteUserById(localStorage.token, id).catch((error) => {
			toast.error(`${error}`);
			return null;
		});
		if (res) {
			referralUsers = referralUsers.filter(u => u.id !== id);
		}
	};

	$: sortedUsers = referralUsers
		.sort((a, b) => {
			if (a[sortKey] < b[sortKey]) return sortOrder === 'asc' ? -1 : 1;
			if (a[sortKey] > b[sortKey]) return sortOrder === 'asc' ? 1 : -1;
			return 0;
		});
</script>

{#if show}
	<div class="fixed inset-0 bg-black/50 z-40" on:click={() => (show = false)} />
	<div
		class="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-full max-h-[90vh] overflow-y-auto max-w-4xl bg-white dark:bg-gray-900 rounded-lg shadow-lg p-3 md:p-6"
	>
		<div class="flex justify-between items-center mb-4 md:mb-6 sticky top-0 bg-white dark:bg-gray-900 py-2 z-10">
			<h2 class="text-lg md:text-xl font-semibold dark:text-white">{$i18n.t('Referral Management')}</h2>
			<button
				class="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
				on:click={() => (show = false)}
				aria-label="Close"
			>
				<svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
				</svg>
			</button>
		</div>

		<div class="overflow-x-auto -mx-3 px-3">
			{#if isLoading}
				<div class="flex justify-center p-4">
					<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 dark:border-white"></div>
				</div>
			{:else}
				<div class="relative overflow-x-auto rounded-lg shadow-sm">
					<table class="w-full text-sm text-left text-gray-500 dark:text-gray-400 min-w-full">
						<thead class="text-xs text-gray-700 uppercase bg-gray-50 dark:bg-gray-850 dark:text-gray-400 sticky top-0">
							<tr>
								<th class="px-2 md:px-3 py-2 cursor-pointer whitespace-nowrap hidden md:table-cell" on:click={() => setSortKey('role')}>
									<div class="flex items-center">
										{$i18n.t('Role')}
										{#if sortKey === 'role'}
											<span class="ml-1">
												{#if sortOrder === 'asc'}
													<ChevronUp className="w-4 h-4" />
												{:else}
													<ChevronDown className="w-4 h-4" />
												{/if}
											</span>
										{/if}
									</div>
								</th>
								<th class="px-2 md:px-3 py-2 cursor-pointer whitespace-nowrap" on:click={() => setSortKey('name')}>
									<div class="flex items-center">
										{$i18n.t('Name')}
										{#if sortKey === 'name'}
											<span class="ml-1">
												{#if sortOrder === 'asc'}
													<ChevronUp className="w-4 h-4" />
												{:else}
													<ChevronDown className="w-4 h-4" />
												{/if}
											</span>
										{/if}
									</div>
								</th>
								<th class="px-2 md:px-3 py-2 cursor-pointer whitespace-nowrap" on:click={() => setSortKey('email')}>
									<div class="flex items-center">
										{$i18n.t('Email')}
										{#if sortKey === 'email'}
											<span class="ml-1">
												{#if sortOrder === 'asc'}
													<ChevronUp className="w-4 h-4" />
												{:else}
													<ChevronDown className="w-4 h-4" />
												{/if}
											</span>
										{/if}
									</div>
								</th>
								<th class="px-2 md:px-3 py-2 cursor-pointer whitespace-nowrap hidden md:table-cell" on:click={() => setSortKey('last_active_at')}>
									<div class="flex items-center">
										{$i18n.t('Last Active')}
										{#if sortKey === 'last_active_at'}
											<span class="ml-1">
												{#if sortOrder === 'asc'}
													<ChevronUp className="w-4 h-4" />
												{:else}
													<ChevronDown className="w-4 h-4" />
												{/if}
											</span>
										{/if}
									</div>
								</th>
								<th class="px-2 md:px-3 py-2 cursor-pointer whitespace-nowrap" on:click={() => setSortKey('created_at')}>
									<div class="flex items-center">
										{$i18n.t('Created')}
										{#if sortKey === 'created_at'}
											<span class="ml-1">
												{#if sortOrder === 'asc'}
													<ChevronUp className="w-4 h-4" />
												{:else}
													<ChevronDown className="w-4 h-4" />
												{/if}
											</span>
										{/if}
									</div>
								</th>
							</tr>
						</thead>
						<tbody>
							{#each sortedUsers as user (user.id)}
								<tr class="bg-white dark:bg-gray-900 dark:border-gray-850 text-xs hover:bg-gray-50 dark:hover:bg-gray-850">
									<td class="px-2 md:px-3 py-2 min-w-[5rem] md:min-w-[7rem] md:w-28 hidden md:table-cell">
										<button
											class="translate-y-0.5"
											on:click={() => {
												const newRole = user.role === 'user' ? 'pending' : 'user';
												updateRoleHandler(user.id, newRole);
											}}
										>
											<Badge
												type={user.role === 'admin' ? 'info' : user.role === 'user' ? 'success' : 'muted'}
												content={$i18n.t(user.role)}
											/>
										</button>
									</td>
									<td class="px-2 md:px-3 py-2 truncate max-w-[100px] md:max-w-none">{user.name}</td>
									<td class="px-2 md:px-3 py-2 truncate max-w-[150px]">{user.email}</td>
									<td class="px-2 md:px-3 py-1 whitespace-nowrap text-xs hidden md:table-cell">
										{dayjs(user.last_active_at * 1000).fromNow()}
									</td>
									<td class="px-2 md:px-3 py-1 whitespace-nowrap text-xs">
										{dayjs(user.created_at * 1000).format('LL')}
									</td>
								</tr>
							{:else}
								<tr class="bg-white dark:bg-gray-900">
									<td colspan="6" class="px-3 py-4 text-center text-gray-500 dark:text-gray-400">
										추천인 데이터가 없습니다.
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{/if}
		</div>
	</div>
{/if}
<UserChatsModal bind:show={showUserChatsModal} user={selectedUser} />
<ConfirmDialog
	show={showDeleteConfirmDialog}
	title="사용자삭제"
	message="사용자를 삭제하시겠습니까?"
	onConfirm={() => {
		if (selectedUser) {
			deleteUserHandler(selectedUser.id);
		}
		showDeleteConfirmDialog = false;
		selectedUser = null;
	}}
	on:cancel={() => {
		showDeleteConfirmDialog = false;
		selectedUser = null;
	}}
/>
