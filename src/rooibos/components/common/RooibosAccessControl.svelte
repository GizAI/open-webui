<script lang="ts">
	import { getContext, onMount } from 'svelte';
	const i18n = getContext('i18n');

	// 그룹 관련 API는 사용하지 않으므로 주석 처리
	// import { getGroups } from '$lib/apis/groups';
	import { getUsers } from '$lib/apis/users';

	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import Plus from '$lib/components/icons/Plus.svelte';
	import UserCircleSolid from '$lib/components/icons/UserCircleSolid.svelte';
	import XMark from '$lib/components/icons/XMark.svelte';
	import Badge from '$lib/components/common/Badge.svelte';
	import { WEBUI_API_BASE_URL } from '$lib/constants';

	export let onChange: Function = () => {};
	export let bookmarkId: any = null;
	export let accessControl: any = null;

	let selectedUserId = '';
	let users: any = [];
	let accessUsers: any = [];

	onMount(async () => {
		fetchAccessUsers();
		const allUsers = await getUsers(localStorage.token);
		users = allUsers.filter(user => user.role === 'user');

		if (accessControl === null) {
			accessControl = null;
		} else {
			accessControl = {
				user_ids: accessControl?.user_ids ?? []
			};
		}
	});

	async function fetchAccessUsers() {
		try {
			const res = await fetch(`${WEBUI_API_BASE_URL}/rooibos/corpbookmarks/${bookmarkId}/accessControl/users`, {
				headers: {
					'Content-Type': 'application/json',
					'Authorization': `Bearer ${localStorage.token}`
				}
			});
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
		if (selectedUserId !== '') {
			try {
				const queryParams = new URLSearchParams({
					user_id: selectedUserId
				});
				const res = await fetch(`${WEBUI_API_BASE_URL}/rooibos/corpbookmarks/${bookmarkId}/accessControl/addUser?${queryParams.toString()}`, {
					method: 'POST',
					headers: {
						'Content-Type': 'application/json',
						'Authorization': `Bearer ${localStorage.token}`
					}
				});
				const result = await res.json();
				if (res.ok) {
					accessControl = result.data;
					onChange(accessControl);
					fetchAccessUsers();
				} else {
					console.error(result.message);
				}
			} catch (error) {
				console.error(error);
			}
			selectedUserId = '';
		}
	}

	async function onRemoveUser(userId: string) {
		try {
			const queryParams = new URLSearchParams({
				user_id: userId
			});
			const res = await fetch(`${WEBUI_API_BASE_URL}/rooibos/corpbookmarks/${bookmarkId}/accessControl/removeUser?${queryParams.toString()}`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					'Authorization': `Bearer ${localStorage.token}`
				}
			});
			const result = await res.json();
			if (res.ok) {
				accessControl = result.data;
				onChange(accessControl);
				fetchAccessUsers();
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
		<div class="text-sm font-semibold mb-1">{$i18n.t('Visibility')}</div>
		<div class="flex gap-2.5 items-center mb-1">
			<div>
				<div class="p-2 bg-black/5 dark:bg-white/5 rounded-full">
					{#if accessControl !== null}
						<!-- private 아이콘 -->
						<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5">
							<path stroke-linecap="round" stroke-linejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
						</svg>
					{:else}
						<!-- public 아이콘 -->
						<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5">
							<path stroke-linecap="round" stroke-linejoin="round" d="M6.115 5.19l.319 1.913A6 6 0 008.11 10.36L9.75 12l-.387.775c-.217.433-.132.956.21 1.298l1.348 1.348c.21.21.329.497.329.795v1.089c0 .426.24.815.622 1.006l.153.076c.433.217.956.132 1.298-.21l.723-.723a8.7 8.7 0 002.288-4.042 1.087 1.087 0 00-.358-1.099l-1.33-1.108c-.251-.21-.582-.299-.905-.245l-1.17.195a1.125 1.125 0 01-.98-.314l-.295-.295a1.125 1.125 0 010-1.591l.13-.132a1.125 1.125 0 011.3-.21l.603.302a.809.809 0 001.086-1.086L14.25 7.5l1.256-.837a4.5 4.5 0 001.528-1.732l.146-.292M6.115 5.19A9 9 0 1017.18 4.64M6.115 5.19A8.965 8.965 0 0112 3c1.929 0 3.716.607 5.18 1.64" />
						</svg>
					{/if}
				</div>
			</div>
			<div>
				<select
					id="models"
					class="outline-hidden bg-transparent text-sm font-medium rounded-lg block w-fit pr-10 max-w-full placeholder-gray-400"
					value={accessControl !== null ? 'private' : 'public'}
					on:change={(e) => {
						if (e.target.value === 'public') {
							accessControl = null;
						} else {
							accessControl = { user_ids: [] };
							// private 모드이면 access_control 유저 fetch
							fetchAccessUsers();
						}
						onChange(accessControl);
					}}
				>
					<option class="text-gray-700" value="private" selected>Private</option>
					<option class="text-gray-700" value="public" selected>Public</option>
				</select>
				<div class="text-xs text-gray-400 font-medium">
					{#if accessControl !== null}
						{$i18n.t('Only select users with permission can access')}
					{:else}
						{$i18n.t('Accessible to all users')}
					{/if}
				</div>
			</div>
		</div>
	</div>

	{#if accessControl !== null}
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
								class="outline-hidden bg-transparent text-sm rounded-lg block w-full pr-10 max-w-full {selectedUserId ? '' : 'text-gray-500'} dark:placeholder-gray-500"
								bind:value={selectedUserId}
							>
								<option class="text-gray-700" value="" disabled selected>{$i18n.t('Select a user')}</option>
								{#each users.filter((user) => !accessControl.user_ids.includes(user.id)) as user}
									<option class="text-gray-700" value={user.id}>{user.name}</option>
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
								<button
									type="button"
									on:click={() => {
										// 필요 시 write 권한 토글 로직 구현
									}}
								>
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
