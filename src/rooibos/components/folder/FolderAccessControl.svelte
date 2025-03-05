<script lang="ts">
	import { getContext, onMount } from 'svelte';
	const i18n = getContext('i18n');

	import { getUsers } from '$lib/apis/users';

	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import Plus from '$lib/components/icons/Plus.svelte';
	import UserCircleSolid from '$lib/components/icons/UserCircleSolid.svelte';
	import XMark from '$lib/components/icons/XMark.svelte';
	import Badge from '$lib/components/common/Badge.svelte';
	import { WEBUI_API_BASE_URL } from '$lib/constants';

	export let onChange: Function = () => {};
	export let accessControl: any = null;
	export let folder: {
		id: string;
		name: string;
		updated_at: string;
		access_control?: any;
	} | null = null;

	let selectedUserId = '';
	let users: any = [];
	let accessUsers: any = [];
	let showUserSelect = false;

	onMount(async () => {
		if (folder) {
			fetchAccessUsers();
			const allUsers = await getUsers(localStorage.token);
			users = allUsers.filter((user: any) => user.role === 'user');

			if (accessControl === null) {
				accessControl = null;
			} else {
				accessControl = {
					user_ids: accessControl?.user_ids ?? []
				};
			}
		}
	});

	async function fetchAccessUsers() {
		if (!folder) return;
		
		try {
			const res = await fetch(
				`${WEBUI_API_BASE_URL}/rooibos/folders/${folder.id}/accessControl/users`,
				{
					headers: {
						'Content-Type': 'application/json',
						Authorization: `Bearer ${localStorage.token}`
					}
				}
			);
			const result = await res.json();
			if (res.ok) {
				accessUsers = result.data;
			} else {
				console.error(result.message);
			}
		} catch (error) {
			console.error(error);
		}
	}

	async function onSelectUser() {
		if (!folder || selectedUserId === '') return;
		
		try {
			const queryParams = new URLSearchParams({
				user_id: selectedUserId
			});
			const res = await fetch(
				`${WEBUI_API_BASE_URL}/rooibos/folders/${folder.id}/accessControl/addUser?${queryParams.toString()}`,
				{
					method: 'POST',
					headers: {
						'Content-Type': 'application/json',
						Authorization: `Bearer ${localStorage.token}`
					}
				}
			);
			const result = await res.json();
			if (res.ok) {
				accessControl = result.data;
				onChange(accessControl);
				fetchAccessUsers();
				showUserSelect = true;
			} else {
				console.error(result.message);
			}
		} catch (error) {
			console.error(error);
		}
		selectedUserId = '';
	}

	async function onRemoveUser(userId: string) {
		if (!folder) return;
		
		try {
			const queryParams = new URLSearchParams({
				user_id: userId
			});
			const res = await fetch(
				`${WEBUI_API_BASE_URL}/rooibos/folders/${folder.id}/accessControl/removeUser?${queryParams.toString()}`,
				{
					method: 'POST',
					headers: {
						'Content-Type': 'application/json',
						Authorization: `Bearer ${localStorage.token}`
					}
				}
			);
			const result = await res.json();
			if (res.ok) {
				accessControl = result.data;
				onChange(accessControl);
				fetchAccessUsers();
				showUserSelect = true;
			} else {
				console.error(result.message);
			}
		} catch (error) {
			console.error(error);
		}
	}

	$: if (selectedUserId) {
		onSelectUser();
	}
</script>

<div class="rounded-lg flex flex-col gap-2">
	<div>
		<div class="flex gap-2.5 items-center mb-1">
			<div>
				<button 
					class="p-2 bg-black/5 dark:bg-white/5 rounded-full cursor-pointer hover:bg-black/10 dark:hover:bg-white/10"
					on:click={() => {
						showUserSelect = !showUserSelect;
						if (!accessControl) {
							accessControl = { user_ids: [] };
							fetchAccessUsers();
							onChange(accessControl);
						}
					}}
				>
					<!-- lock 아이콘 -->
					<svg
						xmlns="http://www.w3.org/2000/svg"
						fill="none"
						viewBox="0 0 24 24"
						stroke-width="1.5"
						stroke="currentColor"
						class="w-5 h-5"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z"
						/>
					</svg>
				</button>
			</div>
			<div>
				<div class="text-sm font-medium">공유</div>
			</div>
		</div>
	</div>

	{#if showUserSelect}
		<!-- 사용자 UI -->
		<div>
			<div class="flex justify-between mb-1.5">
				<div class="text-sm font-semibold">{$i18n.t('Users')}</div>
			</div>
			<div class="mb-1">
				<div class="flex w-full">
					<div class="flex flex-1 items-center">
						<div class="w-full px-0.5">
							<select
								class="outline-hidden bg-transparent text-sm rounded-lg block w-full pr-10 max-w-full hover:bg-gray-50 dark:hover:bg-gray-800 {selectedUserId
									? ''
									: 'text-gray-500'} hover:bg-gray-50 dark:hover:bg-gray-800"
								bind:value={selectedUserId}
							>
								<option
									class="text-gray-700 bg-gray-200 dark:bg-gray-900 hover:bg-gray-50 dark:hover:bg-gray-800"
									value=""
									disabled
									selected>공유하려는 사용자를 선택하세요</option
								>
								{#each users.filter((user) => !((accessControl?.user_ids || []).includes(user.id))) as user}
									<option
										class="text-gray-700 bg-gray-200 dark:bg-gray-900 hover:bg-gray-100 dark:hover:bg-gray-800"
										value={user.id}>{user.name}</option
									>
								{/each}
							</select>
						</div>
					</div>
				</div>
			</div>
			<hr class="border-gray-100 dark:border-gray-700/10 mt-1.5 mb-2.5 w-full" />
			<div class="flex flex-col gap-2 mb-1 px-0.5">
				{#if accessUsers.length > 0}
					{#each accessUsers as user}
						<div class="flex items-center gap-3 justify-between text-xs w-full transition">
							<div class="flex items-center gap-1.5 w-full font-medium">
								<div>
									<UserCircleSolid className="size-4" />
								</div>
								<div>{user.name}</div>
							</div>
							<div class="w-full flex justify-end items-center gap-0.5">
								<button type="button" on:click={() => {}}>
									<Badge type={'info'} content={$i18n.t('Read')} />
								</button>
								<button
									class="rounded-full p-1 hover:bg-gray-100 dark:hover:bg-gray-850 transition"
									type="button"
									on:click={() => onRemoveUser(user.id)}
								>
									<XMark />
								</button>
							</div>
						</div>
					{/each}
				{:else}
					<div class="flex items-center justify-center">
						<div class="text-gray-500 text-xs text-center py-2 px-10">
							{$i18n.t('No users with access, add a user to grant access')}
						</div>
					</div>
				{/if}
			</div>
		</div>
	{/if}
</div>
