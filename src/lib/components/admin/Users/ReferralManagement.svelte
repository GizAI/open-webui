<script lang="ts">
	import { getContext, onMount } from 'svelte';
	import dayjs from 'dayjs';
	import relativeTime from 'dayjs/plugin/relativeTime';
	import localizedFormat from 'dayjs/plugin/localizedFormat';
	dayjs.extend(relativeTime);
	dayjs.extend(localizedFormat);

	import { toast } from 'svelte-sonner';
	import { updateUserRole, deleteUserById, getReferredUsers } from '$lib/apis/users';
	import Badge from '$lib/components/common/Badge.svelte';
	import ChevronUp from '$lib/components/icons/ChevronUp.svelte';
	import ChevronDown from '$lib/components/icons/ChevronDown.svelte';
	import ConfirmDialog from '$lib/components/common/ConfirmDialog.svelte';

	interface User {
		id: string;
		name: string;
		email: string;
		role: string;
		last_active_time?: string;
		created_at: string;
		[key: string]: any;
	}

	const i18n = getContext('i18n');

	export let show = false;
	export let referralUsers: User[] = [];

	let isLoading = false;

	let showDeleteConfirmDialog = false;
	let selectedUser: User | null = null;

	let sortKey: keyof User = 'created_at';
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

	function setSortKey(key: keyof User): void {
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
		class="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-full max-w-4xl bg-white dark:bg-gray-900 rounded-lg shadow-lg p-6"
	>
		<div class="flex justify-between items-center mb-6">
			<h2 class="text-xl font-semibold dark:text-white">{$i18n.t('Referral Management')}</h2>
			<button
				class="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
				on:click={() => (show = false)}
			>
				<svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
				</svg>
			</button>
		</div>

		<div class="overflow-x-auto">
			{#if isLoading}
				<div class="flex justify-center p-4">
					<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 dark:border-white"></div>
				</div>
			{:else}
				<table class="w-full text-sm text-left text-gray-500 dark:text-gray-400">
					<thead class="text-xs text-gray-700 uppercase bg-gray-50 dark:bg-gray-850 dark:text-gray-400">
						<tr>
							<th class="px-3 py-2 cursor-pointer" on:click={() => setSortKey('role')}>
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
							<th class="px-3 py-2 cursor-pointer" on:click={() => setSortKey('name')}>
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
							<th class="px-3 py-2 cursor-pointer" on:click={() => setSortKey('email')}>
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
							<th class="px-3 py-2 cursor-pointer" on:click={() => setSortKey('last_active_time')}>
								<div class="flex items-center">
									{$i18n.t('Last Active')}
									{#if sortKey === 'last_active_time'}
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
							<th class="px-3 py-2 cursor-pointer" on:click={() => setSortKey('created_at')}>
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
							<th class="px-3 py-2">{$i18n.t('Actions')}</th>
						</tr>
					</thead>
					<tbody>
						{#each sortedUsers as user (user.id)}
							<tr class="bg-white dark:bg-gray-900 dark:border-gray-850 text-xs">
								<td class="px-3 py-2">
									<button
										class="px-2 py-1 rounded text-xs font-medium"
										class:bg-blue-100={user.role === 'pending'}
										class:text-blue-800={user.role === 'pending'}
										class:bg-gray-100={user.role === 'user'}
										class:text-gray-800={user.role === 'user'}
										on:click={() => {
											const newRole = user.role === 'user' ? 'pending' : 'user';
											updateRoleHandler(user.id, newRole);
										}}
									>
										{user.role}
									</button>
								</td>
								<td class="px-3 py-2">{user.name}</td>
								<td class="px-3 py-2">{user.email}</td>
								<td class="px-3 py-2">
									{#if user.last_active_time}
										{dayjs(user.last_active_time).fromNow()}
									{:else}
										-
									{/if}
								</td>
								<td class="px-3 py-2">{dayjs(user.created_at).format('L LT')}</td>
								<td class="px-3 py-2">
									<button
										class="text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300"
										on:click={() => {
											selectedUser = user;
											showDeleteConfirmDialog = true;
										}}
									>
										<svg
											class="w-4 h-4"
											fill="none"
											stroke="currentColor"
											viewBox="0 0 24 24"
										>
											<path
												stroke-linecap="round"
												stroke-linejoin="round"
												stroke-width="2"
												d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
											/>
										</svg>
									</button>
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
			{/if}
		</div>
	</div>
{/if}

<ConfirmDialog
	show={showDeleteConfirmDialog}
	title={$i18n.t('Delete User')}
	message={$i18n.t('Are you sure you want to delete this user?')}
	onConfirm={() => {
		if (selectedUser) {
			deleteUserHandler(selectedUser.id);
		}
		showDeleteConfirmDialog = false;
		selectedUser = null;
	}}
	onCancel={() => {
		showDeleteConfirmDialog = false;
		selectedUser = null;
	}}
/>
